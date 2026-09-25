# Quatro projetos — Python 3.14

Edição revisada para Benevaldo em 24/09/2026. Use **CPython 3.14 de 64 bits no Windows x64**. Você pode manter seu Python 3.14; este pacote não pede Python 3.12.

## Comece aqui

1. Extraia este ZIP em uma **pasta nova**. Não misture com as versões antigas.
2. No VS Code, escolha **Arquivo > Abrir Pasta** e selecione `Projeto_Videoaula13`, dentro deste pacote.
3. Veja se `executar.py`, `projeto.py` e `requirements.txt` aparecem diretamente nessa pasta.
4. Abra **Terminal > Novo Terminal**. Pode usar o **Bash** que já está instalado, PowerShell ou CMD.
5. Execute um comando por vez:

```bash
py -3.14 --version
py -3.14 executar.py instalar
py -3.14 executar.py tudo
py -3.14 executar.py testar
```

Não digite o símbolo `$`, nem `PS ...>` junto dos comandos. Se aparecer `>>>`, digite `exit()` antes. O terminal inicia os programas Python; não é necessário entrar no interpretador interativo.

`instalar` cria a `.venv314` dentro do projeto, instala as bibliotecas e exibe o diagnóstico. Não precisa ativar a venv, usar barras de caminhos do Windows nem apagar a `.venv13` antiga. Aguarde o comando terminar. Se houver erro, pare nessa etapa.

Se `py` não for reconhecido, use `python --version`. Somente se mostrar 3.14.x, use `python executar.py instalar` e o mesmo prefixo nos demais comandos.

## Pastas e resultados

| Pasta | Aula e objetivo | Testes aprovados |
|---|---|---:|
| `Projeto_Videoaula13` | 13 — Conexão, extração e análise; Python e R | 12 |
| `Projeto02_Videoaula14` | 14 — Ingestão e pré-processamento para ML | 18 |
| `Projeto03_Videoaula15` | 15 — Automação de consultas e pipelines | 22 |
| `Projeto04_Videoaula16` | 16 — Segurança, governança e versões | 24 |

Cada pasta tem seu próprio README, exercícios comentados, dados simulados e relatório de validação. Abra uma pasta por vez no VS Code. Execute os mesmos quatro comandos dentro de cada projeto: eles são independentes e cada um cria seu próprio ambiente.

## Projeto 1: executar etapa por etapa

Depois de `instalar`, você pode estudar as etapas separadamente:

```bash
py -3.14 executar.py preparar
py -3.14 executar.py extrair
py -3.14 executar.py analisar
py -3.14 executar.py testar
```

`preparar`: 4 produtos e 12 vendas. `extrair`: 10 vendas concluídas. `analisar`: faturamento de R$ 1.053,00, custo de R$ 630,00 e lucro bruto de R$ 423,00. Veja os arquivos em `outputs/python`.

`tudo` executa essas três etapas. A etapa R é separada: os comandos Python podem iniciar Rscript, mas R deve estar instalado. PostgreSQL/Docker também é opcional; o fluxo inicial usa SQLite.

## Correções desta edição

O erro anterior ocorria porque pandas 2.2.3 não possuía wheel para Python 3.14. Agora os projetos usam pandas 2.3.3 e dependências resolvidas para 3.14. O iniciador usa `--only-binary=:all:` para evitar compilações locais. Nos exercícios do Projeto 4, cada `tudo` cria uma nova versão; use `consultar` para reler sem publicar outra.

## Validação e limites

**76 testes passaram**. Os quatro instaladores e quatro fluxos completos foram executados em **Linux com Python 3.14.7**, cada projeto em seu ambiente isolado. Os pacotes para Windows x64/Python 3.14 foram resolvidos e baixados com sucesso, inclusive o driver opcional do PostgreSQL. Isso não equivale a executar os programas em Windows: essa execução deve ser conferida no seu computador. R e servidor PostgreSQL não foram executados nesta revisão.

Consulte `RELATORIO_GERAL.md` e `evidencias/RELATORIO_VALIDACAO.md` em cada projeto. Os arquivos da edição anterior foram preservados fora deste pacote; esta revisão traz evidências novas.
