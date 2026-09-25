import pandas as pd
from sqlalchemy import text
from src.config import ROOT

QUERY=(ROOT/'src/queries/extrair.sql').read_text(encoding='utf-8')

def extrair(origem,desde,limite):
    # Snapshot consistente da origem: limite superior e consulta na mesma transacao.
    with origem.begin() as conn:
        topo=int(conn.scalar(text('SELECT COALESCE(MAX(event_seq),0) FROM eventos')))
        frame=pd.read_sql_query(text(QUERY),conn,params={'desde':desde,'ate':topo,'limite':limite})
    return frame,topo
