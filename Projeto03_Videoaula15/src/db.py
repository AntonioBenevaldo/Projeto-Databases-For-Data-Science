from contextlib import contextmanager
from sqlalchemy import create_engine,event,text
from sqlalchemy.engine import URL
from src.config import ROOT,pasta

@contextmanager
def bancos(base):
    base=pasta(base)
    engines=[]
    try:
        for name in ['origem','analitico']:
            eng=create_engine(URL.create('sqlite',database=str(base/f'data/{name}.db')),
                              connect_args={'timeout':1})
            # Controle explicito: inclui DDL e to_sql na transacao tambem no SQLite.
            @event.listens_for(eng,'connect')
            def configurar(dbapi_conn,record):
                dbapi_conn.isolation_level=None
                dbapi_conn.execute('PRAGMA foreign_keys=ON')
            @event.listens_for(eng,'begin')
            def iniciar(conn): conn.exec_driver_sql('BEGIN')
            engines.append(eng)
        yield tuple(engines)
    finally:
        for eng in engines: eng.dispose()

def esquema(eng,nome):
    with eng.begin() as conn:
        for stmt in (ROOT/f'src/queries/{nome}.sql').read_text(encoding='utf-8').split(';'):
            if stmt.strip(): conn.execute(text(stmt))

def checkpoint(eng):
    with eng.connect() as conn:
        return int(conn.scalar(text('SELECT ultimo_evento FROM controle WHERE id=1')))
