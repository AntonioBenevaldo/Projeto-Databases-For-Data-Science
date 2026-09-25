"""Regras deterministicas e transformador ajustado somente no treino."""
import unicodedata
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.utils.validation import check_is_fitted

ALVO = 'atrasou'
NUM = ['valor_pedido','quantidade','distancia_km','valor_por_item','dia_semana']
CAT = ['canal','regiao']
FEATURES = NUM + CAT
CAMPOS = ['pedido_id','data_pedido','valor_pedido','quantidade','distancia_km',
          'canal','regiao','dias_entrega_real','atrasou']

class LimitarExtremos(BaseEstimator, TransformerMixin):
    """Winsorizacao didatica: limites 1%/99% aprendidos somente em fit(X_treino)."""
    def __init__(self, inferior=0.01, superior=0.99):
        self.inferior = inferior
        self.superior = superior
    def fit(self, X, y=None):
        x=np.asarray(X,dtype=float)
        self.n_features_in_=x.shape[1]
        self.limite_inferior_=np.nanquantile(x,self.inferior,axis=0)
        self.limite_superior_=np.nanquantile(x,self.superior,axis=0)
        return self
    def transform(self,X):
        check_is_fitted(self,'limite_inferior_')
        return np.clip(np.asarray(X,dtype=float),self.limite_inferior_,self.limite_superior_)
    def get_feature_names_out(self,input_features=None):
        return np.asarray(input_features if input_features is not None else
                          [f'x{i}' for i in range(self.n_features_in_)],dtype=object)

def normalizar(valor):
    if pd.isna(valor) or not str(valor).strip(): return np.nan
    value=''.join(c for c in unicodedata.normalize('NFKD',str(valor)) if not unicodedata.combining(c))
    return value.strip().lower()

def limpar(raw):
    if list(raw.columns)!=CAMPOS: raise ValueError('Contrato de colunas diferente do esperado.')
    duplicados=int(raw.duplicated().sum())
    df=raw.drop_duplicates().copy()
    # IDs conflitantes nao sao resolvidos escolhendo arbitrariamente uma linha.
    conflito=df['pedido_id'].duplicated(keep=False)
    motivos=pd.Series('',index=df.index,dtype=object)
    def marcar(mask,texto):
        motivos.loc[mask] += texto+';'
    marcar(conflito,'id_conflitante')
    marcar(df.pedido_id.isna() | ~df.pedido_id.astype(str).str.match(r'^PED[0-9]+$'),'id_invalido')
    dates=pd.to_datetime(df.data_pedido,format='%Y-%m-%d',errors='coerce')
    marcar(dates.isna(),'data_invalida')
    df['data_pedido']=dates.dt.strftime('%Y-%m-%d')
    for c in ['valor_pedido','quantidade','distancia_km','atrasou']:
        original=df[c]
        n=pd.to_numeric(original,errors='coerce')
        marcar(original.notna() & n.isna(),c+'_nao_numerico')
        marcar(n.notna() & ~np.isfinite(n),c+'_nao_finito')
        df[c]=n
    marcar(df.quantidade.isna() | (df.quantidade<=0) | (df.quantidade % 1 != 0),'quantidade_invalida')
    marcar(df.valor_pedido.notna() & (df.valor_pedido<=0),'valor_invalido')
    marcar(df.distancia_km.notna() & (df.distancia_km<0),'distancia_invalida')
    marcar(~df.atrasou.isin([0,1]),'alvo_invalido')
    for c in CAT: df[c]=df[c].map(normalizar)
    rejeitados=df.loc[motivos!=''].copy();rejeitados['motivo']=motivos.loc[motivos!='']
    clean=df.loc[motivos==''].copy().sort_values(['data_pedido','pedido_id']).reset_index(drop=True)
    clean['atrasou']=clean.atrasou.astype(int)
    qualidade={'linhas_brutas':len(raw),'duplicatas_exatas_removidas':duplicados,
        'registros_rejeitados':len(rejeitados),'linhas_validas':len(clean),
        'ausentes_validos':{c:int(clean[c].isna().sum()) for c in NUM[:3]+CAT}}
    return clean,rejeitados,qualidade

def atributos(df):
    """Somente informacoes disponiveis no momento do pedido. Nao usa alvo ou futuro."""
    x=df[['valor_pedido','quantidade','distancia_km','canal','regiao']].copy()
    x['valor_por_item']=x.valor_pedido/x.quantidade
    x['dia_semana']=pd.to_datetime(df.data_pedido).dt.dayofweek
    return x[FEATURES]

def dividir_temporal(df):
    dates=sorted(df.data_pedido.unique())
    if len(dates)<60: raise ValueError('Use ao menos 60 dias distintos para a divisao temporal.')
    corte_val=pd.Timestamp(dates[int(len(dates)*0.60)])
    corte_test=pd.Timestamp(dates[int(len(dates)*0.80)])
    d=pd.to_datetime(df.data_pedido)
    rotulo_disponivel=d+pd.Timedelta(days=7)
    masks={'treino':rotulo_disponivel<corte_val,
        'validacao':(d>=corte_val)&(rotulo_disponivel<corte_test),
        'teste':d>=corte_test}
    parts={k:df.loc[m].copy().reset_index(drop=True) for k,m in masks.items()}
    usado=masks['treino']|masks['validacao']|masks['teste']
    embargo=df.loc[~usado].copy()
    if any(v.empty for v in parts.values()): raise ValueError('Uma particao ficou vazia.')
    if parts['treino'].atrasou.nunique()<2: raise ValueError('O treino precisa das duas classes.')
    info={'corte_validacao':corte_val.date().isoformat(),'corte_teste':corte_test.date().isoformat(),
        'horizonte_rotulo_dias':7,'linhas_embargo':len(embargo),
        'particoes':{k:{'linhas':len(v),'inicio':v.data_pedido.min(),'fim':v.data_pedido.max(),
                       'atrasados':int(v.atrasou.sum())} for k,v in parts.items()}}
    return parts,embargo,info

def construir_transformador():
    num=Pipeline([('limites',LimitarExtremos()),
                  ('mediana',SimpleImputer(strategy='median',add_indicator=True,keep_empty_features=True)),
                  ('escala',StandardScaler())])
    cat=Pipeline([('ausentes',SimpleImputer(strategy='constant',fill_value='desconhecido')),
                  ('onehot',OneHotEncoder(handle_unknown='ignore',sparse_output=False))])
    return ColumnTransformer([('numericas',num,NUM),('categoricas',cat,CAT)],remainder='drop',
                             sparse_threshold=0)
