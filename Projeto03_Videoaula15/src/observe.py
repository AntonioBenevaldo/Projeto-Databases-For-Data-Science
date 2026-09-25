from datetime import datetime,timezone
from pathlib import Path
import json
import hashlib
import pandas as pd
from sqlalchemy import text
from src.db import bancos,checkpoint

def utc():return datetime.now(timezone.utc).isoformat()
def salvar(path,value):
    Path(path).write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
def hash_file(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def log(base,run_id,event,**details):
    entry={'utc':utc(),'run_id':run_id,'evento':event,**details}
    with (base/'outputs/execucoes'/f'{run_id}.jsonl').open('a',encoding='utf-8') as f:
        f.write(json.dumps(entry,ensure_ascii=False)+'\n')

def relatorio(base,run_id=None):
    """Exportacao recuperavel; o estado oficial permanece no banco analitico."""
    with bancos(base) as (_,destino):
        with destino.begin() as conn:
            facts=pd.read_sql_query(text('SELECT * FROM pedidos_analiticos ORDER BY pedido_id'),conn)
            resumo=pd.read_sql_query(text('SELECT * FROM resumo_diario ORDER BY data_venda,categoria'),conn)
            cursor=int(conn.scalar(text('SELECT ultimo_evento FROM controle WHERE id=1')))
    active=facts.loc[facts.status=='concluido']
    ind={'pedidos_no_destino':len(facts),'pedidos_concluidos':len(active),
        'faturamento_centavos':int(active.faturamento_centavos.sum()),
        'custo_total_centavos':int(active.custo_total_centavos.sum()),
        'lucro_bruto_centavos':int(active.lucro_bruto_centavos.sum()),'ultimo_evento':cursor}
    # Cada exportacao tem pasta propria; nunca dois processos escrevendo o mesmo CSV.
    export_id=run_id or ('relatorio_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f'))
    out=base/'outputs/execucoes'/export_id
    out.mkdir(parents=True,exist_ok=True)
    facts.to_csv(out/'pedidos_analiticos.csv',index=False)
    resumo.to_csv(out/'resumo_diario.csv',index=False)
    salvar(out/'indicadores.json',ind)
    lines=['# Relatorio de faturamento','',f'Exportado em UTC: {utc()}',
           f'Checkpoint da fotografia exportada: {cursor}','',
           '| Indicador | Valor |','|---|---:|',
           f"| Pedidos no destino | {len(facts)} |",f"| Pedidos concluidos | {len(active)} |"]
    for c in ['faturamento_centavos','custo_total_centavos','lucro_bruto_centavos']:
        lines.append(f'| {c.replace("_centavos", " (R$)")} | {ind[c]/100:.2f} |')
    lines+=['','Somente pedidos concluidos entram nos indicadores. Cancelados e pendentes permanecem no fato.',
            'Lucro bruto nao desconta tributos e outras despesas. Dados simulados.',
            'Esta fotografia reflete o banco no instante da exportacao; pode incluir outra execucao ja confirmada.']
    (out/'relatorio.md').write_text('\n'.join(lines),encoding='utf-8')
    salvar(out/'manifesto_exportacao.json',{'utc':utc(),'checkpoint_fotografia':cursor,
        'arquivos_sha256':{p.name:hash_file(p) for p in out.iterdir() if p.is_file()}})
    print('RELATORIO:',out)
    print(json.dumps(ind,ensure_ascii=False))
    return ind,out

def historico(base):
    with bancos(base) as (_,destino):
        with destino.connect() as conn:
            df=pd.read_sql_query(text('SELECT run_id,status,tentativas,eventos_lidos,pedidos_alterados,checkpoint_antes,checkpoint_depois FROM execucoes ORDER BY inicio_utc DESC LIMIT 20'),conn)
    print(df.to_string(index=False) if not df.empty else 'Nenhuma execucao registrada.')
    return df
