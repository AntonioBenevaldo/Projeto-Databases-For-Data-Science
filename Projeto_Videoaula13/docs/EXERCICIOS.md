# Exercícios práticos com conferência

Execute na pasta principal. Todos os exemplos abaixo usam SQLite. O ambiente Python deve estar preparado conforme o README.

## Exercício 1 — Fluxo completo

```bash
py -3.14 executar.py tudo
```

Confira: 10 vendas, 57 unidades, faturamento R$ 1.053,00, custo R$ 630,00 e lucro bruto R$ 423,00. Abra o CSV e identifique por que os IDs 4 e 8 não foram extraídos. **Resposta:** venda cancelada e venda pendente, respectivamente.

## Exercício 2 — Mudar o tamanho dos lotes

```bash
py -3.14 executar.py tudo --lote 3 --saida outputs/lote3
```

Quantos lotes não vazios você espera? **Resposta:** quatro, com 3, 3, 3 e 1 venda. Os indicadores devem continuar iguais. Tamanho do lote muda a transferência, não o critério de seleção.

## Exercício 3 — Analisar janeiro

```bash
py -3.14 executar.py tudo --inicio 2026-01-01 --fim 2026-01-31 --saida outputs/janeiro
```

**Resposta:** 3 vendas, 13 unidades, faturamento R$ 143,00, custo R$ 84,00, lucro bruto R$ 59,00 e ticket médio R$ 47,67.

## Exercício 4 — Analisar fevereiro

```bash
py -3.14 executar.py tudo --inicio 2026-02-01 --fim 2026-02-28 --saida outputs/fevereiro
```

**Resposta:** 3 vendas, 25 unidades, faturamento R$ 410,00, custo R$ 236,00 e lucro bruto R$ 174,00.

## Exercício 5 — Consultar período vazio

```bash
py -3.14 executar.py tudo --inicio 2027-01-01 --fim 2027-01-31 --saida outputs/vazio
```

**Resposta:** nenhuma venda, totais zero, ticket e margem sem valor aplicável. O programa não deve inventar vendas nem apresentar divisão por zero.

## Exercício 6 — Detectar datas invertidas

```bash
py -3.14 executar.py extrair --inicio 2026-03-31 --fim 2026-01-01
```

**Resposta:** mensagem de erro informando que a data inicial deve ser anterior ou igual à final. Este é um erro intencional do exercício.

## Exercício 7 — Confirmar que a carga é repetível

```bash
py -3.14 executar.py preparar
py -3.14 executar.py preparar
py -3.14 executar.py tudo
```

**Resposta:** continuam existindo 12 vendas na base e 10 concluídas no recorte completo. Execute `testar` para verificar a contagem total automaticamente.

## Exercício 8 — Python e R

Com R e seus pacotes instalados:

```bash
py -3.14 executar.py tudo
py -3.14 executar.py r
py -3.14 executar.py comparar
```

**Resposta esperada:** os dados extraídos e os dois resumos coincidem. Se Rscript não estiver no PATH, acrescente `--rscript` ao comando R, como explicado no README.

## Exercício 9 — Explicar o resultado de negócio

1. Qual categoria gerou mais faturamento? **Informática: R$ 740,00.**
2. Qual categoria teve maior margem bruta percentual? **Papelaria: 153/313 × 100 ≈ 48,88%; Informática: 270/740 × 100 ≈ 36,49%.**
3. Maior faturamento significa maior margem percentual? **Não. Os custos e descontos mudam essa relação.**
4. O lucro bruto de R$ 423,00 representa lucro líquido? **Não: faltam tributos e outras despesas.**

## Exercício 10 — Evidências do seu aprendizado

Guarde, em uma pasta própria, capturas do diagnóstico, da execução completa, do resumo `Ran 12 tests ... OK` e, se executar R, da comparação aprovada. Explique com suas palavras:

- Qual é o papel do SQLAlchemy?
- Qual é o papel de pandas?
- Por que DBI precisa de um driver?
- Por que enviar parâmetros separados do SQL?
- O que um hash identifica e o que ele não garante?
- Por que uma extração em lotes não garante que a análise posterior caiba na memória?

As evidências entregues registram a validação desta versão. Suas capturas devem mostrar a execução no seu computador.
