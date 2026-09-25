-- Os valores sao enviados separadamente: nunca concatenados ao SQL.
SELECT v.venda_id, v.data_venda, p.produto, p.categoria,
       v.quantidade, v.preco_centavos, v.custo_centavos, v.desconto_centavos
FROM vendas AS v
JOIN produtos AS p ON p.produto_id = v.produto_id
WHERE v.status = :status
  AND v.data_venda >= :inicio AND v.data_venda <= :fim
ORDER BY v.venda_id
