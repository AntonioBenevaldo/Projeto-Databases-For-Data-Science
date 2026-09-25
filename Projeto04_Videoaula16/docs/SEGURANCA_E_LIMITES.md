# Segurança: controles implementados e limites

| Controle | O que protege neste exercício | O que não garante |
|---|---|---|
| Token aleatório | Autenticação da chamada na aplicação | Identidade humana, MFA ou sessão corporativa |
| RBAC por comando | Operações permitidas para cada perfil | Isolamento contra acesso direto ao SQLite, Python ou arquivos |
| HMAC de identificador | Pseudônimo estável com chave | Anonimização ou impossibilidade de correlação |
| Fernet | Confidencialidade e integridade da cópia bruta cifrada | Criptografia do banco, dos CSVs publicados ou do disco |
| Hashes | Detecção de diferenças de conteúdo | Autenticidade sem um ponto de confiança protegido |
| HMAC do manifesto | Autenticação simétrica dos metadados | Assinatura assimétrica ou proteção quando a chave foi comprometida |
| Auditoria encadeada | Detecção de alteração dos registros presentes | Detecção universal de remoção do final, nem armazenamento inviolável |
| Snapshots preservados | Histórico pela interface do projeto | WORM, replicação ou tolerância a perda do disco |
| Restauração de referência | Voltar a consultar uma versão íntegra | Restaurar toda a origem, chaves ou infraestrutura |

## Como usar o laboratório

- Use somente dados simulados.
- Não publique `segredos`, `data`, `versoes` ou saídas sem revisar o conteúdo. O `.gitignore` ajuda com arquivos não rastreados, mas não remove algo já commitado.
- Não cole tokens/chaves no terminal, em capturas ou mensagens. Os comandos recebem caminhos dos arquivos.
- Proteja as chaves e o banco conforme as permissões e recursos do seu sistema operacional. O `chmod` usado para criação é apropriado a permissões POSIX; não configura ACLs individuais do Windows.
- No exercício, a mesma pessoa recebe todas as credenciais para testar os perfis. Em um sistema real, cada pessoa ou serviço teria apenas a credencial necessária.
- Não modifique hashes ou registros de auditoria para fazer um erro desaparecer. Preserve a evidência e recupere uma cópia íntegra.
- Preserve o código, versões de dependências e chaves necessárias junto à estratégia de recuperação, com controles de acesso adequados. A cifra sem a chave não permite recuperar os dados.

## Práticas da aula que ficam como evolução

O exercício não implementa MFA, TLS, redes privadas, cofre gerenciado, rotação/revogação de tokens, separação física de ambientes, gestão de identidades, alertas externos ou armazenamento externo imutável. Ele não instala DVC e não publica repositório Git.

Esses limites importam ao adaptar o projeto: uma aplicação local de estudo não comprova segurança de um ambiente real. A política de retenção é documental; não há serviço que apague versões ao vencer um prazo.

O projeto demonstra controles técnicos e responsabilidades. Não faz análise de bases legais, direitos de titulares ou outros requisitos de um tratamento real; não constitui comprovação automática de conformidade com a LGPD.
