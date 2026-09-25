from datetime import datetime,date
import math
from src.config import EVENTOS

class ErroQualidade(ValueError):pass

def validar(df):
    if list(df.columns)!=EVENTOS:raise ErroQualidade('Esquema inesperado de eventos.')
    if df.empty:return
    if df.isna().any().any():raise ErroQualidade('Existem valores ausentes.')
    if df.event_seq.duplicated().any():raise ErroQualidade('Sequencias de evento duplicadas.')
    if not df.event_seq.is_monotonic_increasing:raise ErroQualidade('Eventos fora de ordem.')
    for c in ['event_seq','pedido_id','quantidade','preco_centavos','custo_centavos','desconto_centavos']:
        for value in df[c]:
            try: n=float(value)
            except (ValueError,TypeError):raise ErroQualidade(f'{c} precisa ser numero inteiro.')
            if not math.isfinite(n) or n%1!=0:raise ErroQualidade(f'{c} precisa ser inteiro finito.')
            if abs(n)>1_000_000_000:raise ErroQualidade(f'{c} excede o limite didatico.')
    if (df[['event_seq','pedido_id','quantidade']]<=0).any().any():raise ErroQualidade('ID, evento ou quantidade invalida.')
    if (df[['preco_centavos','custo_centavos','desconto_centavos']]<0).any().any():raise ErroQualidade('Valor negativo.')
    if (df.desconto_centavos>df.quantidade*df.preco_centavos).any():raise ErroQualidade('Desconto excede o valor bruto.')
    if (df.quantidade*df.preco_centavos>1_000_000_000_000).any():raise ErroQualidade('Venda excede limite de valor didatico.')
    if (df.quantidade*df.custo_centavos>1_000_000_000_000).any():raise ErroQualidade('Custo excede limite didatico.')
    if not df.status.isin(['concluido','pendente','cancelado']).all():raise ErroQualidade('Status invalido.')
    if df.categoria.astype(str).str.strip().eq('').any():raise ErroQualidade('Categoria vazia.')
    for value in df.data_venda:
        try:
            if date.fromisoformat(value).isoformat()!=value:raise ValueError()
        except (ValueError,TypeError):raise ErroQualidade('Data de venda invalida; use AAAA-MM-DD.')
    for value in df.alterado_em:
        try:
            stamp=datetime.fromisoformat(value.replace('Z','+00:00'))
            if stamp.tzinfo is None:raise ValueError()
        except (ValueError,TypeError,AttributeError):raise ErroQualidade('Timestamp precisa de fuso horario.')
