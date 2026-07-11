# URY + ERPNext no Docker — Guia de Setup do Zero (sem erros)

Guia reproduzível para subir o **URY** (sistema de restaurante/POS Frappe) com ERPNext,
HRMS e o POS React funcionando de ponta a ponta. Escrito a partir de um setup real
que teve vários erros — cada armadilha está documentada abaixo para não repetir.

**Ambiente de referência:** servidor `oracle-manchete` (Oracle Linux/Ubuntu VM),
Docker 29+, acesso via Tailscale. App URY do fork `github.com/vbarbosa/ury` (branch `develop`).

---

## 0. Decisões-chave (aprendidas na marra)

| Decisão | Por quê |
|---|---|
| **Usar imagem customizada v15, NÃO o pwd.yml v16 puro** | O URY é feito pra ERPNext **v15**. E, com o `pwd.yml` padrão, o app custom é instalado só no container `backend` — o `frontend` (nginx) fica sem os assets do URY → **tela branca no /pos e layout quebrado no /app**. Build de imagem única resolve: todos os containers usam a MESMA imagem, assets sempre consistentes. |
| **Passar apps.json como `--secret`, não `--build-arg`** | O `images/custom/Containerfile` lê via `--mount=type=secret,id=apps_json`. Passar como `APPS_JSON_BASE64` (build-arg) é **silenciosamente ignorado** → imagem sai só com frappe. |
| **`down -v` com AMBOS os `-f`** | `docker compose -f pwd.yml down -v` NÃO remove os volumes do override. Use `-f pwd.yml -f ury.override.yml down -v`, senão o site velho persiste e o `create-site` pula a criação ("Site already exists"). |
| **Completar setup wizard via CLI** | O wizard web dá "Requisição Inválida" mesmo preenchido. Completar via `setup_complete()` é confiável. |
| **Criar todo o setup do restaurante via script Python** | O POS tem uma cadeia de pré-requisitos (branch↔user, POS Profile, role de billing, caixa aberto) que dá "Access Denied" se faltar qualquer um. Script evita tentativa-e-erro. |

---

## 1. Pré-requisitos do host

- Docker + Docker Compose v2
- `git`, acesso ao GitHub (o URY vem do fork `vbarbosa/ury`)
- Acesso à rede: aqui é via **Tailscale** (IP `100.70.92.116`)

---

## 2. Clonar frappe_docker e preparar apps.json

```bash
cd /home/ubuntu/GitHub
git clone --depth 1 https://github.com/frappe/frappe_docker.git
cd frappe_docker

cat > apps.json <<'EOF'
[
  { "url": "https://github.com/frappe/erpnext", "branch": "version-15" },
  { "url": "https://github.com/frappe/hrms",    "branch": "version-15" },
  { "url": "https://github.com/vbarbosa/ury",   "branch": "develop"    }
]
EOF
```

> HRMS é dependência do URY (relatórios de funcionários). Sempre inclua.

---

## 3. Build da imagem customizada v15

```bash
docker build \
  --secret id=apps_json,src=apps.json \
  --build-arg=FRAPPE_PATH=https://github.com/frappe/frappe \
  --build-arg=FRAPPE_BRANCH=version-15 \
  --tag=ury-erp:v15 \
  --file=images/custom/Containerfile .
```

**Validar que os 4 apps entraram** (crítico — não pule):
```bash
docker run --rm --entrypoint ls ury-erp:v15 -1 /home/frappe/frappe-bench/apps/
# Esperado: erpnext  frappe  hrms  ury
```
Se aparecer só `frappe`, o apps.json não foi lido → confira que usou `--secret` (não build-arg).

---

## 4. Configurar rede (Tailscale) e override

`.env` na raiz do frappe_docker:
```bash
echo "TS_IP=100.70.92.116" > .env
```
(troque pelo IP Tailscale do seu servidor: `tailscale ip -4` ou `ip addr show tailscale0`)

`ury.override.yml` — troca a imagem em todos os serviços, instala os 3 apps no site,
e publica a porta em localhost + Tailscale:
```yaml
services:
  backend:      { image: ury-erp:v15 }
  configurator: { image: ury-erp:v15 }
  create-site:
    image: ury-erp:v15
    command:
      - >
        wait-for-it -t 120 db:3306;
        wait-for-it -t 120 redis-cache:6379;
        wait-for-it -t 120 redis-queue:6379;
        export start=`date +%s`;
        until [[ -n `grep -hs ^ sites/common_site_config.json | jq -r ".db_host // empty"` ]] && \
          [[ -n `grep -hs ^ sites/common_site_config.json | jq -r ".redis_cache // empty"` ]] && \
          [[ -n `grep -hs ^ sites/common_site_config.json | jq -r ".redis_queue // empty"` ]];
        do echo "Waiting for common_site_config.json"; sleep 5;
          if (( `date +%s`-start > 120 )); then echo "timeout"; exit 1; fi; done;
        bench new-site --mariadb-user-host-login-scope='%' --admin-password=admin \
          --db-root-username=root --db-root-password=admin \
          --install-app erpnext --install-app hrms --install-app ury --set-default frontend;
  frontend:
    image: ury-erp:v15
    ports:
      - "127.0.0.1:8080:8080"   # localhost dentro da VM
      - "${TS_IP}:8080:8080"    # acesso via Tailscale
  queue-long:   { image: ury-erp:v15 }
  queue-short:  { image: ury-erp:v15 }
  scheduler:    { image: ury-erp:v15 }
  websocket:    { image: ury-erp:v15 }
```

---

## 5. Subir a stack

```bash
export TS_IP=100.70.92.116
docker compose -f pwd.yml -f ury.override.yml up -d
```

Acompanhar a criação do site (leva ~3-5 min):
```bash
docker compose -f pwd.yml -f ury.override.yml logs -f create-site
# esperar por: "Current Site set to frontend" e "Updating Dashboard for ury"
```

Validar apps no site:
```bash
docker compose -f pwd.yml -f ury.override.yml exec -T backend bench --site frontend list-apps
# frappe 15.x / erpnext 15.x / hrms 15.x / ury 0.2.1
```

**Acesso:** `http://localhost:8080` (dentro da VM) ou `http://100.70.92.116:8080` (Tailscale).
Login: `Administrator` / `admin`.

---

## 6. Completar o setup wizard via CLI (evita "Requisição Inválida")

O padrão para rodar Python no contexto do Frappe **sem** os problemas do console interativo:
escreva um módulo em `apps/frappe/frappe/tmp_X.py` com uma função `run()` e chame com
`bench --site frontend execute frappe.tmp_X.run`. (Copie o arquivo com `docker cp`.)

```python
# tmp_setup.py
import frappe
def run():
    from frappe.desk.page.setup_wizard.setup_wizard import setup_complete
    setup_complete({
        "language": "English", "country": "Brazil", "currency": "BRL",
        "timezone": "America/Sao_Paulo",
        "company_name": "Demo Food", "company_abbr": "DF",
        "chart_of_accounts": "Standard",
        "fy_start_date": "2026-01-01", "fy_end_date": "2026-12-31",
        "setup_demo": 0,
        "full_name": "Vinicius Barbosa Maria", "email": "vbarbosa.maria@gmail.com",
    })
    frappe.db.commit()
    return "OK complete=%s" % frappe.db.get_single_value("System Settings","setup_complete")
```
Idioma pt-BR (opcional): `bench --site frontend set-config lang pt-BR`.

---

## 7. Roles do URY para o usuário

O POS exige que o usuário tenha role do URY. Existem: **URY Manager, URY Captain, URY Cashier**.
```python
u = frappe.get_doc("User", "Administrator")
for r in ["URY Manager","URY Captain","URY Cashier"]:
    u.append("roles", {"role": r})
u.save(ignore_permissions=True); frappe.db.commit()
```

---

## 8. Setup do restaurante (a cadeia que causa "Access Denied")

O POS React (`/pos`) faz, ao abrir: `getBranch` → `getPosProfile` → `posOpening`.
Se qualquer um lançar exceção, a tela mostra **"Access Denied"**. Ordem obrigatória:

1. **Branch** (`Main Branch`) — a child table `user` (URY User) é **obrigatória no insert**.
   Inclua o Administrator já na criação: `b.append("user", {"user":"Administrator"})`.
2. **URY Room** (`Salao Principal`) — `autoname=Prompt` → passe `doc.name`. Obrigatório: `branch`.
   NÃO tem campo "room"; só `branch`, `room_type` (AC/NON-AC), `printer_settings`.
3. **Vincular room** ao Administrator na linha URY User da Branch (`u.room = "Salao Principal"`).
4. **URY Restaurant** (`autoname=prompt`) — obrigatórios: `company`, `invoice_series_prefix`,
   `branch`, `default_room`. E setar `active_menu` (senão getRestaurantMenu dá throw).
5. **URY Table** (`autoname=prompt`) — obrigatórios: `restaurant`, `restaurant_room`, `branch`.
6. **Itens** ERPNext (Item) — `is_stock_item=0` pra não exigir estoque.
7. **URY Menu** (obrig.: `branch`, `items[]`) — ao salvar, gera Price List + Item Price
   automaticamente. Ligar em `URY Restaurant.active_menu`.
8. **POS Profile** — obrigatórios ERPNext: `company`, `warehouse`, `cost_center` (hook
   do URY dá throw se vazio!), `currency`, `write_off_account`, `write_off_cost_center`,
   `write_off_limit`, `payments[]`. E:
   - `applicable_for_users` com ≥1 user (senão `getPosProfile` dá IndexError → Access Denied)
   - **`role_allowed_for_billing` com ≥1 role que o usuário tenha** (senão `hasAccess=false`,
     bloqueia ATÉ o Administrator)
   - `custom_enable_multiple_cashier = 0` (modo simples)
   - `qz_print = 1` (evita exigir impressora física)
   - custom: `restaurant`, `branch`
9. **POS Opening Entry** — criar e **submeter** (`docstatus=1`, `status=Open`). Obrigatórios:
   `posting_date`, `period_start_date`, `company`, `pos_profile`, `user`, `balance_details[]`
   (opening_amount pode ser 0), + custom `restaurant`, `branch`. Sem ela → POS não opera.

> Os scripts completos deste setup estão salvos em `scratchpad/ury_*.py` da sessão.

### Verificação final (deve responder sem erro)
```python
import frappe
def run():
    frappe.set_user("Administrator")
    from ury.ury_pos import api
    return "branch=%s profile=%s posOpening=%s" % (
        api.getBranch(), api.getPosProfile().get("pos_profile"), api.posOpening())
# Esperado: branch=Main Branch | profile=Demo Food POS | posOpening=0  (0 = caixa aberto)
```

---

## 9. Operação diária

```bash
export TS_IP=100.70.92.116
cd /home/ubuntu/GitHub/frappe_docker

# subir / derrubar
docker compose -f pwd.yml -f ury.override.yml up -d
docker compose -f pwd.yml -f ury.override.yml down          # mantém dados
docker compose -f pwd.yml -f ury.override.yml down -v        # APAGA tudo (recomeçar do zero)

# status / logs
docker compose -f pwd.yml -f ury.override.yml ps
docker compose -f pwd.yml -f ury.override.yml logs -f backend

# bench no site
docker compose -f pwd.yml -f ury.override.yml exec backend bench --site frontend <cmd>
```

**Rebuild da imagem** (após atualizar o código do URY no fork):
```bash
docker build --secret id=apps_json,src=apps.json \
  --build-arg=FRAPPE_BRANCH=version-15 --build-arg=CACHE_BUST=$(date +%s) \
  --tag=ury-erp:v15 --file=images/custom/Containerfile .
docker compose -f pwd.yml -f ury.override.yml up -d --force-recreate
```

---

## 10. Troubleshooting rápido

| Sintoma | Causa | Correção |
|---|---|---|
| `/pos` **tela branca** | assets do URY não servidos | usar imagem única v15 (não pwd.yml v16) |
| `/app` **layout quebrado** | idem (CSS 404, hashes divergentes) | idem |
| **"Access Denied"** no /pos | falta POS Profile / role de billing / caixa | completar seção 8 |
| **"User is not Associated with any Branch"** | Administrator não está em `Branch.user` | seção 8 passo 1+3 |
| **"Requisição Inválida"** no wizard | bug do wizard web | completar via CLI (seção 6) |
| `localhost:8080` recusa | porta presa no IP Tailscale | bind duplo (seção 4) ou usar o IP Tailscale |
| `create-site`: "Site already exists" | volume velho persistiu | `down -v` com AMBOS os `-f` |
| imagem só com `frappe` | apps.json ignorado | usar `--secret`, não `--build-arg` |
| página "feia"/sem CSS, HTML pede hashes que dão 404 | rodou `bench build` DENTRO do container → grava mapa de assets novo no Redis, mas os arquivos servidos são os da imagem | **nunca rode `bench build` em runtime** (assets só via rebuild da imagem). Corrigir: `docker compose ... exec redis-cache redis-cli FLUSHALL` |
| 502 após restart do backend | nginx do frontend cacheia o IP antigo do backend | `docker compose ... restart frontend` |

---

## Credenciais / dados de teste

Guardados **fora do repo** em `~/.ury-secrets/credentials.md` (nunca commitar).
Resumo: Administrator/admin · empresa Demo Food (DF) · site `frontend` · pt-BR/BRL/Brazil.
