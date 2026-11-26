"""Report engine: typed, totalled, chartable business reports.

GET /api/v1/business/reports/run/?report=<source>/<group>&from=YYYY-MM-DD&to=YYYY-MM-DD&compare=1

Response:
    {id, title, period:{from,to}, columns:[{key,label,type}], rows:[{key: value}], totals:{key: value},
     previous:{period, totals} | null, chart:{type, x, y:[keys], limit} | null, notes:[str]}

Column types: text, date, int, qty, money, percent. Money/qty are strings with two decimals.
Totals cover int/qty/money columns; percent totals are recomputed where they have a meaning
(share is 100, margin is profit / sales). compare=1 adds the totals of the period of the same
length that ends the day before `from`.

The older /business/sales-reports/ endpoint stays as it is for installed mobile apps.
"""

from collections import defaultdict
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from django.views.decorators.http import require_GET

from apps.core.api.decorators import api_login_required
from apps.core.services.api_response_service import APIResponseService as R
from apps.products.models import Category, Product
from apps.purchasing.models import PurchaseOrder, Supplier, VendorBill
from apps.sales.models import Customer, Invoice, SalesOrder

from .models import BusinessRecord
from .views import permitted

CENT = Decimal("0.01")
MAX_DAYS = 367
MAX_DOCUMENTS = 20000
ZERO = Decimal(0)

SOURCES = {
    # source: model, date field, number field, party field, party model, permission, counted statuses
    "sales": (Invoice, "invoice_date", "invoice_number", "customer", Customer, "invoices.read", ("ISSUED", "PARTIALLY_PAID", "PAID")),
    "purchases": (VendorBill, "bill_date", "bill_number", "supplier", Supplier, "bills.read", ("POSTED", "PARTIALLY_PAID", "PAID")),
    "sales-orders": (SalesOrder, "order_date", "so_number", "customer", Customer, "sales_orders.read", None),
    "purchase-orders": (PurchaseOrder, "order_date", "po_number", "supplier", Supplier, "purchase_orders.read", None),
}
TITLES = {
    "sales": "Sales", "purchases": "Purchases", "sales-orders": "Sales orders", "purchase-orders": "Purchase orders",
    "document": "transactions", "party": "by party", "item": "by item", "party-item": "by party and item",
    "category": "by item category", "hsn": "summary by HSN", "sac": "summary by SAC", "rate": "by GST rate",
    "discount": "invoice discounts", "item-discount": "item-wise discounts", "trend": "trend",
}
DOCUMENT_GROUPS = set(TITLES) - set(SOURCES)


def q2(value):
    return Decimal(value or 0).quantize(CENT)


def col(key, label, kind="text"):
    return {"key": key, "label": label, "type": kind}


def ref_id(document, field):
    value = document._data.get(field)
    return getattr(value, "id", value)


class Lines:
    """Counted documents in a period with their lines, products, categories and parties loaded once."""

    def __init__(self, org, source, start, end):
        model, date_field, number_field, party_field, party_model, _, statuses = SOURCES[source]
        query = {"organization": org, date_field + "__gte": datetime.combine(start, time.min), date_field + "__lte": datetime.combine(end, time.max)}
        docs = model.objects(**query)
        docs = docs.filter(status__in=statuses) if statuses else docs.filter(status__ne="CANCELLED")
        self.documents = list(docs.no_dereference().order_by(date_field, number_field).limit(MAX_DOCUMENTS + 1))
        self.truncated = len(self.documents) > MAX_DOCUMENTS
        self.documents = self.documents[:MAX_DOCUMENTS]
        self.source, self.date_field, self.number_field, self.party_field = source, date_field, number_field, party_field
        product_ids, party_ids = set(), set()
        for d in self.documents:
            party_ids.add(ref_id(d, party_field))
            for line in d.items:
                pid = getattr(line._data.get("product"), "id", line._data.get("product"))
                if pid:
                    product_ids.add(pid)
        self.products = {p.id: p for p in Product.objects(organization=org, id__in=list(product_ids)).no_dereference()} if product_ids else {}
        category_ids = {getattr(p._data.get("category"), "id", p._data.get("category")) for p in self.products.values()}
        self.categories = {c.id: c.name for c in Category.objects(organization=org, id__in=[c for c in category_ids if c]).only("id", "name")}
        self.parties = {p.id: p for p in party_model.objects(organization=org, id__in=[p for p in party_ids if p]).only("id", "name", "code", "gstin")}

    def party(self, document):
        return self.parties.get(ref_id(document, self.party_field))

    def product(self, line):
        ref = line._data.get("product")
        return self.products.get(getattr(ref, "id", ref))

    def category(self, product):
        if not product:
            return "Uncategorised"
        ref = product._data.get("category")
        return self.categories.get(getattr(ref, "id", ref), "Uncategorised")

    def amounts(self, line):
        """(net after discount, tax, total, discount, quantity) for any line type."""
        if self.source == "purchase-orders":
            total, tax = q2(line.total), q2(line.tax_amount)
        else:
            total, tax = q2(line.line_total), q2(line.line_tax)
        return total - tax, tax, total, q2(line.discount), Decimal(line.quantity or 0)

    def item_name(self, line):
        product = self.product(line)
        return getattr(line, "item_name", "") or (product.name if product else "Item")

    def item_type(self, line):
        product = self.product(line)
        return getattr(line, "item_type", "") or (product.item_type if product else "goods") or "goods"

    def hsn(self, line):
        product = self.product(line)
        return getattr(line, "hsn_code", "") or (product.hsn_code if product else "") or "Unclassified"

    def __iter__(self):
        for d in self.documents:
            for line in d.items:
                yield d, line


def bucket_key(day, monthly):
    return day.strftime("%Y-%m") if monthly else day.isoformat()


def as_day(value):
    return value.date() if isinstance(value, datetime) else value


def periods_between(start, end, monthly):
    keys, day = [], start
    while day <= end:
        key = bucket_key(day, monthly)
        if key not in keys:
            keys.append(key)
        day += timedelta(days=1)
    return keys


# ----------------------------------------------------------------------------------------------
# Document reports
# ----------------------------------------------------------------------------------------------

def document_report(org, source, group, start, end):
    data = Lines(org, source, start, end)
    party_word = "Customer" if source.startswith("sales") else "Supplier"
    money = lambda k, l: col(k, l, "money")
    notes = ["Only the first 20,000 documents in this period are included."] if data.truncated else []

    if group == "document" or group == "discount":
        rows = []
        for d in data.documents:
            net = tax = total = disc = ZERO
            for line in d.items:
                n, t, tot, dc, _ = data.amounts(line)
                net, tax, total, disc = net + n, tax + t, total + tot, disc + dc
            if group == "discount" and not disc:
                continue
            party = data.party(d)
            day = as_day(getattr(d, data.date_field))
            base = {"number": getattr(d, data.number_field), "date": day.isoformat() if day else None, "party": party.name if party else ""}
            if group == "document":
                rows.append({**base, "gstin": (party.gstin if party else "") or "", "status": d.status.replace("_", " ").title(),
                             "net": net, "discount": disc, "tax": tax, "total": total})
            else:
                rows.append({**base, "before": net + disc, "discount": disc, "rate": (disc / (net + disc) * 100) if net + disc else ZERO, "net": net})
        if group == "document":
            columns = [col("number", "Number"), col("date", "Date", "date"), col("party", party_word), col("gstin", "GSTIN"), col("status", "Status"),
                       money("net", "Taxable value"), money("discount", "Discount"), money("tax", "GST"), money("total", "Total")]
            return columns, rows, None, notes
        columns = [col("number", "Number"), col("date", "Date", "date"), col("party", party_word), money("before", "Before discount"),
                   money("discount", "Discount"), col("rate", "Discount %", "percent"), money("net", "After discount")]
        return columns, rows, None, notes

    if group == "trend":
        monthly = (end - start).days > 62
        buckets = {key: {"period": key, "documents": 0, "net": ZERO, "tax": ZERO, "total": ZERO} for key in periods_between(start, end, monthly)}
        for d in data.documents:
            day = as_day(getattr(d, data.date_field))
            row = buckets.setdefault(bucket_key(day, monthly), {"period": bucket_key(day, monthly), "documents": 0, "net": ZERO, "tax": ZERO, "total": ZERO})
            row["documents"] += 1
            for line in d.items:
                n, t, tot, _, _ = data.amounts(line)
                row["net"] += n; row["tax"] += t; row["total"] += tot
        columns = [col("period", "Month" if monthly else "Day", "text"), col("documents", "Documents", "int"), money("net", "Taxable value"), money("tax", "GST"), money("total", "Total")]
        return columns, list(buckets.values()), {"type": "line", "x": "period", "y": ["total"]}, notes

    groups = {}

    def row_for(key, base):
        return groups.setdefault(key, {**base, "qty": ZERO, "net": ZERO, "tax": ZERO, "total": ZERO, "discount": ZERO, "documents": set(), "names": []})

    for d, line in data:
        net, tax, total, disc, qty = data.amounts(line)
        party = data.party(d)
        product = data.product(line)
        name = data.item_name(line)
        if group == "party":
            key, base = ref_id(d, data.party_field), {"party": party.name if party else "", "gstin": (party.gstin if party else "") or ""}
        elif group == "item":
            key, base = name, {"item": name, "sku": product.sku if product else "", "unit": (product.unit if product else "") or getattr(line, "unit", "")}
        elif group == "party-item":
            key, base = (ref_id(d, data.party_field), name), {"party": party.name if party else "", "item": name}
        elif group == "category":
            key = data.category(product); base = {"category": key}
        elif group in ("hsn", "sac"):
            if data.item_type(line) != ("service" if group == "sac" else "goods"):
                continue
            key = data.hsn(line); base = {"code": key}
        elif group == "rate":
            key = f"{Decimal(line.tax_rate or 0).normalize():f}%"; base = {"rate": key}
        elif group == "item-discount":
            if not disc:
                continue
            key, base = name, {"item": name}
        else:
            raise ValueError("Unknown report.")
        row = row_for(key, base)
        row["qty"] += qty; row["net"] += net; row["tax"] += tax; row["total"] += total; row["discount"] += disc
        row["documents"].add(d.id)
        if group in ("hsn", "sac") and name not in row["names"] and len(row["names"]) < 3:
            row["names"].append(name)

    rows = list(groups.values())
    grand = sum((r["total"] for r in rows), ZERO)
    for r in rows:
        r["count"] = len(r.pop("documents"))
        r["share"] = (r["total"] / grand * 100) if grand else ZERO
        r["rate_avg"] = (r["net"] / r["qty"]) if r["qty"] else ZERO
        r["items"] = ", ".join(r.pop("names"))
    rows.sort(key=lambda r: -r["total"])
    top = {"type": "bar", "y": ["total"], "limit": 8}
    if group == "party":
        columns = [col("party", party_word), col("gstin", "GSTIN"), col("count", "Documents", "int"), money("net", "Taxable value"), money("tax", "GST"), money("total", "Total"), col("share", "Share", "percent")]
        return columns, rows, {**top, "x": "party"}, notes
    if group == "item":
        columns = [col("item", "Item"), col("sku", "SKU"), col("qty", "Quantity", "qty"), col("unit", "Unit"), money("rate_avg", "Avg rate"), money("net", "Taxable value"), money("tax", "GST"), money("total", "Total"), col("share", "Share", "percent")]
        return columns, rows, {**top, "x": "item"}, notes
    if group == "party-item":
        columns = [col("party", party_word), col("item", "Item"), col("qty", "Quantity", "qty"), money("net", "Taxable value"), money("total", "Total")]
        return columns, rows, None, notes
    if group == "category":
        columns = [col("category", "Category"), col("qty", "Quantity", "qty"), money("net", "Taxable value"), money("tax", "GST"), money("total", "Total"), col("share", "Share", "percent")]
        return columns, rows, {**top, "x": "category"}, notes
    if group in ("hsn", "sac"):
        rows.sort(key=lambda r: r["code"])
        columns = [col("code", "HSN" if group == "hsn" else "SAC"), col("items", "Items"), col("qty", "Quantity", "qty"), money("net", "Taxable value"), money("tax", "GST"), money("total", "Total")]
        return columns, rows, None, notes
    if group == "rate":
        rows.sort(key=lambda r: Decimal(r["rate"].rstrip("%")))
        columns = [col("rate", "GST rate"), col("count", "Documents", "int"), money("net", "Taxable value"), money("tax", "GST"), money("total", "Total")]
        return columns, rows, {"type": "bar", "x": "rate", "y": ["net"], "limit": 12}, notes
    columns = [col("item", "Item"), col("qty", "Quantity", "qty"), money("discount", "Discount"), money("net", "After discount")]
    return columns, sorted(rows, key=lambda r: -r["discount"]), None, notes


# ----------------------------------------------------------------------------------------------
# Profit, overview, expenses, inventory
# ----------------------------------------------------------------------------------------------

def profit_report(org, group, start, end):
    data = Lines(org, "sales", start, end)
    groups = {}
    unvalued = set()
    for d, line in data:
        net, _, _, _, qty = data.amounts(line)
        product = data.product(line)
        cost_price = Decimal(product.cost_price or 0) if product else ZERO
        if data.item_type(line) == "goods" and not cost_price:
            unvalued.add(data.item_name(line))
        cost = q2(cost_price * qty)
        if group == "item":
            name = data.item_name(line)
            key, base = name, {"item": name, "sku": product.sku if product else ""}
        else:
            party = data.party(d)
            key, base = ref_id(d, "customer"), {"party": party.name if party else ""}
        row = groups.setdefault(key, {**base, "qty": ZERO, "sales": ZERO, "cost": ZERO})
        row["qty"] += qty; row["sales"] += net; row["cost"] += cost
    rows = list(groups.values())
    for r in rows:
        r["profit"] = r["sales"] - r["cost"]
        r["margin"] = (r["profit"] / r["sales"] * 100) if r["sales"] else ZERO
    rows.sort(key=lambda r: -r["profit"])
    notes = ["Cost uses each item's current cost price, not the price paid at the time of sale."]
    if unvalued:
        notes.append(f"{len(unvalued)} item{'s' if len(unvalued) != 1 else ''} without a cost price count as zero cost: " + ", ".join(sorted(unvalued)[:5]) + ("…" if len(unvalued) > 5 else ""))
    lead = [col("item", "Item"), col("sku", "SKU"), col("qty", "Quantity", "qty")] if group == "item" else [col("party", "Customer")]
    columns = lead + [col("sales", "Sales (taxable)", "money"), col("cost", "Cost", "money"), col("profit", "Gross profit", "money"), col("margin", "Margin", "percent")]
    return columns, rows, {"type": "bar", "x": "item" if group == "item" else "party", "y": ["profit"], "limit": 8}, notes


def expense_rows(org, start, end):
    return BusinessRecord.objects(organization=org, kind="expenses", data__date__gte=start.isoformat(), data__date__lte=end.isoformat())


def overview_report(request, org, start, end):
    keys = periods_between(start, end, True)
    rows = {k: {"period": k, "sales": ZERO, "purchases": ZERO, "expenses": ZERO} for k in keys}
    notes = []
    for source, field, permission in (("sales", "sales", "invoices.read"), ("purchases", "purchases", "bills.read")):
        if not permitted(request, permission):
            notes.append(f"{field.title()} hidden: your role cannot read them.")
            continue
        data = Lines(org, source, start, end)
        for d, line in data:
            rows[bucket_key(as_day(getattr(d, data.date_field)), True)][field] += data.amounts(line)[0]
    if permitted(request, "expenses.read"):
        for e in expense_rows(org, start, end):
            try:
                rows[str(e.data.get("date", ""))[:7]]["expenses"] += Decimal(str(e.data.get("amount") or 0))
            except (KeyError, ArithmeticError):
                continue
    else:
        notes.append("Expenses hidden: your role cannot read them.")
    for r in rows.values():
        r["result"] = r["sales"] - r["purchases"] - r["expenses"]
    notes.append("Sales and purchases are taxable values (before GST); expenses are amounts paid. This is a cash-style view, not the profit and loss statement.")
    columns = [col("period", "Month"), col("sales", "Sales", "money"), col("purchases", "Purchases", "money"), col("expenses", "Expenses", "money"), col("result", "Sales − purchases − expenses", "money")]
    return columns, list(rows.values()), {"type": "bar", "x": "period", "y": ["sales", "purchases", "expenses"]}, notes


def expense_report(org, group, start, end):
    if group == "document":
        rows = []
        for e in expense_rows(org, start, end).order_by("data.date"):
            d = e.data
            rows.append({"date": d.get("date"), "reference": d.get("reference") or e.key, "category": d.get("category") or "Unclassified",
                         "description": d.get("description") or "", "payee": d.get("payee") or "", "mode": d.get("payment_mode") or "",
                         "amount": Decimal(str(d.get("amount") or 0))})
        columns = [col("date", "Date", "date"), col("reference", "Reference"), col("category", "Category"), col("description", "Description"),
                   col("payee", "Paid to"), col("mode", "Mode"), col("amount", "Amount", "money")]
        return columns, rows, None, []
    field = "category" if group == "category" else "description"
    groups = defaultdict(lambda: {"count": 0, "amount": ZERO})
    for e in expense_rows(org, start, end):
        label = e.data.get(field) or "Unclassified"
        groups[label]["count"] += 1
        groups[label]["amount"] += Decimal(str(e.data.get("amount") or 0))
    total = sum((g["amount"] for g in groups.values()), ZERO)
    rows = [{"label": k, **v, "share": (v["amount"] / total * 100) if total else ZERO} for k, v in groups.items()]
    rows.sort(key=lambda r: -r["amount"])
    columns = [col("label", "Category" if group == "category" else "Description"), col("count", "Entries", "int"), col("amount", "Amount", "money"), col("share", "Share", "percent")]
    return columns, rows, {"type": "bar", "x": "label", "y": ["amount"], "limit": 8}, []


def inventory_report(org, group, can_cost):
    from apps.inventory.models import Inventory
    stock = defaultdict(Decimal)
    for entry in Inventory.objects(organization=org).no_dereference().only("product", "quantity"):
        ref = entry._data.get("product")
        stock[getattr(ref, "id", ref)] += Decimal(entry.quantity or 0)
    products = list(Product.objects(organization=org, is_active=True, item_type="goods").no_dereference())
    categories = {c.id: c.name for c in Category.objects(organization=org).only("id", "name")}
    if group == "low":
        levels = {r.key: Decimal(str(r.data.get("level") or 0)) for r in BusinessRecord.objects(organization=org, kind="reorder_rule", data__enabled=True)}
        rows = []
        for p in products:
            level = levels.get(str(p.id))
            qty = stock[p.id]
            if level is not None and qty <= level:
                rows.append({"sku": p.sku, "item": p.name, "unit": p.unit, "stock": qty, "level": level, "short": level - qty})
        rows.sort(key=lambda r: -r["short"])
        columns = [col("sku", "SKU"), col("item", "Item"), col("unit", "Unit"), col("stock", "In stock", "qty"), col("level", "Reorder level", "qty"), col("short", "Short by", "qty")]
        return columns, rows, None, ["Open Stock → Low stock to create a draft purchase order from these items."]
    groups = defaultdict(lambda: {"items": 0, "qty": ZERO, "value": ZERO})
    for p in products:
        ref = p._data.get("category")
        g = groups[categories.get(getattr(ref, "id", ref), "Uncategorised")]
        g["items"] += 1
        g["qty"] += stock[p.id]
        g["value"] += stock[p.id] * Decimal(p.cost_price or 0)
    rows = [{"category": k, **v} for k, v in sorted(groups.items())]
    columns = [col("category", "Category"), col("items", "Items", "int"), col("qty", "Quantity", "qty")]
    notes = ["Quantities add up different units; use them per category."]
    if can_cost:
        columns.append(col("value", "Value at cost", "money"))
        return columns, rows, {"type": "bar", "x": "category", "y": ["value"], "limit": 8}, notes
    for r in rows:
        r.pop("value")
    return columns, rows, None, notes


# ----------------------------------------------------------------------------------------------
# Running and shaping
# ----------------------------------------------------------------------------------------------

def run(request, report, start, end):
    """Returns (title, columns, rows, chart, notes, dated) or raises PermissionError/ValueError."""
    org = request.api_organization
    source, _, group = report.partition("/")
    if source in SOURCES:
        if group not in DOCUMENT_GROUPS:
            raise ValueError("Unknown report.")
        if not permitted(request, SOURCES[source][5]):
            raise PermissionError("You cannot read these documents.")
        if group in ("hsn", "sac", "rate") and not permitted(request, "taxation.read"):
            raise PermissionError("GST reports need the taxation.read permission.")
        title = f"{TITLES[source]} {TITLES[group]}" if group != "discount" else f"{TITLES[source]} — invoice discounts"
        return (title, *document_report(org, source, group, start, end), True)
    if source == "profit" and group in ("item", "party"):
        if not (permitted(request, "invoices.read") and permitted(request, "products.read_cost")):
            raise PermissionError("Profit reports need invoices.read and products.read_cost.")
        return ("Gross profit by " + ("item" if group == "item" else "customer"), *profit_report(org, group, start, end), True)
    if report == "overview/monthly":
        return ("Monthly business overview", *overview_report(request, org, start, end), True)
    if source == "expenses" and group in ("document", "category", "item"):
        if not permitted(request, "expenses.read"):
            raise PermissionError("Expense reports need the expenses.read permission.")
        title = {"document": "Expense transactions", "category": "Expenses by category", "item": "Expenses by description"}[group]
        return (title, *expense_report(org, group, start, end), True)
    if source == "inventory" and group in ("low", "category"):
        if not permitted(request, "inventory.read"):
            raise PermissionError("Stock reports need the inventory.read permission.")
        title = "Low stock summary" if group == "low" else "Stock summary by category"
        return (title, *inventory_report(org, group, permitted(request, "products.read_cost")), False)
    raise ValueError("Unknown report.")


def totals_for(columns, rows):
    totals = {}
    for c in columns:
        if c["type"] in ("int", "qty", "money") and c["key"] not in ("rate_avg",):
            totals[c["key"]] = sum((Decimal(str(r.get(c["key"]) or 0)) for r in rows), ZERO)
    keys = {c["key"] for c in columns}
    if "share" in keys:
        totals["share"] = Decimal(100) if rows else ZERO
    if "margin" in keys:
        totals["margin"] = (totals["profit"] / totals["sales"] * 100) if totals.get("sales") else ZERO
    if "rate" in keys and "before" in keys:
        totals["rate"] = (totals["discount"] / totals["before"] * 100) if totals.get("before") else ZERO
    return totals


def shape(value, kind):
    if kind in ("money", "qty", "percent"):
        return str(Decimal(value or 0).quantize(CENT))
    if kind == "int":
        return int(value or 0)
    return "" if value is None else value


def shaped(columns, row):
    return {c["key"]: shape(row.get(c["key"]), c["type"]) for c in columns}


def parse_period(request):
    try:
        start = date.fromisoformat(request.GET.get("from", ""))
        end = date.fromisoformat(request.GET.get("to", ""))
    except ValueError:
        raise ValueError("Choose a from and to date.")
    if end < start:
        raise ValueError("The to date is before the from date.")
    if (end - start).days >= MAX_DAYS:
        raise ValueError("Choose a period of up to one year.")
    return start, end


@api_login_required
@require_GET
def run_report(request):
    report = request.GET.get("report", "")
    try:
        start, end = parse_period(request)
        title, columns, rows, chart, notes, dated = run(request, report, start, end)
        totals = totals_for(columns, rows)
        previous = None
        if dated and request.GET.get("compare") in ("1", "true"):
            length = (end - start).days + 1
            prev_end = start - timedelta(days=1)
            prev_start = prev_end - timedelta(days=length - 1)
            _, p_columns, p_rows, _, _, _ = run(request, report, prev_start, prev_end)
            p_totals = totals_for(p_columns, p_rows)
            previous = {"period": {"from": prev_start.isoformat(), "to": prev_end.isoformat()},
                        "totals": {k: shape(v, next(c["type"] for c in p_columns if c["key"] == k)) for k, v in p_totals.items()}}
    except PermissionError as exc:
        return R.forbidden(message=str(exc), request=request)
    except ValueError as exc:
        return R.validation_error(message=str(exc), request=request)
    kinds = {c["key"]: c["type"] for c in columns}
    return R.success(data={
        "id": report, "title": title, "dated": dated,
        "period": {"from": start.isoformat(), "to": end.isoformat()},
        "columns": columns,
        "rows": [shaped(columns, r) for r in rows],
        "totals": {k: shape(v, kinds[k]) for k, v in totals.items()},
        "previous": previous, "chart": chart, "notes": notes,
    }, request=request)
