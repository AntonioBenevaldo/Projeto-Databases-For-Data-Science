CREATE TABLE IF NOT EXISTS produtos (
    produto_id INTEGER PRIMARY KEY,
    produto TEXT NOT NULL,
    categoria TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS vendas (
    venda_id INTEGER PRIMARY KEY,
    data_venda DATE NOT NULL,
    produto_id INTEGER NOT NULL REFERENCES produtos(produto_id),
    quantidade INTEGER NOT NULL CHECK (quantidade > 0),
    preco_centavos INTEGER NOT NULL CHECK (preco_centavos >= 0),
    custo_centavos INTEGER NOT NULL CHECK (custo_centavos >= 0),
    desconto_centavos INTEGER NOT NULL CHECK (
        desconto_centavos >= 0 AND desconto_centavos <= quantidade * preco_centavos
    ),
    status TEXT NOT NULL CHECK (status IN ('concluida', 'cancelada', 'pendente'))
);
CREATE INDEX IF NOT EXISTS idx_vendas_status_data ON vendas(status, data_venda);
