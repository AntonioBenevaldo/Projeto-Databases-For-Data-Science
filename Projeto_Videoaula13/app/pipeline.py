"""Conexao, carga, extracao em partes e analise. Valores monetarios em centavos."""
from pathlib import Path
from datetime import datetime, timezone, date
import hashlib
import json
import platform
import os
import pandas as pd
import sqlalchemy as sa
from sqlalchemy import create_engine, text, event
from sqlalchemy.engine import URL
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
QUERY = (ROOT / 'sql/extracao.sql').read_text(encoding='utf-8')
COLUNAS = ['venda_id','data_venda','produto','categoria','quantidade',
           'preco_centavos','custo_centavos','desconto_centavos']
NUMERICAS = ['venda_id','quantidade','preco_centavos','custo_centavos','desconto_centavos']

def engine(banco='sqlite', sqlite_path=None):
    """Uma Engine por processo; credenciais nao sao impressas."""
    load_dotenv(ROOT / '.env')
    if banco == 'sqlite':
        path = Path(sqlite_path) if sqlite_path else ROOT / 'data/vendas.db'
        path.parent.mkdir(parents=True, exist_ok=True)
        eng = create_engine(URL.create('sqlite', database=str(path)))
        @event.listens_for(eng, 'connect')
        def foreign_keys(dbapi_connection, _):
            dbapi_connection.execute('PRAGMA foreign_keys=ON')
        return eng
    senha = os.getenv('PGPASSWORD')
    if not senha:
        raise ValueError('Configure .env com python projeto.py configurar-postgres.')
    return create_engine(URL.create('postgresql+psycopg',
        username=os.getenv('PGUSER','ds_user'), password=senha,
        host=os.getenv('PGHOST','127.0.0.1'), port=int(os.getenv('PGPORT','5432')),
        database=os.getenv('PGDATABASE','videoaula13')), pool_pre_ping=True,
        connect_args={'connect_timeout': 8})

def inicializar(eng):
    """Transacao: todo o lote e confirmado ou revertido. Repeticao nao duplica."""
    with eng.begin() as conn:
        for stmt in (ROOT / 'sql/schema.sql').read_text(encoding='utf-8').split(';'):
            if stmt.strip(): conn.execute(text(stmt))
        for table in ('produtos', 'vendas'):
            frame = pd.read_csv(ROOT / f'data/{table}.csv')
            if table == 'vendas':
                frame['data_venda'] = pd.to_datetime(frame['data_venda']).dt.date
            columns = list(frame.columns)  # Cabecalhos dos arquivos do projeto, nao entrada SQL livre.
            placeholders = ', '.join(':'+c for c in columns)
            query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders}) ON CONFLICT DO NOTHING"
            conn.execute(text(query), frame.to_dict(orient='records'))
    print('Banco preparado: carga por identificador, sem duplicar registros existentes.')

def validar_periodo(inicio, fim, chunk):
    if date.fromisoformat(inicio) > date.fromisoformat(fim):
        raise ValueError('A data inicial deve ser anterior ou igual a final.')
    if chunk < 1: raise ValueError('O tamanho do lote precisa ser maior que zero.')

def validar_dados(df):
    if list(df.columns) != COLUNAS: raise ValueError('Colunas inesperadas na extracao.')
    if df.empty: return
    if df.isna().any().any(): raise ValueError('Existem valores ausentes.')
    if df['venda_id'].duplicated().any(): raise ValueError('Existem vendas duplicadas.')
    pd.to_datetime(df['data_venda'], errors='raise')
    for c in NUMERICAS:
        n = pd.to_numeric(df[c], errors='raise')
        if ((n % 1) != 0).any(): raise ValueError(f'{c} precisa ser inteiro.')
    if (df['quantidade'] <= 0).any(): raise ValueError('Quantidade invalida.')
    if (df[['preco_centavos','custo_centavos','desconto_centavos']] < 0).any().any():
        raise ValueError('Valor monetario negativo.')
    if (df['desconto_centavos'] > df['quantidade']*df['preco_centavos']).any():
        raise ValueError('Desconto maior que o valor bruto.')

def extrair(eng, saida, inicio, fim, chunk=4):
    validar_periodo(inicio, fim, chunk)
    saida = Path(saida); saida.mkdir(parents=True,exist_ok=True)
    target = saida / 'vendas_extraidas.csv'
    temp = saida / 'extracao.tmp'
    params = {'status':'concluida','inicio':date.fromisoformat(inicio),'fim':date.fromisoformat(fim)}
    total = 0
    # stream_results ajuda os drivers que suportam cursores no servidor (PostgreSQL).
    try:
        with eng.connect().execution_options(stream_results=True) as conn:
            first = True
            for frame in pd.read_sql_query(text(QUERY), conn, params=params, chunksize=chunk):
                validar_dados(frame)
                frame.to_csv(temp, index=False, mode='w' if first else 'a', header=first, encoding='utf-8')
                total += len(frame); first = False
                print(f'  Lote: {len(frame)} venda(s); acumulado: {total}.')
            if first: pd.DataFrame(columns=COLUNAS).to_csv(temp,index=False)
        temp.replace(target)
    finally:
        temp.unlink(missing_ok=True)
    manifest = {'extraido_em_utc':datetime.now(timezone.utc).isoformat(),
        'banco':eng.dialect.name,'inicio':inicio,'fim':fim,'status':'concluida',
        'linhas':total,'chunk':chunk,'dataset':'vendas-demo-v1',
        'query_sha256':hashlib.sha256(QUERY.encode()).hexdigest(),
        'csv_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),
        'fontes_sha256':{n:hashlib.sha256((ROOT/'data'/n).read_bytes()).hexdigest()
                         for n in ('produtos.csv','vendas.csv')},
        'versoes':{'python':platform.python_version(),'pandas':pd.__version__,'sqlalchemy':sa.__version__}}
    (saida/'metadados.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding='utf-8')
    print(f'Extracao salva: {target}')
    return manifest

def calcular(df):
    validar_dados(df)
    df = df.copy()
    for c in NUMERICAS: df[c] = pd.to_numeric(df[c]).astype('int64')
    df['faturamento_centavos'] = df.quantidade * df.preco_centavos - df.desconto_centavos
    df['custo_total_centavos'] = df.quantidade * df.custo_centavos
    df['lucro_bruto_centavos'] = df.faturamento_centavos - df.custo_total_centavos
    return df

def analisar(saida):
    saida = Path(saida)
    path = saida/'vendas_extraidas.csv'
    meta = json.loads((saida/'metadados.json').read_text(encoding='utf-8'))
    if hashlib.sha256(path.read_bytes()).hexdigest() != meta['csv_sha256']:
        raise ValueError('CSV alterado apos extracao. Execute extrair novamente.')
    df = calcular(pd.read_csv(path))
    df['mes'] = df['data_venda'].astype(str).str[:7]
    metrics = ['faturamento_centavos','custo_total_centavos','lucro_bruto_centavos']
    for coluna, nome in [('categoria','resumo_categoria.csv'), ('mes','resumo_mensal.csv')]:
        df.groupby(coluna)[metrics].sum().reset_index().to_csv(saida/nome,index=False)
    faturamento = int(df.faturamento_centavos.sum())
    custo = int(df.custo_total_centavos.sum())
    indicadores = {'vendas':len(df),'unidades':int(df.quantidade.sum()),
        'faturamento_centavos':faturamento,'custo_total_centavos':custo,
        'lucro_bruto_centavos':faturamento-custo,
        'ticket_medio_reais':round(faturamento / len(df) / 100, 2) if len(df) else None,
        'margem_bruta_percentual':round((faturamento-custo)/faturamento*100,2) if faturamento else None}
    (saida/'indicadores.json').write_text(json.dumps(indicadores,indent=2),encoding='utf-8')
    print('\nINDICADORES (moeda em reais na exibicao)')
    for k,v in indicadores.items():
        print(f'  {k.replace("_centavos", "_reais")}: {v/100:.2f}' if k.endswith('_centavos') else f'  {k}: {v}')
    if df.empty: print('Sem vendas no periodo: totais zero; ticket e margem nao se aplicam.')
    print('\nResumo por categoria (valores em centavos):')
    print(pd.read_csv(saida/'resumo_categoria.csv').to_string(index=False))
    return indicadores

def comparar(py_dir, r_dir):
    for nome, chaves in [('vendas_extraidas.csv',['venda_id']),('resumo_categoria.csv',['categoria']),('resumo_mensal.csv',['mes'])]:
        a = pd.read_csv(Path(py_dir)/nome).sort_values(chaves).reset_index(drop=True)
        b = pd.read_csv(Path(r_dir)/nome).sort_values(chaves).reset_index(drop=True)
        pd.testing.assert_frame_equal(a,b,check_dtype=False,check_exact=True)
    print('OK: extracao, resumo por categoria e resumo mensal identicos em Python e R.')
