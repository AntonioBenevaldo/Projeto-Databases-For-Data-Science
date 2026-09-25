# Explicação do código

## 1. Interface e identidade

`argparse` interpreta os comandos. `--pasta` seleciona um laboratório; `--credencial` aponta para um arquivo local de token. O padrão é admin para facilitar a primeira execução, mas o roteiro ensina a usar os perfis limitados.

`autenticar()` calcula SHA-256 do token e compara com os hashes cadastrados, usando `hmac.compare_digest`. Os tokens são aleatórios de alta entropia; não são senhas humanas. Essa escolha não significa que SHA-256 puro seja apropriado para armazenar senhas escolhidas por pessoas.

A autorização usa a matriz `ROLES`, no código. Ter uma credencial válida não concede automaticamente todas as operações.

## 2. Uma transação para o estado lógico

`chamar()` abre uma transação `BEGIN IMMEDIATE`, verifica a auditoria, autentica e executa a operação. Alterações nas tabelas, referência ativa e registro de sucesso são confirmadas juntas.

Negativas de acesso são registradas e confirmadas antes do erro ser retornado. Erros de operações fazem rollback; quando possível, um novo registro de falha é escrito sem incluir dados sensíveis. Uma cadeia já corrompida não é reescrita para parecer válida.

A transação SQLite não inclui os arquivos no sistema de arquivos. A publicação prepara uma pasta temporária, move a pasta completa e registra a versão. Exceções tratadas removem artefatos recém-criados. Um encerramento abrupto pode deixar uma pasta órfã: o projeto a detecta pelo nome existente e não a sobrescreve.

## 3. Extração e qualidade

A consulta usa `?` para início e fim e envia os parâmetros separados do texto SQL. A data é inclusiva. As linhas selecionadas passam por regras de chave, tipo, nulidade, faixa, desconto e domínio.

As regras só avaliam o recorte extraído. O projeto não faz varredura universal do banco nem aceita qualquer conjunto externo. O contrato exige identificadores e contatos do gerador simulado.

## 4. Minimização e pseudonimização

`transformar()` inclui apenas pedidos concluídos. O contato não é copiado para a publicação. A entidade recebe um código HMAC com chave separada, estável dentro do laboratório.

O mesmo identificador produz o mesmo pseudônimo com a mesma chave. Outro laboratório terá outra chave e, portanto, outros pseudônimos. Isso permite estudar estabilidade sem usar um hash simples de identificadores previsíveis.

O conjunto continua contendo ID do pedido, data e valores. Não se deve chamar isso de anonimização. Neste exercício os registros são sintéticos, sem pessoas reais.

## 5. Cópia bruta e Fernet

O CSV bruto é montado em memória. Fernet produz conteúdo cifrado com autenticação, que é gravado como `origem.csv.fernet`. A verificação decifra em memória e confere seu hash, sem exportar a origem em texto.

A chave fica em `segredos/criptografia.key`, fora do código e das pastas das versões. Fernet usa aleatoriedade: cifrar o mesmo conteúdo duas vezes pode produzir arquivos diferentes. Isso não indica alteração dos dados originais.

O banco de origem continua legível para quem tem acesso direto ao arquivo SQLite. Criptografar uma cópia não cifra automaticamente todas as outras cópias ou o disco.

## 6. Versão, manifesto e linhagem

Cada publicação recebe v0001, v0002 etc. O manifesto registra:

- período e consulta;
- perfil criador e horário UTC;
- contagens e indicadores;
- hash do CSV bruto e dos arquivos da versão;
- hashes do código e da configuração;
- versões de Python e cryptography;
- versão do esquema.

Esquema, catálogo, políticas e SQL acompanham o snapshot. O código completo deve ser preservado junto com a entrega: um hash identifica uma versão, mas não reconstrói o código que foi perdido.

A aplicação não sobrescreve versões anteriores. Isso é uma regra de publicação, não uma garantia de imutabilidade física do armazenamento.

## 7. SHA-256 e HMAC têm funções diferentes

SHA-256 calcula a impressão digital de um conteúdo. Sozinho, ele não impede que alguém altere o arquivo e seu hash.

HMAC usa uma chave para autenticar o manifesto. O catálogo também guarda o hash do manifesto. Para forjar tudo, um atacante com acesso suficiente precisaria conseguir comprometer os pontos de confiança correspondentes. Se ele controla todo o computador e as chaves, os controles locais não o impedem.

A chave de HMAC é simétrica: quem pode validar com a chave também tem material para produzir novos códigos. Não é uma assinatura digital com chave pública, nem fornece não repúdio entre participantes.

## 8. Verificação antes do uso

`conferir()` exige versão no padrão `vNNNN`, recusa links simbólicos nos caminhos de snapshots verificados, confere a lista exata de arquivos esperados e valida conteúdo e manifesto. Ele lê os bytes para memória antes de usá-los, reduzindo inconsistências entre a verificação e o consumo desses mesmos bytes.

`consultar`, `comparar` e `restaurar` passam por essa verificação. `listar` mostra somente o catálogo; não substitui a verificação dos arquivos.

## 9. Comparação e alerta

Os conjuntos são comparados por `pedido_id`. Um pedido que se tornou concluído pode aparecer como adicionado mesmo já existindo na origem. Um cancelamento aparece como remoção da publicação. Valores ou pseudônimos diferentes fazem uma chave comum aparecer como alterada.

A variação de linhas é calculada em percentual. O limiar da política do segundo snapshot gera um sinal didático quando ultrapassado. Não há detecção estatística de drift, nem envio de mensagens.

## 10. Restaurar é mudar uma referência

A tabela `estado` indica a versão ativa. Restaurar confere a versão e modifica essa referência. Não apaga snapshots, não recria o banco e não desfaz mudanças operacionais. Consultas sem versão explícita passam a usar a versão restaurada.

A cópia bruta cifrada serve como evidência do recorte; não é um backup completo do laboratório com usuários, auditoria e chaves. O projeto não oferece comando de restauração total de desastre.

## 11. Auditoria encadeada

Cada registro inclui o código do registro anterior. A autenticação cobre esse encadeamento e o conteúdo do evento. Alterar um evento existente ou quebrar a sequência provoca erro na verificação.

A cadeia local não tem âncora externa: apagar o final e deixar um prefixo íntegro pode não ser detectado. Quem controla as chaves e todo o armazenamento também pode reconstruí-la. Em produção, isso pede armazenamento e administração separados.

Os logs evitam valores secretos, contatos e linhas brutas. Em negativa de um perfil autenticado, registram esse perfil; em token inválido, registram `nao_autenticado`.

## 12. Testes e evidências

Os testes usam bancos e arquivos temporários. Eles tentam publicar com analista, adulteram cópias, mudam manifestos e hashes, verificam a cifra, comparam dados e restauram referências.

Um teste que altera o hash no catálogo mas preserva uma assinatura HMAC inválida verifica por que o hash isolado não basta. Outro confirma que uma falha de publicação não muda a versão ativa.

Os arquivos em `evidencias` documentam os testes realmente executados; não contêm as chaves usadas durante essa execução.
