# Videoaula 13 — Banco de dados, Python e R no terminal

## Começar no seu Windows com Python 3.14

Esta é a edição atualizada para **CPython 3.14 de 64 bits (Windows x64)**. Use uma pasta nova para extrair este pacote e mantenha os estudos antigos separados. Não copie bancos, modelos ou ambientes virtuais da edição anterior.

Abra no VS Code a pasta deste projeto, onde estão `executar.py`, `projeto.py` e `requirements.txt`, e abra **Terminal > Novo Terminal**. Os comandos abaixo são iguais no **Git Bash, PowerShell e CMD**:

```bash
py -3.14 --version
py -3.14 executar.py instalar
py -3.14 executar.py tudo
py -3.14 executar.py testar
```

Execute um comando por vez; se houver erro, resolva essa etapa antes de continuar. `instalar` cria a `.venv314` dentro deste projeto, usa o Python 3.14 que chamou o script, instala apenas pacotes prontos e mostra o diagnóstico. Pode levar alguns minutos. Precisa de internet na primeira instalação. Não precisa executar `activate` nem recriar manualmente a venv.

O comando `py -3.14 --version` deve mostrar **3.14.x**. Se `py` não existir, confira `python --version`; somente se mostrar 3.14.x, substitua `py -3.14` por `python` em todos os comandos. Se aparecer `>>>`, saia com `exit()`; os comandos são para o terminal que inicia o programa Python.

Se aparecer “não foi possível abrir executar.py”, a pasta do terminal ainda está errada. No Explorador do VS Code, clique com o botão direito na pasta que contém esse arquivo e selecione **Abrir no Terminal Integrado**. No Bash, `pwd` mostra a pasta e `ls` lista os arquivos; no PowerShell, use `Get-Location` e `dir`.

Leia também `evidencias/RELATORIO_VALIDACAO.md` para o escopo dos testes desta edição. R e PostgreSQL/Docker, quando usados, continuam exigindo seus próprios programas.


**Projeto didático: análise de vendas e faturamento.**

Preparado para Benevaldo, com base na seção “Videoaula 13 — Conexão com Python e R para extração e análise (pandas, DBI, SQLAlchemy)” do PDF *CONTEÚDO DESTA UNIDADE 4*, da disciplina Databases for Data Science. O projeto é uma implementação didática própria baseada no texto fornecido e no print; não é uma reprodução do código do professor nem pressupõe acesso ao vídeo.

## 1. O que você vai construir

Um fluxo que cria um banco, carrega vendas simuladas, consulta apenas vendas concluídas, transfere os resultados para Python ou R, calcula indicadores e salva arquivos para conferência.

| Etapa | Tecnologia | Resultado |
|---|---|---|
| Armazenar | SQLite; PostgreSQL opcional | Produtos e vendas relacionados |
| Conectar em Python | SQLAlchemy | Engine e conexões gerenciadas |
| Extrair em Python | pandas + SQL parametrizado | DataFrame e CSV por lotes |
| Analisar em Python | pandas | Indicadores e agrupamentos |
| Conectar e extrair em R | DBI + RSQLite ou RPostgres | data.frame com os mesmos dados |
| Analisar em R | Funções do R | Indicadores e agrupamentos equivalentes |
| Conferir | unittest e comparador Python/R | Testes e identificação de divergências |

Você inicia as etapas com comandos Python no terminal do VS Code. **R é outra linguagem:** o comando `projeto.py r` chama o executável `Rscript`; por isso R precisa estar instalado para essa etapa. RStudio não é necessário.

Comece com SQLite. O print utiliza PostgreSQL 16 em Docker; essa opção também está incluída, com instruções na seção 10. Os conceitos centrais são os mesmos, mas o driver e a infraestrutura mudam.

## 2. Preparação do ambiente

Use os quatro comandos da seção “Começar no seu Windows com Python 3.14”, no início deste README. O restante do guia usa o mesmo iniciador `executar.py`.

## 3. O que a preparação faz

`py -3.14 executar.py instalar` cria um ambiente isolado `.venv314`, instala NumPy, pandas, SQLAlchemy e python-dotenv a partir de pacotes prontos e exibe o diagnóstico. Cada projeto mantém seu próprio ambiente. As etapas seguintes usam `executar.py` para selecionar esse mesmo Python.

## 4. Executar cada etapa com explicação

### Etapa 1 — Preparar o banco

```bash
py -3.14 executar.py preparar
```

**O que acontece:**

1. O SQLAlchemy cria uma Engine apontando para `data/vendas.db`.
2. `sql/schema.sql` cria as tabelas `produtos` e `vendas`, a chave estrangeira e um índice de status/data.
3. pandas lê `data/produtos.csv` e `data/vendas.csv`.
4. `engine.begin()` executa a carga em uma transação: se houver erro, o lote é revertido.
5. Os registros são inseridos por comandos parametrizados.

**Resultado esperado:** 4 produtos e 12 vendas no banco. Rodar novamente preserva registros com o mesmo identificador e não duplica a carga. Essa carga inicial não atualiza vendas já existentes: se você editar um CSV de origem, os IDs existentes no banco continuarão com os valores antigos. Para exercícios de edição, use uma cópia nova da pasta, sem `data/vendas.db`, e prepare novamente.

### Etapa 2 — Extrair dados por lotes

```bash
py -3.14 executar.py extrair --inicio 2026-01-01 --fim 2026-03-31 --lote 4
```

**O que acontece:**

1. Valida datas e tamanho de lote.
2. Abre uma conexão com o banco.
3. Faz `JOIN` entre vendas e produtos.
4. Usa filtros de status e datas diretamente no SQL.
5. Envia valores dos filtros separadamente, sem concatená-los ao SQL.
6. `pd.read_sql_query(..., chunksize=4)` entrega resultados em partes.
7. Cada lote é validado e escrito no CSV, sem juntar todos os lotes na memória nessa etapa.
8. Salva um JSON com período, quantidade de linhas, versões e hashes.

**Resultado esperado:** lotes de 4, 4 e 2 vendas; total de 10. A venda cancelada e a pendente ficam de fora. As duas datas dos filtros são inclusivas.

Arquivos gerados:

- `outputs/python/vendas_extraidas.csv`: fotografia dos dados extraídos;
- `outputs/python/metadados.json`: informações para rastrear e reproduzir a extração.

O hash SHA-256 é uma impressão digital do conteúdo. Ele ajuda a detectar alterações; não é criptografia e não prova a veracidade do dado.

### Etapa 3 — Analisar com pandas

```bash
py -3.14 executar.py analisar
```

**O que acontece:**

1. Confere se o CSV mantém o hash registrado na extração.
2. Abre os dados com pandas e verifica colunas, valores ausentes, duplicidades e regras de negócio.
3. Calcula faturamento após descontos, custo total e lucro bruto por venda.
4. Agrupa por categoria e por mês com `groupby()`.
5. Exibe indicadores no terminal e grava os resultados.

Arquivos adicionais:

- `outputs/python/resumo_categoria.csv`;
- `outputs/python/resumo_mensal.csv`;
- `outputs/python/indicadores.json`.

**Nesta análise didática, o CSV inteiro é carregado em memória.** A extração em lotes limita o volume por lote, mas não torna toda a análise ilimitadamente escalável. Para milhões de linhas, faça agregações no banco ou implemente agregação incremental.

### Etapa 4 — Executar o fluxo Python completo

Depois de conhecer as etapas, você pode usar:

```bash
py -3.14 executar.py tudo
```

Esse comando executa **preparar + extrair + analisar**, na sequência. “Tudo” aqui significa o fluxo Python. As etapas R e PostgreSQL permanecem explícitas porque exigem instalações adicionais.

A cada nova execução, arquivos com o mesmo nome na pasta de saída são substituídos. Para guardar um experimento separado:

```bash
py -3.14 executar.py tudo --inicio 2026-01-01 --fim 2026-01-31 --saida outputs/janeiro
```

## 5. Conferir os resultados esperados

Para o período completo de 01/01/2026 a 31/03/2026:

| Indicador | Resultado |
|---|---:|
| Vendas concluídas | 10 |
| Unidades vendidas | 57 |
| Faturamento após descontos | R$ 1.053,00 |
| Custo das mercadorias vendidas | R$ 630,00 |
| Lucro bruto | R$ 423,00 |
| Ticket médio por venda | R$ 105,30 |
| Margem bruta | 40,17% |

| Mês | Faturamento | Custo | Lucro bruto |
|---|---:|---:|---:|
| Janeiro | R$ 143,00 | R$ 84,00 | R$ 59,00 |
| Fevereiro | R$ 410,00 | R$ 236,00 | R$ 174,00 |
| Março | R$ 500,00 | R$ 310,00 | R$ 190,00 |

| Categoria | Faturamento | Custo | Lucro bruto |
|---|---:|---:|---:|
| Informática | R$ 740,00 | R$ 470,00 | R$ 270,00 |
| Papelaria | R$ 313,00 | R$ 160,00 | R$ 153,00 |

O terminal usa ponto decimal; os CSVs e o JSON guardam valores monetários inteiros em **centavos**, salvo os indicadores cujo nome contém `_reais`. Assim, `105300` significa R$ 1.053,00.

Neste modelo simplificado, **cada linha é uma venda de um único tipo de produto**, com uma ou mais unidades. Não existem pedidos com múltiplas linhas. O desconto é o total da venda, não o desconto por unidade. O preço e o custo unitários são os registrados na venda.

Fórmulas:

```text
faturamento = quantidade × preço unitário − desconto total
custo total = quantidade × custo unitário
lucro bruto = faturamento − custo total
ticket médio = faturamento total ÷ número de vendas
margem bruta (%) = lucro bruto total ÷ faturamento total × 100
```

Exemplo: venda 3 → 1 mouse × R$ 80,00 − R$ 5,00 de desconto = R$ 75,00. Custo: R$ 50,00. Lucro bruto: R$ 25,00.

Esse lucro bruto **não representa lucro líquido**: não desconta tributos, frete, despesas administrativas ou financeiras. O exercício não faz apuração fiscal.

## 6. Testar o projeto

```bash
py -3.14 executar.py testar
```

O comando usa `unittest`, que já acompanha Python. Não precisa instalar pytest.

São 12 testes: totais esperados, repetição da carga, filtro inclusivo de datas, período vazio, equivalência entre tamanhos de lote, parâmetro semelhante a SQL malicioso, quantidade inválida, chave estrangeira, alteração do CSV, duplicidades, argumentos inválidos e divergência entre arquivos comparados.

**Procure `Ran 12 tests` e `OK`.** Há mensagens do pipeline junto ao relatório, e a ordem visual pode variar pela saída do terminal. Os testes usam bancos temporários e não alteram seu banco de estudo.

O teste do comparador usa dois resultados Python para conferir a lógica de comparação. **Ele não executa R.** A comparação real entre linguagens é feita nas próximas etapas.

## 7. Instalar os pacotes de R usando o comando Python

Primeiro instale R no Windows, se ainda não o tiver. Você pode conferir a instalação na pasta `C:\Program Files\R`. Ter RStudio instalado não garante que `Rscript` esteja no PATH do terminal.

Se `Rscript` for encontrado automaticamente:

```bash
py -3.14 executar.py r-instalar
```

Esse comando chama `r/instalar.R`, que instala **DBI e RSQLite** em uma biblioteca pessoal do R, quando necessário. Precisa de internet. Não instala a linguagem R: isso deve ser feito antes.

Se não for encontrado, informe o caminho real do executável:

```bash
py -3.14 executar.py r-instalar --rscript "C:\Program Files\R\R-x.y.z\bin\Rscript.exe"
```

**Substitua `R-x.y.z` pelo nome exato da pasta do seu computador.** O texto acima é um exemplo de caminho, não uma versão a instalar. Se necessário, procure o executável também na subpasta `bin\x64` da sua instalação.

## 8. Extrair e analisar com R, iniciado pelo Python

Depois de executar `preparar` e instalar os pacotes R:

```bash
py -3.14 executar.py r
```

Se precisou informar o caminho do Rscript, repita a opção:

```bash
py -3.14 executar.py r --rscript "C:\Program Files\R\R-x.y.z\bin\Rscript.exe"
```

**Explicação do script R:**

1. `DBI::dbConnect()` cria a conexão usando o driver RSQLite ou RPostgres.
2. `dbGetQuery()` executa uma consulta pequena para conferir a conexão.
3. `dbSendQuery()` prepara a consulta de vendas.
4. `dbBind()` envia os parâmetros separadamente.
5. `dbFetch(n=lote)` busca os resultados em partes.
6. O script reúne os lotes em um `data.frame` para a análise didática.
7. `aggregate()` resume os valores por categoria e mês.
8. `write.csv()` exporta os resultados para `outputs/r`.
9. `dbClearResult()` libera o resultado e `dbDisconnect()` encerra a conexão. `on.exit()` garante a limpeza ao sair das funções.

No exemplo R, os lotes são reunidos em memória antes de analisar: o consumo total cresce com o recorte selecionado. Use períodos pequenos para estudar.

Também são gerados `indicadores.csv` e `metadados_r.txt`, com período, consulta e informações da sessão R. As versões R são registradas, mas não há um arquivo de bloqueio de dependências R neste projeto.

## 9. Comparar os resultados Python e R

Execute ambos para o mesmo banco e período, sem alterar os dados entre eles:

```bash
py -3.14 executar.py tudo
py -3.14 executar.py r
py -3.14 executar.py comparar
```

Esperado: `OK: extracao, resumo por categoria e resumo mensal identicos em Python e R.`

O comparador ordena os registros e confere valores e colunas. Compara dados extraídos e resumos em centavos; não compara datas de execução nem a apresentação do JSON/CSV de indicadores.

Para janeiro em pastas separadas:

```bash
py -3.14 executar.py tudo --inicio 2026-01-01 --fim 2026-01-31 --saida outputs/janeiro_python
py -3.14 executar.py r --inicio 2026-01-01 --fim 2026-01-31 --saida-r outputs/janeiro_r
py -3.14 executar.py comparar --saida outputs/janeiro_python --saida-r outputs/janeiro_r
```

Acrescente `--rscript` ao comando R se necessário.

## 10. Opção PostgreSQL + Docker, próxima ao ambiente do print

Faça esta parte depois do fluxo SQLite. Ela exige Docker Desktop instalado e em execução, com suporte a contêineres Linux e Docker Compose com `--wait`. Não é preciso instalar PostgreSQL diretamente no Windows.

```bash
./.venv314/Scripts/python.exe -m pip install --only-binary=:all: -r requirements-postgres.txt
py -3.14 executar.py configurar-postgres
py -3.14 executar.py postgres-iniciar
py -3.14 executar.py tudo --banco postgres --saida outputs/postgres_python
```

**Explicação:**

- `psycopg` é o driver Python do PostgreSQL.
- `configurar-postgres` cria `.env` com senha aleatória; preserva um `.env` existente.
- `postgres-iniciar` chama `docker compose up -d --wait`, baixa a imagem PostgreSQL 16 quando necessário e espera o healthcheck.
- O servidor fica acessível somente em `127.0.0.1`. Os dados ficam em volume Docker persistente.
- A criação das tabelas e a carga são feitas pelo Python; não dependem de uma pasta de inicialização do contêiner.
- `--banco postgres` seleciona PostgreSQL. Sem essa opção, o comando usa SQLite.
- `URL.create()` monta a conexão sem concatenar usuário e senha. As credenciais não são impressas no terminal pelo projeto.

Para R com PostgreSQL:

```bash
py -3.14 executar.py r-instalar --banco postgres
py -3.14 executar.py r --banco postgres --saida-r outputs/postgres_r
py -3.14 executar.py comparar --saida outputs/postgres_python --saida-r outputs/postgres_r
```

Use `--rscript` quando necessário. Nesse modo, o pacote R é **RPostgres**. O processo Python carrega `.env` e passa as variáveis ao processo R.

Para parar o servidor sem apagar os dados:

```bash
py -3.14 executar.py postgres-parar
```

O arquivo `.env` está excluído pelo `.gitignore` e não acompanha a entrega. Não publique senhas. Se a porta 5432 estiver ocupada, configure outra porta em `PGPORT` no `.env` antes de iniciar. Se o volume já foi inicializado, mudar a senha no `.env` não muda automaticamente a senha dentro do PostgreSQL.

## 11. Arquivos para estudar

| Arquivo/pasta | Finalidade |
|---|---|
| `projeto.py` | Recebe os comandos e organiza as etapas |
| `app/pipeline.py` | Conexão, carga, extração, análise e comparação |
| `sql/schema.sql` | Estrutura e regras do banco |
| `sql/extracao.sql` | Consulta parametrizada compartilhada pelas linguagens |
| `data/*.csv` | Dados simulados, editáveis em uma cópia de estudo |
| `r/instalar.R` | Instala dependências de R |
| `r/analisar.R` | Conecta, extrai e analisa em R |
| `tests/test_pipeline.py` | Testes de comportamento em SQLite |
| `docs/EXPLICACAO_DO_CODIGO.md` | Leitura guiada do código e conceitos |
| `docs/EXERCICIOS.md` | Exercícios, comandos e respostas esperadas |
| `evidencias/` | Relatório e resultados da execução de validação |
| `outputs/` | Resultados que você vai produzir ao executar |

Os CSVs são arquivos de dados. Não são programas: execute `projeto.py`, não o CSV. Para visualizar os textos Markdown no VS Code, abra o arquivo e use **Ctrl+Shift+V**.

## 12. Resolver problemas comuns

| Mensagem/situação | Como resolver |
|---|---|
| `can't open file ... projeto.py` | Abra o terminal na pasta que contém `projeto.py`. |
| `No module named ...` | Rode o `pip install` com o mesmo `.venv314/Scripts/python.exe` usado para executar. |
| `.venv314/Scripts/python.exe` não existe | Crie o ambiente com `py -3.14 executar.py instalar`; confira se o terminal está na pasta correta. |
| `SyntaxError` ao digitar um comando | Saia de `>>>` com `exit()` e execute no PowerShell. |
| Tabela não encontrada | Execute `preparar` para o banco selecionado. |
| CSV ou metadados não encontrados | Execute `extrair` antes de `analisar`, usando a mesma `--saida`. |
| CSV alterado após extração | Rode `extrair` novamente; não edite o CSV de evidência antes de analisar. |
| R não localizado | Instale R ou use `--rscript` com o caminho real. |
| Falha na etapa R | Rode `r-instalar` para o banco escolhido; confira se `preparar` foi executado e se o servidor está ativo. |
| Falha para instalar RPostgres | Confira os avisos da instalação; instalações a partir de código-fonte podem exigir ferramentas de compilação e bibliotecas PostgreSQL. |
| Falha PostgreSQL | Abra Docker Desktop; confira `.env`, a porta e o comando `postgres-iniciar`. |
| Comparação divergiu | Execute Python e R com o mesmo banco, período e pastas; não altere a origem entre execuções. |
| Sem vendas | Confira o período: a demonstração tem vendas de janeiro a março de 2026. |

Para Linux/macOS, use `python3.14 executar.py instalar` e troque `py -3.14` por `python3.14` nos comandos. O iniciador seleciona automaticamente `.venv314/bin/python`.

## 13. Limites e referências

Projeto local de estudo, com produtos e transações simulados, sem cadastros de pessoas. Não inclui API, interface web, machine learning, agendamento automático nem implantação. O foco é a Videoaula 13.

SQLite/Python foi executado e testado. R e PostgreSQL/Docker não estavam disponíveis no ambiente de validação: os arquivos dessas etapas foram elaborados e revisados, mas precisam de execução local. Veja o registro em `evidencias/RELATORIO_VALIDACAO.md`.

Referências técnicas consultadas em 21/09/2026:

- Material enviado: *Databases for Data Science — Unidade IV*, seção Videoaula 13.
- pandas — leitura SQL: https://pandas.pydata.org/docs/reference/api/pandas.read_sql.html
- SQLAlchemy — conexões e transações: https://docs.sqlalchemy.org/en/20/tutorial/dbapi_transactions.html
- DBI — conexão: https://dbi.r-dbi.org/reference/dbConnect.html
- DBI — consulta: https://dbi.r-dbi.org/reference/dbGetQuery.html
- DBI — parâmetros: https://dbi.r-dbi.org/reference/dbBind.html
- RSQLite — driver: https://rsqlite.r-dbi.org/reference/SQLite.html
- RPostgres — consultas: https://rpostgres.r-dbi.org/reference/postgres-query.html

A documentação online pode mostrar versões posteriores às fixadas neste projeto. As versões Python efetivamente utilizadas constam nos metadados e no relatório de validação.

## Atualização para Python 3.14 — 24/09/2026

- pandas 2.3.3 substitui 2.2.3 nos projetos que usam pandas.
- NumPy 2.3.5 é fixado nesses projetos para reproduzir o ambiente da revisão.
- O Projeto 4 usa cryptography 46.0.7.
- `executar.py` prepara o ambiente com pacotes binários e encaminha comandos para `projeto.py`.
- Os exercícios e explicações das etapas foram preservados; os exemplos principais usam `py -3.14 executar.py`.
- Não reutilize modelos `.joblib` nem ambientes virtuais da edição anterior. O Projeto 2 treina novos modelos com `tudo`.

Referências da atualização:
- pandas 2.3.3 e Python 3.14: https://pandas.pydata.org/pandas-docs/version/2.3/whatsnew/v2.3.3.html
- scikit-learn 1.8: https://scikit-learn.org/1.8/whats_new/v1.8.html
- cryptography 46.0.7: https://cryptography.io/en/46.0.7/changelog/
