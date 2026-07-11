# URY — Customizações do POS e notas de operação

Complementa o `URY_DOCKER_SETUP.md`. Documenta comportamentos do POS/KOT que causam
confusão e as customizações aplicadas no fork `vbarbosa/ury`.

---

## 1. Cliente padrão pré-selecionado (evita pedir cliente a cada pedido)

### O problema
Por padrão, o URY **exige um cliente em todo pedido** (herança do ERPNext — toda
POS Invoice precisa de um Customer). No POS React:
- `OrderPanel.tsx` bloqueia o lançamento se `!selectedCustomer` → toast "Selecione um cliente".
- O estado inicia `selectedCustomer: null` (`pos-store.ts`) e **nunca** era pré-preenchido.
- Ao **reabrir uma mesa que já tem pedido**, o cliente salvo É restaurado (`loadTableOrder`,
  campo `order.customer`). O incômodo era só na **mesa vazia / primeiro item**.

### A solução (commit `feat(pos): pre-select POS Profile default customer`)
1. **Backend** (`ury/ury_pos/api.py`, `getPosProfile`): passou a retornar
   `"default_customer": pos_profiles.customer` (o campo `customer` padrão do POS Profile).
2. **Frontend** (`pos/src/lib/pos-profile-api.ts`): `default_customer` propagado nas
   interfaces `PosProfileLimited` e `PosProfileCombined` e no merge.
3. **Frontend** (`pos/src/store/pos-store.ts`):
   - helper `getDefaultCustomer()` monta um `Customer` a partir de `posProfile.default_customer`;
   - `fetchPosProfile` pré-seleciona o cliente ao carregar o profile (se nenhum escolhido);
   - `loadTableOrder` (mesa vazia + erro), `clearTableOrder` e `resetOrderState` usam
     `getDefaultCustomer()` em vez de `null`.
   - Uma mesa já aberta continua restaurando **seu próprio** cliente salvo (inalterado).

### Como ativar num ambiente
Basta definir o campo **`customer`** do POS Profile como um cliente genérico
(ex.: **"Consumidor Final"**). A seed já faz isso automaticamente:
- cria o Customer `Consumidor Final`;
- seta `POS Profile.customer = "Consumidor Final"`.

Manualmente: Desk → POS Profile → campo *Customer* → escolher o cliente genérico → salvar.
Depois rebuildar o POS (ou já estar usando a imagem com o fork atualizado) e limpar o cache.

---

## 2. Tela da cozinha (URYMosaic) — por que fica vazia

### A URL precisa da produção no fim
O Mosaic lê a **unidade de produção do último segmento da URL** (`kot.vue`:
`production = url.split('/').pop()`), e só mostra KOTs com `kot.production === production`.

- ❌ `/URYMosaic` → produção vazia → nada aparece
- ✅ `/URYMosaic/Cozinha` → mostra os KOTs da produção "Cozinha"

### Pré-requisitos para um KOT existir
1. Uma **URY Production Unit** ligada à branch, com `item_groups` cobrindo o item_group
   dos itens do cardápio (a seed usa o grupo `Products`). Sem Production Unit, **nenhum KOT
   é gerado** e o Mosaic fica sempre vazio. A seed cria a Production Unit **"Cozinha"**.
2. Um **pedido** lançado no POS cujos itens pertençam a esse item_group.
3. O KOT é gerado pela tarefa agendada `kotValidationThread` (cron, a cada minuto) — que só
   processa invoices criadas **entre 1 e 5 minutos atrás** (janela de tempo). Para gerar na
   hora em testes, chamar `create_kot` diretamente (ver `scratchpad/ury_force_kot.py`).
4. O KOT precisa de `order_status = "Ready For Prepare"` e `docstatus = 1` para aparecer
   (`ury_kot_display.kot_list`).

---

## 3. ⚠️ Bug encontrado no URY (candidato a PR)

`ury/ury/api/ury_kot_validation.py` → `get_productions_for_branch()` faz:
```python
frappe.get_all("URY Production Unit", filters={"branch": branch}, fields=["name", "item_groups"])
```
Mas **`item_groups` é uma child table**, não uma coluna → `OperationalError (1054)
Unknown column 'item_groups' in 'SELECT'`. Isso quebra a geração automática de KOT.

**Correção sugerida:** buscar só `["name"]` e ler `item_groups` via `frappe.get_doc(...).item_groups`.
Também há divergência de nome de campo entre v15/v16: `kot_naming_series` vs
`custom_kot_naming_series` no POS Profile.

---

## 4. Referência rápida — criar pedido de teste + KOT via CLI

Scripts em `scratchpad/` (padrão: escrever `tmp_X.py` em apps/frappe/frappe/, `docker cp`,
`bench --site frontend execute frappe.tmp_X.run`, limpar depois):
- `ury_test_order.py` — cria um pedido (sync_order) numa mesa. **Atenção:** o payload de item
  usa a chave `item` (não `item_code`) — é o que `sync_order` lê.
- `ury_production_unit.py` — cria a Production Unit "Cozinha".
- `ury_force_kot.py` — gera o KOT do pedido pendente (contorna a janela de tempo e o bug acima).

Verificação de que o Mosaic verá o KOT:
```python
from ury.ury.api.ury_kot_display import kot_list
kot_list()  # deve retornar {'KOT': N, 'Branch': 'Main Branch', ...} com N>0
```
