from src.config import COLUNAS_FATO

def transformar(df):
    df=df.copy()
    if df.empty:
        for c in ['faturamento_centavos','custo_total_centavos','lucro_bruto_centavos']:df[c]=[]
        return df[COLUNAS_FATO]
    df['categoria']=df.categoria.str.strip().str.lower()
    df['faturamento_centavos']=df.quantidade*df.preco_centavos-df.desconto_centavos
    df['custo_total_centavos']=df.quantidade*df.custo_centavos
    df['lucro_bruto_centavos']=df.faturamento_centavos-df.custo_total_centavos
    # Um pedido pode ter varios eventos no lote: a maior sequencia representa seu estado final.
    return df.sort_values('event_seq').drop_duplicates('pedido_id',keep='last')[COLUNAS_FATO]
