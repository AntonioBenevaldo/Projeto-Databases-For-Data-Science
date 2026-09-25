import csv
import io
import re
from datetime import date
from src.config import RAW,COLS,QUERY
from src.security import pseudonimo

INITIAL=[(1,'2026-01-01','Papelaria',2,5000,3000,0,'concluido'),
(2,'2026-01-01','Informatica',1,20000,12000,1000,'concluido'),
(3,'2026-01-02','Papelaria',3,4000,2500,0,'pendente'),
(4,'2026-01-02','Papelaria',5,1000,600,0,'concluido'),
(5,'2026-01-03','Informatica',1,8000,5000,0,'cancelado'),
(6,'2026-01-03','Informatica',2,12000,8000,500,'concluido')]
DELTA=[(2,'2026-01-01','Informatica',2,20000,12000,1000,'concluido'),
(3,'2026-01-02','Papelaria',3,4000,2500,0,'concluido'),
(4,'2026-01-02','Papelaria',5,1000,600,0,'cancelado'),
(7,'2026-01-04','Informatica',1,15000,9000,0,'concluido'),
(8,'2026-01-01','Papelaria',2,2500,1500,0,'concluido')]

def inserir(conn,rows):
    update=','.join(f'{c}=excluded.{c}' for c in RAW if c!='pedido_id')
    for row in rows:
        id,day,cat,q,p,c,d,status=row
        vals=(id,day,f'DEMO_ENTIDADE_{id:03d}',f'demo_{id:03d}@example.invalid',cat,q,p,c,d,status)
        conn.execute(f"INSERT INTO pedidos({','.join(RAW)}) VALUES({','.join('?' for _ in RAW)}) ON CONFLICT(pedido_id) DO UPDATE SET {update}",vals)

def extrair(conn,inicio,fim):
    if date.fromisoformat(inicio)>date.fromisoformat(fim):raise ValueError('Periodo invertido.')
    return [dict(r) for r in conn.execute(QUERY,(inicio,fim))]

def validar(rows):
    seen=set()
    for r in rows:
        if list(r)!=RAW or any(v is None for v in r.values()):raise ValueError('Contrato ou valores ausentes invalidos.')
        for c in ['pedido_id','quantidade','preco_centavos','custo_unitario_centavos','desconto_centavos']:
            if not isinstance(r[c],int) or isinstance(r[c],bool):raise ValueError('Tipo inteiro esperado.')
        if r['pedido_id']<=0 or r['pedido_id'] in seen:raise ValueError('Chave invalida ou repetida.')
        seen.add(r['pedido_id'])
        if not 1<=r['quantidade']<=100000:raise ValueError('Quantidade invalida.')
        for c in ['preco_centavos','custo_unitario_centavos','desconto_centavos']:
            if not 0<=r[c]<=1_000_000_000:raise ValueError('Valor fora da faixa.')
        if r['desconto_centavos']>r['quantidade']*r['preco_centavos']:raise ValueError('Desconto invalido.')
        if date.fromisoformat(r['data_venda']).isoformat()!=r['data_venda']:raise ValueError('Data invalida.')
        if r['status'] not in ['concluido','pendente','cancelado']:raise ValueError('Status invalido.')
        if not isinstance(r['categoria'],str) or not r['categoria'].strip():raise ValueError('Categoria vazia.')
        if not re.fullmatch(r'DEMO_ENTIDADE_[0-9]{3,}',r['cliente_simulado']):raise ValueError('Identificador fora do contrato simulado.')
        if not re.fullmatch(r'demo_[0-9]{3,}@example\.invalid',r['contato_simulado']):raise ValueError('Contato fora do contrato simulado.')

def transformar(base,rows):
    out=[]
    for r in rows:
        if r['status']!='concluido':continue
        fat=r['quantidade']*r['preco_centavos']-r['desconto_centavos'];cost=r['quantidade']*r['custo_unitario_centavos']
        out.append(dict(zip(COLS,[r['pedido_id'],r['data_venda'],pseudonimo(base,r['cliente_simulado']),r['categoria'].strip().lower(),r['quantidade'],fat,cost,fat-cost])))
    return out

def csv_bytes(rows,cols):
    buf=io.StringIO(newline='');w=csv.DictWriter(buf,fieldnames=cols,lineterminator='\n')
    w.writeheader();w.writerows(rows)
    return buf.getvalue().encode('utf-8')

def ler_csv(data):
    rows=list(csv.DictReader(io.StringIO(data.decode('utf-8'))))
    for r in rows:
        for c in ['pedido_id','quantidade','faturamento_centavos','custo_total_centavos','lucro_bruto_centavos']:r[c]=int(r[c])
    return rows

def indicadores(rows):return {'pedidos_concluidos':len(rows),'faturamento_centavos':sum(r['faturamento_centavos'] for r in rows),'custo_total_centavos':sum(r['custo_total_centavos'] for r in rows),'lucro_bruto_centavos':sum(r['lucro_bruto_centavos'] for r in rows)}
