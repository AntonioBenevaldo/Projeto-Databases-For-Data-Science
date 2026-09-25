# Exercícios para fixar o aprendizado

Execute na pasta principal com o ambiente já instalado. Guarde suas evidências em uma pasta própria. Não confunda os resultados de referência entregues com a execução no seu computador.

## 1. Executar e conferir a preparação

```bash
py -3.14 executar.py tudo
```

**Confira:** 1.226 linhas brutas; 20 duplicatas removidas; 6 registros rejeitados; 1.200 pedidos válidos. Abra `outputs/qualidade.json` e identifique as contagens de ausências que existiam antes da imputação.

Pergunta: a presença das seis linhas na quarentena é uma falha? **Resposta:** não; são problemas inseridos para demonstrar detecção e separação.

## 2. Ler os motivos da quarentena

Abra `data/tratados/quarentena.csv` no VS Code. **Resposta esperada:** duas quantidades inválidas, um valor de pedido negativo, uma data inválida, um alvo ausente e uma distância negativa.

Por que não preencher o alvo ausente com a mediana? **Resposta:** o alvo é o resultado que queremos aprender, não uma variável de entrada a ser imputada arbitrariamente.

## 3. Explicar a divisão temporal

Abra `outputs/qualidade.json`, seção `divisao`.

**Resposta esperada:** 685 treino, 205 validação, 240 teste e 70 no intervalo temporal. O conjunto completo tem 1.200 pedidos válidos.

Por que os intervalos existem? **Resposta:** o atraso só é conhecido após sete dias. Pedidos muito próximos ao corte ainda não teriam rótulo disponível no momento simulado.

## 4. Encontrar as medianas

No JSON de qualidade, procure `parametros_aprendidos_no_treino` e `medianas_apos_limitar`.

Explique a diferença entre `fit` e `transform`. **Resposta:** `fit` aprende os parâmetros; `transform` aplica os parâmetros já aprendidos. Validação e teste não devem recalcular a mediana.

## 5. Identificar a coluna proibida

Abra `data/brutos/pedidos.csv` e depois `outputs/features.json`.

`dias_entrega_real` deve aparecer nas features? **Não.** Ela informa o futuro, disponível depois da entrega, e praticamente revela a resposta ao compará-la com sete dias.

`atrasou` deve aparecer entre as features? **Não.** É o alvo.

## 6. Examinar a matriz de confusão

Abra `outputs/matriz_confusao.png`.

Na referência padrão:

- 101 pedidos no prazo foram corretamente previstos no prazo;
- 35 pedidos no prazo foram previstos como atraso;
- 51 atrasos passaram sem ser identificados;
- 53 atrasos foram identificados.

Calcule a acurácia: `(101 + 53) / 240 ≈ 64,17%`.
Calcule o recall dos atrasos: `53 / (53 + 51) ≈ 50,96%`.

Aprovar os testes significa identificar todos os atrasos? **Não.** Os testes verificam o programa; as métricas descrevem o desempenho preditivo nesta simulação.

## 7. Repetir uma ingestão

```bash
py -3.14 executar.py ingerir
py -3.14 executar.py ingerir
py -3.14 executar.py preprocessar
py -3.14 executar.py treinar
py -3.14 executar.py avaliar
```

**Resposta:** o banco permanece com 1.226 linhas brutas. A ingestão é um snapshot, não uma soma de lotes. Como a ingestão e seus metadados mudaram, reexecute as etapas seguintes.

## 8. Criar outro experimento sem substituir o primeiro

```bash
py -3.14 executar.py tudo --pasta execucoes/semente7 --semente 7
```

**Resposta:** a estrutura e as contagens de problemas permanecem; os pedidos simulados, as medianas e as métricas podem mudar. As métricas de outra semente não comprovam melhoria: a amostra mudou.

## 9. Demonstrar o controle de integridade

Use somente uma cópia de experimento:

```bash
py -3.14 executar.py tudo --pasta execucoes/integridade
```

Abra `execucoes/integridade/data/brutos/pedidos.csv`, altere um valor e salve. Execute:

```bash
py -3.14 executar.py treinar --pasta execucoes/integridade
```

**Resposta esperada:** erro de arquivo alterado; o programa impede combinar dados e preparação de versões diferentes. Para restaurar esse experimento:

```bash
py -3.14 executar.py tudo --pasta execucoes/integridade
```

Isso substitui os dados editados da cópia pelos dados da demonstração. O projeto não oferece neste momento um comando de importação arbitrária de CSV externo; o gerador e seu manifesto definem a origem do exercício.

## 10. Executar testes e registrar seu aprendizado

```bash
py -3.14 executar.py testar
```

**Esperado:** `Ran 18 tests` e `OK`. Guarde uma captura do terminal e responda:

1. Qual é a diferença entre dado bruto, tratado e analítico?
2. Por que a mediana é calculada somente no treino?
3. Por que a ordem cronológica importa?
4. O que acontece com uma categoria nova no OneHotEncoder?
5. Por que um baseline é útil?
6. Por que a acurácia sozinha pode esconder problemas?

**Respostas resumidas:** bruto preserva origem; tratado segue regras de qualidade; analítico está organizado para o modelo. Mediana só no treino evita aprender com a avaliação. Ordem temporal simula disponibilidade real. Categoria desconhecida vira zeros no bloco correspondente, sem reajuste. Baseline fornece uma referência simples. Acurácia pode parecer aceitável mesmo ignorando boa parte dos atrasos.
