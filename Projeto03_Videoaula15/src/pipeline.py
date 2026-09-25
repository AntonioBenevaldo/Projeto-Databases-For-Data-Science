"""Coordenacao local: parametros, dependencias, retries, auditoria e publicacao."""
import time
import uuid
import platform
import importlib.metadata
from pathlib import Path
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from src.config import pasta,ROOT
from src.db import bancos,checkpoint
from src.extract import extrair,QUERY
from src.validate import validar
from src.transform import transformar
from src.load import carregar,Concorrencia
from src.observe import log,salvar,utc,relatorio,hash_file

class FalhaTransitoria(RuntimeError):pass

def transitoria(exc):
    if isinstance(exc,(FalhaTransitoria,Concorrencia)):return True
    return isinstance(exc,OperationalError) and any(t in str(exc).lower() for t in ['database is locked','database is busy'])

def executar(base,limite=100,desde=None,tentativas=3,espera=1.0,falha='nenhuma',exportar=True):
    base=pasta(base)
    if limite<1 or limite>10000:raise ValueError('--limite deve estar entre 1 e 10000.')
    if tentativas<1 or tentativas>10:raise ValueError('--tentativas deve estar entre 1 e 10.')
    if espera<0 or espera>30:raise ValueError('--espera deve estar entre 0 e 30 segundos.')
    if desde is not None and desde<0:raise ValueError('--desde-evento nao pode ser negativo.')
    run_id=uuid.uuid4().hex[:16];start=time.monotonic();inicio=utc()
    run_dir=base/'outputs/execucoes'/run_id;run_dir.mkdir()
    with bancos(base) as (origem,destino):
        # Falhas antes deste registro (banco nao preparado/disco inacessivel) sao exibidas no terminal.
        with destino.begin() as conn:
            conn.execute(text("INSERT INTO execucoes(run_id,inicio_utc,status) VALUES(:run,:inicio,'executando')"),{'run':run_id,'inicio':inicio})
        log(base,run_id,'inicio',limite=limite,desde_evento=desde)
        try:
            for attempt in range(1,tentativas+1):
                try:
                    old=checkpoint(destino)
                    lower=old if desde is None else desde
                    if lower>old:raise ValueError('--desde-evento nao pode ultrapassar o checkpoint; isso pularia eventos.')
                    if falha=='transitoria' and attempt==1:raise FalhaTransitoria('Falha transitoria simulada na extracao.')
                    raw,top=extrair(origem,lower,limite)
                    if top<old:raise ValueError('Origem esta atras do checkpoint. Nao reutilize um destino com outra origem.')
                    raw.to_csv(run_dir/'eventos_extraidos.csv',index=False)
                    log(base,run_id,'extracao',tentativa=attempt,eventos=len(raw),checkpoint=old,topo_origem=top)
                    if falha=='qualidade' and not raw.empty:raw.loc[raw.index[0],'quantidade']=-1
                    validar(raw)
                    transformed=transformar(raw)
                    transformed.to_csv(run_dir/'pedidos_transformados.csv',index=False)
                    # Avanca somente ate a ultima linha efetivamente lida, nunca ate o topo nao consumido.
                    new=int(raw.event_seq.max()) if not raw.empty else old
                    info={'fim':utc(),'tentativas':attempt,'lidos':len(raw),'duracao':time.monotonic()-start}
                    changed=carregar(destino,transformed,old,new,run_id,info,falhar=falha=='carga')
                    result={'run_id':run_id,'status':'sucesso','tentativas':attempt,'eventos_lidos':len(raw),
                        'pedidos_alterados':changed,'checkpoint_antes':old,'checkpoint_depois':max(old,new),
                        'topo_origem_na_extracao':top,'eventos_ainda_pendentes':top-max(old,new),
                        'duracao_segundos':round(time.monotonic()-start,6)}
                    break
                except Exception as exc:
                    if transitoria(exc) and attempt<tentativas:
                        delay=min(espera*(2**(attempt-1)),30)
                        log(base,run_id,'retentativa',tentativa=attempt,espera_segundos=delay,erro=str(exc))
                        print(f'RETRY {attempt}/{tentativas}: aguardar {delay:g}s.')
                        time.sleep(delay)
                    else:raise
        except Exception as exc:
            with destino.begin() as conn:
                conn.execute(text("UPDATE execucoes SET status='falha',fim_utc=:fim,tentativas=:n,duracao_segundos=:duracao,erro=:erro WHERE run_id=:run"),
                    {'fim':utc(),'n':attempt,'duracao':time.monotonic()-start,'erro':str(exc),'run':run_id})
            log(base,run_id,'falha',tipo=type(exc).__name__,erro=str(exc))
            salvar(base/'outputs/alertas'/f'{run_id}.json',{'run_id':run_id,'utc':utc(),'tipo':type(exc).__name__,'erro':str(exc),'acao':'Corrigir a causa e executar novamente. Checkpoint preservado pela transacao.'})
            raise
    # Commit ja confirmado. Falha de exportacao nao e reportada como rollback do banco.
    try:
        log(base,run_id,'commit_confirmado',**{k:v for k,v in result.items() if k!='run_id'})
        import hashlib
        salvar(run_dir/'metadados.json',{**result,'inicio_utc':inicio,'fim_utc':utc(),
            'query_sha256':hashlib.sha256(QUERY.encode()).hexdigest(),
            'arquivos_sha256':{name:hash_file(run_dir/name) for name in ['eventos_extraidos.csv','pedidos_transformados.csv']},
            'codigo_sha256':{str(p.relative_to(ROOT)):hash_file(p) for p in sorted((ROOT/'src').glob('*.py'))},
            'versoes':{p:importlib.metadata.version(p) for p in ['pandas','SQLAlchemy']},'python':platform.python_version()})
        if exportar:relatorio(base,run_id)
    except Exception as exc:
        result['aviso_exportacao']=str(exc)
        print('AVISO: carga confirmada no banco; exportacao incompleta. Execute relatorio para recuperar.')
    print('PIPELINE:',result)
    return result

def automatizar(base,intervalo=10,repeticoes=3,**kwargs):
    if intervalo<0 or repeticoes<1:raise ValueError('Intervalo >= 0; repeticoes >= 1.')
    results=[]
    print('Automacao local em primeiro plano. Ctrl+C interrompe. Primeira execucao imediata.')
    try:
        for n in range(repeticoes):
            print(f'CICLO {n+1}/{repeticoes}')
            # Falha permanente para a agenda; nao anuncia sucesso nem continua silenciosamente.
            results.append(executar(base,**kwargs))
            if n+1<repeticoes:time.sleep(intervalo)
    except KeyboardInterrupt:
        print('Automacao interrompida pelo usuario. Confira historico se a interrupcao ocorreu durante uma carga.')
        raise
    return results
