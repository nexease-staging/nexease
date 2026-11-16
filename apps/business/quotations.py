from datetime import date
from decimal import Decimal
from uuid import uuid4

from django.views.decorators.http import require_http_methods
from apps.core.api.decorators import api_login_required
from apps.core.services.api_response_service import APIResponseService as R
from .models import BusinessRecord
from .payroll import amount, money
from .views import payload, permitted


def price_quote(raw):
    customer = raw.get("customer", {})
    party = customer.get("name", "") if isinstance(customer, dict) else ""
    if not isinstance(party, str) or not 1 <= len(party.strip()) <= 200:
        raise ValueError("Enter the customer name.")
    when = date.fromisoformat(raw.get("invoice_date", ""))
    expiry = raw.get("due_date") or ""
    if expiry and date.fromisoformat(expiry) < when:
        raise ValueError("Validity must extend through the quotation date.")
    source = raw.get("items")
    if not isinstance(source, list) or not 1 <= len(source) <= 100:
        raise ValueError("Add between 1 and 100 items.")
    lines = []
    total = Decimal(0)
    for item in source:
        if not isinstance(item, dict):
            raise ValueError("Invalid quotation item.")
        name = item.get("name")
        if not isinstance(name, str) or not 1 <= len(name.strip()) <= 200:
            raise ValueError("Enter an item name.")
        qty = amount(item.get("quantity"), "Quantity")
        rate = amount(item.get("unit_price"), "Price")
        discount = amount(item.get("discount", 0), "Discount")
        tax = amount(item.get("tax_rate", 0), "Tax rate", "100")
        if qty <= 0 or any(v != v.quantize(Decimal(".01")) for v in (qty, rate, discount, tax)):
            raise ValueError("Use positive quantities and at most two decimal places.")
        net = Decimal(money(qty * rate)) - discount
        if net < 0:
            raise ValueError("Discount exceeds item value.")
        gross = net + Decimal(money(net * tax / 100))
        total += gross
        lines.append(dict(name=name.strip(), quantity=str(qty), unit_price=money(rate), discount=money(discount),
                          tax_rate=str(tax), total=money(gross)))
    return dict(customer=party.strip(), date=when.isoformat(), valid_until=expiry, items=lines,
                total=money(total), notes=str(raw.get("notes", ""))[:1000])


@api_login_required
@require_http_methods(["GET", "POST"])
def quotations(request):
    if not permitted(request, "invoices.create" if request.method == "POST" else "invoices.read"):
        return R.forbidden(message="Sales permission required.", request=request)
    records = BusinessRecord.objects(organization=request.api_organization, kind="quotation")
    try:
        if request.method == "POST":
            data = price_quote(payload(request))
            quote = BusinessRecord(organization=request.api_organization, kind="quotation",
                                   key="EST-" + uuid4().hex[:12].upper(), data=data, created_by=request.api_user).save()
            return R.success(data={"number": quote.key}, request=request)
        page = max(1, int(request.GET.get("page", "1")))
        rows = list(records.order_by("-created_at", "-id").skip((page-1)*25).limit(26))
        return R.success(data={"rows": [dict(number=x.key, **x.data) for x in rows[:25]], "more": len(rows)>25}, request=request)
    except (ValueError, TypeError) as exc:
        return R.validation_error(message=str(exc), request=request)
