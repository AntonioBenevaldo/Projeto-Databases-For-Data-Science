# Explicação do código — Projeto 03

## 1. ETL e orquestração

**ETL** é extrair, transformar e carregar os dados. **Orquestrar** é coordenar a ordem, as dependências, as tentativas e a agenda. No projeto, `extract.py`, `transform.py` e `load.py` cuidam do ETL; `pipeline.py` coordena a execução, usa `validate.py` como critério de entrada e registra os acontecimentos com `observe.py`.

A automação do terminal é um coordenador simples. Um orquestrador como Airflow teria outras capacidades de agenda e monitoramento, mas não é necessário para estudar os fundamentos aqui.

## 2. Caminhos e Engines

`Path` representa caminhos sem fixar nomes de usuário. `--pasta` define onde ficam os bancos e resultados. O código continua na pasta original do projeto.

`bancos()` cria uma Engine SQLAlchemy para cada arquivo SQLite e as libera ao terminar. Os eventos de conexão configuram transações explícitas, inclusive para operações feitas pelo pandas. Isso evita depender de particularidades do modo legado de transação do driver SQLite.

## 3. Origem e histórico de eventos

A tabela `pedidos` guarda o estado atual. A tabela `eventos` guarda fotografias sequenciais de alterações. `event_seq` é uma chave inteira crescente, gerada pelo SQLite.

`aplicar()` grava o estado atual e seu evento dentro da mesma transação. A marca em `lotes_demo` impede reaplicar o mesmo lote de demonstração. Se uma inserção falhar, a marca também é revertida.

O histórico é um modelo didático semelhante a um log de alterações. Não há captura automática de toda instrução SQL: se alguém alterar `pedidos` manualmente sem registrar um evento, o pipeline não saberá dessa mudança. Preserve a disciplina do produtor ou implemente captura real em uma evolução.

## 4. Incrementalidade por sequência

```sql
WHERE event_seq > :desde AND event_seq <= :ate
ORDER BY event_seq
LIMIT :limite
```

`:desde` é o último evento confirmado, `:ate` é o máximo observado na mesma fotografia da origem e `:limite` restringe o tamanho do lote. Os valores não são concatenados ao texto SQL.

Datas de negócio e ordem de captura são coisas diferentes. Um pedido de 01/01 pode chegar depois de pedidos de 03/01. A sequência identifica o que mudou na origem, enquanto `data_venda` determina o dia no relatório.

O checkpoint avança até o máximo efetivamente lido. Se existe evento 100, mas foram lidos apenas 1 a 10, ele vai para 10, não para 100.

## 5. Contrato de qualidade

`validar()` recusa:

- estrutura de colunas diferente;
- campos ausentes;
- eventos repetidos ou fora de ordem;
- IDs/quantidades não positivos;
- números fracionários onde se espera inteiro;
- valores negativos ou acima dos limites didáticos;
- descontos superiores ao valor bruto;
- status desconhecidos;
- categorias vazias;
- datas inválidas e timestamps sem fuso.

O lote inválido não é publicado parcialmente. Uma implementação de quarentena exigiria uma política explícita de retomada e de checkpoint; o projeto usa a opção mais simples: interromper e corrigir.

## 6. Transformação e granularidade

Cada pedido representa um tipo de item com quantidade. `transformar()` normaliza categoria e calcula valores em centavos inteiros.

Se há vários eventos de um pedido no lote, `sort_values` e `drop_duplicates(keep='last')` mantêm sua última fotografia. Por isso um lote pode ler 11 eventos e alterar somente 8 pedidos.

Isso é apropriado para uma tabela de **estado atual por pedido**. Não é uma tabela de todos os movimentos contábeis nem um razão financeiro. O histórico integral permanece na origem e nas extrações, enquanto o destino guarda a última versão de cada pedido.

## 7. Upsert e replay seguro

A carga usa `INSERT ... ON CONFLICT(pedido_id) DO UPDATE`, com a condição:

```sql
WHERE excluded.event_seq > pedidos_analiticos.event_seq
```

Um pedido novo é inserido. Um pedido existente recebe apenas uma versão mais recente. Versões iguais e antigas não sobrescrevem o estado atual. Isso permite repetir uma extração e evita que um replay antigo desfaça um cancelamento mais novo.

A idempotência diz respeito aos dados analíticos: mesmos eventos não geram vendas duplicadas. Logs e histórico de execução recebem novos registros em cada tentativa ou execução, como se espera de uma auditoria.

## 8. O que a transação protege

`carregar()` usa `with destino.begin()` para reunir:

- atualização dos pedidos;
- recomposição do resumo;
- avanço do checkpoint;
- registro de sucesso no histórico.

Se qualquer uma dessas operações falhar, o bloco é revertido. O teste de falha do `to_sql` verifica que apagar o resumo e falhar ao regravá-lo não deixa a tabela vazia nem o checkpoint adiantado.

O pandas recebe uma conexão SQLAlchemy já em transação ao escrever o resumo. A confirmação pertence ao bloco da carga.

Há dois bancos físicos. A leitura da origem e a carga do destino não são uma única transação distribuída. A segurança da retomada depende da preservação do log da origem e da atomicidade entre dados e checkpoint no destino.

## 9. Concorrência

No início da carga, uma atualização condicional confere o checkpoint esperado e obtém o bloqueio de escrita no destino. Se outra execução já avançou o marcador, a carga é recusada com `Concorrencia` e o fluxo pode refazer a extração.

Isso não transforma SQLite em um banco distribuído. O projeto é local e os testes verificam o comportamento de checkpoint obsoleto; não foi realizado teste de estresse multiusuário. Evite iniciar muitas agendas na mesma pasta.

## 10. Retentativas e espera progressiva

`transitoria()` reconhece somente falhas que o projeto trata como recuperáveis: bloqueio temporário SQLite, conflito de checkpoint ou falha transitória simulada.

`time.sleep()` faz a espera; `time.monotonic()` mede a duração sem depender de ajustes do relógio de calendário. O delay dobra a cada nova tentativa, até 30 segundos.

Erro de qualidade não melhora simplesmente esperando, portanto é encerrado sem retries. Cada retentativa registra motivo e duração da espera no JSONL.

## 11. Estado da execução e alertas

Antes de extrair, a tabela `execucoes` recebe `executando`. O sucesso é confirmado junto com a carga. Uma falha tratada registra `falha` depois do rollback, em uma transação separada, e produz um alerta JSON local.

Um encerramento abrupto pode deixar `executando` no histórico. Se ocorreu antes do commit, os dados não devem ter sido confirmados; se depois, o sucesso já faz parte da mesma transação. O histórico e o checkpoint permitem investigar. Não há um serviço para marcar automaticamente execuções abandonadas.

Falhas muito precoces, como banco não preparado ou impossibilidade de abrir o disco, podem impedir o próprio registro. Nesses casos, a mensagem do terminal e o código de saída são os sinais disponíveis. O sistema não promete registrar logs quando o armazenamento está inacessível.

## 12. Banco confirmado versus arquivo exportado

O destino é confirmado antes de exportar relatórios. Se a exportação falhar, a carga não é desfeita nem anunciada como rollback. O comando orienta executar `relatorio` para reconstruir os arquivos.

Uma execução com aviso de exportação ainda retorna sucesso da carga. Se você automatizar exigindo também a entrega dos arquivos, deve tratar esse aviso como uma condição própria de monitoramento.

Os relatórios de duas execuções ficam em pastas diferentes. Em execuções sobrepostas, uma exportação pode incluir uma atualização já confirmada por outra execução. O manifesto registra o checkpoint da fotografia exportada para deixar isso explícito.

## 13. Hashes e versão

SHA-256 identifica o conteúdo dos arquivos e da consulta. Os metadados também registram versões das bibliotecas, Python, IDs, horários e contagens. Os hashes não criptografam o conteúdo nem garantem autenticidade contra alguém que também possa alterar o manifesto.

Para reproduzir um resultado histórico, preserve juntos o código, dependências, eventos extraídos e metadados. A tabela de estado atual sozinha não reconstrói todos os estados antigos. O projeto não cria um repositório Git automaticamente; o versionamento do código pode ser acrescentado pelo usuário.

## 14. Como os testes sustentam a explicação

Os testes executam bancos reais temporários, verificam valores calculados previamente, provocam falhas dentro da carga, reproduzem eventos antigos e verificam a preservação do checkpoint. Também testam o caminho em que o banco confirma, mas a exportação falha.

Eles cobrem situações específicas. Não são uma prova geral contra toda falha de infraestrutura, disco, processo ou sistema operacional.
