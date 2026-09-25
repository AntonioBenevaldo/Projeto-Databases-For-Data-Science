# Exercícios com respostas

Use uma pasta nova para manter os nomes de versões previsíveis. Nos comandos, `--pasta execucoes/aula16` separa este exercício do laboratório principal.

## 1. Criar a primeira versão

```bash
py -3.14 executar.py tudo --pasta execucoes/aula16
```

**Esperado:** v0001, quatro pedidos concluídos, faturamento de R$ 575,00. A verificação retorna `OK`.

## 2. Consultar com menor privilégio

```bash
py -3.14 executar.py consultar --pasta execucoes/aula16 --credencial execucoes/aula16/segredos/analista.token
```

**Esperado:** consulta permitida. O relatório não contém contatos ou identificadores de entidade originais.

## 3. Tentar uma operação proibida

```bash
py -3.14 executar.py publicar --pasta execucoes/aula16 --credencial execucoes/aula16/segredos/analista.token
```

**Esperado:** erro de permissão; nenhuma nova versão. A negativa fica registrada. Esse erro é intencional.

## 4. Atualizar e versionar

```bash
py -3.14 executar.py simular-lote --pasta execucoes/aula16
py -3.14 executar.py publicar --pasta execucoes/aula16
py -3.14 executar.py comparar --pasta execucoes/aula16 --de v0001 --para v0002
```

**Esperado:** v0002 com seis pedidos concluídos e faturamento de R$ 1.045,00. Adicionados: 3, 7 e 8. Removido: 4. Alterado: 2. Diferença: R$ 470,00.

Por que o pedido 3 é adicionado, se já existia? **Porque passou de pendente para concluído e entrou no conjunto publicado.**

## 5. Voltar à versão anterior

```bash
py -3.14 executar.py restaurar --pasta execucoes/aula16 --versao v0001
py -3.14 executar.py consultar --pasta execucoes/aula16
py -3.14 executar.py listar --pasta execucoes/aula16
```

**Esperado:** consulta com R$ 575,00, mas as duas versões continuam no catálogo. A origem não voltou ao estado inicial.

## 6. Conferir auditoria

```bash
py -3.14 executar.py auditoria --pasta execucoes/aula16 --credencial execucoes/aula16/segredos/auditor.token
```

**Esperado:** cadeia `OK`. Abra o arquivo indicado e localize a negativa do analista. Não deve haver conteúdo dos tokens.

## 7. Detectar adulteração em cópia de estudo

Crie outro laboratório:

```bash
py -3.14 executar.py tudo --pasta execucoes/integridade
```

Abra somente `execucoes/integridade/versoes/v0001/dados.csv`, altere um valor e salve. Depois:

```bash
py -3.14 executar.py verificar --pasta execucoes/integridade --versao v0001
```

**Esperado:** falha de integridade. Esse laboratório foi adulterado de propósito. Não modifique o manifesto para contornar a falha; preserve-o para observar o resultado. Use outra pasta para novos exercícios.

## 8. Interpretar os três pilares

1. Quem pode restaurar? **Admin.**
2. Quem define o significado do faturamento? **O catálogo e as regras do domínio; o código aplica a definição documentada.**
3. Como saber qual conjunto foi usado? **Identificador da versão, arquivos, consulta, hashes e metadados.**
4. HMAC é assinatura digital assimétrica? **Não; usa chave compartilhada.**
5. A cópia cifrada torna o SQLite cifrado? **Não; são artefatos diferentes.**
6. Pseudônimo significa anonimização? **Não; ainda pode permitir associação/correlação.**
7. Restaurar a versão apaga a mais nova? **Não.**
8. Repetir `publicar` sem mudanças cria versão? **Sim; os dados publicados podem ser iguais, mas a publicação tem outro registro.**
9. O alerta de aumento de 50% prova erro? **Não; aponta uma mudança para revisão.**

## 9. Testes finais

```bash
py -3.14 executar.py testar
```

**Esperado:** `Ran 24 tests` e `OK`. Os testes usam pastas temporárias, inclusive para adulterações intencionais. Registre a execução no seu computador e explique três testes com suas palavras.

## 10. Como os quatro projetos se relacionam

| Projeto | Pergunta principal |
|---|---|
| 01 — Conexão Python/R | Como acessar e analisar os dados do banco? |
| 02 — Pré-processamento | Como preparar dados para machine learning sem aprender com o teste? |
| 03 — Automação | Como repetir consultas e cargas com controle de falhas? |
| 04 — Governança e versões | Quem pode operar, como verificar os dados e como recuperar uma versão? |

Os projetos são independentes para facilitar o aprendizado. Eles não foram integrados automaticamente em um único sistema.
