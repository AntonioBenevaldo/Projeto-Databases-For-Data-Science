# Projeto 03 — Videoaula 15

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

## Automação de consultas e criação de pipelines de dados

**Tema:** atualização automática de um relatório de faturamento com pedidos novos, alterações e cancelamentos.

Preparado para Benevaldo a partir da seção “Videoaula 15 — Automação de consultas e criação de pipelines de dados” do PDF *CONTEÚDO DESTA UNIDADE 4*, da disciplina Databases for Data Science. A organização em módulos segue a ideia do print fornecido. A implementação é própria e didática; o vídeo e o código original do professor não foram acessados.

O projeto é independente dos Projetos 01 e 02. Todas as etapas são iniciadas com comandos Python no terminal do VS Code. Não exige JupyterLab, Docker, R ou um servidor de banco: usa dois arquivos SQLite locais.

## 1. O que o projeto faz

1. Prepara um banco de origem com pedidos simulados e um histórico sequencial de alterações.
2. Consulta apenas os eventos posteriores ao último evento carregado.
3. Valida estrutura, tipos, datas, status, quantidades e valores.
4. Padroniza categorias e calcula faturamento, custo e lucro bruto.
5. Atualiza o destino por chave de pedido, sem duplicar registros.
6. Recalcula o resumo de vendas concluídas.
7. Confirma os dados e o marcador de progresso juntos, na mesma transação.
8. Registra tentativas, duração, erros e resultados.
9. Exporta CSVs e um relatório legível.
10. Pode repetir o fluxo automaticamente enquanto o terminal estiver aberto.

| Conceito da aula | Aplicação |
|---|---|
| Parametrização | SQL com `:desde`, `:ate` e `:limite` |
| Incrementalidade | Consulta pelo número sequencial do evento |
| Idempotência | Upsert por pedido e proteção contra versões antigas |
| Dependências | Extração → validação → transformação → carga |
| Transação | Dados, resumo, checkpoint e registro de sucesso confirmados juntos |
| Retentativas | Falhas transitórias com espera progressiva |
| Observabilidade | Histórico no banco, logs JSONL e alertas locais |
| Rastreabilidade | Parâmetros, hashes dos arquivos e do código, versões e horários UTC |
| Agenda local | Repetição por intervalo, com quantidade de ciclos definida |

## 2. Preparação do ambiente

Use os quatro comandos da seção “Começar no seu Windows com Python 3.14”, no início deste README. O restante do guia usa o mesmo iniciador `executar.py`.

## 3. Executar o fluxo inicial

```bash
py -3.14 executar.py tudo
```

`tudo` executa **preparar + executar**, com os dados disponíveis. Não cria automaticamente o segundo lote: esse lote é um exercício explícito.

Na primeira execução, você deve obter:

| Indicador | Resultado inicial |
|---|---:|
| Eventos lidos | 6 |
| Pedidos no destino | 6 |
| Pedidos concluídos | 4 |
| Faturamento após descontos | R$ 575,00 |
| Custo dos pedidos concluídos | R$ 370,00 |
| Lucro bruto | R$ 205,00 |
| Último evento confirmado | 6 |

Os pedidos pendentes e cancelados permanecem no destino para preservar seu estado, mas não entram nos indicadores de faturamento.

O terminal imprime a pasta de saída da execução: `outputs/execucoes/<run_id>/`. Cada execução tem um identificador diferente, para preservar seus arquivos.

## 4. Etapa 1 — Preparar origem e destino

```bash
py -3.14 executar.py preparar
```

Cria:

- `data/origem.db`: tabelas `pedidos`, `eventos` e `lotes_demo`;
- `data/analitico.db`: tabelas `pedidos_analiticos`, `resumo_diario`, `controle` e `execucoes`.

A origem possui seis pedidos iniciais. Cada criação/alteração produz um evento com a fotografia completa do pedido. Pedido e evento são gravados na mesma transação na origem.

`preparar` não apaga um banco existente e não reaplica o lote inicial. Para começar novamente do zero, use outra pasta:

```bash
py -3.14 executar.py tudo --pasta execucoes/novo_estudo
```

Se escolher outra pasta, repita `--pasta` em todos os comandos daquele estudo.

## 5. Etapa 2 — Executar o pipeline

```bash
py -3.14 executar.py executar
```

### Extração

O programa lê o `ultimo_evento` confirmado no destino. Na origem, consulta eventos com sequência maior que esse marcador e menor ou igual ao máximo disponível no início da consulta.

A consulta SQL está em `src/queries/extrair.sql`. Os valores são enviados como parâmetros, separados do SQL. A ordenação é pela sequência do evento.

O limite padrão é 100 eventos por execução. Para estudar lotes pequenos, use uma pasta nova:

```bash
py -3.14 executar.py preparar --pasta execucoes/lotes_pequenos
py -3.14 executar.py executar --pasta execucoes/lotes_pequenos --limite 2
py -3.14 executar.py executar --pasta execucoes/lotes_pequenos --limite 2
py -3.14 executar.py executar --pasta execucoes/lotes_pequenos --limite 2
```

Os checkpoints avançam para **2, 4 e 6**. O marcador não pula até o evento 6 quando só os dois primeiros foram lidos. O terminal mostra `eventos_ainda_pendentes` para indicar que restam eventos além do lote.

### Validação

Confere colunas, valores ausentes, sequência de eventos, IDs, quantidades, moedas em centavos, descontos, datas e status. Uma falha de qualidade interrompe o lote inteiro. O destino e o checkpoint não avançam parcialmente.

O projeto não descarta silenciosamente um registro inválido. A causa deve ser corrigida antes da retomada.

### Transformação

Padroniza categorias para minúsculas, calcula as métricas e mantém a versão de maior sequência quando um pedido tem vários eventos no mesmo lote.

```text
faturamento = quantidade × preço unitário − desconto total
custo total = quantidade × custo unitário
lucro bruto = faturamento − custo total
```

Todos os cálculos monetários do pipeline usam centavos inteiros. `57500` representa R$ 575,00. O desconto é o total do pedido, não por unidade.

### Carga e confirmação

A tabela analítica possui uma chave primária por pedido. O programa insere pedidos novos e atualiza os existentes somente se a sequência recebida for mais recente.

Na mesma transação do destino, ele:

1. confere se o checkpoint ainda é o esperado;
2. aplica as versões novas dos pedidos;
3. recalcula `resumo_diario`, filtrando status `concluido`;
4. atualiza o checkpoint;
5. registra sucesso na tabela `execucoes`;
6. confirma o conjunto com `commit`.

Se ocorrer erro antes do commit, essas alterações são revertidas. O resumo é pequeno e recalculado por inteiro nesta versão; a consulta de origem e a atualização dos pedidos são incrementais.

### Exportação

Depois do commit, os arquivos de relatório são exportados. O banco é a fonte oficial do resultado. Se a exportação falhar, o programa avisa que a carga já foi confirmada. Para recuperar o relatório, use:

```bash
py -3.14 executar.py relatorio
```

## 6. Confirmar que repetir não duplica

Depois da carga inicial:

```bash
py -3.14 executar.py executar
```

**Esperado:** zero eventos novos, zero pedidos alterados, checkpoint 6 e os mesmos totais. Uma nova linha de histórico é registrada porque houve outra execução; isso não é duplicação de pedidos.

Para reler os eventos antigos de propósito:

```bash
py -3.14 executar.py executar --desde-evento 0
```

Esse comando relê os eventos posteriores ao zero. Versões já aplicadas não são gravadas novamente como novas vendas. O checkpoint não retrocede. Você não pode usar `--desde-evento` maior que o checkpoint, pois isso pularia eventos ainda não carregados.

## 7. Simular novos pedidos, alterações e cancelamento

```bash
py -3.14 executar.py simular-lote
py -3.14 executar.py executar
```

O lote acrescenta cinco eventos:

| Evento | Pedido | Alteração |
|---|---:|---|
| 7 | 2 | Quantidade muda de 1 para 2 |
| 8 | 3 | Pedido pendente passa a concluído |
| 9 | 4 | Pedido concluído é cancelado |
| 10 | 7 | Novo pedido concluído |
| 11 | 8 | Novo pedido com data de venda antiga |

**Resultado após carregar o lote:**

| Indicador | Antes | Depois |
|---|---:|---:|
| Pedidos no destino | 6 | 8 |
| Pedidos concluídos | 4 | 6 |
| Faturamento | R$ 575,00 | R$ 1.045,00 |
| Custo | R$ 370,00 | R$ 655,00 |
| Lucro bruto | R$ 205,00 | R$ 390,00 |
| Checkpoint | 6 | 11 |

A conta do faturamento é: **575 + 200 + 120 − 50 + 150 + 50 = 1.045 reais**.

O pedido 8 é um exemplo de chegada tardia: sua venda ocorreu em 01/01, mas seu evento foi registrado depois. Usar apenas a data da venda para incrementalidade poderia ignorá-lo; a sequência do evento permite capturá-lo.

`simular-lote` aplica esse lote apenas uma vez. Repetir o comando não gera novos pedidos indefinidamente. Para refazer a demonstração, use uma nova `--pasta`.

## 8. Consultar resultados e histórico

```bash
py -3.14 executar.py relatorio
py -3.14 executar.py historico
```

`relatorio` lê uma fotografia consistente do destino e exporta:

- `pedidos_analiticos.csv`;
- `resumo_diario.csv`;
- `indicadores.json`;
- `relatorio.md`;
- `manifesto_exportacao.json`.

`historico` mostra as últimas 20 execuções, com status, tentativas, eventos lidos, pedidos alterados e checkpoints.

Cada execução também produz um log `outputs/execucoes/<run_id>.jsonl`. Cada linha é um evento do processo, como início, extração, retentativa e commit confirmado. A pasta da execução guarda os eventos extraídos, os pedidos transformados e os metadados.

Para visualizar os textos Markdown no VS Code, abra o arquivo e use **Ctrl+Shift+V**.

## 9. Automatizar pelo terminal

Para executar três ciclos, esperando cinco segundos entre o término de um ciclo e o início do próximo:

```bash
py -3.14 executar.py automatizar --intervalo 5 --repeticoes 3
```

A primeira execução é imediata. O próximo ciclo começa após terminar o anterior e aguardar o intervalo. Portanto, não é uma agenda de horários fixos: a duração do trabalho também compõe o tempo entre os inícios.

Para estudar com mais tempo:

```bash
py -3.14 executar.py automatizar --intervalo 30 --repeticoes 10
```

Enquanto esse comando estiver rodando, você pode abrir **outro terminal na mesma pasta** e executar `simular-lote`. O próximo ciclo que consultar a origem encontrará os eventos novos. Essa demonstração exige que o lote ainda não tenha sido aplicado naquela pasta.

**Condições desta automação:** o computador precisa estar ligado e o processo Python precisa continuar aberto. `Ctrl+C` interrompe. Fechar o terminal encerra a agenda. Não é instalado serviço, tarefa do Windows ou agenda no ChatGPT.

Uma falha permanente interrompe os ciclos e retorna erro, para não esconder um problema de dados. Falhas transitórias são retentadas dentro do ciclo. Com poucos ciclos e `--limite` pequeno, pode restar backlog; confira `eventos_ainda_pendentes`.

## 10. Simular uma falha transitória e observar o retry

```bash
py -3.14 executar.py executar --falha transitoria --desde-evento 0
```

A primeira tentativa falha de propósito antes da extração. A segunda tenta novamente. O terminal mostra `RETRY` e, no cenário normal, a execução termina com sucesso e `tentativas: 2`.

O padrão permite até três tentativas. As esperas são 1 e 2 segundos. Você pode ajustar:

```bash
py -3.14 executar.py executar --falha transitoria --tentativas 3 --espera 2 --desde-evento 0
```

O backoff dobra a espera, com teto de 30 segundos. Na implementação, apenas a falha simulada transitória, bloqueios temporários SQLite e conflito de checkpoint são considerados retentáveis. Erros de esquema, qualidade ou programação não são repetidos indiscriminadamente.

## 11. Simular erro de qualidade

```bash
py -3.14 executar.py executar --falha qualidade --desde-evento 0
```

O programa muda uma quantidade **somente na cópia em memória** para um valor negativo, produz um erro intencional, registra a falha e cria um alerta JSON em `outputs/alertas`. A origem não é corrompida.

O checkpoint e os dados publicados permanecem como estavam. Retome sem a simulação:

```bash
py -3.14 executar.py executar
```

Se os eventos já estavam carregados antes do teste, a retomada naturalmente encontrará zero eventos novos. O arquivo de eventos extraídos da execução com falha representa o que foi lido da origem antes da alteração artificial em memória.

## 12. Demonstrar rollback e retomada

Use uma pasta separada para obter exatamente os resultados abaixo:

```bash
py -3.14 executar.py tudo --pasta execucoes/rollback
py -3.14 executar.py simular-lote --pasta execucoes/rollback
py -3.14 executar.py executar --pasta execucoes/rollback --falha carga
py -3.14 executar.py relatorio --pasta execucoes/rollback
```

O terceiro comando falha de propósito depois de tentar gravar os pedidos, antes do commit. O relatório ainda deve mostrar **R$ 575,00 e checkpoint 6**.

Agora retome:

```bash
py -3.14 executar.py executar --pasta execucoes/rollback
```

**Esperado:** cinco eventos processados, faturamento **R$ 1.045,00**, checkpoint **11**. O programa não perdeu o lote porque não avançou o marcador durante a falha.

## 13. Executar os testes

```bash
py -3.14 executar.py testar
```

Procure **`Ran 22 tests` e `OK`**. Os testes criam bancos temporários e não alteram seus bancos de estudo.

Cobrem: totais iniciais, repetição vazia, lote incremental, replay antigo, paginação, retries, falha de qualidade, rollback de upsert, rollback do resumo, lotes repetidos, checkpoint obsoleto, chegada tardia, múltiplos eventos por pedido, impedimento de pular eventos, schema/faixas, ordem, automação, logs, exportação, parâmetros SQL e argumentos inválidos.

O relatório de validação informa o que foi efetivamente executado nesta entrega. A aprovação dos testes não equivale a certificação de um sistema de produção.

## 14. Organização semelhante ao print

| Arquivo/pasta | Responsabilidade |
|---|---|
| `projeto.py` | Comandos do terminal |
| `scripts/init_db.py` | Atalho de preparação |
| `scripts/inspect_results.py` | Atalho de relatório |
| `scripts/run_pipeline.py` | Atalho para uma execução |
| `src/config.py` | Pastas e contrato de colunas |
| `src/db.py` | Engines, conexões e transações |
| `src/demo.py` | Dados e alterações simuladas |
| `src/extract.py` | Consulta incremental parametrizada |
| `src/validate.py` | Regras de qualidade |
| `src/transform.py` | Métricas e última versão por pedido |
| `src/load.py` | Upsert, resumo e checkpoint atômicos |
| `src/pipeline.py` | Coordenação, retries e ciclos |
| `src/observe.py` | Logs, indicadores e relatórios |
| `src/queries/` | Consultas e estruturas SQL |
| `docs/` | Explicação do código, exercícios e dicionário |
| `evidencias/` | Resultados reais da validação desta entrega |

Os atalhos abaixo são equivalentes aos comandos principais; não precisa executar as duas formas:

```bash
./.venv314/Scripts/python.exe scripts/init_db.py
./.venv314/Scripts/python.exe scripts/run_pipeline.py
./.venv314/Scripts/python.exe scripts/inspect_results.py
```

O projeto local não usa credenciais nem exige `.env`. A pasta é configurada por `--pasta`. Em uma adaptação a servidor com senha, credenciais devem ser configuradas fora do código e não registradas nos logs.

## 15. Resolver problemas

| Situação | Como resolver |
|---|---|
| `python` não encontrado | Configure Python 3.14; se disponível, use `py -3.14` para criar a venv. |
| `can't open file projeto.py` | Abra o terminal na pasta principal do projeto. |
| Dependência ausente | Instale requirements.txt usando o mesmo Python da venv. |
| `SyntaxError` ao colar comando | Saia de `>>>` com `exit()` e use o terminal Bash/PowerShell/CMD. |
| `no such table` | Execute `preparar` na mesma `--pasta`. |
| Nenhum evento novo | Pode ser resultado correto: todos já foram carregados. Use `simular-lote` uma vez para criar alterações. |
| Lote já aplicado | Use outra pasta se quiser repetir a demonstração desde o início. |
| Erro ao usar `--desde-evento` | O valor deve ser não negativo e não maior que o checkpoint atual. |
| Banco bloqueado | Aguarde outro processo terminar; o pipeline retenta os bloqueios transitórios cobertos. |
| Falha com `--falha qualidade` ou `--falha carga` | É intencional. Reexecute sem essa opção após observar o resultado. |
| Aviso de exportação | A carga pode já estar confirmada. Execute `relatorio` e confira `historico`. |
| Status ficou `executando` após desligamento | Pode ter havido interrupção antes do encerramento. Confira o checkpoint e execute novamente; não edite o marcador manualmente. |

Para Linux/macOS, use `python3.14 executar.py instalar` e troque `py -3.14` por `python3.14` nos comandos. O iniciador seleciona automaticamente `.venv314/bin/python`.

## 16. Limites e referências

Esta é uma orquestração local e didática. Não instala Airflow, não envia e-mails, não agenda tarefas do sistema operacional e não executa consultas em serviços externos.

O log de eventos é criado pelo próprio gerador, não por um conector CDC real. Ele pressupõe que o histórico seja preservado e que toda alteração relevante gere um novo evento. Cancelamento é representado por status; exclusões físicas arbitrárias da origem não são propagadas. Não substitua `origem.db` por outro banco mantendo o destino antigo.

O lote é carregado em memória, limitado por `--limite`, e o resumo inteiro é recalculado. A versão não oferece escala distribuída, retenção automática de logs, recuperação automática de processos interrompidos ou garantia de disponibilidade contínua. As saídas por execução ficam preservadas e ocupam espaço ao longo do uso.

Os valores são simulados. O lucro bruto não desconta tributos ou despesas administrativas e não é lucro líquido.

Pipeline e testes executados em Linux/Python 3.14. As instruções Windows foram preparadas, mas não executadas em Windows nesta sessão.

Fontes consultadas em 21/09/2026:

- PDF enviado: *Databases for Data Science — Unidade IV*, seção Videoaula 15.
- pandas — escrita SQL: https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_sql.html
- SQLAlchemy — conexões e transações: https://docs.sqlalchemy.org/en/20/core/connections.html
- SQLAlchemy — SQLite e upsert: https://docs.sqlalchemy.org/en/20/dialects/sqlite.html
- Python — tempo e relógio monotônico: https://docs.python.org/3.14/library/time.html

As versões Python utilizadas estão fixadas em requirements.txt e registradas nos metadados. A documentação online pode apresentar versões posteriores.

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
