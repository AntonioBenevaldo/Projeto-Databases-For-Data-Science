import pandas as pd
from sqlalchemy import text
from src.config import ROOT,COLUNAS_FATO

class Concorrencia(RuntimeError):pass
class FalhaCarga(RuntimeError):pass
RESUMO=(ROOT/'src/queries/resumo.sql').read_text(encoding='utf-8')

def carregar(destino,df,checkpoint_esperado,checkpoint_novo,run_id,info,falhar=False):
    """Upsert, resumo, checkpoint e sucesso confirmados na MESMA transacao."""
    changed=0
    with destino.begin() as conn:
        # Escrita condicional adquire lock e evita confirmar uma extracao com cursor obsoleto.
        lock=conn.execute(text('UPDATE controle SET ultimo_evento=ultimo_evento WHERE id=1 AND ultimo_evento=:antigo'),{'antigo':checkpoint_esperado})
        if lock.rowcount!=1:raise Concorrencia('Outro processo avancou o checkpoint; repetir a extracao.')
        names=','.join(COLUNAS_FATO);binds=','.join(':'+c for c in COLUNAS_FATO)
        updates=','.join(f'{c}=excluded.{c}' for c in COLUNAS_FATO if c!='pedido_id')
        query=text(f'INSERT INTO pedidos_analiticos ({names}) VALUES ({binds}) '
                   f'ON CONFLICT(pedido_id) DO UPDATE SET {updates} '
                   'WHERE excluded.event_seq > pedidos_analiticos.event_seq')
        for row in df.to_dict(orient='records'):
            changed+=conn.execute(query,row).rowcount
        if falhar:raise FalhaCarga('Falha de carga simulada antes do commit.')
        # Incremental na extracao/fato; resumo pequeno recalculado inteiro para clareza didatica.
        resumo=pd.read_sql_query(text(RESUMO),conn,params={'status':'concluido'})
        conn.execute(text('DELETE FROM resumo_diario'))
        if not resumo.empty:resumo.to_sql('resumo_diario',conn,if_exists='append',index=False)
        conn.execute(text('UPDATE controle SET ultimo_evento=:novo WHERE id=1'),{'novo':max(checkpoint_esperado,checkpoint_novo)})
        conn.execute(text("""UPDATE execucoes SET status='sucesso',fim_utc=:fim,
            tentativas=:tentativas,eventos_lidos=:lidos,pedidos_alterados=:alterados,
            checkpoint_antes=:antes,checkpoint_depois=:depois,duracao_segundos=:duracao
            WHERE run_id=:run"""),{**info,'run':run_id,'alterados':changed,
            'antes':checkpoint_esperado,'depois':max(checkpoint_esperado,checkpoint_novo)})
    return changed
