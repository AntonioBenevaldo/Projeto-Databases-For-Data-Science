SELECT data_venda,categoria,COUNT(*) AS pedidos,
       SUM(faturamento_centavos) AS faturamento_centavos,
       SUM(custo_total_centavos) AS custo_total_centavos,
       SUM(lucro_bruto_centavos) AS lucro_bruto_centavos
FROM pedidos_analiticos
WHERE status = :status
GROUP BY data_venda,categoria
ORDER BY data_venda,categoria
