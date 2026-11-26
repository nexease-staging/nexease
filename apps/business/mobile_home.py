"""Phone home screen and parties list: balances, today's numbers and a recent-activity feed.

Read-only. Every figure respects the caller's permissions: a section the user cannot read is
returned as null (numbers) or left out (feed rows).
"""
from datetime import datetime, time, timedelta
from decimal import Decimal

from django.views.decorators.http import require_http_methods
from mongoengine.queryset.visitor import Q

from apps.core.api.decorators import api_login_required
from apps.core.services.api_response_service import APIResponseService as R
from apps.purchasing.models import Supplier, SupplierPayment, VendorBill
from apps.sales.models import Customer, CustomerPayment, Invoice

from .payments_hub import IST, SIDES, money, today_ist
from .views import permitted

CENT = Decimal("0.01")
SALE_STATUSES = ("ISSUED", "PARTIALLY_PAID", "PAID")
BILL_STATUSES = ("POSTED", "PARTIALLY_PAID", "PAID")
FEED_SIZE = 25


def _utc_range(start, end):
    """IST calendar days [start, end] as UTC datetimes, the way documents store dates."""
    return datetime.combine(start, time.min) - IST, datetime.combine(end + timedelta(days=1), time.min) - IST


def _sum(qs, field="total_amount"):
    return sum((Decimal(str(getattr(d, field) or 0)) for d in qs.only(field)), Decimal(0)).quantize(CENT)


def _day(value):
    return (value + IST).date().isoformat() if value else None


def _outstanding(org, side):
    rows = side.rows(org, side.open_documents(org))
    by_party = {}
    for row in rows:
        p = by_party.setdefault(row["party_id"], {"balance": Decimal(0), "overdue": Decimal(0)})
        p["balance"] += row["outstanding"]
        if row["days_overdue"] > 0:
            p["overdue"] += row["outstanding"]
    return by_party


def _names(Model, refs):
    ids = {getattr(r, "id", r) for r in refs if r}
    return {p.id: p.name for p in Model.objects(id__in=list(ids)).only("id", "name")} if ids else {}


def _feed(request, org):
    rows = []
    if permitted(request, "invoices.read"):
        docs = list(Invoice.objects(organization=org).only("id", "invoice_number", "customer", "invoice_date", "total_amount", "balance_due", "status", "created_at").order_by("-created_at").limit(FEED_SIZE))
        names = _names(Customer, [d._data.get("customer") for d in docs])
        for d in docs:
            ref = d._data.get("customer")
            rows.append({"type": "sale", "id": str(d.id), "number": d.invoice_number, "party": names.get(getattr(ref, "id", ref), ""),
                         "date": _day(d.invoice_date), "amount": money(d.total_amount), "balance": money(d.balance_due), "status": d.status,
                         "href": "/invoices?view=" + str(d.id), "at": d.created_at})
    if permitted(request, "bills.read"):
        docs = list(VendorBill.objects(organization=org).only("id", "bill_number", "supplier", "bill_date", "total_amount", "balance_due", "status", "created_at").order_by("-created_at").limit(FEED_SIZE))
        names = _names(Supplier, [d._data.get("supplier") for d in docs])
        for d in docs:
            ref = d._data.get("supplier")
            rows.append({"type": "purchase", "id": str(d.id), "number": d.bill_number, "party": names.get(getattr(ref, "id", ref), ""),
                         "date": _day(d.bill_date), "amount": money(d.total_amount), "balance": money(d.balance_due), "status": d.status,
                         "href": "/vendor-bills?view=" + str(d.id), "at": d.created_at})
    for direction, Model, Party, field, permission in (("payment_in", CustomerPayment, Customer, "customer", ("invoices.read", "customer_payments.read")),
                                                       ("payment_out", SupplierPayment, Supplier, "supplier", ("bills.read",))):
        if not any(permitted(request, p) for p in permission):
            continue
        docs = list(Model.objects(organization=org).only("id", "payment_number", field, "payment_date", "amount", "payment_method", "created_at").order_by("-payment_date").limit(FEED_SIZE))
        names = _names(Party, [d._data.get(field) for d in docs])
        for d in docs:
            ref = d._data.get(field)
            rows.append({"type": direction, "id": str(d.id), "number": d.payment_number, "party": names.get(getattr(ref, "id", ref), ""),
                         "date": _day(d.payment_date), "amount": money(d.amount), "balance": None, "status": d.payment_method,
                         "href": "/payments", "at": getattr(d, "created_at", None) or d.payment_date})
    if permitted(request, "expenses.read") or permitted(request, "expenses.manage"):
        from .models import BusinessRecord
        for r in BusinessRecord.objects(organization=org, kind="expenses").order_by("-created_at").limit(FEED_SIZE):
            data = r.data or {}
            rows.append({"type": "expense", "id": str(r.id), "number": data.get("reference", ""), "party": data.get("payee", "") or data.get("category", ""),
                         "date": data.get("date"), "amount": money(Decimal(str(data.get("amount") or 0))), "balance": None, "status": data.get("category", ""),
                         "href": "/expenses", "at": getattr(r, "created_at", None)})
    rows.sort(key=lambda r: r["at"] or datetime.min, reverse=True)
    for r in rows:
        r.pop("at")
    return rows[:FEED_SIZE]


@api_login_required
@require_http_methods(["GET"])
def home(request):
    org = request.api_organization
    today = today_ist()
    month_start = today.replace(day=1)
    data = {"as_of": today.isoformat(), "receivable": None, "payable": None, "sales_today": None, "sales_month": None,
            "purchases_month": None, "money_in_month": None, "money_out_month": None}
    if permitted(request, "invoices.read"):
        data["receivable"] = money(sum((p["balance"] for p in _outstanding(org, SIDES["receivable"]).values()), Decimal(0)))
        lo, hi = _utc_range(today, today)
        data["sales_today"] = money(_sum(Invoice.objects(organization=org, status__in=SALE_STATUSES, invoice_date__gte=lo, invoice_date__lt=hi)))
        lo, hi = _utc_range(month_start, today)
        data["sales_month"] = money(_sum(Invoice.objects(organization=org, status__in=SALE_STATUSES, invoice_date__gte=lo, invoice_date__lt=hi)))
        data["money_in_month"] = money(_sum(CustomerPayment.objects(organization=org, payment_date__gte=lo, payment_date__lt=hi), "amount"))
    if permitted(request, "bills.read"):
        data["payable"] = money(sum((p["balance"] for p in _outstanding(org, SIDES["payable"]).values()), Decimal(0)))
        lo, hi = _utc_range(month_start, today)
        data["purchases_month"] = money(_sum(VendorBill.objects(organization=org, status__in=BILL_STATUSES, bill_date__gte=lo, bill_date__lt=hi)))
        data["money_out_month"] = money(_sum(SupplierPayment.objects(organization=org, payment_date__gte=lo, payment_date__lt=hi), "amount"))
    data["transactions"] = _feed(request, org)
    return R.success(data=data, request=request)


@api_login_required
@require_http_methods(["GET"])
def parties(request):
    org = request.api_organization
    customers = request.GET.get("side", "customers") != "suppliers"
    if not permitted(request, "customers.read" if customers else "suppliers.read"):
        return R.forbidden(message="You do not have access to this party list.", request=request)
    Party = Customer if customers else Supplier
    can_see_balance = permitted(request, "invoices.read" if customers else "bills.read")
    balances = _outstanding(org, SIDES["receivable" if customers else "payable"]) if can_see_balance else {}
    qs = Party.objects(organization=org, is_active=True)
    term = (request.GET.get("search") or "").strip()
    if term:
        qs = qs.filter(Q(name__icontains=term) | Q(code__icontains=term) | Q(phone__icontains=term) | Q(gstin__icontains=term))
    rows = []
    for p in qs.only("id", "name", "code", "phone", "email", "gstin", "city").limit(500):
        b = balances.get(str(p.id), {"balance": Decimal(0), "overdue": Decimal(0)})
        rows.append({"id": str(p.id), "name": p.name, "code": p.code, "phone": p.phone or "", "email": p.email or "", "gstin": p.gstin or "",
                     "city": getattr(p, "city", "") or "", "balance": money(b["balance"]) if can_see_balance else None,
                     "overdue": money(b["overdue"]) if can_see_balance else None})
    rows.sort(key=lambda r: (-(Decimal(r["balance"]) if r["balance"] else Decimal(0)), r["name"].lower()))
    total = sum((Decimal(r["balance"]) for r in rows if r["balance"]), Decimal(0))
    return R.success(data={"side": "customers" if customers else "suppliers", "parties": rows, "count": len(rows),
                           "total_balance": money(total) if can_see_balance else None, "with_balance": sum(1 for r in rows if r["balance"] and Decimal(r["balance"]) > 0)}, request=request)
