# Validação da edição Python 3.14

Data: 24/09/2026. Ambiente executado: Linux x86_64, CPython 3.14.7.

## Resultado deste projeto

- `executar.py instalar`: aprovado, em ambiente virtual novo e isolado.
- `executar.py tudo`: aprovado.
- `executar.py testar`: **18 testes aprovados**.
- O iniciador foi chamado por caminho absoluto a partir de outra pasta (`/tmp`), conferindo que localiza corretamente os arquivos do projeto.
- Cada projeto foi instalado em sua própria `.venv314`, sem usar bibliotecas globais.

As saídas reais estão em `instalar_python314.txt`, `tudo_python314.txt` e `testar_python314.txt`. As versões instaladas estão em `versoes_instaladas_python314.txt`. Resultados de referência estão em `resultado_referencia/`.

## Dependências diretas

```text
numpy==2.3.5
pandas==2.3.3
scikit-learn==1.8.0
joblib==1.5.3
matplotlib==3.10.8
```

## Windows: o que foi conferido

O pip conseguiu resolver e baixar todos os pacotes como wheels para **CPython 3.14, ABI cp314, Windows x64 (`win_amd64`)**. A verificação incluiu as dependências transitivas e o driver opcional psycopg. Isso confirma a disponibilidade dos pacotes prontos para a plataforma, evitando a compilação que falhava com pandas 2.2.3.

**Não houve execução em Windows.** Os testes de código foram realizados em Linux/Python 3.14.7. Python 3.14.0 e 3.14.6 não foram executados separadamente. Não foram testados Python de 32 bits, Windows ARM64 nem a compilação free-threaded.

R e PostgreSQL/Docker não foram executados nesta revisão. O Projeto 1 mantém essas etapas opcionais, que exigem programas separados. O fluxo SQLite/Python foi executado.

## Entrega

O pacote não inclui ambientes virtuais, bancos gerados, modelos treinados, tokens ou chaves. Eles são criados no computador do aluno. Os resultados são didáticos e usam dados simulados. A validação técnica não constitui auditoria ou certificação de segurança.
