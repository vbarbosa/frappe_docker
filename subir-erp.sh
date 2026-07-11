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
echo ">> Subindo a stack do ERP (todos os serviços) com bind em ${TS_IP}:8080 ..."

# 2. Subir a stack completa (o compose lê ${TS_IP} e o .env do ambiente).
#    Subir só o frontend deixaria backend/db fora e o nginx falha em
#    "host not found in upstream backend:8000".
TS_IP="${TS_IP}" docker compose -f pwd.yml up -d

# 3. Confirmar o binding aplicado
echo ">> Binding atual:"
docker inspect frappe_docker-frontend-1 \
  --format '{{json .HostConfig.PortBindings}}' 2>/dev/null || true

echo ""
echo ">> Pronto. ERP acessível em:  http://${TS_IP}:8080  (somente pela VPN)"
