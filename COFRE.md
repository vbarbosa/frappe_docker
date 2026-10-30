# Segredos no OCI Vault

Desde 30/10/2026 os segredos técnicos deste projeto (senhas de banco, chaves, tokens) **vêm do OCI Vault em runtime** e não ficam em `.env` nem na configuração dos containers.
O mecanismo é comum aos projetos desta VM: `vault-secrets@<projeto>.service` lê o Vault com a identidade da VM (Instance Principal) e grava em `/run/vault-secrets/<projeto>` (tmpfs). Documentação completa: `manchete-stack/infra/vm/vault-secrets/README.md`.
O `.env` (0600) guarda só configuração e, quando houver, senhas de contas de usuário da aplicação.

## Este projeto
- Parado (sem containers). A senha técnica do banco (`frappe_docker__env__DB_PASSWORD`, compartimento `manchete`) saiu do `.env` e existe só no Vault. `ADMIN_PASSWORD` (conta de usuário) continua no `.env`.
