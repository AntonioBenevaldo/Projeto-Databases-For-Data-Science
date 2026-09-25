# Leitura guiada do código

Leia junto com `app/pipeline.py`, `sql/extracao.sql` e `r/analisar.R`. Os trechos abaixo explicam o código entregue; não precisam ser executados separadamente.

## 1. Engine, conexão e DataFrame são objetos diferentes

- **Banco**: guarda as tabelas e aplica regras.
- **Driver**: conversa com o banco; aqui sqlite3 (Python padrão), psycopg, RSQLite ou RPostgres.
- **Engine**: objeto SQLAlchemy que centraliza a configuração e administra conexões. Criá-la não necessariamente abre imediatamente uma conexão física.
- **Conexão**: sessão usada para executar consultas.
- **DataFrame**: tabela em memória para análise no Python. O equivalente usado no R é `data.frame`.

`engine()` cria uma Engine por execução do comando. `main()` a reutiliza nas etapas e chama `dispose()` ao terminar. O gerenciador `with` encerra/devolve cada conexão corretamente, inclusive em falhas.

## 2. Configuração e caminho dos arquivos

```python
ROOT = Path(__file__).resolve().parents[1]
```

O código calcula a pasta do projeto a partir da localização do próprio arquivo. Assim, dados e SQL não dependem de um caminho como `C:\Users\Nome\Desktop` gravado no código.

SQLite usa `data/vendas.db`. PostgreSQL lê variáveis de ambiente, com suporte a `.env` via python-dotenv. `URL.create()` recebe campos separados e evita problemas com caracteres especiais de senha em URLs construídas manualmente.

Os parâmetros `--saida` e `--saida-r`, quando relativos, são interpretados a partir da pasta do terminal. Para seguir exatamente o guia, mantenha o terminal na pasta principal.

## 3. Estrutura do banco e significado dos campos

Uma linha de `produtos` pode estar relacionada a muitas vendas. A coluna `produto_id` em vendas referencia o produto cadastrado.

| Campo em vendas | Significado |
|---|---|
| `venda_id` | Identificador único da transação |
| `data_venda` | Data da venda, no formato ano-mês-dia |
| `produto_id` | Produto vendido |
| `quantidade` | Unidades da venda, sempre maior que zero |
| `preco_centavos` | Preço de uma unidade, em centavos |
| `custo_centavos` | Custo de uma unidade na data da venda |
| `desconto_centavos` | Desconto total da venda |
| `status` | concluida, cancelada ou pendente |

A chave primária evita repetir identificadores. A chave estrangeira impede referenciar produto inexistente. `CHECK` restringe quantidades, descontos e status. Em SQLite, o projeto ativa explicitamente `PRAGMA foreign_keys=ON` em cada nova conexão.

A tabela guarda custos e preços na própria venda para que a análise não dependa de um preço de catálogo que possa mudar depois.

## 4. Carga transacional e repetível

```python
with eng.begin() as conn:
    conn.execute(text(query), registros)
```

A lista `registros` contém dicionários de valores. SQLAlchemy envia os valores separados do comando. O gerenciador confirma a transação ao finalizar com sucesso e faz rollback se ocorrer erro.

`ON CONFLICT DO NOTHING` evita duplicar chaves existentes. Isso é adequado à carga inicial do conjunto de demonstração. Não é sincronização de atualizações: mudar um CSV não atualiza automaticamente registros existentes.

Os nomes de tabelas e colunas vêm de arquivos fixos do projeto; não são fornecidos por usuários em uma aplicação pública. Parâmetros SQL protegem valores, não nomes de tabela. Não transforme os CSVs e os nomes de tabelas em entrada arbitrária sem implementar validação de esquema.

## 5. Consulta parametrizada

```sql
WHERE v.status = :status
  AND v.data_venda >= :inicio AND v.data_venda <= :fim
```

`:status`, `:inicio` e `:fim` são marcadores. Exemplo conceitual:

```python
params = {'status': 'concluida', 'inicio': data_inicial, 'fim': data_final}
frame = pd.read_sql_query(text(QUERY), conn, params=params)
```

O driver recebe comando e valores separadamente. Um valor semelhante a SQL permanece um valor. O projeto possui um teste para conferir esse comportamento.

`JOIN` acrescenta produto e categoria a cada venda. `SELECT` enumera apenas as colunas necessárias. `ORDER BY` estabiliza a ordem da exportação. Filtrar na origem reduz transferência e uso de memória.

## 6. Extração em partes

```python
for frame in pd.read_sql_query(text(QUERY), conn,
                              params=params, chunksize=chunk):
    validar_dados(frame)
    frame.to_csv(...)
```

Com lote 4 e 10 registros, chegam três partes: 4, 4 e 2. O cabeçalho é escrito uma única vez; os demais lotes são anexados. O arquivo temporário substitui o CSV final somente ao concluir a extração.

`stream_results=True` também solicita streaming ao driver quando suportado. No PostgreSQL isso ajuda a evitar que o driver carregue todo o resultado antes de entregá-lo ao pandas. `chunksize` sozinho não garante o mesmo comportamento de memória em todos os drivers.

A escrita do CSV evita substituir o arquivo anterior por um CSV parcialmente extraído. CSV e JSON de metadados são dois arquivos separados, portanto não formam uma única transação de sistema de arquivos; uma interrupção entre as gravações exige executar a extração novamente. O hash permite identificar inconsistências ao analisar.

## 7. Validação e transformação

`validar_dados()` verifica esquema, nulos, identificadores repetidos, tipos inteiros e regras de valores. O banco também aplica restrições: controles nas duas camadas ajudam a detectar problemas em momentos diferentes.

`calcular()` trabalha com centavos inteiros e cria três colunas. Essa escolha evita usar frações binárias para representar centavos durante somas e multiplicações. Ticket e margem usam divisão e arredondamento na apresentação.

```python
df.groupby('categoria')[metricas].sum().reset_index()
```

`groupby` separa por categoria; a seleção escolhe as métricas; `sum` soma; `reset_index` devolve a categoria como uma coluna comum.

O mês é obtido dos sete primeiros caracteres da data ISO: `2026-01`. Como datas foram validadas, o agrupamento é consistente.

## 8. Períodos sem dados

Ausência de vendas é um resultado válido. O projeto exporta CSV com cabeçalhos, resumos vazios e totais zero. Ticket e margem ficam `null` no JSON Python, pois divisão por zero não tem interpretação adequada. No R os indicadores correspondentes ficam `NA`.

## 9. DBI em R

DBI é a interface; RSQLite e RPostgres implementam a comunicação com cada banco.

```r
rs <- DBI::dbSendQuery(con, sql)
DBI::dbBind(rs, list("concluida", inicio, fim))
parte <- DBI::dbFetch(rs, n = lote)
```

O script reutiliza a consulta SQL do projeto e adapta somente os marcadores: `?` em SQLite e `$1`, `$2`, `$3` em PostgreSQL. Os valores não são inseridos por concatenação.

`dbGetQuery()` aparece no teste simples de conexão; para o exercício de extração em partes usamos explicitamente `dbSendQuery`, `dbBind`, `dbFetch` e `dbClearResult`.

A função interna `buscar()` registra a liberação do resultado com `on.exit()`. Quando ela termina, o resultado já foi liberado. A função externa `main()` desconecta ao terminar. Isso mantém a ordem correta de limpeza.

## 10. Python iniciando R

```python
subprocess.run([executavel_r, caminho_script, ...], check=True)
```

Uma lista de argumentos preserva caminhos com espaços. O programa não monta uma linha de shell com valores concatenados. `check=True` faz a etapa falhar se R terminar com código de erro, em vez de anunciar sucesso.

A configuração PostgreSQL é passada no ambiente do processo, não como senha em argumentos da linha de comando. O projeto não imprime a senha.

## 11. Evidência e reprodutibilidade

`metadados.json` registra a consulta por hash, recorte, data UTC, número de linhas, hash do CSV extraído, hashes dos CSVs de origem e versões Python. Os hashes dos arquivos de origem identificam a semente local; não garantem que um banco existente ainda corresponda à semente se alguém o tiver alterado. O CSV extraído e seu hash representam o resultado real dessa execução.

Para reproduzir, preserve juntos: código, dependências, banco ou dados de origem aplicáveis, parâmetros, CSV extraído e metadados. Um hash sozinho não reconstrói o arquivo perdido.

O projeto é para uso local por uma pessoa. Não oferece bloqueio para duas execuções simultâneas na mesma pasta de saída. Para experimentos paralelos, use pastas distintas.
