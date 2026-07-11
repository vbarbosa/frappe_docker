"""
Seed completo do restaurante de teste URY — idempotente.

Cria: Branch + URY User(admin) + Room + Restaurant + Tables + Items + Menu +
POS Profile + POS Opening Entry, na ordem correta, evitando o "Access Denied".

Uso (dentro do frappe_docker):
    BACKEND=$(docker compose -f pwd.yml -f ury.override.yml ps -q backend | head -1)
    docker cp ury_seed_restaurant.py $BACKEND:/home/frappe/frappe-bench/apps/frappe/frappe/tmp_seed.py
    docker compose -f pwd.yml -f ury.override.yml exec -T backend \
        bench --site frontend execute frappe.tmp_seed.run

Ajuste as constantes abaixo conforme sua empresa (abbr muda os nomes de warehouse/cost center).
"""
import frappe
from frappe.utils import now_datetime, today

# Cardápio real da Dallago's Pizzeria (extraído da API pública deles). 133 itens.
# (código do item, preço R$, curso/categoria)
DALLAGO_MENU = [
    ("COMBO FAMÍLIA | 1 Pizza Grande + 1 Pizza Doce Broto + 1 Refri 2L", 139.7, "Combos"),
    ("COMBO NOITE PERFEITA | 1 Pizza Grande + 1 Refri 2L", 99.7, "Combos"),
    ("COMBO FESTA EM CASA | 3 Pizzas Grandes + 1 Pizza Doce Grande + 2 Refri 2L", 359.7, "Combos"),
    ("Borda Nostra", 38.7, "Entradas & Bordas"),
    ("Rotolinas", 43.7, "Entradas & Bordas"),
    ("Doce Grande 2 sabores", 84.7, "Pizzas Doces"),
    ("Doce Média 2 sabores", 74.7, "Pizzas Doces"),
    ("Coca-Cola 2L", 19.0, "Bebidas"),
    ("Coca-Cola Zero 2L", 19.0, "Bebidas"),
    ("Guaraná Antarctica 2L", 18.0, "Bebidas"),
    ("Coca-Cola 600mL", 10.5, "Bebidas"),
    ("Coca-Cola Zero 600mL", 10.5, "Bebidas"),
    ("Guaraná Antarctica 600mL", 10.0, "Bebidas"),
    ("Coca-Cola Lata 350mL", 8.0, "Bebidas"),
    ("Coca-Cola Zero Lata 350mL", 8.0, "Bebidas"),
    ("Guaraná Antarctica Lata 350mL", 8.0, "Bebidas"),
    ("Água sem gás 500mL", 6.0, "Bebidas"),
    ("Água com gás 500mL", 6.0, "Bebidas"),
    ("Pizza Burrata (G)", 128.7, "Pizzas Salgadas"),
    ("Pizza Burrata & Parma (G)", 128.7, "Pizzas Salgadas"),
    ("Pizza Atum (G)", 88.7, "Pizzas Salgadas"),
    ("Pizza Bacon & Brócolis (G)", 88.7, "Pizzas Salgadas"),
    ("Pizza Barreado (G)", 98.7, "Pizzas Salgadas"),
    ("Pizza Blumenau (G)", 93.7, "Pizzas Salgadas"),
    ("Pizza Calabresa (G)", 88.7, "Pizzas Salgadas"),
    ("Pizza Camarão (G)", 108.7, "Pizzas Salgadas"),
    ("Pizza Carbonara (G)", 93.7, "Pizzas Salgadas"),
    ("Pizza Carne-seca (G)", 93.7, "Pizzas Salgadas"),
    ("Pizza Carrettiera (G)", 106.7, "Pizzas Salgadas"),
    ("Pizza Costela Santa Massa (G)", 98.7, "Pizzas Salgadas"),
    ("Pizza Do Chef (G)", 98.7, "Pizzas Salgadas"),
    ("Pizza Dolce Diavola (G)", 88.7, "Pizzas Salgadas"),
    ("Pizza Frango Cremoso (G)", 88.7, "Pizzas Salgadas"),
    ("Pizza Lombo Barbecue (G)", 93.7, "Pizzas Salgadas"),
    ("Pizza Lombo Canadense (G)", 88.7, "Pizzas Salgadas"),
    ("Pizza Margherita al Filetto (G)", 98.7, "Pizzas Salgadas"),
    ("Pizza Margherita Verace (G)", 98.7, "Pizzas Salgadas"),
    ("Pizza Marguerita Paulistana (G)", 88.7, "Pizzas Salgadas"),
    ("Pizza Melanzana (G)", 88.7, "Pizzas Salgadas"),
    ("Pizza Palmito (G)", 88.7, "Pizzas Salgadas"),
    ("Pizza Pantaneira (G)", 98.7, "Pizzas Salgadas"),
    ("Pizza Parma (G)", 128.7, "Pizzas Salgadas"),
    ("Pizza Perugia (G)", 98.7, "Pizzas Salgadas"),
    ("Pizza Picanha Cremosa (G)", 98.7, "Pizzas Salgadas"),
    ("Pizza Portuguesa (G)", 88.7, "Pizzas Salgadas"),
    ("Pizza Quatro Queijos (G)", 88.7, "Pizzas Salgadas"),
    ("Pizza Tomate Seco & Rúcula (G)", 93.7, "Pizzas Salgadas"),
    ("Pizza Zucchine (G)", 88.7, "Pizzas Salgadas"),
    ("Pizza Burrata (M)", 118.7, "Pizzas Salgadas"),
    ("Pizza Burrata & Parma (M)", 118.7, "Pizzas Salgadas"),
    ("Pizza Atum (M)", 78.7, "Pizzas Salgadas"),
    ("Pizza Bacon & Brócolis (M)", 78.7, "Pizzas Salgadas"),
    ("Pizza Barreado (M)", 88.7, "Pizzas Salgadas"),
    ("Pizza Blumenau (M)", 83.7, "Pizzas Salgadas"),
    ("Pizza Calabresa (M)", 78.7, "Pizzas Salgadas"),
    ("Pizza Camarão (M)", 98.7, "Pizzas Salgadas"),
    ("Pizza Carbonara (M)", 83.7, "Pizzas Salgadas"),
    ("Pizza Carne-seca (M)", 83.7, "Pizzas Salgadas"),
    ("Pizza Carrettiera (M)", 96.7, "Pizzas Salgadas"),
    ("Pizza Costela Santa Massa (M)", 88.7, "Pizzas Salgadas"),
    ("Pizza Do Chef (M)", 88.7, "Pizzas Salgadas"),
    ("Pizza Dolce Diavola (M)", 78.7, "Pizzas Salgadas"),
    ("Pizza Frango Cremoso (M)", 78.7, "Pizzas Salgadas"),
    ("Pizza Lombo Barbecue (M)", 83.7, "Pizzas Salgadas"),
    ("Pizza Lombo Canadense (M)", 78.7, "Pizzas Salgadas"),
    ("Pizza Margherita Verace (M)", 88.7, "Pizzas Salgadas"),
    ("Pizza Margherita al Filetto (M)", 88.7, "Pizzas Salgadas"),
    ("Pizza Marguerita Paulistana (M)", 78.7, "Pizzas Salgadas"),
    ("Pizza Melanzana (M)", 78.7, "Pizzas Salgadas"),
    ("Pizza Palmito (M)", 78.7, "Pizzas Salgadas"),
    ("Pizza Pantaneira (M)", 88.7, "Pizzas Salgadas"),
    ("Pizza Parma (M)", 118.7, "Pizzas Salgadas"),
    ("Pizza Perugia (M)", 88.7, "Pizzas Salgadas"),
    ("Pizza Picanha Cremosa (M)", 88.7, "Pizzas Salgadas"),
    ("Pizza Portuguesa (M)", 78.7, "Pizzas Salgadas"),
    ("Pizza Quatro Queijos (M)", 78.7, "Pizzas Salgadas"),
    ("Pizza Tomate Seco & Rúcula (M)", 83.7, "Pizzas Salgadas"),
    ("Pizza Zucchine (M)", 78.7, "Pizzas Salgadas"),
    ("Pizza Burrata (Broto)", 92.7, "Pizzas Salgadas"),
    ("Pizza Burrata & Parma (Broto)", 92.7, "Pizzas Salgadas"),
    ("Pizza Atum (Broto)", 52.7, "Pizzas Salgadas"),
    ("Pizza Bacon & Brócolis (Broto)", 52.7, "Pizzas Salgadas"),
    ("Pizza Barreado (Broto)", 61.7, "Pizzas Salgadas"),
    ("Pizza Blumenau (Broto)", 56.7, "Pizzas Salgadas"),
    ("Pizza Calabresa (Broto)", 52.7, "Pizzas Salgadas"),
    ("Pizza Camarão (Broto)", 67.7, "Pizzas Salgadas"),
    ("Pizza Carbonara (Broto)", 61.7, "Pizzas Salgadas"),
    ("Pizza Carne-seca (Broto)", 56.7, "Pizzas Salgadas"),
    ("Pizza Carrettiera (Broto)", 61.7, "Pizzas Salgadas"),
    ("Pizza Costela Santa Massa (Broto)", 61.7, "Pizzas Salgadas"),
    ("Pizza Do Chef (Broto)", 61.7, "Pizzas Salgadas"),
    ("Pizza Dolce Diavola (Broto)", 52.7, "Pizzas Salgadas"),
    ("Pizza Frango Cremoso (Broto)", 52.7, "Pizzas Salgadas"),
    ("Pizza Lombo Barbecue (Broto)", 61.7, "Pizzas Salgadas"),
    ("Pizza Lombo Canadense (Broto)", 52.7, "Pizzas Salgadas"),
    ("Pizza Margherita al Filetto (Broto)", 56.7, "Pizzas Salgadas"),
    ("Pizza Margherita Verace (Broto)", 56.7, "Pizzas Salgadas"),
    ("Pizza Marguerita Paulistana (Broto)", 52.7, "Pizzas Salgadas"),
    ("Pizza Melanzana (Broto)", 52.7, "Pizzas Salgadas"),
    ("Pizza Palmito (Broto)", 52.7, "Pizzas Salgadas"),
    ("Pizza Pantaneira (Broto)", 61.7, "Pizzas Salgadas"),
    ("Pizza Parma (Broto)", 91.7, "Pizzas Salgadas"),
    ("Pizza Perugia (Broto)", 61.7, "Pizzas Salgadas"),
    ("Pizza Picanha Cremosa (Broto)", 61.7, "Pizzas Salgadas"),
    ("Pizza Portuguesa (Broto)", 52.7, "Pizzas Salgadas"),
    ("Pizza Quatro Queijos (Broto)", 52.7, "Pizzas Salgadas"),
    ("Pizza Tomate Seco & Rúcula (Broto)", 56.7, "Pizzas Salgadas"),
    ("Pizza Zucchine (Broto)", 52.7, "Pizzas Salgadas"),
    ("Pizza Doce Abacachoffe (G)", 98.7, "Pizzas Doces"),
    ("Pizza Doce Avelã & Morangos (G)", 99.9, "Pizzas Doces"),
    ("Pizza Doce Banana & Canela (G)", 84.7, "Pizzas Doces"),
    ("Pizza Doce Chocolate Branco & Nozes (G)", 84.7, "Pizzas Doces"),
    ("Pizza Doce Pistache (G)", 109.7, "Pizzas Doces"),
    ("Pizza Doce Abacachoffe (M)", 79.7, "Pizzas Doces"),
    ("Pizza Doce Avelã & Morangos (M)", 89.9, "Pizzas Doces"),
    ("Pizza Doce Banana & Canela (M)", 74.7, "Pizzas Doces"),
    ("Pizza Doce Chocolate Branco & Nozes (M)", 74.7, "Pizzas Doces"),
    ("Pizza Doce Pistache (M)", 96.7, "Pizzas Doces"),
    ("Pizza Doce Abacachoffe (Broto)", 55.7, "Pizzas Doces"),
    ("Pizza Doce Avelã & Morangos (Broto)", 58.7, "Pizzas Doces"),
    ("Pizza Doce Banana & Canela (Broto)", 48.7, "Pizzas Doces"),
    ("Pizza Doce Chocolate Branco & Nozes (Broto)", 48.7, "Pizzas Doces"),
    ("Pizza Doce Pistache (Broto)", 61.7, "Pizzas Doces"),
    ("Borda Nostra com molho pomodoro e creme de queijos", 38.7, "Entradas & Bordas"),
    ("Molho pomodoro", 10.7, "Entradas & Bordas"),
    ("Creme de queijos", 10.7, "Entradas & Bordas"),
    ("Rotolina Calabresa", 43.7, "Entradas & Bordas"),
    ("Rotolina Santa Massa", 43.7, "Entradas & Bordas"),
    ("Adicional Pistache", 17.0, "Adicionais Doce"),
    ("Adicional Avelã", 8.5, "Adicionais Doce"),
    ("Adicional Choco Branco", 10.5, "Adicionais Doce"),
    ("Adicional Morango", 9.0, "Adicionais Doce"),
    ("Adicional Nozes", 12.0, "Adicionais Doce"),
]

COMPANY = "Demo Food"
ABBR = "DF"
USER = "Administrator"
BRANCH = "Main Branch"
ROOM = "Salao Principal"
RESTAURANT = "Demo Food Pizzaria"
MENU = "Cardapio Pizzaria"
PROFILE = "Demo Food POS"
BILLING_ROLE = "URY Manager"

WAREHOUSE = f"Stores - {ABBR}"
COST_CENTER = f"Main - {ABBR}"
WRITE_OFF = f"Write Off - {ABBR}"

# Cardápio de pizzaria (baseado no cardápio real da Dallago's Pizzeria).
# (código do item, preço R$, curso/categoria) — 133 itens agrupados por curso.
ITEMS = DALLAGO_MENU  # definido no fim do arquivo


def _f(dt):
    return [f.fieldname for f in frappe.get_meta(dt).fields]


def run():
    log = []

    # roles URY no usuario
    u = frappe.get_doc("User", USER)
    have = {r.role for r in u.roles}
    for r in ["URY Manager", "URY Captain", "URY Cashier"]:
        if r not in have:
            u.append("roles", {"role": r})
    u.save(ignore_permissions=True)

    # 1. Branch (child user obrigatoria no insert)
    if not frappe.db.exists("Branch", BRANCH):
        b = frappe.new_doc("Branch")
        b.branch = BRANCH
        b.append("user", {"user": USER})
        b.insert(ignore_permissions=True)
        log.append("Branch")

    # 2. Room (autoname Prompt)
    if not frappe.db.exists("URY Room", ROOM):
        r = frappe.new_doc("URY Room")
        r.branch = BRANCH
        if "room_type" in _f("URY Room"):
            r.room_type = "AC"
        r.name = ROOM
        r.insert(ignore_permissions=True)
        log.append("Room")

    # 3. room -> Administrator
    if "room" in _f("URY User"):
        bdoc = frappe.get_doc("Branch", BRANCH)
        ch = False
        for row in bdoc.get("user", []):
            if row.user == USER and not row.get("room"):
                row.room = ROOM
                ch = True
        if ch:
            bdoc.save(ignore_permissions=True)

    # 5b. URY Menu Course (categorias do cardápio)
    courses = []
    seen_c = set()
    for _, _, course in ITEMS:
        if course not in seen_c:
            seen_c.add(course)
            courses.append(course)
    for course in courses:
        if not frappe.db.exists("URY Menu Course", course):
            c = frappe.new_doc("URY Menu Course")
            c.course = course
            c.name = course
            c.insert(ignore_permissions=True)
    log.append("Courses=%d" % len(courses))

    # 6. Items (antes do menu)
    ig = "Products" if frappe.db.exists("Item Group", "Products") else frappe.db.get_value("Item Group", {"is_group": 0}, "name")
    uom = "Nos" if frappe.db.exists("UOM", "Nos") else frappe.db.get_value("UOM", {}, "name")
    n_items = 0
    for code, rate, course in ITEMS:
        if not frappe.db.exists("Item", code):
            it = frappe.new_doc("Item")
            it.item_code = code
            it.item_name = code
            it.item_group = ig
            it.stock_uom = uom
            it.is_stock_item = 0
            it.standard_rate = rate
            it.insert(ignore_permissions=True)
            n_items += 1
    log.append("Items+%d" % n_items)

    # 7. Menu (gera Price List/Item Price no on_update)
    mi_fields = _f("URY Menu Item")
    if not frappe.db.exists("URY Menu", MENU):
        m = frappe.new_doc("URY Menu")
        m.name = MENU
        m.branch = BRANCH
        if "enabled" in _f("URY Menu"):
            m.enabled = 1
        for code, rate, course in ITEMS:
            row = {"item": code, "rate": rate}
            if "course" in mi_fields:
                row["course"] = course
            m.append("items", row)
        m.insert(ignore_permissions=True)
        m.save(ignore_permissions=True)
        log.append("Menu(%d itens)" % len(ITEMS))

    # 4. Restaurant (+ active_menu)
    if not frappe.db.exists("URY Restaurant", RESTAURANT):
        rest = frappe.new_doc("URY Restaurant")
        rest.company = COMPANY
        rest.invoice_series_prefix = "DFR-"
        rest.branch = BRANCH
        rest.default_room = ROOM
        rest.name = RESTAURANT
        rest.insert(ignore_permissions=True)
        log.append("Restaurant")
    rest = frappe.get_doc("URY Restaurant", RESTAURANT)
    if "active_menu" in _f("URY Restaurant") and not rest.active_menu:
        rest.active_menu = MENU
        rest.save(ignore_permissions=True)

    # 5. Tables
    for tname in ["Mesa 1", "Mesa 2", "Mesa 3", "Mesa 4"]:
        if not frappe.db.exists("URY Table", tname):
            t = frappe.new_doc("URY Table")
            t.restaurant = RESTAURANT
            t.restaurant_room = ROOM
            t.branch = BRANCH
            if "no_of_seats" in _f("URY Table"):
                t.no_of_seats = 4
            if "table_shape" in _f("URY Table"):
                t.table_shape = "Square"
            t.name = tname
            t.insert(ignore_permissions=True)

    # 8. POS Profile
    if not frappe.db.exists("POS Profile", PROFILE):
        pf_fields = _f("POS Profile")
        p = frappe.new_doc("POS Profile")
        if "profile_name" in pf_fields:
            p.profile_name = PROFILE
        else:
            p.name = PROFILE
        p.company = COMPANY
        p.warehouse = WAREHOUSE
        p.cost_center = COST_CENTER
        p.write_off_account = WRITE_OFF
        p.write_off_cost_center = COST_CENTER
        p.write_off_limit = 1
        p.currency = frappe.db.get_value("Company", COMPANY, "default_currency")
        if "restaurant" in pf_fields:
            p.restaurant = RESTAURANT
        if "branch" in pf_fields:
            p.branch = BRANCH
        if "custom_enable_multiple_cashier" in pf_fields:
            p.custom_enable_multiple_cashier = 0
        if "qz_print" in pf_fields:
            p.qz_print = 1
        p.append("payments", {"mode_of_payment": "Cash", "default": 1})
        p.append("applicable_for_users", {"user": USER})
        if "role_allowed_for_billing" in pf_fields:
            p.append("role_allowed_for_billing", {"role": BILLING_ROLE})
        p.insert(ignore_permissions=True)
        log.append("POS Profile")

    # 9. POS Opening Entry (submit)
    existing = frappe.get_all("POS Opening Entry",
                              filters={"status": "Open", "docstatus": 1, "pos_profile": PROFILE},
                              pluck="name")
    if not existing:
        oe = frappe.new_doc("POS Opening Entry")
        oe.posting_date = today()
        oe.period_start_date = now_datetime()
        oe.company = COMPANY
        oe.pos_profile = PROFILE
        oe.user = USER
        of = _f("POS Opening Entry")
        if "restaurant" in of:
            oe.restaurant = RESTAURANT
        if "branch" in of:
            oe.branch = BRANCH
        for pay in frappe.get_doc("POS Profile", PROFILE).get("payments", []):
            oe.append("balance_details", {"mode_of_payment": pay.mode_of_payment, "opening_amount": 0})
        oe.insert(ignore_permissions=True)
        oe.submit()
        log.append("POS Opening")

    frappe.db.commit()

    # verificacao
    frappe.set_user(USER)
    from ury.ury_pos import api
    check = "branch=%s profile=%s posOpening=%s" % (
        api.getBranch(), api.getPosProfile().get("pos_profile"), api.posOpening())
    return "SEED OK [%s] | VERIFY: %s" % (", ".join(log) or "nada novo", check)
