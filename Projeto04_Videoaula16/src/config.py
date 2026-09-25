from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=['pedido_id','data_venda','cliente_simulado','contato_simulado','categoria','quantidade','preco_centavos','custo_unitario_centavos','desconto_centavos','status']
COLS=['pedido_id','data_venda','cliente_pseudo','categoria','quantidade','faturamento_centavos','custo_total_centavos','lucro_bruto_centavos']
ROLES={
 'admin':{'publicar','simular-lote','listar','consultar','verificar','comparar','restaurar','auditoria','catalogo'},
 'engenheiro':{'publicar','simular-lote','listar','consultar','verificar','comparar','catalogo'},
 'analista':{'listar','consultar','verificar','catalogo'},
 'auditor':{'listar','verificar','comparar','auditoria','catalogo'}}
QUERY='SELECT '+','.join(RAW)+' FROM pedidos WHERE data_venda>=? AND data_venda<=? ORDER BY pedido_id'
FILES={'dados.csv','origem.csv.fernet','esquema.json','catalogo.json','politicas.json','consulta.sql'}

def layout(base):
    base=Path(base).resolve()
    for n in ['data','versoes','outputs']:(base/n).mkdir(parents=True,exist_ok=True)
    return base
