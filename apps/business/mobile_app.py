"""Phone app screens: transaction lists, the dashboard tab, items with stock, and a document sheet.

Read-only and permission-aware like mobile_home. Every list is paginated and searchable so the
phone never downloads more than a screen needs.
"""
import re
from datetime import timedelta
from decimal import Decimal

from django.views.decorators.http import require_http_methods
from mongoengine.queryset.visitor import Q

from apps.core.api.decorators import api_login_required
from apps.core.services.api_response_service import APIResponseService as R
from apps.purchasing.models import Supplier, SupplierPayment, VendorBill
from apps.sales.models import Customer, CustomerPayment, Invoice

from .mobile_home import BILL_STATUSES, SALE_STATUSES, _day, _names, _outstanding, _utc_range
from .payments_hub import SIDES, money, today_ist
from .views import permitted

PAGE = 30


def _page(request):
    try:
        return max(0, int(request.GET.get("page") or 0))
    except ValueError:
        return 0


def _term(request):
    return (request.GET.get("search") or "").strip()[:80]


def _party_ids(Model, org, term):
    return [p.id for p in Model.objects(organization=org).filter(Q(name__icontains=term) | Q(phone__icontains=term) | Q(gstin__icontains=term)).only("id").limit(200)]


def _rows_sales(request, org, term, page, status):
    qs = Invoice.objects(organization=org)
    if status == "due":
        qs = qs.filter(status__in=["ISSUED", "PARTIALLY_PAID"])
    elif status:
        qs = qs.filter(status=status.upper())
    if term:
        qs = qs.filter(Q(invoice_number__icontains=term) | Q(billing_name__icontains=term) | Q(customer__in=_party_ids(Customer, org, term)))
    docs = list(qs.only("id", "invoice_number", "customer", "billing_name", "invoice_date", "due_date", "total_amount", "balance_due", "status").order_by("-invoice_date", "-created_at").skip(page * PAGE).limit(PAGE + 1))
    names = _names(Customer, [d._data.get("customer") for d in docs])
    out = []
    for d in docs[:PAGE]:
        ref = d._data.get("customer")
        out.append({"type": "sale", "id": str(d.id), "number": d.invoice_number, "party": names.get(getattr(ref, "id", ref), "") or d.billing_name or "",
                    "party_id": str(getattr(ref, "id", ref) or ""), "date": _day(d.invoice_date), "due_date": _day(getattr(d, "due_date", None)),
                    "amount": money(d.total_amount), "balance": money(d.balance_due), "status": d.status})
    return out, len(docs) > PAGE


def _rows_purchases(request, org, term, page, status):
    qs = VendorBill.objects(organization=org)
    if status == "due":
        qs = qs.filter(status__in=["POSTED", "PARTIALLY_PAID"])
    elif status:
        qs = qs.filter(status=status.upper())
    if term:
        qs = qs.filter(Q(bill_number__icontains=term) | Q(supplier_invoice_number__icontains=term) | Q(supplier__in=_party_ids(Supplier, org, term)))
    docs = list(qs.only("id", "bill_number", "supplier_invoice_number", "supplier", "bill_date", "due_date", "total_amount", "balance_due", "status").order_by("-bill_date", "-created_at").skip(page * PAGE).limit(PAGE + 1))
    names = _names(Supplier, [d._data.get("supplier") for d in docs])
    out = []
    for d in docs[:PAGE]:
        ref = d._data.get("supplier")
        out.append({"type": "purchase", "id": str(d.id), "number": d.supplier_invoice_number or d.bill_number, "party": names.get(getattr(ref, "id", ref), ""),
                    "party_id": str(getattr(ref, "id", ref) or ""), "date": _day(d.bill_date), "due_date": _day(getattr(d, "due_date", None)),
                    "amount": money(d.total_amount), "balance": money(d.balance_due), "status": d.status})
    return out, len(docs) > PAGE


def _rows_payments(request, org, term, page, direction):
    Model, Party, field = (CustomerPayment, Customer, "customer") if direction == "payment_in" else (SupplierPayment, Supplier, "supplier")
    qs = Model.objects(organization=org)
    if term:
        qs = qs.filter(Q(payment_number__icontains=term) | Q(reference_number__icontains=term) | Q(**{f"{field}__in": _party_ids(Party, org, term)}))
    docs = list(qs.only("id", "payment_number", field, "payment_date", "amount", "payment_method").order_by("-payment_date").skip(page * PAGE).limit(PAGE + 1))
    names = _names(Party, [d._data.get(field) for d in docs])
    out = []
    for d in docs[:PAGE]:
        ref = d._data.get(field)
        out.append({"type": direction, "id": str(d.id), "number": d.payment_number, "party": names.get(getattr(ref, "id", ref), ""), "party_id": str(getattr(ref, "id", ref) or ""),
                    "date": _day(d.payment_date), "due_date": None, "amount": money(d.amount), "balance": None, "status": (d.payment_method or "").replace("_", " ").title()})
    return out, len(docs) > PAGE


def _rows_expenses(request, org, term, page, status):
    from .models import BusinessRecord
    qs = BusinessRecord.objects(organization=org, kind="expenses")
    if term:
        rx = re.compile(re.escape(term), re.I)
        qs = qs.filter(Q(data__payee=rx) | Q(data__category=rx) | Q(data__description=rx) | Q(data__reference=rx))
    docs = list(qs.order_by("-created_at").skip(page * PAGE).limit(PAGE + 1))
    out = []
    for r in docs[:PAGE]:
        d = r.data or {}
        out.append({"type": "expense", "id": str(r.id), "number": d.get("reference", "") or r.key, "party": d.get("payee", "") or d.get("category", "") or "Expense", "party_id": "",
                    "date": d.get("date"), "due_date": None, "amount": money(Decimal(str(d.get("amount") or 0))), "balance": None,
                    "status": d.get("category", ""), "note": d.get("description", ""), "mode": d.get("payment_mode", "")})
    return out, len(docs) > PAGE


LISTS = {"sale": (("invoices.read",), _rows_sales), "purchase": (("bills.read",), _rows_purchases), "expense": (("expenses.read", "expenses.manage"), _rows_expenses),
         "payment_in": (("invoices.read", "customer_payments.read"), lambda r, o, t, p, s: _rows_payments(r, o, t, p, "payment_in")),
         "payment_out": (("bills.read",), lambda r, o, t, p, s: _rows_payments(r, o, t, p, "payment_out"))}


@api_login_required
@require_http_methods(["GET"])
def transactions(request):
    kind = request.GET.get("type", "sale")
    if kind not in LISTS:
        return R.validation_error(message="Unknown list.", request=request)
    perms, fn = LISTS[kind]
    if not any(permitted(request, p) for p in perms):
        return R.forbidden(message="You do not have access to this list.", request=request)
    rows, more = fn(request, request.api_organization, _term(request), _page(request), (request.GET.get("status") or "").strip().lower())
    return R.success(data={"type": kind, "rows": rows, "page": _page(request), "more": more}, request=request)


def _month_starts(today, n):
    out, d = [], today.replace(day=1)
    for _ in range(n):
        out.append(d)
        d = (d - timedelta(days=1)).replace(day=1)
    return list(reversed(out))


@api_login_required
@require_http_methods(["GET"])
def dashboard(request):
    org = request.api_organization
    today = today_ist()
    months = _month_starts(today, 6)
    data = {"as_of": today.isoformat(), "receivable": None, "payable": None, "overdue_receivable": None, "trend": [], "top_dues": [], "banks": [], "tally": None,
            "sales_month": None, "purchases_month": None, "sales_prev": None}
    sales_ok, bills_ok = permitted(request, "invoices.read"), permitted(request, "bills.read")
    trend = []
    for i, start in enumerate(months):
        end = (months[i + 1] - timedelta(days=1)) if i + 1 < len(months) else today
        lo, hi = _utc_range(start, end)
        row = {"month": start.isoformat()[:7], "sales": None, "purchases": None}
        if sales_ok:
            row["sales"] = money(sum((Decimal(str(d.total_amount or 0)) for d in Invoice.objects(organization=org, status__in=SALE_STATUSES, invoice_date__gte=lo, invoice_date__lt=hi).only("total_amount")), Decimal(0)))
        if bills_ok:
            row["purchases"] = money(sum((Decimal(str(d.total_amount or 0)) for d in VendorBill.objects(organization=org, status__in=BILL_STATUSES, bill_date__gte=lo, bill_date__lt=hi).only("total_amount")), Decimal(0)))
        trend.append(row)
    data["trend"] = trend
    if sales_ok:
        rec = _outstanding(org, SIDES["receivable"])
        data["receivable"] = money(sum((p["balance"] for p in rec.values()), Decimal(0)))
        data["overdue_receivable"] = money(sum((p["overdue"] for p in rec.values()), Decimal(0)))
        data["sales_month"], data["sales_prev"] = trend[-1]["sales"], trend[-2]["sales"]
        top = sorted(rec.items(), key=lambda kv: -kv[1]["balance"])[:5]
        names = {str(c.id): (c.name, c.phone or "") for c in Customer.objects(organization=org, id__in=[k for k, _ in top]).only("id", "name", "phone")} if top else {}
        data["top_dues"] = [{"id": k, "name": names.get(k, ("", ""))[0], "phone": names.get(k, ("", ""))[1], "balance": money(v["balance"]), "overdue": money(v["overdue"])}
                            for k, v in top if v["balance"] > 0]
    if bills_ok:
        data["payable"] = money(sum((p["balance"] for p in _outstanding(org, SIDES["payable"]).values()), Decimal(0)))
        data["purchases_month"] = trend[-1]["purchases"]
    if permitted(request, "accounting_reports.read") or permitted(request, "bank_accounts.read"):
        from apps.finance.models import BankAccount
        data["banks"] = [{"id": str(b.id), "name": b.account_name, "type": b.account_type, "balance": money(b.current_balance)}
                         for b in BankAccount.objects(organization=org, is_active=True).only("id", "account_name", "account_type", "current_balance").limit(8)]
        from mongoengine.connection import get_db
        company = get_db().tally_companies.find_one({"org_id": str(org.id), "enabled": True})
        if company:
            state = get_db().tally_state.find_one({"_id": str(org.id)}) or {}
            seen = state.get("tally_seen_at")
            data["tally"] = {"company": company["name"], "last_seen": seen.isoformat() + "Z" if seen else None}
    return R.success(data=data, request=request)


@api_login_required
@require_http_methods(["GET"])
def items(request):
    if not permitted(request, "products.read"):
        return R.forbidden(message="You do not have access to items.", request=request)
    from apps.inventory.models import Inventory
    from apps.products.models import Product
    org = request.api_organization
    qs = Product.objects(organization=org, is_active=True)
    kind = request.GET.get("type")
    if kind in ("goods", "service"):
        qs = qs.filter(item_type=kind)
    term = _term(request)
    if term:
        qs = qs.filter(Q(name__icontains=term) | Q(sku__icontains=term) | Q(hsn_code__icontains=term) | Q(barcode=term))
    page = _page(request)
    docs = list(qs.only("id", "name", "sku", "unit", "hsn_code", "selling_price", "item_type").order_by("name").skip(page * PAGE).limit(PAGE + 1))
    stock = {}
    if docs:
        pipeline = [{"$match": {"organization": org.id, "product": {"$in": [d.id for d in docs]}}}, {"$group": {"_id": "$product", "qty": {"$sum": {"$toDecimal": "$quantity"}}}}]
        try:
            stock = {str(r["_id"]): Decimal(str(r["qty"])) for r in Inventory._get_collection().aggregate(pipeline)}
        except Exception:  # stores without the aggregation operator: add up in Python
            for inv in Inventory.objects(organization=org, product__in=[d.id for d in docs]).only("product", "quantity"):
                pid = str(inv._data.get("product").id if hasattr(inv._data.get("product"), "id") else inv._data.get("product"))
                stock[pid] = stock.get(pid, Decimal(0)) + Decimal(str(inv.quantity or 0))
    rows = [{"id": str(d.id), "name": d.name, "sku": d.sku, "unit": d.unit, "hsn": d.hsn_code or "", "price": money(d.selling_price), "type": d.item_type,
             "stock": (f"{stock.get(str(d.id), Decimal(0)).normalize():f}" if d.item_type != "service" else None)} for d in docs[:PAGE]]
    return R.success(data={"rows": rows, "page": page, "more": len(docs) > PAGE}, request=request)


@api_login_required
@require_http_methods(["GET"])
def document(request):
    """One sale or purchase for the phone sheet: party contact, lines, totals and what can be done next."""
    kind, ident = request.GET.get("type"), request.GET.get("id", "")
    from bson import ObjectId
    if kind not in ("sale", "purchase") or not ObjectId.is_valid(ident):
        return R.not_found(message="Document not found.", request=request)
    org = request.api_organization
    if kind == "sale":
        if not permitted(request, "invoices.read"):
            return R.forbidden(request=request)
        d = Invoice.objects(organization=org, id=ident).first()
        party, number, when = (d.customer if d else None), (d.invoice_number if d else ""), (d.invoice_date if d else None)
    else:
        if not permitted(request, "bills.read"):
            return R.forbidden(request=request)
        d = VendorBill.objects(organization=org, id=ident).first()
        party, number, when = (d.supplier if d else None), ((d.supplier_invoice_number or d.bill_number) if d else ""), (d.bill_date if d else None)
    if not d:
        return R.not_found(message="Document not found.", request=request)
    lines = []
    for it in d.items or []:
        product = getattr(it, "product", None)
        name = getattr(it, "item_name", "") or (getattr(product, "name", "") if product else "") or "Item"
        lines.append({"name": name, "qty": f"{Decimal(str(it.quantity or 0)).normalize():f}", "unit": getattr(it, "unit", "") or (getattr(product, "unit", "") if product else ""),
                      "rate": money(it.unit_price), "tax_rate": f"{Decimal(str(getattr(it, 'tax_rate', 0) or 0)).normalize():f}",
                      "amount": money(getattr(it, "line_total", None) or getattr(it, "total", None) or 0)})
    balance = Decimal(str(d.balance_due or 0))
    live = d.status not in ("DRAFT", "CANCELLED")
    data = {"type": kind, "id": str(d.id), "number": number, "status": d.status, "date": _day(when), "due_date": _day(getattr(d, "due_date", None)),
            "party": {"id": str(party.id) if party else "", "name": getattr(party, "name", "") if party else (getattr(d, "billing_name", "") or ""),
                      "phone": getattr(party, "phone", "") or "" if party else "", "email": getattr(party, "email", "") or "" if party else ""},
            "subtotal": money(getattr(d, "subtotal", None) or 0), "tax": money(d.tax_amount), "discount": money(getattr(d, "discount_amount", None) or 0),
            "total": money(d.total_amount), "paid": money(Decimal(str(d.total_amount or 0)) - balance), "balance": money(balance), "lines": lines,
            "can_pay": live and balance > 0 and permitted(request, "invoices.record_payment" if kind == "sale" else "bills.record_payment"),
            "href": ("/invoices?view=" if kind == "sale" else "/vendor-bills?view=") + str(d.id)}
    return R.success(data=data, request=request)
