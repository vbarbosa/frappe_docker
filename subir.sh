#!/bin/bash
# Sobe o ambiente URY (ERPNext + POS + Mosaic) de forma robusta, corrigindo os
# 3 problemas recorrentes deste setup:
#   1. timing: backend tenta conectar no DB antes dele subir
#   2. CSS quebrado: Redis guarda mapa de assets fantasma apos recriar o backend
#   3. 502 Bad Gateway: nginx do frontend cacheia o IP antigo do backend
#
# Uso:  cd /home/ubuntu/GitHub/frappe_docker && bash subir.sh
set -u
cd "$(dirname "$0")"

export TS_IP="${TS_IP:-100.70.92.116}"
CO="docker compose -f pwd.yml -f ury.override.yml"
URL_LOCAL="http://localhost:8080"
URL_VPN="http://${TS_IP}:8080"

echo "==> 1/5  Subindo os containers"
$CO up -d 2>&1 | grep -viE "warning|is up-to-date" | sed 's/^/     /'

echo "==> 2/5  Aguardando o backend responder"
for i in $(seq 1 40); do
  code=$(curl -s -o /dev/null -w "%{http_code}" "$URL_LOCAL/api/method/ping" 2>/dev/null || echo 000)
  if [ "$code" = "502" ]; then
    # nginx com IP velho do backend -> re-resolver
    $CO restart frontend >/dev/null 2>&1
  elif [ "$code" != "000" ]; then
    break
  fi
  sleep 3
done
echo "     backend respondeu (HTTP $code)"

echo "==> 3/5  Limpando o cache do Redis (corrige CSS/assets)"
$CO exec -T redis-cache redis-cli FLUSHALL >/dev/null 2>&1 && echo "     redis-cache limpo"

echo "==> 4/5  Limpando o cache do site"
$CO exec -T backend bench --site frontend clear-cache 2>&1 | grep -viE "warning|TS_IP" | tail -1 | sed 's/^/     /'

echo "==> 5/5  Verificando as rotas"
all_ok=1
for p in "/login" "/pos" "/app" "/URYMosaic/Cozinha"; do
  code=$(curl -s -o /dev/null -w "%{http_code}" "$URL_LOCAL$p" 2>/dev/null)
  case "$code" in 200|301|302) tag="OK" ;; *) tag="FALHOU"; all_ok=0 ;; esac
  printf "     %-24s %s (%s)\n" "$p" "$tag" "$code"
done
# amostra de CSS (o sintoma da pagina "feia")
css_ok=0; css_tot=0
for css in $(curl -s -L "$URL_LOCAL/login" 2>&1 | grep -oiE '/assets/[^"'\'' ]*\.css' | sort -u | head -6); do
  css_tot=$((css_tot+1)); [ "$(curl -s -o /dev/null -w '%{http_code}' "$URL_LOCAL$css")" = "200" ] && css_ok=$((css_ok+1))
done
printf "     CSS (amostra)            %s/%s carregam\n" "$css_ok" "$css_tot"

echo ""
if [ "$all_ok" = "1" ] && [ "$css_ok" = "$css_tot" ]; then
  echo "PRONTO! Acesse pela VPN Tailscale:"
else
  echo "ATENCAO: algo ficou vermelho acima. Rode 'bash subir.sh' de novo ou veja os logs."
  echo "Enderecos:"
fi
echo "  POS ............. $URL_VPN/pos"
echo "  Cozinha (KOT) ... $URL_VPN/URYMosaic/Cozinha"
echo "  Admin (ERPNext) . $URL_VPN/app"
echo "  Login ........... Administrator / admin"
