SELECT event_seq,pedido_id,data_venda,categoria,quantidade,preco_centavos,
       custo_centavos,desconto_centavos,status,alterado_em
FROM eventos
WHERE event_seq > :desde AND event_seq <= :ate
ORDER BY event_seq
LIMIT :limite
