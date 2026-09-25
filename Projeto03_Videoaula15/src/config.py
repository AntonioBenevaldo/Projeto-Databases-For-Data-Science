from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
CAMPOS = ['pedido_id','data_venda','categoria','quantidade','preco_centavos',
          'custo_centavos','desconto_centavos','status','alterado_em']
EVENTOS = ['event_seq']+CAMPOS
COLUNAS_FATO = EVENTOS+['faturamento_centavos','custo_total_centavos','lucro_bruto_centavos']

def pasta(base):
    base=Path(base).resolve()
    for name in ['data','outputs/execucoes','outputs/alertas']:
        (base/name).mkdir(parents=True,exist_ok=True)
    return base
