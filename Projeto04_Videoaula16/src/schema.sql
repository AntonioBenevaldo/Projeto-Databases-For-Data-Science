CREATE TABLE credenciais(perfil TEXT PRIMARY KEY,token_hash TEXT NOT NULL);
CREATE TABLE pedidos(pedido_id INTEGER PRIMARY KEY,data_venda TEXT,cliente_simulado TEXT,contato_simulado TEXT,categoria TEXT,quantidade INTEGER,preco_centavos INTEGER,custo_unitario_centavos INTEGER,desconto_centavos INTEGER,status TEXT);
CREATE TABLE lotes(lote TEXT PRIMARY KEY);
CREATE TABLE versoes(versao TEXT PRIMARY KEY,criada_utc TEXT NOT NULL,manifesto_hash TEXT NOT NULL,linhas INTEGER NOT NULL,faturamento_centavos INTEGER NOT NULL);
CREATE TABLE estado(id INTEGER PRIMARY KEY CHECK(id=1),ativa TEXT REFERENCES versoes(versao));
INSERT INTO estado VALUES(1,NULL);
CREATE TABLE auditoria(seq INTEGER PRIMARY KEY,payload TEXT NOT NULL,anterior TEXT NOT NULL,assinatura TEXT NOT NULL);
