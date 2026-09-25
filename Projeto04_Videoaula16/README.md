# Projeto 04 — Videoaula 16

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

## Boas práticas de segurança, governança e versionamento de dados

**Laboratório de dados comerciais simulados, executado pelo terminal Python.**

Preparado para Benevaldo com base na seção “Videoaula 16 — Boas práticas de segurança, governança e versionamento de dados” do PDF *CONTEÚDO DESTA UNIDADE 4*, da disciplina Databases for Data Science. A organização em módulos considera o print enviado. O código é uma implementação didática própria; o vídeo e o código do professor não foram acessados.

Este quarto projeto é independente dos três anteriores. Não é necessário copiar bancos ou arquivos entre eles. O foco é entender permissões, qualidade, catálogo, auditoria, proteção de cópias e recuperação de uma versão anterior.

## 1. O que está implementado

| Pilar | Recurso prático |
|---|---|
| Segurança | Credenciais aleatórias, autenticação por token e permissões por perfil nos comandos |
| Minimização | Exclusão dos contatos e substituição do identificador da entidade por pseudônimo |
| Criptografia | Cópia bruta do recorte cifrada com Fernet |
| Integridade | SHA-256 dos arquivos, HMAC do manifesto e verificação antes de ler/restaurar |
| Governança | Catálogo, dicionário, políticas e regras de qualidade no código |
| Auditoria | Ações permitidas, recusadas e falhas; registros encadeados por HMAC |
| Versionamento | Snapshots v0001, v0002 etc., sem sobrescrever versões anteriores |
| Comparação | Pedidos adicionados, removidos e alterados, e diferença de faturamento |
| Recuperação | Alteração da versão ativa sem apagar as versões nem modificar a origem |

Os dados são artificiais: identificadores começam com `DEMO_ENTIDADE_` e contatos usam o domínio `example.invalid`. Não coloque dados reais neste laboratório.

**Limite importante:** as permissões são verificadas pela aplicação. Quem controla a pasta, o Python e todos os arquivos de credenciais pode assumir todos os perfis. Este é um exercício de controles, não um servidor seguro multiusuário. Leia `docs/SEGURANCA_E_LIMITES.md`.

## 2. Preparação do ambiente

Use os quatro comandos da seção “Começar no seu Windows com Python 3.14”, no início deste README. O restante do guia usa o mesmo iniciador `executar.py`.

## 3. Executar o fluxo completo inicial

```bash
py -3.14 executar.py tudo
py -3.14 executar.py testar
```

`tudo` inicializa o laboratório, publica uma versão, verifica sua integridade e consulta os indicadores. Na primeira execução, gera `v0001`.

| Indicador | Resultado inicial |
|---|---:|
| Pedidos na origem | 6 |
| Pedidos concluídos publicados | 4 |
| Faturamento após descontos | R$ 575,00 |
| Custo total | R$ 370,00 |
| Lucro bruto | R$ 205,00 |

Os valores monetários aparecem em centavos: `57500` significa R$ 575,00. O lucro bruto não desconta tributos ou outras despesas.

Os testes devem mostrar **`Ran 24 tests` e `OK`**.

**Cada chamada de `publicar` ou `tudo` cria uma nova versão**, mesmo quando os dados não mudaram. Para consultar novamente sem criar versão, use `consultar`.

## 4. Etapa 1 — Inicialização e credenciais

```bash
py -3.14 executar.py inicializar
```

Esse comando cria:

- `data/laboratorio.db`: dados simulados, hashes das credenciais, catálogo das versões, referência ativa e auditoria;
- `segredos/admin.token`, `engenheiro.token`, `analista.token` e `auditor.token`;
- três chaves separadas: criptografia, autenticação de manifestos/auditoria e pseudonimização.

As credenciais são geradas aleatoriamente no seu computador. Nenhuma senha fixa acompanha o ZIP e nenhum token é mostrado no terminal. O banco armazena o hash do token, não o token original.

Repetir `inicializar` preserva o ambiente existente. As chaves não são regeneradas automaticamente. Se perder as chaves, não será possível validar ou decifrar adequadamente as versões antigas. Para um estudo novo, prefira outra pasta:

```bash
py -3.14 executar.py tudo --pasta execucoes/novo_estudo
```

Repita `--pasta` nos comandos daquele estudo. O caminho informado em `--credencial`, quando relativo, é relativo ao terminal, não à opção `--pasta`.

## 5. Etapa 2 — Entender os perfis

| Operação | Admin | Engenheiro | Analista | Auditor |
|---|---|---|---|---|
| Publicar versão | Sim | Sim | Não | Não |
| Simular alteração na origem | Sim | Sim | Não | Não |
| Listar e verificar versões | Sim | Sim | Sim | Sim |
| Consultar/exportar dados publicados | Sim | Sim | Sim | Não |
| Comparar versões | Sim | Sim | Não | Sim |
| Restaurar versão ativa | Sim | Não | Não | Não |
| Exportar auditoria | Sim | Não | Não | Sim |
| Consultar catálogo | Sim | Sim | Sim | Sim |

O padrão usa a credencial admin do laboratório para facilitar o roteiro. Para praticar menor privilégio, informe explicitamente a credencial do perfil adequado.

Consulta permitida para analista:

```bash
py -3.14 executar.py consultar --credencial segredos/analista.token
```

Publicação proibida para analista:

```bash
py -3.14 executar.py publicar --credencial segredos/analista.token
```

**Esperado:** o segundo comando retorna erro de permissão e registra a negativa na auditoria. Isso é um teste intencional, não defeito de instalação. Não altere a credencial para “corrigir” essa negativa: compare a operação com a matriz de permissões.

Não copie o conteúdo dos arquivos `.token` para comandos ou capturas. Informe somente o caminho do arquivo.

## 6. Etapa 3 — Publicar uma versão

```bash
py -3.14 executar.py publicar --credencial segredos/engenheiro.token
```

A publicação executa:

1. Autentica o token e verifica a permissão.
2. Verifica a cadeia de auditoria existente.
3. Extrai o recorte por consulta SQL parametrizada.
4. Valida campos, chaves, valores, datas e o contrato de dados simulados.
5. Seleciona somente pedidos concluídos.
6. Remove `contato_simulado` e substitui `cliente_simulado` por HMAC.
7. Calcula faturamento, custo total e lucro bruto em centavos inteiros.
8. Criptografa a cópia bruta do recorte em memória e grava apenas o conteúdo cifrado.
9. Copia esquema, catálogo, políticas e SQL para a pasta da versão.
10. Registra hashes, código, parâmetros, versões das ferramentas e horário UTC.
11. Grava o manifesto autenticado e atualiza o catálogo e a referência ativa.

A pasta de uma versão contém:

| Arquivo | Finalidade |
|---|---|
| `dados.csv` | Conjunto minimizado e pseudonimizado para análise |
| `origem.csv.fernet` | Cópia cifrada das linhas de origem do recorte |
| `manifesto.json` | Metadados, hashes e autenticação HMAC |
| `esquema.json` | Estrutura e regras documentadas |
| `catalogo.json` | Finalidade, fonte e responsabilidades |
| `politicas.json` | Políticas didáticas e limites |
| `consulta.sql` | Consulta usada na extração |

Para outro período:

```bash
py -3.14 executar.py publicar --inicio 2026-01-01 --fim 2026-01-02
```

Os limites são inclusivos. Um período sem pedidos é válido e gera um CSV com cabeçalhos e totais zero. As regras são aplicadas ao recorte extraído; registros fora do período não são avaliados por essa publicação.

## 7. Etapa 4 — Listar, verificar e consultar

```bash
py -3.14 executar.py listar
py -3.14 executar.py verificar --versao v0001
py -3.14 executar.py consultar --versao v0001
```

`listar` mostra o catálogo e a versão ativa. Ele não lê e verifica todos os arquivos; para verificar o conteúdo, use `verificar`.

`verificar` confere o manifesto em relação ao catálogo, seu HMAC, todos os hashes, a cópia cifrada e seu conteúdo decifrado em memória. Não exporta a cópia bruta.

`consultar` verifica a versão antes de gerar uma pasta de relatório em `outputs/consulta_<versao>_<id>/`, contendo:

- `dados_publicados.csv`;
- `indicadores.json`;
- `relatorio.md`.

Sem `--versao`, consulta a referência ativa. Abra o Markdown no VS Code e use **Ctrl+Shift+V** para visualizar.

## 8. Etapa 5 — Criar a segunda versão

Para reproduzir exatamente os nomes v0001 e v0002, use este roteiro em uma pasta nova:

```bash
py -3.14 executar.py tudo --pasta execucoes/comparacao
py -3.14 executar.py simular-lote --pasta execucoes/comparacao
py -3.14 executar.py publicar --pasta execucoes/comparacao
py -3.14 executar.py comparar --pasta execucoes/comparacao --de v0001 --para v0002
```

O lote atualiza dois pedidos, cancela um e acrescenta dois. A origem muda, mas uma versão já publicada não muda junto: é preciso publicar outra.

| Indicador | v0001 | v0002 |
|---|---:|---:|
| Pedidos concluídos | 4 | 6 |
| Faturamento | R$ 575,00 | R$ 1.045,00 |
| Custo total | R$ 370,00 | R$ 655,00 |
| Lucro bruto | R$ 205,00 | R$ 390,00 |

Comparação esperada:

- pedidos adicionados ao conjunto publicado: **3, 7 e 8**;
- pedido removido do conjunto publicado: **4**, por cancelamento;
- pedido alterado: **2**;
- diferença de faturamento: **R$ 470,00**;
- aumento do número de linhas: **50%**.

O pedido 3 já existia na origem, mas passou de pendente para concluído. Por isso é “adicionado” à publicação. A comparação descreve conjuntos publicados, não somente inserções físicas no banco.

O aumento de volume ultrapassa o limiar didático de 30% definido na política e gera `alerta_volume: true`. É um sinal para revisão, não um teste estatístico de drift nem prova de erro.

## 9. Etapa 6 — Restaurar a referência ativa

Na mesma pasta do exercício anterior:

```bash
py -3.14 executar.py restaurar --pasta execucoes/comparacao --versao v0001
py -3.14 executar.py consultar --pasta execucoes/comparacao
```

**Esperado:** a consulta ativa volta ao faturamento de **R$ 575,00**.

A restauração verifica a integridade antes de mudar a referência. Ela preserva a v0002 e o estado atual da origem. Não desfaz alterações da tabela operacional e não apaga histórico.

Para retornar à segunda versão:

```bash
py -3.14 executar.py restaurar --pasta execucoes/comparacao --versao v0002
```

Esse comando exige admin. O papel de engenheiro pode publicar versões, mas não restaurar a referência ativa.

## 10. Etapa 7 — Consultar governança e auditoria

```bash
py -3.14 executar.py catalogo
py -3.14 executar.py auditoria --credencial segredos/auditor.token
```

A governança documenta finalidade, origem, classificação, dono e gestor do dado por funções simuladas, periodicidade e regras. As validações efetivas estão em `src/data.py`: editar o texto da política não altera automaticamente todas as regras do código.

A auditoria registra perfil, ação, status, horário UTC e detalhes selecionados. Não inclui tokens, chaves, contatos nem linhas brutas. Cada evento recebe HMAC ligado ao evento anterior.

A exportação da auditoria verifica a cadeia e escreve um JSON em `outputs`. O evento da própria leitura é acrescentado depois da exportação; por isso o arquivo contém os registros anteriores à conclusão desse comando.

## 11. Testes automatizados

```bash
py -3.14 executar.py testar
```

Os **24 testes** usam pastas temporárias e não alteram seu laboratório. Cobrem permissões, tokens inválidos, minimização, criptografia, alterações de CSV/manifesto/auditoria, comparação, restauração, qualidade, hashes, pseudônimos, falhas e preservação de versões.

Os testes aprovados validam esses comportamentos no ambiente testado. Não equivalem a auditoria de segurança, certificação ou comprovação de conformidade legal.

## 12. Arquivos para estudar

| Local | Responsabilidade |
|---|---|
| `projeto.py` | Interface de comandos |
| `src/service.py` | Autorização, operações e transações |
| `src/security.py` | Tokens, hashes, HMAC e Fernet |
| `src/audit.py` | Cadeia de auditoria |
| `src/data.py` | Extração, validação e minimização |
| `src/snapshot.py` | Publicação, verificação e comparação |
| `src/config.py` | Colunas, perfis e SQL |
| `src/schema.sql` | Estrutura do banco |
| `governance/` | Catálogo, esquema e políticas |
| `docs/EXPLICACAO_DO_CODIGO.md` | Explicação técnica por etapa |
| `docs/SEGURANCA_E_LIMITES.md` | O que cada controle protege e seus limites |
| `docs/EXERCICIOS.md` | Exercícios e respostas esperadas |
| `evidencias/` | Resultados reais da validação da entrega |

Também existem atalhos semelhantes à organização do print:

```bash
./.venv314/Scripts/python.exe scripts/init_project.py
./.venv314/Scripts/python.exe scripts/run_pipeline.py
./.venv314/Scripts/python.exe scripts/inspect_versions.py
```

Eles correspondem a `inicializar`, `publicar` e `listar`; não é necessário executar as duas formas.

## 13. Problemas comuns

| Situação | Como resolver |
|---|---|
| Python não encontrado | Configure Python 3.14; se disponível, use o inicializador `py -3.14`. |
| `can't open file projeto.py` | Abra o terminal na pasta principal correta. |
| Dependência ausente | Execute `pip install -r requirements.txt` usando o Python da mesma venv. |
| `SyntaxError` ao colar um comando | Saia do prompt `>>>` com `exit()` e use o terminal. |
| Credencial não encontrada | Confira a inicialização e o caminho do arquivo `.token`. |
| Perfil sem permissão | Confira a matriz. Use a credencial adequada à operação autorizada. |
| Versão não encontrada | Execute `listar` e informe um identificador existente. |
| Integridade falhou | Não use a versão alterada; investigue ou recupere uma cópia íntegra. Não edite hashes para forçar aprovação. |
| Chaves perdidas | Recupere as chaves originais do seu backup protegido; novas chaves não abrem cópias antigas. |
| Pasta residual de versão | Pode ter ocorrido interrupção entre arquivos e banco. Preserve para investigação ou use uma pasta nova para o estudo; não sobrescreva versões silenciosamente. |
| v0001/v0002 não correspondem ao roteiro | Publicações repetidas criam novas versões. Use a pasta nova indicada no exercício. |

Para Linux/macOS, use `python3.14 executar.py instalar` e troque `py -3.14` por `python3.14` nos comandos. O iniciador seleciona automaticamente `.venv314/bin/python`.

## 14. Limites e fontes

O banco SQLite e os CSVs publicados não são criptografados por este projeto. A criptografia Fernet protege a cópia bruta em cada snapshot. As chaves precisam ser protegidas separadamente para que essa proteção seja útil.

O código usa HMAC para autenticação simétrica, não assinatura digital assimétrica. Pseudonimização não é anonimização. Os snapshots são preservados pela aplicação, mas não estão em armazenamento imutável do tipo WORM.

Esta versão não instala MFA, TLS, serviço de rede, cofre externo, DVC, Git ou permissões de Windows por usuário. Não publica dados na internet. A política de retenção é documentada; não há exclusão automática de versões.

Validação realizada em Linux/Python 3.14. Os comandos Windows estão documentados, mas não foram executados em Windows nesta sessão.

Fontes utilizadas:

- Material enviado: *Databases for Data Science — Unidade IV*, seção Videoaula 16.
- Fernet, documentação oficial: https://cryptography.io/en/stable/fernet/
- HMAC, documentação Python: https://docs.python.org/3.14/library/hmac.html

Documentação técnica consultada durante a elaboração em 21/09/2026. Finalização e testes desta entrega em 22/09/2026. A biblioteca utilizada está fixada em requirements.txt; a documentação online pode mostrar outra versão.

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
