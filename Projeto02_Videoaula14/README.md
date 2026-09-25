# Projeto 02 — Videoaula 14

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

## Ingestão e pré-processamento para machine learning no terminal

**Tema:** preparação de pedidos comerciais simulados para prever atraso na entrega.

Preparado para Benevaldo com base na seção “Videoaula 14 — Ingestão e pré-processamento para machine learning” do PDF *CONTEÚDO DESTA UNIDADE 4*, da disciplina Databases for Data Science. O print fornecido orientou a organização dos scripts. Esta é uma implementação didática própria: não é o código original do professor, e o vídeo não foi acessado.

O projeto funciona de forma independente do Projeto 01. Não é necessário copiar bancos ou arquivos entre os projetos. Todas as etapas podem ser iniciadas por comandos Python no terminal do VS Code, sem JupyterLab, R, Docker ou servidor de banco. SQLite já acompanha Python.

## 1. O que você vai aprender

| Conteúdo da aula | Aplicação neste projeto |
|---|---|
| Ingestão batch | Importação de um CSV completo para SQLite |
| Camada bruta | CSV e tabela que preservam problemas simulados |
| Camada tratada | Dados padronizados, duplicatas removidas e registros inválidos separados |
| Camada analítica | Features, rótulos e matrizes de treino, validação e teste |
| Ausências | Mediana nas numéricas e categoria “desconhecido” nas categóricas |
| Valores extremos | Limites de percentis aprendidos somente no treino |
| Escalas | StandardScaler nas variáveis numéricas |
| Categorias | OneHotEncoder com suporte a categorias não vistas |
| Engenharia de atributos | Valor por item e dia da semana |
| Prevenção de leakage | Divisão temporal, intervalo entre conjuntos e exclusão de informação futura |
| Rastreabilidade | Hashes, semente, versões, parâmetros e relatórios |

A aula também apresenta streaming e CDC. Aqui implementamos **batch por snapshot**, adequado a um exercício local. Não implementamos captura em tempo real nem CDC.

## 2. Preparação do ambiente

Use os quatro comandos da seção “Começar no seu Windows com Python 3.14”, no início deste README. O restante do guia usa o mesmo iniciador `executar.py`.

## 3. Entender o ambiente

Execute `py -3.14 executar.py instalar` como explicado no início do guia. Esse comando cria a `.venv314`, instala as dependências e mostra o diagnóstico. Os demais comandos usam automaticamente esse mesmo ambiente.

## 4. Caminho rápido: executar tudo

```bash
py -3.14 executar.py tudo
py -3.14 executar.py testar
```

O primeiro comando executa `gerar → ingerir → preprocessar → treinar → avaliar → prever` e grava dados e resultados. O segundo executa testes em pastas temporárias, sem modificar os dados de estudo.

Resultado esperado da preparação padrão:

| Item | Quantidade |
|---|---:|
| Registros brutos | 1.226 |
| Duplicatas exatas removidas | 20 |
| Registros inválidos separados | 6 |
| Pedidos válidos | 1.200 |
| Treino | 685 |
| Validação | 205 |
| Teste | 240 |
| Intervalos de segurança temporal | 70 |

Os 70 pedidos dos intervalos continuam na camada tratada e ficam em um CSV específico; não são erros nem são usados para treinar ou avaliar. **685 + 205 + 240 + 70 = 1.200.**

Para estudar, siga as etapas abaixo uma de cada vez.

## 5. Etapa 00 — Gerar dados

```bash
py -3.14 executar.py gerar
```

**O que faz:** cria 1.200 pedidos únicos, cinco por dia, começando em 01/01/2025. Acrescenta 20 linhas duplicadas e 6 linhas inválidas. Introduz ausências, diferenças de maiúsculas/espaços e valores extremos conhecidos.

A semente padrão é `42`, para reproduzir os mesmos dados no mesmo ambiente. O alvo é gerado por um mecanismo probabilístico artificial, portanto haverá incerteza e erros de classificação mesmo após a preparação.

**Arquivos:**

- `data/brutos/pedidos.csv`: dados brutos, incluindo problemas;
- `data/brutos/novos_pedidos.csv`: cinco exemplos de entrada sem alvo, derivados de perfis sintéticos do gerador;
- `outputs/geracao.json`: semente, tamanho e hashes.

Os cinco exemplos de previsão são uma demonstração do uso do modelo; não são um novo teste independente de desempenho.

## 6. Etapa 01 — Ingerir no SQLite

```bash
py -3.14 executar.py ingerir
```

**O que faz:** lê o CSV, verifica o contrato de colunas, cria a tabela `pedidos_brutos` em `data/pedidos.db` e confere a quantidade de linhas importadas.

A ingestão preserva os problemas de origem; a limpeza vem depois. Ela usa um snapshot completo: repetir a etapa substitui a versão anterior da tabela, em vez de acumular o lote novamente. As 20 duplicatas que já existem no CSV continuam na camada bruta até a limpeza.

O banco é construído em um arquivo temporário e a conexão é fechada antes de substituir o banco anterior. Isso evita entregar um banco parcialmente importado.

**Esperado:** 1.226 linhas no SQLite; metadados em `outputs/ingestao.json`.

## 7. Etapa 02 — Limpar, dividir e pré-processar

```bash
py -3.14 executar.py preprocessar
```

A ordem desta etapa é importante:

1. **Ler o SQLite.** Seleciona as colunas previstas no contrato.
2. **Remover duplicatas exatas.** Uma linha repetida não vira uma segunda observação.
3. **Separar registros inválidos.** Datas inválidas, quantidades não positivas, valores negativos e alvo ausente vão para `quarentena.csv`, com o motivo. IDs conflitantes também vão para quarentena; o programa não escolhe arbitrariamente uma versão.
4. **Padronizar formatos.** Datas ISO, categorias sem espaços externos, em minúsculas e sem acentos.
5. **Separar por tempo.** Os dias mais antigos são reservados ao treino, depois validação, depois teste.
6. **Excluir intervalos próximos aos cortes.** O alvo demora sete dias para ficar disponível.
7. **Criar atributos por linha.** Valor por item e dia da semana, sem usar dados futuros.
8. **Ajustar transformações somente no treino.** Limites de extremos, medianas, escala e categorias.
9. **Transformar validação e teste.** Reutiliza os parâmetros do treino, sem `fit` nesses conjuntos.
10. **Exportar matrizes e parâmetros.** Confere se as matrizes numéricas estão sem NaN/infinito e têm as mesmas colunas.

### Limpeza não é o mesmo que aprender estatísticas

Remover uma quantidade negativa segue uma regra definida previamente. Calcular uma mediana aprende uma propriedade dos dados. Por isso a primeira pode ocorrer na limpeza do conjunto, enquanto a segunda deve ocorrer depois da divisão, usando somente treino.

### Como funciona a divisão

Os cortes são definidos em aproximadamente **60% / 20% / 20% dos dias**, sem embaralhamento. Depois retiramos os sete dias imediatamente anteriores a cada corte para não usar rótulos que ainda não estariam disponíveis. Por isso as proporções finais de linhas não são exatamente 60/20/20.

No conjunto padrão:

| Conjunto | Datas dos pedidos | Linhas |
|---|---|---:|
| Treino | 01/01/2025 a 17/05/2025 | 685 |
| Intervalo antes da validação | 18/05/2025 a 24/05/2025 | 35 |
| Validação | 25/05/2025 a 04/07/2025 | 205 |
| Intervalo antes do teste | 05/07/2025 a 11/07/2025 | 35 |
| Teste | 12/07/2025 a 28/08/2025 | 240 |

A comparação usa “data do pedido + sete dias < início do próximo conjunto”, preservando uma separação conservadora na resolução diária.

### O que ocorre com ausências, extremos e categorias

- Valores numéricos ausentes são substituídos pela mediana do treino, calculada após o limite de extremos. Indicadores de ausência também são acrescentados quando aplicável.
- Numéricas são limitadas nos percentis 1 e 99 do treino e depois padronizadas. Isso não remove as linhas. É uma escolha didática, não uma regra universal de negócio.
- Categorias ausentes recebem `desconhecido`.
- One-hot cria colunas binárias. Categorias novas recebem zeros nas colunas daquele atributo por `handle_unknown='ignore'`. Isso evita falha técnica, mas não garante boa previsão para categorias novas.
- A categoria `parceiro` aparece somente no período futuro para permitir testar essa situação.

**Arquivos principais:**

- `data/tratados/pedidos_limpos.csv`;
- `data/tratados/quarentena.csv`;
- `data/tratados/embargo_temporal.csv`;
- `data/analiticos/treino.csv`, `validacao.csv` e `teste.csv`;
- `data/analiticos/X_*.csv`: matrizes de atributos transformados;
- `data/analiticos/y_*.csv`: identificador e alvo, alinhados na mesma ordem das matrizes;
- `modelos/preprocessador.joblib`;
- `outputs/qualidade.json` e `outputs/features.json`.

## 8. Etapa 03 — Treinar e conferir a validação

```bash
py -3.14 executar.py treinar
```

O projeto treina:

- **Regressão logística:** classificador que estima a probabilidade de atraso;
- **DummyClassifier:** referência que usa a frequência de atraso do treino, sem aprender relação com os atributos.

O transformador já foi ajustado no treino. O comando o reutiliza, transforma os atributos e ajusta os classificadores apenas com os rótulos do treino. Depois mede o resultado na validação.

O limiar é fixo em **0,5**: probabilidade maior ou igual a 0,5 vira classe 1. Não há busca automática de hiperparâmetros ou ajuste do limiar. O conjunto de teste não é avaliado nesta etapa.

**Arquivos:** `modelos/modelo.joblib`, `outputs/metricas_validacao.json` e `outputs/treinamento.json`.

O pacote salvo contém o pré-processamento e o modelo, mantendo as mesmas transformações para previsões futuras. Arquivos `joblib` podem executar código ao carregar: use somente os gerados localmente por este projeto, não arquivos de origem desconhecida. Os hashes servem para consistência, não para autenticar um arquivo malicioso.

## 9. Etapa 04 — Avaliar no teste e gerar relatório

```bash
py -3.14 executar.py avaliar
```

O comando usa o modelo já treinado no período final reservado, sem reajustar parâmetros. Gera:

- `outputs/metricas_teste.json`;
- `outputs/previsoes_teste.csv`;
- `outputs/matriz_confusao.png`;
- `outputs/relatorio.md`;
- `outputs/avaliacao.json`.

Para visualizar o relatório no VS Code, abra `relatorio.md` e pressione **Ctrl+Shift+V**. Clique no PNG para visualizar a matriz de confusão.

Resultados observados na validação desta entrega, com semente 42 e 1.200 pedidos:

| Métrica do teste | Regressão logística | Baseline |
|---|---:|---:|
| Acurácia | 64,17% | 56,67% |
| Recall da classe atraso | 50,96% | 0,00% |
| F1 da classe atraso | 0,5521 | 0,0000 |
| ROC-AUC | 0,7148 | 0,5000 |

Pequenas diferenças numéricas podem ocorrer entre plataformas/bibliotecas. As contagens da preparação são a primeira referência para conferir a execução padrão.

A acurácia não deve ser interpretada sozinha. Neste teste, o modelo encontra 53 dos 104 atrasos e deixa passar 51. Os resultados não justificam uso operacional: refletem apenas o mecanismo de dados simulados.

**Não ajuste o modelo repetidamente olhando o teste.** Para estudar outra semente use outra pasta; isso não demonstra melhoria do modelo. Uma avaliação operacional exigiria dados reais apropriados e um novo período final independente.

## 10. Etapa extra — Prever novos exemplos

```bash
py -3.14 executar.py prever
```

Lê os cinco exemplos de `novos_pedidos.csv`, aplica a engenharia de atributos e o pipeline já ajustado, sem reaprender parâmetros. Salva `outputs/previsoes_novos.csv`.

Os exemplos não possuem `atrasou` nem `dias_entrega_real`. O comando não fornece uma validação extra de qualidade, pois os perfis vêm do próprio gerador. As probabilidades são saídas do modelo; não foram calibradas como riscos operacionais reais.

## 11. Testar e conferir

```bash
py -3.14 executar.py testar
```

Procure `Ran 18 tests` e `OK`.

Os testes verificam: contagens da limpeza, divisão sem sobreposição, disponibilidade temporal dos rótulos, exclusão do futuro, ajuste apenas no treino, categorias novas, matrizes sem NaN, conflitos de ID, métricas conhecidas, modelo salvo, hashes, geração reproduzível, ingestão repetida, novos exemplos, propagação de alterações, argumentos inválidos e imputação.

**Testes aprovados significam que os comportamentos cobertos funcionaram. Não significam que as previsões são perfeitas.**

## 12. Scripts com organização semelhante ao print

Você pode usar a interface `projeto.py` ou estes atalhos. Não é necessário executar as duas formas.

```bash
./.venv314/Scripts/python.exe src/00_generate_data.py
./.venv314/Scripts/python.exe src/01_ingest_to_sqlite.py
./.venv314/Scripts/python.exe src/02_preprocess_build_features.py
./.venv314/Scripts/python.exe src/03_train_baseline.py
./.venv314/Scripts/python.exe src/04_evaluate_and_report.py
```

Para executar tudo pelo atalho:

```bash
./.venv314/Scripts/python.exe src/run_pipeline.py
```

Os atalhos chamam a mesma implementação central. O atalho completo também executa a demonstração de previsão.

## 13. Repetições, pastas e experimentos

`gerar` e `tudo` substituem os dados simulados na pasta selecionada. `ingerir` substitui o snapshot SQLite. Demais etapas substituem os próprios arquivos de saída. Não use uma pasta com dados reais ou outros arquivos de mesmo nome.

Para preservar a primeira execução:

```bash
py -3.14 executar.py tudo --pasta execucoes/semente7 --semente 7
```

Para mais pedidos:

```bash
py -3.14 executar.py tudo --pasta execucoes/base2000 --linhas 2000
```

`--linhas` deve ser múltiplo de cinco e pelo menos 300. `--semente` e `--linhas` só atuam em `gerar` e `tudo`. As etapas seguintes usam os arquivos existentes. Para executar por etapas em outra pasta, repita `--pasta` em cada comando.

As matrizes e o conjunto são carregados em memória. Este é um exercício pequeno; não é um pipeline distribuído para milhões de registros. Não execute simultaneamente dois comandos gravando na mesma pasta.

## 14. Organização dos arquivos

| Local | Função |
|---|---|
| `projeto.py` | Interface de comandos |
| `src/pipeline.py` | Etapas e geração de relatórios |
| `src/preparacao.py` | Limpeza, atributos, divisão e transformador |
| `src/00_...` a `04_...` | Atalhos numerados |
| `docs/EXPLICACAO_DO_CODIGO.md` | Explicação das funções e conceitos |
| `docs/EXERCICIOS.md` | Exercícios com respostas |
| `docs/DICIONARIO_DADOS.md` | Significado e disponibilidade de cada campo |
| `tests/test_projeto.py` | Testes automatizados |
| `evidencias/` | Registros reais da validação desta entrega |
| `data/`, `outputs/`, `modelos/` | Artefatos produzidos quando você executa |

A entrega não inclui ambiente virtual, banco pronto ou modelo pré-carregado. O comando `tudo` gera esses arquivos no seu computador. Resultados de referência estão separados em `evidencias/resultado_referencia`.

## 15. Solução de problemas

| Situação | Ação |
|---|---|
| `python` não encontrado ou abre a Store | Instale/configure Python 3.14. Se disponível, use `py -3.14 executar.py instalar`. |
| Não encontra `projeto.py` | Abra a pasta principal no VS Code e crie um novo terminal nela. |
| Não encontra `.venv314/Scripts/python.exe` | Execute `py -3.14 executar.py instalar` na pasta do projeto. |
| `No module named ...` | Instale `requirements.txt` com o mesmo executável da `.venv314`. |
| `SyntaxError` em um comando | Você pode estar dentro de `>>>`; digite `exit()` e volte ao terminal. |
| “Execute a etapa anterior” | Siga gerar, ingerir, preprocessar, treinar e avaliar, nessa ordem. |
| “Arquivo ausente ou alterado” | Os hashes não conferem. Reexecute a etapa indicada e as seguintes; para restaurar a demonstração inteira, use `tudo`. |
| Resultado mudou após outra semente | É esperado; compare as contagens e os metadados do experimento correto. |
| Teste automatizado falhou | Leia o nome do teste e a mensagem; não considere `FAILED` como aprovação. |
| CSV aberto no Excel impede a gravação | Feche o arquivo antes de repetir a etapa. |
| Quarentena tem 6 linhas | É esperado na demonstração; examine a coluna `motivo`. |

Para Linux/macOS, use `python3.14 executar.py instalar` e troque `py -3.14` por `python3.14` nos comandos. O iniciador seleciona automaticamente `.venv314/bin/python`.

## 16. Validação e fontes

Pipeline e testes executados em Linux/Python 3.14. As instruções Windows usam caminhos padrão, mas não foram executadas em Windows nesta sessão. Veja `evidencias/RELATORIO_VALIDACAO.md`.

Fontes consultadas em 21/09/2026:

- PDF enviado: *Databases for Data Science — Unidade IV*, seção Videoaula 14.
- scikit-learn — prevenção de leakage: https://scikit-learn.org/stable/common_pitfalls.html
- scikit-learn — tipos mistos e pipeline: https://scikit-learn.org/stable/auto_examples/compose/plot_column_transformer_mixed_types.html

A documentação online pode apresentar versões diferentes das fixadas no projeto. As versões efetivamente usadas estão no diagnóstico e nos metadados de treinamento.

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
