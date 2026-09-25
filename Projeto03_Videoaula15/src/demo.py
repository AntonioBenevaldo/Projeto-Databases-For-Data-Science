"""Origem simulada; pedido e evento sao gravados na MESMA transacao."""
from sqlalchemy import text
from src.config import CAMPOS
from src.db import bancos,esquema

INICIAL=[
 (1,'2026-01-01','Papelaria',2,5000,3000,0,'concluido'),
 (2,'2026-01-01','Informatica',1,20000,12000,1000,'concluido'),
 (3,'2026-01-02','Papelaria',3,4000,2500,0,'pendente'),
 (4,'2026-01-02','Papelaria',5,1000,600,0,'concluido'),
 (5,'2026-01-03','Informatica',1,8000,5000,0,'cancelado'),
 (6,'2026-01-03','Informatica',2,12000,8000,500,'concluido')]
DELTA=[
 (2,'2026-01-01','Informatica',2,20000,12000,1000,'concluido'),
 (3,'2026-01-02','Papelaria',3,4000,2500,0,'concluido'),
 (4,'2026-01-02','Papelaria',5,1000,600,0,'cancelado'),
 (7,'2026-01-04','Informatica',1,15000,9000,0,'concluido'),
 (8,'2026-01-01','Papelaria',2,2500,1500,0,'concluido')]

def aplicar(conn,lote,linhas,data):
    # INSERT antes da consulta serializa a escrita do lote dentro do SQLite.
    result=conn.execute(text('INSERT OR IGNORE INTO lotes_demo(lote) VALUES(:lote)'),{'lote':lote})
    if result.rowcount==0:return 0
    cols=','.join(CAMPOS);params=','.join(':'+c for c in CAMPOS)
    updates=','.join(f'{c}=excluded.{c}' for c in CAMPOS if c!='pedido_id')
    for row in linhas:
        values=dict(zip(CAMPOS,(*row,data)))
        conn.execute(text(f'INSERT INTO pedidos ({cols}) VALUES ({params}) ON CONFLICT(pedido_id) DO UPDATE SET {updates}'),values)
        conn.execute(text(f'INSERT INTO eventos ({cols}) VALUES ({params})'),values)
    return len(linhas)

def preparar(base):
    with bancos(base) as (origem,destino):
        esquema(origem,'origem');esquema(destino,'destino')
        with origem.begin() as conn:
            count=aplicar(conn,'inicial',INICIAL,'2026-01-04T08:00:00Z')
    print(f'PREPARAR: {count} eventos iniciais inseridos. Repetir preserva dados existentes.')
    return count

def simular_lote(base):
    with bancos(base) as (origem,_):
        with origem.begin() as conn:
            exists=conn.scalar(text("SELECT COUNT(*) FROM lotes_demo WHERE lote='inicial'"))
            if not exists:raise ValueError('Execute preparar primeiro.')
            count=aplicar(conn,'delta',DELTA,'2026-01-05T08:00:00Z')
    print(f'SIMULAR-LOTE: {count} eventos novos; 2 pedidos novos, 2 atualizacoes e 1 cancelamento.')
    return count
