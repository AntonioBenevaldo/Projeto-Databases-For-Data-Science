# Dicionário dos dados

| Campo | Tipo | Significado |
|---|---|---|
| event_seq | Inteiro crescente | Ordem de registro da alteração na origem |
| pedido_id | Inteiro positivo | Chave do pedido; uma linha por pedido no destino |
| data_venda | Data AAAA-MM-DD | Dia de negócio, usado no resumo |
| categoria | Texto | Categoria comercial simulada |
| quantidade | Inteiro positivo | Quantidade de itens daquele pedido |
| preco_centavos | Inteiro | Preço unitário em centavos |
| custo_centavos | Inteiro | Custo unitário em centavos |
| desconto_centavos | Inteiro | Desconto total do pedido |
| status | Texto | concluido, pendente ou cancelado |
| alterado_em | Timestamp com fuso | Horário informativo da alteração da origem |
| faturamento_centavos | Inteiro | Quantidade × preço − desconto |
| custo_total_centavos | Inteiro | Quantidade × custo |
| lucro_bruto_centavos | Inteiro | Faturamento − custo total |
| ultimo_evento | Inteiro | Última sequência confirmada no destino |
| run_id | Texto | Identificador de uma execução do pipeline |

O watermark/checkpoint usa `event_seq`, não `alterado_em`. Empates de horário não fazem eventos serem perdidos por comparação de timestamps.

Valores calculados continuam presentes nas linhas canceladas e pendentes como representação comercial do pedido. Os indicadores e o resumo sempre filtram status `concluido`; somar todas as linhas do fato sem esse filtro produziria outro significado.

O projeto não modela pedidos com múltiplas linhas de produtos, devoluções parciais, impostos ou escrituração. Cancelamento retira o pedido inteiro dos indicadores atuais. Para um modelo contábil com movimentos históricos, seriam necessárias regras e tabelas específicas.
