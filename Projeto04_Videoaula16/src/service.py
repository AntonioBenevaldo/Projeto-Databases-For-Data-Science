from contextlib import closing
from pathlib import Path
import json
import sqlite3
import secrets
import shutil
import uuid
from cryptography.fernet import Fernet
from src.config import ROOT,ROLES,layout
from src.security import privado,digest,autenticar,AcessoNegado,IntegridadeError
from src.audit import registrar,verificar
from src.data import inserir,INITIAL,DELTA,indicadores,ler_csv
from src.snapshot import publicar,conferir,comparar


def conectar(base):
    p=base/'data/laboratorio.db'
    if not p.exists():raise ValueError('Execute inicializar primeiro.')
    c=sqlite3.connect(p,timeout=5,isolation_level=None);c.row_factory=sqlite3.Row
    c.execute('PRAGMA foreign_keys=ON')
    return c

def inicializar(base):
    base=layout(base);db=base/'data/laboratorio.db';folder=base/'segredos'
    if db.exists():
        if not folder.exists():raise ValueError('Banco existente sem segredos. Recupere as chaves originais; nao sao regeneradas automaticamente.')
        return {'estado':'ja_inicializado','nota':'Dados e segredos existentes preservados.'}
    if folder.exists():raise ValueError('Pasta de segredos existente sem banco. Use uma pasta de estudo nova.')
    folder.mkdir(mode=0o700)
    try:
        privado(folder/'criptografia.key',Fernet.generate_key())
        privado(folder/'assinatura.key',secrets.token_hex(32).encode())
        privado(folder/'pseudonimo.key',secrets.token_hex(32).encode())
        with closing(sqlite3.connect(db)) as conn:
            conn.row_factory=sqlite3.Row
            with conn:
                for stmt in (ROOT/'src/schema.sql').read_text().split(';'):
                    if stmt.strip():conn.execute(stmt)
                for role in ROLES:
                    token=secrets.token_urlsafe(32).encode();privado(folder/f'{role}.token',token+b'\n')
                    conn.execute('INSERT INTO credenciais VALUES(?,?)',(role,digest(token)))
                inserir(conn,INITIAL)
                registrar(base,conn,'bootstrap','inicializar','sucesso',{'pedidos_simulados':6})
    except Exception:
        # Somente arquivos recem-criados por esta inicializacao incompleta.
        db.unlink(missing_ok=True);shutil.rmtree(folder);raise
    return {'estado':'inicializado','pedidos_simulados':6,'nota':'Credenciais geradas localmente em segredos; nenhum valor secreto e exibido.'}


def operar(base,conn,role,action,args,created):
    version=args.get('versao')
    if action=='publicar':return publicar(base,conn,role,args.get('inicio','2026-01-01'),args.get('fim','2026-01-31'),created)
    if action=='simular-lote':
        r=conn.execute("INSERT OR IGNORE INTO lotes VALUES('delta')")
        if r.rowcount==0:return {'atualizacoes':0,'nota':'Lote ja aplicado.'}
        inserir(conn,DELTA);return {'atualizacoes':5,'nota':'Publique outra versao para atualizar o conjunto ativo.'}
    if action=='listar':
        active=conn.execute('SELECT ativa FROM estado WHERE id=1').fetchone()[0]
        return {'ativa':active,'versoes':[dict(r) for r in conn.execute('SELECT versao,criada_utc,linhas,faturamento_centavos FROM versoes ORDER BY versao')]}
    if action=='verificar':
        m,_=conferir(base,conn,version);return {'versao':m['versao'],'integridade':'OK','linhas':m['linhas_publicadas']}
    if action=='restaurar':
        if version is None:raise ValueError('Restaurar exige --versao explicita.')
        m,_=conferir(base,conn,version)
        conn.execute('UPDATE estado SET ativa=? WHERE id=1',(m['versao'],))
        return {'ativa':m['versao'],'nota':'Referencia ativa restaurada. Origem e outras versoes preservadas.'}
    if action=='comparar':
        if not args.get('de') or not args.get('para'):raise ValueError('Comparar exige --de e --para.')
        return comparar(base,conn,args['de'],args['para'])
    if action=='consultar':
        m,buf=conferir(base,conn,version)
        rows=ler_csv(buf['dados.csv']);ind=indicadores(rows)
        out=base/'outputs'/f'consulta_{m["versao"]}_{uuid.uuid4().hex[:10]}'
        out.mkdir();created.append(out)
        (out/'dados_publicados.csv').write_bytes(buf['dados.csv'])
        (out/'indicadores.json').write_text(json.dumps(ind,indent=2),encoding='utf-8')
        lines=['# Relatorio de faturamento',f'\nVersao consultada: {m["versao"]}','\n| Indicador | Valor |','|---|---:|']
        for k,v in ind.items():lines.append(f'| {k} | {v} |')
        lines+=['\nValores monetarios em centavos. Somente pedidos concluidos.',
                'Dados simulados. Lucro bruto nao inclui tributos e outras despesas.',
                'Os contatos e identificadores originais foram excluidos desta exportacao.']
        (out/'relatorio.md').write_text('\n'.join(lines),encoding='utf-8')
        return {'versao':m['versao'],**ind,'pasta_relatorio':str(out)}
    if action=='auditoria':
        n,_=verificar(base,conn)
        rows=[json.loads(r['payload']) for r in conn.execute('SELECT payload FROM auditoria ORDER BY seq')]
        out=base/'outputs'/f'auditoria_{uuid.uuid4().hex[:10]}.json'
        out.write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8');created.append(out)
        return {'cadeia':'OK','registros_anteriores':n,'arquivo':str(out),'nota':'O registro desta leitura e acrescentado depois da exportacao.'}
    if action=='catalogo':return {n:json.loads((ROOT/'governance'/n).read_text(encoding='utf-8')) for n in ['catalogo.json','esquema.json','politicas.json']}
    raise ValueError('Acao desconhecida.')


def chamar(base,action,credencial=None,**args):
    base=layout(base)
    credential=Path(credencial) if credencial else base/'segredos/admin.token'
    created=[];role='nao_autenticado'
    with closing(conectar(base)) as conn:
        conn.execute('BEGIN IMMEDIATE')
        try:
            verificar(base,conn)
            try:role=autenticar(conn,credential,action)
            except AcessoNegado as denied:
                registrar(base,conn,denied.perfil,action,'negado')
                conn.commit();raise
            result=operar(base,conn,role,action,args,created)
            # Apenas metadados selecionados; nao registrar tokens, chaves ou contatos.
            details={k:result[k] for k in ['versao','ativa','atualizacoes','integridade'] if k in result}
            registrar(base,conn,role,action,'sucesso',details)
            conn.commit()
            return result
        except AcessoNegado:raise
        except Exception as exc:
            conn.rollback()
            for p in created:
                if p.is_dir():shutil.rmtree(p)
                else:p.unlink(missing_ok=True)
            # Em corrupcao da auditoria, falha fechada: nao reescrever nem consertar a cadeia.
            if not isinstance(exc,IntegridadeError) or 'Auditoria' not in str(exc):
                try:
                    conn.execute('BEGIN IMMEDIATE')
                    registrar(base,conn,role,action,'falha',{'tipo':type(exc).__name__})
                    conn.commit()
                except Exception:conn.rollback()
            raise
