# Como o código funciona

Leia este roteiro junto com `src/pipeline.py` e `src/preparacao.py`. Não é necessário executar os trechos desta explicação isoladamente: `projeto.py` organiza as etapas.

## 1. Uma interface, várias etapas

`argparse` interpreta o comando e as opções. `projeto.py gerar` chama `gerar()`, `projeto.py ingerir` chama `ingerir()` e assim por diante. `tudo` percorre a sequência completa e para ao encontrar um erro. O programa retorna código zero no sucesso e um no erro.

`Path(__file__)` localiza a pasta pelo arquivo de código. Assim, não existe um caminho fixo com nome de usuário. Os atalhos em `src` apontam para as mesmas funções.

## 2. Geração não é ingestão

`gerar()` cria a fonte CSV para o exercício, com `numpy.random.default_rng(seed)`. O alvo vem de uma probabilidade artificial relacionada à distância, quantidade, canal e região. Depois são inseridos problemas conhecidos.

`ingerir()` transporta o CSV para o SQLite. Ela não inventa novos valores nem corrige os problemas. Usa `pandas.read_csv()` e `DataFrame.to_sql()`, com verificação de quantidade.

`contextlib.closing()` fecha a conexão SQLite de forma explícita antes de renomear o arquivo temporário. Isso é relevante para Windows, que pode impedir a substituição de um arquivo aberto.

## 3. Contrato de dados

`CAMPOS` enumera as colunas esperadas e sua ordem. O pipeline recusa uma estrutura diferente. O contrato didático espera datas ISO e números com ponto decimal; não é um importador genérico de qualquer planilha brasileira.

Se você adaptar a entrada, altere também o contrato, os tipos, as regras de qualidade, a documentação e os testes. Não renomeie uma coluna sem revisar as etapas que a usam.

## 4. Limpeza com rastreabilidade

`limpar()` remove duplicatas exatas e acumula os motivos de rejeição. Uma linha pode ter mais de um motivo. O original continua na camada bruta, e os rejeitados ficam na quarentena.

Uma duplicata exata é diferente de duas linhas com o mesmo ID e valores divergentes. No segundo caso, todas as versões conflitantes são rejeitadas, para evitar selecionar uma arbitrariamente.

Categorias são normalizadas com funções de texto e `unicodedata`. Isso é determinístico: não aprende frequências nem usa o alvo. Ausências válidas são mantidas nessa fase para que a mediana seja aprendida depois, apenas no treino.

## 5. Separação temporal e disponibilidade do alvo

`dividir_temporal()` usa dias distintos ordenados. Os cortes 60% e 80% definem o início da validação e do teste. Um pedido só pode entrar no treino se seu alvo já estiver disponível antes do início da validação. A mesma lógica limita os rótulos da validação antes do teste.

Exemplo: não seria correto simular um modelo pronto em 25/05 usando o resultado de um pedido de 24/05, pois ainda não se passaram sete dias. Esse pedido fica fora daquele conjunto de treino.

Não há clientes repetidos ou grupos pessoais neste modelo de dados. Em um projeto real com várias observações da mesma entidade, seria necessário revisar também a separação por grupos, além das datas.

## 6. Engenharia de atributos sem informação futura

`atributos()` devolve uma lista explícita de colunas permitidas, em ordem estável:

- valor, quantidade e distância do pedido;
- valor por item: valor dividido por quantidade;
- dia da semana do pedido;
- canal e região.

Esses atributos existem no momento da previsão. `atrasou` é o alvo, `pedido_id` é identificador e `dias_entrega_real` só existe depois da entrega. Os três são excluídos. A data absoluta também é excluída; apenas o dia da semana é usado.

O alvo poderia ser reconstruído quase diretamente com `dias_entrega_real > 7`. Isso produziria uma avaliação enganosa: no momento do pedido, esse dado não está disponível. O teste de prevenção de leakage altera essa coluna e o alvo e confere que os atributos de entrada permanecem iguais.

## 7. O transformador numérico

`LimitarExtremos` segue a interface do scikit-learn:

- `fit(X_treino)` aprende os percentis 1 e 99 de cada coluna;
- `transform(X)` usa os mesmos limites para restringir valores, sem recalculá-los;
- `get_feature_names_out()` preserva os nomes no relatório.

O `SimpleImputer` aprende as medianas dos valores numéricos do treino após a limitação. `add_indicator=True` acrescenta indicadores para as colunas que apresentavam ausências no treino. `StandardScaler` aprende média e escala depois da imputação.

Assim, a sequência é **limitar → imputar → padronizar**, sempre com parâmetros do treino. Os limites são aplicados uniformemente às numéricas para fins didáticos; em dados reais, contagens e variáveis de calendário podem exigir tratamento diferente. Limitar extremos não equivale a comprovar que eram erros.

O dia da semana é usado como número ordinal simples. Uma evolução seria codificação categórica ou cíclica; o exercício não faz busca de alternativas olhando o teste.

## 8. O transformador categórico

`SimpleImputer(strategy='constant')` preenche ausências com `desconhecido`. `OneHotEncoder` aprende no treino quais categorias existem e cria colunas 0/1.

`handle_unknown='ignore'` aceita uma categoria nova sem criar uma coluna depois do treinamento. As colunas daquele atributo ficam zeradas. É um comportamento técnico conhecido, que deve ser monitorado em aplicações reais.

`ColumnTransformer` combina o ramo numérico e o categórico. `remainder='drop'` descarta campos não listados. `FEATURES` também limita explicitamente a entrada.

## 9. fit, transform e predict

| Operação | O que faz | Onde usar neste projeto |
|---|---|---|
| `fit` do pré-processador | Aprende limites, medianas, escala e categorias | Somente no treino |
| `transform` | Aplica parâmetros já aprendidos | Treino, validação, teste e novos exemplos |
| `fit` do classificador | Aprende relação entre atributos e alvo | Somente no treino |
| `predict_proba` | Produz a probabilidade da classe | Validação, teste e novos exemplos |

As matrizes de validação e teste são transformadas na etapa de preparação, mas não influenciam os parâmetros ajustados. O teste só é pontuado na etapa `avaliar`.

## 10. Modelos e limiar

`LogisticRegression` é um classificador, apesar do nome “regressão”. O método `predict_proba` fornece uma probabilidade para cada classe. O código usa a coluna referente à classe 1 e aplica limiar 0,5.

`DummyClassifier(strategy='prior')` retorna a distribuição do alvo observada no treino. Com o limiar padrão, funciona como previsão constante da classe predominante. Serve como referência mínima: um modelo mais complexo deve ser comparado a algo simples.

A validação é diagnóstica nesta versão. Não há seleção automática de modelo, ajuste de limiar ou retreinamento com treino+validação. O mesmo modelo ajustado no treino segue para o teste.

## 11. Métricas

- **Acurácia:** fração de previsões corretas.
- **Acurácia balanceada:** média do recall das classes; ajuda a observar desequilíbrio.
- **Precisão:** entre os pedidos previstos como atrasados, quantos atrasaram.
- **Recall:** entre os atrasos reais, quantos foram identificados.
- **F1:** combina precisão e recall.
- **ROC-AUC:** avalia ordenação dos escores em diferentes limiares; não é porcentagem de acertos e não mede calibração.

A matriz de confusão usa linhas como classe real e colunas como prevista, na ordem 0/1:

|  | Previsto no prazo | Previsto atraso |
|---|---:|---:|
| Real no prazo | Verdadeiros negativos | Falsos positivos |
| Real atraso | Falsos negativos | Verdadeiros positivos |

Se não houver previsões positivas, a precisão é registrada como zero, conforme a convenção configurada. Se só houver uma classe real, a ROC-AUC fica indisponível (`null`).

## 12. Hashes, versões e repetição

Cada etapa grava um manifesto JSON com hashes SHA-256. Antes de usar uma etapa anterior, o código confere os artefatos e suas dependências. Alterar o CSV depois da ingestão invalida etapas futuras, evitando misturar versões silenciosamente.

Os manifestos não são assinaturas digitais nem um controle de segurança contra adulteração intencional. Eles detectam inconsistência entre arquivos e os hashes registrados. Os dois poderiam ser modificados por alguém com acesso à pasta.

O treinamento registra versões e hashes dos principais arquivos de código. Preservar a mesma semente, dados, regras e ambiente facilita a reprodução. Datas de execução nos metadados serão diferentes; a reprodutibilidade esperada se refere ao conteúdo de dados e aos resultados dentro da precisão numérica.

A escrita de todos os artefatos não é uma única transação. Se uma etapa for interrompida, reexecute-a antes de continuar. As verificações de hashes ajudam a identificar arquivos incompletos ou desatualizados.

## 13. O que este projeto não implementa

Não há streaming, CDC, orquestrador externo, processamento distribuído, monitoramento de produção, dashboard ou API. Não há dados pessoais. O objetivo é executar e compreender um pipeline local de ingestão e pré-processamento, com um classificador simples para completar o ciclo.
