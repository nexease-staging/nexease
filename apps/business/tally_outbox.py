"""NexEase → Tally: turn new or changed NexEase records into Tally import jobs.

Runs inside a connector poll once Tally → NexEase is caught up. For each kind the user has switched
on, records changed since that kind's cursor (never earlier than the "push from" date, which defaults
to the day Tally was connected, so old history is not copied into Tally unless asked) are converted:

  customers / suppliers → ledgers under Sundry Debtors / Sundry Creditors
  products              → unit + stock item (HSN, GST rate, price)
  invoices              → Sales            vendor bills       → Purchase
  customer payments     → Receipt          supplier payments  → Payment
  credit notes          → Credit Note      vendor debit notes → Debit Note
  sales / purchase orders → Sales Order / Purchase Order
  expenses              → Payment (expense ledger by category)
  manual journals       → Journal

Each voucher has REMOTEID "NX-<kind>-<id>", so later edits alter the same Tally voucher and a
cancellation cancels it. A record whose Tally ledgers are not mapped yet is held as "blocked" with
the reason, and retried automatically once the mapping is saved.
"""
from datetime import date, datetime, timedelta
from decimal import Decimal

from . import tally_xml as tx
from .tally_masters import _org, gst_rate_of, party_payload, product_payload
from .tally_sync import db, enqueue, fingerprint, link, set_link, settings

IST = timedelta(hours=5, minutes=30)
CENT = Decimal("0.01")
D0 = Decimal(0)
BATCH = 40
MAX_QUEUED = 25
STATE_NAMES = {"01": "Jammu and Kashmir", "02": "Himachal Pradesh", "03": "Punjab", "04": "Chandigarh", "05": "Uttarakhand", "06": "Haryana", "07": "Delhi",
               "08": "Rajasthan", "09": "Uttar Pradesh", "10": "Bihar", "11": "Sikkim", "12": "Arunachal Pradesh", "13": "Nagaland", "14": "Manipur",
               "15": "Mizoram", "16": "Tripura", "17": "Meghalaya", "18": "Assam", "19": "West Bengal", "20": "Jharkhand", "21": "Odisha", "22": "Chhattisgarh",
               "23": "Madhya Pradesh", "24": "Gujarat", "25": "Daman and Diu", "26": "Dadra and Nagar Haveli and Daman and Diu", "27": "Maharashtra",
               "29": "Karnataka", "30": "Goa", "31": "Lakshadweep", "32": "Kerala", "33": "Tamil Nadu", "34": "Puducherry", "35": "Andaman and Nicobar Islands",
               "36": "Telangana", "37": "Andhra Pradesh", "38": "Ladakh", "97": "Other Territory"}
CODES = {v.lower(): k for k, v in STATE_NAMES.items()}


class Blocked(Exception):
    """The record cannot go to Tally yet (missing mapping, unknown ledger…)."""


def money(v):
    return Decimal(str(v or 0)).quantize(CENT)


def day(value):
    if value is None:
        return date.today().isoformat()
    if isinstance(value, datetime):
        return (value + IST).date().isoformat()
    return value.isoformat()


def state_code(value):
    value = (value or "").strip()
    if len(value) == 2 and value.isdigit():
        return value
    return CODES.get(value.lower(), "")


class Context:
    """Everything a build needs: settings, mapping and what exists in Tally right now."""

    def __init__(self, org_id, company):
        self.org_id = org_id
        self.org = _org(org_id)
        self.company = company["name"]
        self.company_state = state_code(company.get("state", "")) or (company.get("gstin") or "")[:2]
        self.s = settings(org_id)
        self.map = self.s["mapping"]
        objs = db().tally_objects
        q = {"org_id": org_id, "company": self.company, "deleted": False}
        self.ledgers = {o["name"] for o in objs.find({**q, "kind": "ledger"}, {"name": 1})}
        self.items = {o["name"] for o in objs.find({**q, "kind": "stockitem"}, {"name": 1})}
        self.units = {o["name"] for o in objs.find({**q, "kind": "unit"}, {"name": 1})}
        self.types = self.s["voucher_types"]
        mode = self.s.get("invoice_mode", "auto")
        self.inventory = bool(self.items) if mode == "auto" else mode == "item"
        self.deps = []

    def ledger(self, key, label=None):
        name = (self.map.get(key) or "").strip()
        if not name:
            raise Blocked(f"Choose the Tally ledger for “{label or key.replace('_', ' ')}” in Tally → Settings → Ledger mapping.")
        if name not in self.ledgers:
            raise Blocked(f"Ledger “{name}” is not in Tally. Pick another one in Tally → Settings → Ledger mapping.")
        return name

    def bank(self, method, bank_account):
        if (method or "").upper() == "CASH":
            return self.ledger("cash", "cash")
        if bank_account is not None:
            name = self.s["bank_ledgers"].get(str(getattr(bank_account, "id", bank_account)))
            if name and name in self.ledgers:
                return name
        return self.ledger("bank", "bank")

    # Parties and items a voucher needs: link to what is in Tally, or push them first.
    def party(self, doc, model):
        if doc is None:
            raise Blocked("The entry has no party.")
        row = link(self.org_id, model, doc.id)
        if row and row.get("tally_name") and (row.get("state") == "synced" or row["tally_name"] in self.ledgers):
            return row["tally_name"]
        if doc.name in self.ledgers:
            set_link(self.org_id, model, doc.id, tally_name=doc.name, hash=fingerprint(party_payload(doc, model)), state="synced", origin="matched")
            return doc.name
        self.deps.append(build_party(self, doc, model))
        return doc.name

    def item(self, product):
        row = link(self.org_id, "product", product.id)
        if row and row.get("tally_name") and (row.get("state") == "synced" or row["tally_name"] in self.items):
            return row["tally_name"]
        if product.name in self.items:
            set_link(self.org_id, "product", product.id, tally_name=product.name, hash=fingerprint(product_payload(product)), state="synced", origin="matched")
            return product.name
        self.deps.extend(build_product(self, product))
        return product.name


# --------------------------------------------------------------------------------------------
# Masters
# --------------------------------------------------------------------------------------------

def build_party(ctx, doc, model):
    payload = party_payload(doc, model)
    row = link(ctx.org_id, model, doc.id) or {}
    old = row.get("tally_name") if row.get("tally_name") and row.get("tally_name") in ctx.ledgers else None
    if not old and payload["name"] in ctx.ledgers:
        old = payload["name"]
    group = ctx.s["debtors_group"] if model == "customer" else ctx.s["creditors_group"]
    state = STATE_NAMES.get(state_code(payload["state"]), payload["state"]) or STATE_NAMES.get(payload["gstin"][:2], "")
    xml = tx.ledger_xml(ctx.company, payload["name"], group, old_name=old, gstin=payload["gstin"], state=state, address=payload["address"], phone=payload["phone"],
                        email=payload["email"], pincode=payload["pincode"])
    return {"model": model, "id": str(doc.id), "hash": fingerprint(payload), "label": f"{'Customer' if model == 'customer' else 'Supplier'} {payload['name']}",
            "tally_name": payload["name"], "xml": xml, "priority": 4}


def build_product(ctx, product):
    payload = product_payload(product)
    row = link(ctx.org_id, "product", product.id) or {}
    if row.get("state") == "synced" and row.get("hash") == fingerprint(payload):
        return []
    jobs = []
    unit_done = db().tally_jobs.find_one({"org_id": ctx.org_id, "unique": f"unit:{payload['unit']}", "status": {"$in": ["queued", "sent", "done"]}})
    if payload["unit"] not in ctx.units and not unit_done:
        jobs.append({"model": "", "id": "", "unique": f"unit:{payload['unit']}", "label": f"Unit {payload['unit']}", "xml": tx.unit_xml(ctx.company, payload["unit"]), "priority": 3.5})
        ctx.units.add(payload["unit"])
    old = row.get("tally_name") if row.get("tally_name") in ctx.items else (payload["name"] if payload["name"] in ctx.items else None)
    xml = tx.stockitem_xml(ctx.company, payload["name"], payload["unit"], hsn=payload["hsn"], gst_rate=gst_rate_of(product), old_name=old,
                           price=Decimal(payload["price"]) or None, description=payload["description"])
    jobs.append({"model": "product", "id": str(product.id), "hash": fingerprint(payload), "label": f"Item {payload['name']}", "tally_name": payload["name"], "xml": xml, "priority": 4})
    return jobs


# --------------------------------------------------------------------------------------------
# Vouchers
# --------------------------------------------------------------------------------------------

def _tax_lines(ctx, tax, interstate, side, sign):
    """GST ledger lines; side 'out' (sales) or 'in' (purchase); sign +1 debit / -1 credit."""
    tax = money(tax)
    if not tax:
        return []
    if interstate:
        return [{"ledger": ctx.ledger(f"igst_{side}", f"IGST {'output' if side == 'out' else 'input'}"), "amount": str(sign * tax)}]
    half = (tax / 2).quantize(CENT)
    return [{"ledger": ctx.ledger(f"cgst_{side}", f"CGST {'output' if side == 'out' else 'input'}"), "amount": str(sign * half)},
            {"ledger": ctx.ledger(f"sgst_{side}", f"SGST {'output' if side == 'out' else 'input'}"), "amount": str(sign * (tax - half))}]


def _goods_lines(ctx, items, ledger_key, sign, label):
    """Item lines → inventory entries (when Tally keeps stock) or a ledger line per account."""
    inventory, ledgers = [], {}
    for it in items:
        product = getattr(it, "product", None)
        taxable = money(getattr(it, "line_subtotal", None) if getattr(it, "line_subtotal", None) is not None else getattr(it, "subtotal", 0))
        is_service = getattr(it, "item_type", "goods") == "service" or (product is not None and getattr(product, "item_type", "goods") == "service")
        key = "service_income" if is_service and ledger_key == "sales" and ctx.map.get("service_income") else ledger_key
        ledger = ctx.ledger(key, label if key == ledger_key else "service income")
        if ctx.inventory and product is not None and not is_service:
            qty = Decimal(str(it.quantity or 0))
            inventory.append({"item": ctx.item(product), "qty": f"{qty:g}", "unit": (getattr(it, "unit", "") or product.unit or "Nos"),
                              "rate": str(money(it.unit_price)), "amount": str(sign * taxable), "ledger": ledger})
        else:
            ledgers[ledger] = ledgers.get(ledger, D0) + taxable
    return inventory, [{"ledger": k, "amount": str(sign * v)} for k, v in ledgers.items() if v]


def _round(ctx, v):
    """Round-off so the voucher balances to the document total."""
    diff = sum((Decimal(l["amount"]) for l in v["lines"]), D0) + sum((Decimal(i["amount"]) for i in v["inventory"]), D0)
    if abs(diff) >= CENT:
        v["lines"].append({"ledger": ctx.ledger("round_off", "round off"), "amount": str(-diff)})


def _trade(ctx, doc, kind, number, when, party_doc, party_model, total, tax, interstate, vtype, items, sell, bill_type, bill_ref, reference="", order=False):
    """Sales, purchase, credit/debit notes and orders share one shape.

    sell=True:  party Dr, sales Cr, output tax Cr   (Sales, Debit Note to customer reversed…)
    The sign of the whole voucher flips for returns via `flip`.
    """
    party = ctx.party(party_doc, party_model)
    party_sign = 1 if sell else -1
    total = money(total)
    v = {"remote_id": f"NX-{kind}-{doc.id}", "voucher_type": vtype, "date": day(when), "number": number, "reference": reference,
         "narration": f"From NexEase {number}", "party": party, "party_gstin": (getattr(party_doc, "gstin", "") or "").upper(), "is_order": order, "lines": [], "inventory": []}
    pos = STATE_NAMES.get(getattr(doc, "_pos", "") or "", "")
    if pos:
        v["place_of_supply"] = pos
    bills = [{"name": bill_ref, "type": bill_type}] if bill_ref and not order else None
    v["lines"].append({"ledger": party, "amount": str(party_sign * total), "party": True, "bills": bills})
    ledger_key = "sales" if (sell and kind in ("INV", "SO")) or (not sell and kind == "CN") else "purchase"
    inventory, lines = _goods_lines(ctx, items, ledger_key, -party_sign, "sales" if ledger_key == "sales" else "purchase")
    v["inventory"] = inventory
    v["lines"] += lines + _tax_lines(ctx, tax, interstate, "out" if ledger_key == "sales" else "in", -party_sign)
    _round(ctx, v)
    if order and not v["inventory"]:
        raise Blocked("Orders need stock items in Tally (turn on inventory in this company, or switch off order sync).")
    return v


def _interstate(ctx, pos, supplier_state=""):
    pos = state_code(pos)
    home = state_code(supplier_state) or ctx.company_state
    return bool(pos and home and pos != home)


def build_invoice(ctx, doc):
    bd = doc.billing_details or {}
    doc._pos = bd.get("place_of_supply") or (doc.customer_gstin or "")[:2]
    inter = _interstate(ctx, doc._pos, bd.get("supplier_state", ""))
    return _trade(ctx, doc, "INV", doc.invoice_number, doc.invoice_date, doc.customer, "customer", doc.total_amount, doc.tax_amount, inter,
                  ctx.types["sales"], doc.items, True, "New Ref", doc.invoice_number)


def build_bill(ctx, doc):
    gstin = (doc.supplier_gstin or getattr(doc.supplier, "gstin", "") or "")
    doc._pos = ctx.company_state
    inter = bool(gstin[:2] and ctx.company_state and gstin[:2] != ctx.company_state)
    ref = doc.supplier_invoice_number or doc.bill_number
    return _trade(ctx, doc, "BILL", doc.bill_number, doc.bill_date, doc.supplier, "supplier", doc.total_amount, doc.tax_amount, inter,
                  ctx.types["purchase"], doc.items, False, "New Ref", ref, reference=doc.supplier_invoice_number or "")


def build_credit_note(ctx, doc):
    inv = doc.invoice
    bd = (inv.billing_details if inv else None) or {}
    doc._pos = bd.get("place_of_supply") or (getattr(doc.customer, "gstin", "") or "")[:2]
    inter = _interstate(ctx, doc._pos, bd.get("supplier_state", ""))
    return _trade(ctx, doc, "CN", doc.credit_note_number, doc.credit_note_date, doc.customer, "customer", doc.total_amount, doc.tax_amount, inter,
                  ctx.types["credit_note"], doc.items, False, "Agst Ref" if inv else "New Ref", inv.invoice_number if inv else doc.credit_note_number)


def build_debit_note(ctx, doc):
    bill = doc.vendor_bill
    gstin = getattr(doc.supplier, "gstin", "") or ""
    doc._pos = ctx.company_state
    inter = bool(gstin[:2] and ctx.company_state and gstin[:2] != ctx.company_state)
    ref = (bill.supplier_invoice_number or bill.bill_number) if bill else doc.debit_note_number
    return _trade(ctx, doc, "DN", doc.debit_note_number, doc.debit_note_date, doc.supplier, "supplier", doc.total_amount, doc.tax_amount, inter,
                  ctx.types["debit_note"], doc.items, True, "Agst Ref" if bill else "New Ref", ref)


def build_sales_order(ctx, doc):
    doc._pos = (getattr(doc.customer, "gstin", "") or "")[:2]
    inter = _interstate(ctx, doc._pos)
    return _trade(ctx, doc, "SO", doc.so_number, doc.order_date, doc.customer, "customer", doc.total_amount, doc.tax_amount, inter, ctx.types["sales_order"],
                  doc.items, True, "", "", order=True)


def build_purchase_order(ctx, doc):
    gstin = getattr(doc.supplier, "gstin", "") or ""
    doc._pos = ctx.company_state
    inter = bool(gstin[:2] and ctx.company_state and gstin[:2] != ctx.company_state)
    return _trade(ctx, doc, "PO", doc.po_number, doc.order_date, doc.supplier, "supplier", doc.total_amount, doc.tax_amount, inter, ctx.types["purchase_order"],
                  doc.items, False, "", "", order=True)


def _settlement(ctx, doc, kind, party_doc, model, refs, vtype, receipt):
    party = ctx.party(party_doc, model)
    amount = money(doc.amount)
    allocated = D0
    bills = []
    for ref, amt in refs:
        amt = money(amt)
        if ref and amt:
            bills.append({"name": ref, "type": "Agst Ref", "amount": str(-amt if receipt else amt)})
            allocated += amt
    if amount - allocated >= CENT:
        rest = amount - allocated
        bills.append({"name": doc.payment_number, "type": "On Account", "amount": str(-rest if receipt else rest)})
    bank = ctx.bank(doc.payment_method, doc.bank_account)
    sign = 1 if receipt else -1  # bill amounts above are debit-positive, like the party line they belong to
    return {"remote_id": f"NX-{kind}-{doc.id}", "voucher_type": vtype, "date": day(doc.payment_date), "number": doc.payment_number,
            "reference": doc.reference_number or "", "narration": (doc.notes or f"From NexEase {doc.payment_number}")[:500], "party": party,
            "lines": [{"ledger": bank, "amount": str(sign * amount)}, {"ledger": party, "amount": str(-sign * amount), "party": True, "bills": bills}], "inventory": []}


def build_receipt(ctx, doc):
    refs = [(a.invoice.invoice_number if a.invoice else "", a.amount) for a in doc.allocations or []]
    return _settlement(ctx, doc, "RCPT", doc.customer, "customer", refs, ctx.types["receipt"], True)


def build_payment(ctx, doc):
    refs = [((a.vendor_bill.supplier_invoice_number or a.vendor_bill.bill_number) if a.vendor_bill else "", a.amount) for a in doc.allocations or []]
    return _settlement(ctx, doc, "PAY", doc.supplier, "supplier", refs, ctx.types["payment"], False)


def build_expense(ctx, rec):
    d = rec.data or {}
    amount = money(d.get("amount"))
    if amount <= 0:
        raise Blocked("Expense amount is zero.")
    category = (d.get("category") or "").strip()
    ledger = ctx.s["expense_ledgers"].get(category) or ctx.map.get("expense_default")
    if not ledger:
        raise Blocked(f"Choose the Tally expense ledger for “{category or 'expenses'}” in Tally → Settings.")
    if ledger not in ctx.ledgers:
        raise Blocked(f"Ledger “{ledger}” is not in Tally. Pick another one in Tally → Settings.")
    mode = (d.get("payment_mode") or "").strip().lower()
    bank = ctx.ledger("cash", "cash") if mode in ("", "cash") else ctx.ledger("bank", "bank")
    when = d.get("date") or day(rec.created_at)
    narration = " · ".join(p for p in [category, d.get("payee", ""), d.get("description", "")] if p)
    return {"remote_id": f"NX-EXP-{rec.id}", "voucher_type": ctx.types["payment"], "date": str(when)[:10], "number": rec.key[:40], "reference": str(d.get("reference", ""))[:60],
            "narration": narration[:500] or "Expense from NexEase", "lines": [{"ledger": ledger, "amount": str(amount)}, {"ledger": bank, "amount": str(-amount)}], "inventory": []}


def build_journal(ctx, doc):
    lines = []
    accounts = ctx.s.get("journal_accounts", {})
    for l in doc.lines:
        acc = l.account
        name = accounts.get(str(acc.id)) if acc else None
        name = name or (acc.account_name if acc else "")
        if name not in ctx.ledgers:
            raise Blocked(f"Account “{name}” has no matching Tally ledger. Map it in Tally → Settings → Accounts.")
        amt = money(l.debit) - money(l.credit)
        if amt:
            lines.append({"ledger": name, "amount": str(amt)})
    return {"remote_id": f"NX-JV-{doc.id}", "voucher_type": ctx.types["journal"], "date": day(doc.journal_date), "number": doc.journal_number,
            "narration": (doc.description or f"From NexEase {doc.journal_number}")[:500], "lines": lines, "inventory": []}


# --------------------------------------------------------------------------------------------
# Sources
# --------------------------------------------------------------------------------------------

def _sources():
    from apps.business.models import BusinessRecord
    from apps.finance.models import JournalEntry
    from apps.products.models import Product
    from apps.purchasing.models import PurchaseOrder, Supplier, SupplierPayment, VendorBill, VendorDebitNote
    from apps.sales.models import CreditNote, Customer, CustomerPayment, Invoice, SalesOrder
    live_sale, live_bill = ("ISSUED", "PARTIALLY_PAID", "PAID"), ("POSTED", "PARTIALLY_PAID", "PAID")
    return {
        # kind: (model key, Model, extra filter, builder, is_voucher, status → push / cancel / skip)
        "customers": ("customer", Customer, {}, None, False, None),
        "suppliers": ("supplier", Supplier, {}, None, False, None),
        "products": ("product", Product, {}, None, False, None),
        "invoices": ("invoice", Invoice, {}, build_invoice, True, lambda d: "push" if d.status in live_sale else "cancel" if d.status == "CANCELLED" else "skip"),
        "bills": ("bill", VendorBill, {}, build_bill, True, lambda d: "push" if d.status in live_bill else "cancel" if d.status == "CANCELLED" else "skip"),
        "receipts": ("receipt", CustomerPayment, {}, build_receipt, True, lambda d: "push"),
        "payments": ("payment", SupplierPayment, {}, build_payment, True, lambda d: "push"),
        "credit_notes": ("credit_note", CreditNote, {}, build_credit_note, True, lambda d: "push" if d.status not in ("DRAFT", "CANCELLED") else "cancel" if d.status == "CANCELLED" else "skip"),
        "debit_notes": ("debit_note", VendorDebitNote, {}, build_debit_note, True, lambda d: "push" if d.status not in ("DRAFT", "CANCELLED") else "cancel" if d.status == "CANCELLED" else "skip"),
        "sales_orders": ("sales_order", SalesOrder, {}, build_sales_order, True, lambda d: "push" if d.status not in ("DRAFT", "CANCELLED") else "cancel" if d.status == "CANCELLED" else "skip"),
        "purchase_orders": ("purchase_order", PurchaseOrder, {}, build_purchase_order, True, lambda d: "push" if d.status not in ("DRAFT", "CANCELLED") else "cancel" if d.status == "CANCELLED" else "skip"),
        "expenses": ("expense", BusinessRecord, {"kind": "expenses"}, build_expense, True, lambda d: "push"),
        "journals": ("journal", JournalEntry, {"source_type": "MANUAL"}, build_journal, True,
                     lambda d: "push" if d.status == "POSTED" else "cancel" if d.status == "REVERSED" else "skip"),
    }


def _number_and_date(model, doc):
    for f in ("invoice_number", "bill_number", "payment_number", "credit_note_number", "debit_note_number", "so_number", "po_number", "journal_number", "key"):
        if getattr(doc, f, None):
            return getattr(doc, f)
    return str(doc.id)


def build(ctx, kind, doc):
    """→ list of job dicts (dependencies first) for one record."""
    model, Model, _, builder, is_voucher, decide = _sources()[kind]
    ctx.deps = []
    if not is_voucher:
        return [build_party(ctx, doc, model)] if model in ("customer", "supplier") else build_product(ctx, doc)
    action = decide(doc)
    if action == "skip":
        return []
    row = link(ctx.org_id, model, doc.id) or {}
    label = f"{kind.replace('_', ' ').rstrip('s').capitalize()} {_number_and_date(model, doc)}"
    if action == "cancel":
        if row.get("state") != "synced" or row.get("cancelled"):
            return []
        v = {"remote_id": f"NX-{row.get('prefix') or ''}{doc.id}", "voucher_type": row.get("voucher_type", ""), "date": row.get("date") or day(None),
             "number": row.get("number", ""), "cancelled": True}
        v["remote_id"] = row.get("remote_id") or v["remote_id"]
        return [{"model": model, "id": str(doc.id), "hash": fingerprint(v), "label": f"Cancel {label}", "xml": tx.voucher_xml(ctx.company, v), "priority": 5,
                 "extra": {"cancelled": True}}]
    v = builder(ctx, doc)
    if not tx.balanced(v):
        raise Blocked("Debits and credits do not match; check the entry's totals.")
    job = {"model": model, "id": str(doc.id), "hash": fingerprint(v), "label": label, "xml": tx.voucher_xml(ctx.company, v), "priority": 5,
           "extra": {"remote_id": v["remote_id"], "voucher_type": v["voucher_type"], "date": v["date"], "number": v.get("number", ""), "cancelled": False}}
    deps = ctx.deps
    return (deps if isinstance(deps, list) else []) + [job]


def queue(ctx, jobs):
    for j in jobs:
        if j.get("model"):
            row = link(ctx.org_id, j["model"], j["id"]) or {}
            if row.get("hash") == j["hash"] and row.get("state") == "synced":
                continue
        source = {k: j.get(k) for k in ("model", "id", "hash", "label", "tally_name")} if j.get("model") else {"label": j["label"]}
        source["extra"] = j.get("extra", {})
        unique = j.get("unique") or f"push:{j['model']}:{j['id']}"
        enqueue(ctx.org_id, "push", j["xml"], ctx.company, j.get("model", ""), source=source, priority=j.get("priority", 5), unique=unique)
        if j.get("model"):
            set_link(ctx.org_id, j["model"], j["id"], state="queued", error="", label=j["label"])


def produce(org_id, company):
    jobs = db().tally_jobs
    if jobs.count_documents({"org_id": org_id, "type": "push", "status": {"$in": ["queued", "sent"]}}) >= MAX_QUEUED:
        return
    s = settings(org_id)
    if not s.get("push_from"):
        s["push_from"] = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) - IST
        db().tally_settings.update_one({"_id": org_id}, {"$set": {"push_from": s["push_from"]}}, upsert=True)
    ctx = Context(org_id, company)
    if not ctx.org:
        return
    sources = _sources()
    budget = BATCH
    cursors = dict(s.get("out_cursor", {}))
    for kind in [k for k in sources if s["write_back"].get(k, True)]:
        model, Model, extra, _, _, _ = sources[kind]
        since = max(cursors.get(kind) or s["push_from"], s["push_from"])
        docs = list(Model.objects(organization=ctx.org, updated_at__gte=since, **extra).order_by("updated_at").limit(budget))
        for doc in docs:
            try:
                queue(ctx, build(ctx, kind, doc))
            except Blocked as e:
                set_link(org_id, model, doc.id, state="blocked", error=str(e), label=f"{kind.replace('_', ' ')} {_number_and_date(model, doc)}", kind=kind)
            except Exception as e:  # one bad record must not stop the rest
                set_link(org_id, model, doc.id, state="error", error=f"Could not prepare: {e}"[:300], label=f"{kind.replace('_', ' ')} {_number_and_date(model, doc)}", kind=kind)
            cursors[kind] = doc.updated_at + timedelta(microseconds=1)
            budget -= 1
        if budget <= 0:
            break
    db().tally_settings.update_one({"_id": org_id}, {"$set": {"out_cursor": cursors}}, upsert=True)
    retry_blocked(ctx, sources)
    sweep_cancelled(ctx, sources)


CANCEL_STATUS = {"invoice": "CANCELLED", "bill": "CANCELLED", "credit_note": "CANCELLED", "debit_note": "CANCELLED", "sales_order": "CANCELLED",
                 "purchase_order": "CANCELLED", "journal": "REVERSED"}


def sweep_cancelled(ctx, sources, every_minutes=10):
    """Some screens cancel with a direct database update that leaves updated_at alone; catch those."""
    state = db().tally_state.find_one({"_id": ctx.org_id}) or {}
    if state.get("sweep_at") and state["sweep_at"] > datetime.utcnow() - timedelta(minutes=every_minutes):
        return
    db().tally_state.update_one({"_id": ctx.org_id}, {"$set": {"sweep_at": datetime.utcnow()}}, upsert=True)
    by_model = {v[0]: (k, v[1]) for k, v in sources.items()}
    for model, status in CANCEL_STATUS.items():
        kind, Model = by_model[model]
        if not ctx.s["write_back"].get(kind, True):
            continue
        ids = [r["nexease_id"] for r in db().tally_links.find({"org_id": ctx.org_id, "model": model, "state": "synced", "cancelled": {"$ne": True}}, {"nexease_id": 1})]
        for i in range(0, len(ids), 500):
            for doc in Model.objects(organization=ctx.org, id__in=ids[i:i + 500], status=status):
                try:
                    queue(ctx, build(ctx, kind, doc))
                except Blocked:
                    pass


def retry_blocked(ctx, sources, limit=15):
    by_model = {v[0]: (k, v[1]) for k, v in sources.items()}
    for row in db().tally_links.find({"org_id": ctx.org_id, "state": {"$in": ["blocked", "retry"]}}).limit(limit):
        if row["model"] not in by_model:
            continue
        kind, Model = by_model[row["model"]]
        if not ctx.s["write_back"].get(kind, True):
            continue
        doc = Model.objects(id=row["nexease_id"], organization=ctx.org).first()
        if not doc:
            db().tally_links.delete_one({"_id": row["_id"]})
            continue
        try:
            queue(ctx, build(ctx, kind, doc))
        except Blocked as e:
            db().tally_links.update_one({"_id": row["_id"]}, {"$set": {"state": "blocked", "error": str(e)}})
        except Exception as e:
            db().tally_links.update_one({"_id": row["_id"]}, {"$set": {"state": "error", "error": f"Could not prepare: {e}"[:300]}})
