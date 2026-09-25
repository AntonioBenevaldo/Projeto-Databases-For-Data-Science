CREATE TABLE IF NOT EXISTS pedidos (
 pedido_id INTEGER PRIMARY KEY,
 data_venda TEXT NOT NULL,
 categoria TEXT NOT NULL,
 quantidade INTEGER NOT NULL,
 preco_centavos INTEGER NOT NULL,
 custo_centavos INTEGER NOT NULL,
 desconto_centavos INTEGER NOT NULL,
 status TEXT NOT NULL,
 alterado_em TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS eventos (
 event_seq INTEGER PRIMARY KEY AUTOINCREMENT,
 pedido_id INTEGER NOT NULL,
 data_venda TEXT NOT NULL,
 categoria TEXT NOT NULL,
 quantidade INTEGER NOT NULL,
 preco_centavos INTEGER NOT NULL,
 custo_centavos INTEGER NOT NULL,
 desconto_centavos INTEGER NOT NULL,
 status TEXT NOT NULL,
 alterado_em TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS lotes_demo (lote TEXT PRIMARY KEY);
