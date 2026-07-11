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

COMPANY = "Demo Food"
ABBR = "DF"
USER = "Administrator"
BRANCH = "Main Branch"
ROOM = "Salao Principal"
RESTAURANT = "Demo Food Restaurant"
MENU = "Cardapio Principal"
PROFILE = "Demo Food POS"
BILLING_ROLE = "URY Manager"

WAREHOUSE = f"Stores - {ABBR}"
COST_CENTER = f"Main - {ABBR}"
WRITE_OFF = f"Write Off - {ABBR}"

ITEMS = [("Hamburguer", 25.0), ("Pizza Margherita", 45.0), ("Refrigerante", 8.0), ("Batata Frita", 15.0)]


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

    # 6. Items (antes do menu)
    ig = "Products" if frappe.db.exists("Item Group", "Products") else frappe.db.get_value("Item Group", {"is_group": 0}, "name")
    uom = "Nos" if frappe.db.exists("UOM", "Nos") else frappe.db.get_value("UOM", {}, "name")
    for code, rate in ITEMS:
        if not frappe.db.exists("Item", code):
            it = frappe.new_doc("Item")
            it.item_code = code
            it.item_name = code
            it.item_group = ig
            it.stock_uom = uom
            it.is_stock_item = 0
            it.standard_rate = rate
            it.insert(ignore_permissions=True)

    # 7. Menu (gera Price List/Item Price no on_update)
    if not frappe.db.exists("URY Menu", MENU):
        m = frappe.new_doc("URY Menu")
        m.name = MENU
        m.branch = BRANCH
        if "enabled" in _f("URY Menu"):
            m.enabled = 1
        for code, rate in ITEMS:
            m.append("items", {"item": code, "rate": rate})
        m.insert(ignore_permissions=True)
        m.save(ignore_permissions=True)
        log.append("Menu")

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
