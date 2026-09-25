# Exercícios com resultados para conferência

Use o terminal na pasta principal. Todos os comandos pressupõem a venv e as dependências instaladas.

## 1. Carga inicial em pasta própria

```bash
py -3.14 executar.py tudo --pasta execucoes/exercicios
```

**Confira:** seis eventos, seis pedidos no destino, quatro concluídos, faturamento R$ 575,00 e checkpoint 6.

Por que dois pedidos não entram no faturamento? **Resposta:** um está pendente e outro cancelado.

## 2. Repetição normal

```bash
py -3.14 executar.py executar --pasta execucoes/exercicios
```

**Esperado:** zero eventos novos e nenhum pedido alterado. O novo registro no histórico não representa pedido duplicado.

## 3. Atualizar e cancelar

```bash
py -3.14 executar.py simular-lote --pasta execucoes/exercicios
py -3.14 executar.py executar --pasta execucoes/exercicios
```

**Confira:** cinco eventos lidos, oito pedidos no destino, seis concluídos, faturamento R$ 1.045,00 e checkpoint 11.

Explique a diferença entre “eventos lidos” e “pedidos no destino”. **Resposta:** um pedido pode ter vários eventos; o destino guarda somente sua última versão.

## 4. Reprocessar uma versão antiga

```bash
py -3.14 executar.py executar --pasta execucoes/exercicios --desde-evento 0 --limite 6
```

**Esperado:** seis eventos antigos relidos, zero pedidos alterados, faturamento R$ 1.045,00 e checkpoint 11. O cancelamento do pedido 4 não deve ser desfeito por sua versão antiga concluída.

## 5. Paginar sem pular eventos

```bash
py -3.14 executar.py preparar --pasta execucoes/paginacao
py -3.14 executar.py executar --pasta execucoes/paginacao --limite 2
py -3.14 executar.py executar --pasta execucoes/paginacao --limite 2
py -3.14 executar.py executar --pasta execucoes/paginacao --limite 2
```

**Esperado:** checkpoints 2, 4 e 6; contagens pendentes 4, 2 e 0. O relatório pode mostrar um estado parcial enquanto ainda há eventos pendentes.

## 6. Retentativa

```bash
py -3.14 executar.py executar --pasta execucoes/exercicios --falha transitoria --desde-evento 0
```

**Esperado:** uma mensagem de retry e sucesso na segunda tentativa. Abra o JSONL da execução e procure `retentativa`.

Por que a próxima espera seria maior se outra falha ocorresse? **Resposta:** o backoff dá mais tempo para um recurso temporariamente indisponível se recuperar.

## 7. Falha de qualidade

```bash
py -3.14 executar.py executar --pasta execucoes/exercicios --falha qualidade --desde-evento 0
py -3.14 executar.py historico --pasta execucoes/exercicios
```

**Esperado:** mensagem de erro intencional, histórico com `falha`, alerta local e checkpoint preservado. A quantidade inválida só foi simulada em memória.

Por que não repetir três vezes automaticamente? **Resposta:** dados inválidos não se corrigem com espera.

## 8. Rollback real da carga

```bash
py -3.14 executar.py tudo --pasta execucoes/falha_carga
py -3.14 executar.py simular-lote --pasta execucoes/falha_carga
py -3.14 executar.py executar --pasta execucoes/falha_carga --falha carga
py -3.14 executar.py relatorio --pasta execucoes/falha_carga
```

**Esperado após a falha:** R$ 575,00 e checkpoint 6. Retome:

```bash
py -3.14 executar.py executar --pasta execucoes/falha_carga
```

**Esperado:** R$ 1.045,00 e checkpoint 11. O lote não foi perdido.

## 9. Automatizar três ciclos

```bash
py -3.14 executar.py automatizar --pasta execucoes/exercicios --intervalo 5 --repeticoes 3
```

**Esperado:** três execuções registradas, com primeira execução imediata e pausas entre elas. Como essa pasta já está atualizada, é normal que todas leiam zero eventos novos.

A agenda continua se fechar o terminal? **Não.** É um processo em primeiro plano, não um serviço instalado.

## 10. Interpretar a arquitetura

1. Por que não usar somente a data da venda para incrementalidade? **Porque alterações ou pedidos antigos podem chegar depois.**
2. Por que dados e checkpoint precisam do mesmo commit? **Para impedir que o marcador avance sem a carga ou que a carga seja tratada como não realizada de forma inconsistente.**
3. O resumo é incremental? **Nesta implementação, a extração e o fato são incrementais, mas o resumo é recalculado inteiro.**
4. Onde está a fonte oficial depois da carga? **No banco analítico. CSVs são exportações recuperáveis.**
5. Uma exportação com falha significa rollback do banco? **Não; a exportação ocorre depois do commit.**
6. Os alertas enviam e-mail? **Não; são arquivos locais para o exercício.**

## 11. Evidências dos testes

```bash
py -3.14 executar.py testar
```

**Esperado:** `Ran 22 tests` e `OK`. Guarde uma captura e explique pelo menos três testes usando suas próprias palavras. As evidências entregues mostram a validação desta versão; sua captura deve mostrar a execução no seu computador.
