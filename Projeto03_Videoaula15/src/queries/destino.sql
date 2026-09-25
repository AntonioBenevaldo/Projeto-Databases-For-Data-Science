CREATE TABLE IF NOT EXISTS controle (
 id INTEGER PRIMARY KEY CHECK(id=1),
 ultimo_evento INTEGER NOT NULL CHECK(ultimo_evento>=0)
);
INSERT OR IGNORE INTO controle(id,ultimo_evento) VALUES(1,0);
CREATE TABLE IF NOT EXISTS pedidos_analiticos (
 pedido_id INTEGER PRIMARY KEY,
 event_seq INTEGER NOT NULL,
 data_venda TEXT NOT NULL,
 categoria TEXT NOT NULL,
 quantidade INTEGER NOT NULL CHECK(quantidade>0),
 preco_centavos INTEGER NOT NULL CHECK(preco_centavos>=0),
 custo_centavos INTEGER NOT NULL CHECK(custo_centavos>=0),
 desconto_centavos INTEGER NOT NULL CHECK(desconto_centavos>=0),
 status TEXT NOT NULL CHECK(status IN ('concluido','pendente','cancelado')),
 alterado_em TEXT NOT NULL,
 faturamento_centavos INTEGER NOT NULL CHECK(faturamento_centavos>=0),
 custo_total_centavos INTEGER NOT NULL CHECK(custo_total_centavos>=0),
 lucro_bruto_centavos INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS resumo_diario (
 data_venda TEXT NOT NULL,
 categoria TEXT NOT NULL,
 pedidos INTEGER NOT NULL,
 faturamento_centavos INTEGER NOT NULL,
 custo_total_centavos INTEGER NOT NULL,
 lucro_bruto_centavos INTEGER NOT NULL,
 PRIMARY KEY(data_venda,categoria)
);
CREATE TABLE IF NOT EXISTS execucoes (
 run_id TEXT PRIMARY KEY,
 inicio_utc TEXT NOT NULL,
 fim_utc TEXT,
 status TEXT NOT NULL,
 tentativas INTEGER NOT NULL DEFAULT 0,
 eventos_lidos INTEGER NOT NULL DEFAULT 0,
 pedidos_alterados INTEGER NOT NULL DEFAULT 0,
 checkpoint_antes INTEGER,
 checkpoint_depois INTEGER,
 duracao_segundos REAL,
 erro TEXT
);
