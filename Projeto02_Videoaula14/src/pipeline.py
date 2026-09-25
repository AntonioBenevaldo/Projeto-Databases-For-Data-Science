"""Etapas explicitas, artefatos verificaveis e reproducao local."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import sqlite3
from contextlib import closing
import platform
import importlib.metadata
import numpy as np
import pandas as pd
import joblib
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.dummy import DummyClassifier
from sklearn.metrics import (accuracy_score,balanced_accuracy_score,precision_score,
                             recall_score,f1_score,roc_auc_score,confusion_matrix)
from src.preparacao import (CAMPOS,FEATURES,NUM,CAT,ALVO,limpar,atributos,
                           dividir_temporal,construir_transformador)

ROOT=Path(__file__).resolve().parents[1]
VERSAO='pedidos-demo-v1'

def gravar_json(path,obj):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')

def ler_json(path): return json.loads(Path(path).read_text(encoding='utf-8'))
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def agora(): return datetime.now(timezone.utc).isoformat()
def dirs(work):
    work=Path(work)
    for d in ['data/brutos','data/tratados','data/analiticos','outputs','modelos']:
        (work/d).mkdir(parents=True,exist_ok=True)
    return work

def manifesto(work,nome,arquivos,**extra):
    gravar_json(work/f'outputs/{nome}.json',{'etapa':nome,'utc':agora(),
        'arquivos':{str(Path(p).relative_to(work)):sha(p) for p in arquivos},**extra})

def conferir(work,nome):
    anteriores={'ingestao':'geracao','preprocessamento':'ingestao','treinamento':'preprocessamento','avaliacao':'treinamento'}
    if nome in anteriores: conferir(work,anteriores[nome])
    path=work/f'outputs/{nome}.json'
    if not path.exists(): raise ValueError(f'Execute a etapa anterior ({nome}) primeiro.')
    m=ler_json(path)
    for rel,digest in m['arquivos'].items():
        p=work/rel
        if not p.exists() or sha(p)!=digest:
            raise ValueError(f'Arquivo ausente ou alterado: {rel}. Reexecute a partir da etapa {nome}.')
    return m

def gerar(work,seed=42,n=1200):
    work=dirs(work)
    if n<300 or n%5: raise ValueError('--linhas deve ser multiplo de 5 e pelo menos 300.')
    rng=np.random.default_rng(seed)
    qtd=rng.integers(1,11,n)
    valor=np.round(rng.lognormal(5.7,0.65,n),2)
    distancia=np.round(rng.uniform(5,1000,n),1)
    canal=rng.choice(['loja','site','aplicativo'],n)
    regiao=rng.choice(['sudeste','sul','nordeste','norte','centro-oeste'],n)
    datas=pd.date_range('2025-01-01',periods=n//5).repeat(5)
    # Mecanismo artificial: probabilidades nao sao uma realidade empresarial observada.
    z=-3.3+0.0038*distancia+0.13*qtd+0.45*(canal=='site')+0.4*(regiao=='norte')
    prob=1/(1+np.exp(-z))
    atraso=(rng.random(n)<prob).astype(int)
    prazo_real=np.where(atraso==1,rng.integers(8,16,n),rng.integers(1,8,n))
    df=pd.DataFrame({'pedido_id':[f'PED{i+1:06d}' for i in range(n)],
        'data_pedido':datas.strftime('%Y-%m-%d'),'valor_pedido':valor,'quantidade':qtd,
        'distancia_km':distancia,'canal':canal,'regiao':regiao,
        'dias_entrega_real':prazo_real,'atrasou':atraso})
    # Problemas conhecidos para observar a limpeza, sem usar dados pessoais.
    for col in ['valor_pedido','distancia_km']:
        df.loc[rng.choice(n,n//25,replace=False),col]=np.nan
    for col in CAT:
        df.loc[rng.choice(n,n//50,replace=False),col]=np.nan
    idx=df.index[df.canal.notna()][:25]
    df.loc[idx,'canal']=df.loc[idx,'canal'].str.upper().map(lambda s:' '+s+' ')
    df.loc[[50,150,250],'valor_pedido']=[30000.,40000.,50000.]
    # Categoria apenas em periodo futuro: demonstra handle_unknown, sem aprender no teste.
    df.loc[n-10:n-1,'canal']='parceiro'
    invalidos=df.iloc[:6].copy()
    invalidos['pedido_id']=[f'PED{n+i+1:06d}' for i in range(6)]
    invalidos.loc[0,'quantidade']=-2
    invalidos.loc[1,'quantidade']=0
    invalidos.loc[2,'valor_pedido']=-100
    invalidos.loc[3,'data_pedido']='data-invalida'
    invalidos.loc[4,'atrasou']=np.nan
    invalidos.loc[5,'distancia_km']=-5
    raw=pd.concat([df,df.iloc[:20].copy(),invalidos],ignore_index=True)
    file=work/'data/brutos/pedidos.csv'
    raw.to_csv(file,index=False)
    exemplo=df.tail(5).drop(columns=['dias_entrega_real','atrasou']).copy()
    exemplo['pedido_id']=[f'NOVO{i}' for i in range(1,6)]
    exemplo['data_pedido']=(datas[-1]+pd.Timedelta(days=8)).strftime('%Y-%m-%d')
    exemplo.to_csv(work/'data/brutos/novos_pedidos.csv',index=False)
    manifesto(work,'geracao',[file,work/'data/brutos/novos_pedidos.csv'],seed=seed,
        linhas_base=n,linhas_brutas=len(raw),dataset=VERSAO)
    print(f'GERAR: {len(raw)} linhas brutas; semente {seed}; base simulada de {n} pedidos.')

def ingerir(work):
    work=dirs(work);g=conferir(work,'geracao')
    source=work/'data/brutos/pedidos.csv'
    raw=pd.read_csv(source)
    if list(raw.columns)!=CAMPOS: raise ValueError('Contrato CSV invalido.')
    # Snapshot batch completo. Banco temporario substitui o anterior somente apos sucesso.
    temp=work/'data/ingestao.tmp.db'; target=work/'data/pedidos.db'
    temp.unlink(missing_ok=True)
    try:
        with closing(sqlite3.connect(temp)) as con:
            raw.to_sql('pedidos_brutos',con,if_exists='replace',index=False)
            count=con.execute('SELECT COUNT(*) FROM pedidos_brutos').fetchone()[0]
            if count!=len(raw): raise ValueError('Contagem da ingestao divergente.')
        temp.replace(target)
    finally: temp.unlink(missing_ok=True)
    manifesto(work,'ingestao',[source,target,work/'outputs/geracao.json'],linhas=count,
        estrategia='batch_snapshot',seed=g['seed'])
    print(f'INGERIR: {count} linhas em SQLite; snapshot substituido, sem acumular duplicatas de execucoes.')

def preprocessar(work):
    work=dirs(work);conferir(work,'ingestao')
    with closing(sqlite3.connect(work/'data/pedidos.db')) as con:
        raw=pd.read_sql_query('SELECT '+','.join(CAMPOS)+' FROM pedidos_brutos',con)
    clean,rejeitados,quality=limpar(raw)
    if clean.empty: raise ValueError('Nenhuma linha valida apos limpeza.')
    parts,embargo,split=dividir_temporal(clean)
    arquivos=[]
    for name,df in [('pedidos_limpos',clean),('quarentena',rejeitados),('embargo_temporal',embargo)]:
        p=work/f'data/tratados/{name}.csv';df.to_csv(p,index=False);arquivos.append(p)
    prep=construir_transformador()
    X=atributos(parts['treino'])
    if X[NUM].isna().all().any(): raise ValueError('Coluna numerica inteiramente ausente no treino.')
    prep.fit(X) # Nenhum fit em validacao ou teste.
    nomes=prep.get_feature_names_out().tolist()
    for name,df in parts.items():
        p=work/f'data/analiticos/{name}.csv';df.to_csv(p,index=False);arquivos.append(p)
        transformed=prep.transform(atributos(df))
        if not np.isfinite(transformed).all(): raise ValueError('Matriz com NaN ou infinito.')
        p=work/f'data/analiticos/X_{name}.csv'
        pd.DataFrame(transformed,columns=nomes).to_csv(p,index=False);arquivos.append(p)
        p=work/f'data/analiticos/y_{name}.csv';df[['pedido_id',ALVO]].to_csv(p,index=False);arquivos.append(p)
    p=work/'modelos/preprocessador.joblib';joblib.dump(prep,p);arquivos.append(p)
    num=prep.named_transformers_['numericas']
    quality['divisao']=split
    quality['features_modelo']=FEATURES
    quality['colunas_proibidas']=['pedido_id','dias_entrega_real','atrasou','data_pedido (data absoluta)']
    quality['parametros_aprendidos_no_treino']={
        'limites_inferiores':dict(zip(NUM,num.named_steps['limites'].limite_inferior_.tolist())),
        'limites_superiores':dict(zip(NUM,num.named_steps['limites'].limite_superior_.tolist())),
        'medianas_apos_limitar':dict(zip(NUM,num.named_steps['mediana'].statistics_.tolist())),
        'categorias':{c:vals.tolist() for c,vals in zip(CAT,prep.named_transformers_['categoricas'].named_steps['onehot'].categories_)}}
    p=work/'outputs/qualidade.json';gravar_json(p,quality);arquivos.append(p)
    p=work/'outputs/features.json';gravar_json(p,nomes);arquivos.append(p)
    arquivos += [work/'outputs/ingestao.json',work/'data/pedidos.db']
    manifesto(work,'preprocessamento',arquivos,linhas_validas=len(clean),n_features=len(nomes))
    print(f'PREPROCESSAR: {len(clean)} validos; {len(rejeitados)} rejeitados; {quality["duplicatas_exatas_removidas"]} duplicatas removidas.')
    print('Particoes:',{k:len(v) for k,v in parts.items()},'; embargo:',len(embargo))
    return quality

def metricas(y,p):
    pred=(np.asarray(p)>=0.5).astype(int)
    return {'linhas':len(y),'atrasados_reais':int(np.asarray(y).sum()),
        'acuracia':float(accuracy_score(y,pred)),
        'acuracia_balanceada':float(balanced_accuracy_score(y,pred)),
        'precisao':float(precision_score(y,pred,zero_division=0)),
        'recall':float(recall_score(y,pred,zero_division=0)),
        'f1':float(f1_score(y,pred,zero_division=0)),
        'roc_auc':float(roc_auc_score(y,p)) if len(np.unique(y))==2 else None,
        'matriz_confusao':confusion_matrix(y,pred,labels=[0,1]).tolist()}

def treinar(work):
    work=dirs(work);conferir(work,'preprocessamento')
    train=pd.read_csv(work/'data/analiticos/treino.csv')
    val=pd.read_csv(work/'data/analiticos/validacao.csv')
    # Somente artefato gerado localmente por este projeto e conferido pelo manifesto.
    prep=joblib.load(work/'modelos/preprocessador.joblib')
    Xt=prep.transform(atributos(train))
    model=LogisticRegression(max_iter=2000,random_state=42)
    model.fit(Xt,train[ALVO])
    pipe=Pipeline([('preprocessamento',prep),('modelo',model)])
    baseline=DummyClassifier(strategy='prior').fit(Xt,train[ALVO])
    p=pipe.predict_proba(atributos(val))[:,1]
    d=baseline.predict_proba(prep.transform(atributos(val)))[:,1]
    report={'limiar_fixo':0.5,'regressao_logistica':metricas(val[ALVO],p),'baseline_prior':metricas(val[ALVO],d),
        'nota':'Parametros fixos; validacao para diagnostico. Teste nao avaliado nesta etapa.'}
    gravar_json(work/'outputs/metricas_validacao.json',report)
    joblib.dump({'pipeline':pipe,'baseline':baseline,'features':FEATURES},work/'modelos/modelo.joblib')
    arquivos=[work/'modelos/modelo.joblib',work/'outputs/metricas_validacao.json',work/'outputs/preprocessamento.json']
    manifesto(work,'treinamento',arquivos,versoes={p:importlib.metadata.version(p) for p in
        ['numpy','pandas','scikit-learn','scipy','joblib','threadpoolctl']},python=platform.python_version(),
        codigo_sha256={str(p.relative_to(ROOT)):sha(p) for p in [ROOT/'projeto.py',ROOT/'src/pipeline.py',ROOT/'src/preparacao.py',ROOT/'requirements.txt']})
    print('TREINAR: regressao logistica e baseline ajustados somente no treino.')
    print('Validacao:',json.dumps(report['regressao_logistica'],ensure_ascii=False))
    return report

def avaliar(work):
    work=dirs(work);conferir(work,'preprocessamento');conferir(work,'treinamento')
    test=pd.read_csv(work/'data/analiticos/teste.csv')
    bundle=joblib.load(work/'modelos/modelo.joblib')
    pipe=bundle['pipeline'];X=atributos(test)
    p=pipe.predict_proba(X)[:,1]
    dummy=bundle['baseline'].predict_proba(pipe.named_steps['preprocessamento'].transform(X))[:,1]
    report={'limiar_fixo':0.5,'regressao_logistica':metricas(test[ALVO],p),'baseline_prior':metricas(test[ALVO],dummy),
        'nota':'Dados artificiais. Metricas nao demonstram desempenho em uma empresa real.'}
    gravar_json(work/'outputs/metricas_teste.json',report)
    out=test[['pedido_id','data_pedido',ALVO]].copy()
    out['probabilidade_atraso']=p;out['previsao']=(p>=0.5).astype(int)
    out.to_csv(work/'outputs/previsoes_teste.csv',index=False)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    cm=np.array(report['regressao_logistica']['matriz_confusao'])
    fig,ax=plt.subplots(figsize=(6,4.5),layout='constrained')
    ax.imshow(cm,cmap='Blues')
    for (i,j),v in np.ndenumerate(cm): ax.text(j,i,str(v),ha='center',va='center',fontsize=17,
        color='white' if v>cm.max()*0.65 else '#14263d')
    ax.set(xticks=[0,1],yticks=[0,1],xticklabels=['No prazo','Atraso'],yticklabels=['No prazo','Atraso'],
        xlabel='Classe prevista',ylabel='Classe real',title='Matriz de confusao | teste temporal\nDados simulados - limiar 0,5')
    fig.savefig(work/'outputs/matriz_confusao.png',dpi=160);plt.close(fig)
    quality=ler_json(work/'outputs/qualidade.json')
    lines=['# Relatorio da execucao','',f'Gerado em UTC: {agora()}','',
        '## Qualidade dos dados','',f"- Brutos: {quality['linhas_brutas']}",
        f"- Duplicatas removidas: {quality['duplicatas_exatas_removidas']}",
        f"- Rejeitados: {quality['registros_rejeitados']}",f"- Validos: {quality['linhas_validas']}",
        f"- Embargo temporal: {quality['divisao']['linhas_embargo']}",'',
        '## Metricas do teste','', '| Indicador | Regressao logistica | Baseline |','|---|---:|---:|']
    for k in ['acuracia','acuracia_balanceada','precisao','recall','f1','roc_auc']:
        vals=[report[name][k] for name in ['regressao_logistica','baseline_prior']]
        cells=['N/A' if v is None else f'{v:.4f}' for v in vals]
        lines.append(f'| {k} | {cells[0]} | {cells[1]} |')
    lines += ['','O baseline usa a frequencia do alvo no treino. Limiar fixo: 0,5.',
        'Precisao e recall referem-se a classe atraso=1. Precisao sem previsoes positivas e registrada como zero.',
        'AUC fica N/A quando ha uma unica classe no conjunto avaliado.','',
        '## Metodo e limites','',
        'Divisao cronologica por dias; rotulo de atraso observado depois de 7 dias. Intervalos de 7 dias evitam usar rotulos indisponiveis no corte.',
        'Medianas, limites de extremos, escala e categorias aprendidos somente no treino.',
        'dias_entrega_real, identificador e alvo excluidos das entradas do modelo.',
        'Este resultado mede somente um mecanismo de simulacao. Nao e validacao operacional.',
        'Nao ajuste o modelo olhando o teste; novos ajustes exigem novo periodo final independente.','',
        '![Matriz de confusao](matriz_confusao.png)']
    (work/'outputs/relatorio.md').write_text('\n'.join(lines),encoding='utf-8')
    manifesto(work,'avaliacao',[work/'outputs/metricas_teste.json',work/'outputs/previsoes_teste.csv',
        work/'outputs/matriz_confusao.png',work/'outputs/relatorio.md',work/'outputs/treinamento.json'])
    print('AVALIAR: teste temporal reservado, sem reajustar o modelo.')
    print(json.dumps(report['regressao_logistica'],ensure_ascii=False))
    return report

def prever(work):
    work=dirs(work);conferir(work,'preprocessamento');conferir(work,'treinamento');conferir(work,'geracao')
    # Exemplo didatico fornecido pela propria geracao, sem colunas de alvo ou futuro.
    new=pd.read_csv(work/'data/brutos/novos_pedidos.csv')
    for c in CAT:
        from src.preparacao import normalizar
        new[c]=new[c].map(normalizar)
    bundle=joblib.load(work/'modelos/modelo.joblib')
    p=bundle['pipeline'].predict_proba(atributos(new))[:,1]
    new['probabilidade_atraso']=p;new['previsao_atraso']=(p>=0.5).astype(int)
    new.to_csv(work/'outputs/previsoes_novos.csv',index=False)
    print('PREVER: cinco exemplos sem rotulo; categoria nova aceita sem reajuste.')
    print(new[['pedido_id','probabilidade_atraso','previsao_atraso']].to_string(index=False))
    return new
