# Dicionário de dados e disponibilidade

| Campo | Tipo/unidade | Significado | Disponível no pedido? | Uso |
|---|---|---|---|---|
| pedido_id | Texto | Identificador do pedido simulado | Sim | Rastreabilidade; excluído do modelo |
| data_pedido | Data ISO | Dia em que o pedido foi feito | Sim | Divisão temporal e dia da semana |
| valor_pedido | Número, reais | Valor comercial total do pedido | Sim | Atributo numérico; ausência permitida |
| quantidade | Inteiro positivo | Número de itens | Sim | Atributo; inválidos rejeitados |
| distancia_km | Número, km | Distância estimada de transporte | Sim | Atributo; ausência permitida |
| canal | Texto | loja, site, aplicativo ou categoria futura | Sim | Atributo categórico |
| regiao | Texto | Região de entrega simulada | Sim | Atributo categórico |
| dias_entrega_real | Inteiro, dias | Duração efetiva até a entrega | Não | Apenas demonstração de leakage; excluído |
| atrasou | Binário 0/1 | Ultrapassou o prazo fixo de sete dias | Não | Alvo, nunca atributo |
| valor_por_item | Número, reais/item | valor_pedido / quantidade | Sim | Atributo derivado |
| dia_semana | Inteiro 0–6 | Segunda=0, domingo=6 | Sim | Atributo derivado |

O conjunto é retrospectivo: todos os rótulos utilizados no teste são considerados observados após o prazo. Não existem pedidos em aberto com alvo ainda desconhecido sendo tratados como zero.

Valor monetário é usado como atributo de ML com ponto flutuante. O projeto não executa escrituração ou cálculo financeiro contábil que exija tratamento de centavos exatos.

Os nomes `NUM`, `CAT`, `FEATURES` e `CAMPOS` em `src/preparacao.py` definem o contrato de entrada. `outputs/features.json` registra as colunas finais após imputação, indicadores, escala e one-hot.
