#!/usr/bin/env bash
#
# Sobe o ERPNext com a porta 8080 fixada no IP ATUAL da Tailscale.
# Resolve o IP na hora — não há IP hard-coded no pwd.yml.
# Se você reinstalar o Tailscale e o IP mudar, basta rodar este script de novo.
#
set -euo pipefail

cd "$(dirname "$0")"

# 1. Descobrir o IP atual da Tailscale
TS_IP="$(tailscale ip -4 2>/dev/null | head -n1 || true)"

if [[ -z "${TS_IP}" ]]; then
  echo "ERRO: não consegui obter o IP da Tailscale (tailscale ip -4 vazio)."
  echo "      O Tailscale está ativo?  ->  sudo tailscale status"
  exit 1
fi

echo ">> IP Tailscale detectado: ${TS_IP}"

# 2. Detectar override da imagem customizada (ury-erp).
#    Se ury.override.yml existir, ele é aplicado por cima do pwd.yml,
#    trocando as imagens padrão pela imagem custom (frappe+erpnext+hrms+ury).
COMPOSE_FILES=(-f pwd.yml)
if [[ -f ury.override.yml ]]; then
  COMPOSE_FILES+=(-f ury.override.yml)
  echo ">> Override detectado: usando ury.override.yml (imagem customizada)."
else
  echo ">> Sem override — usando imagens padrão do pwd.yml."
fi

echo ">> Subindo a stack do ERP (todos os serviços) com bind em ${TS_IP}:8080 ..."

# 3. Subir a stack completa (o compose lê ${TS_IP} e o .env do ambiente).
#    Subir só o frontend deixaria backend/db fora e o nginx falha em
#    "host not found in upstream backend:8000".
TS_IP="${TS_IP}" docker compose "${COMPOSE_FILES[@]}" up -d

# 3. Confirmar o binding aplicado
echo ">> Binding atual:"
docker inspect frappe_docker-frontend-1 \
  --format '{{json .HostConfig.PortBindings}}' 2>/dev/null || true

echo ""
echo ">> Pronto. ERP acessível em:  http://${TS_IP}:8080  (somente pela VPN)"
