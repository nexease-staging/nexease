"""Sales and purchasing analysis from source document lines."""
from collections import defaultdict
from datetime import date, datetime, time
from decimal import Decimal

from django.views.decorators.http import require_GET
from apps.core.api.decorators import api_login_required
from apps.core.services.api_response_service import APIResponseService as R
from apps.sales.models import Invoice, SalesOrder
from apps.purchasing.models import VendorBill, PurchaseOrder
from .models import BusinessRecord
from .views import permitted

SOURCES = {
    "sales": (Invoice, "invoice_date", "invoice_number", "invoices.read"),
    "purchases": (VendorBill, "bill_date", "bill_number", "bills.read"),
    "sales-orders": (SalesOrder, "order_date", "so_number", "sales_orders.read"),
    "purchase-orders": (PurchaseOrder, "order_date", "po_number", "purchase_orders.read"),
}
GROUPS = {"document", "party", "item", "party-item", "category", "discount", "item-discount", "hsn", "sac", "rate"}


@api_login_required
@require_GET
def report(request):
    try:
        source = request.GET.get("source", "sales")
        group = request.GET.get("group", "document")
        start = date.fromisoformat(request.GET.get("from", ""))
        end = date.fromisoformat(request.GET.get("to", ""))
        if end < start or (end-start).days > 366:
            raise ValueError("Select a date range of up to 367 days.")
        org = request.api_organization
        if source=="inventory" and group in {"low","category"}:
            from apps.inventory.models import Inventory
            from apps.products.models import Product
            if not permitted(request,"inventory.read"):
                return R.forbidden(message="Inventory read permission required.",request=request)
            stock = defaultdict(Decimal)
            for entry in Inventory.objects(organization=org).no_dereference().only("product","quantity"):
                ref = entry.product
                stock[str(getattr(ref,"id",ref))] += entry.quantity
            levels = {r.key:Decimal(r.data["level"]) for r in BusinessRecord.objects(organization=org,kind="reorder_rule",data__enabled=True)}
            by_unit = defaultdict(Decimal)
            rows = []
            for product in Product.objects(organization=org,is_active=True,item_type="goods"):
                qty = stock[str(product.id)]
                if group=="category":
                    by_unit[(product.category.name,product.unit)] += qty
                elif str(product.id) in levels and qty < levels[str(product.id)]:
                    rows.append([product.sku,product.name,product.unit,str(qty),str(levels[str(product.id)])])
            if group=="category":
                rows=[[cat,unit,str(qty)] for (cat,unit),qty in sorted(by_unit.items())]
            return R.success(data={"columns":["Category","Unit","Current stock"] if group=="category" else ["SKU","Item","Unit","Current stock","Reorder level"],"rows":rows},request=request)
        if source == "expenses" and group in {"document", "category", "item"}:
            if not permitted(request, "expenses.read"):
                return R.forbidden(message="Expense read permission required.", request=request)
            rows = defaultdict(Decimal)
            for entry in BusinessRecord.objects(organization=org, kind="expenses", data__date__gte=start.isoformat(), data__date__lte=end.isoformat()):
                d = entry.data
                label = entry.key if group=="document" else d.get("category" if group=="category" else "description") or "Unclassified"
                rows[label] += Decimal(d["amount"])
            return R.success(data={"columns":["Expense", "Amount"], "rows":[[k,str(v)] for k,v in sorted(rows.items())]},request=request)
        if source not in SOURCES or group not in GROUPS:
            raise ValueError("Unknown report.")
        model, date_field, number_field, permission = SOURCES[source]
        if not permitted(request, permission):
            return R.forbidden(message="Source document read permission required.", request=request)
        if group in {"hsn","sac","rate"} and not permitted(request,"taxation.read"):
            return R.forbidden(message="Taxation read permission required.", request=request)
        query = {date_field+"__gte":datetime.combine(start,time.min), date_field+"__lte":datetime.combine(end,time.max)}
        documents = model.objects(organization=org, **query)
        if source in {"sales","purchases"}:
            documents = documents.filter(status__in=["ISSUED" if source=="sales" else "POSTED", "PAID","PARTIALLY_PAID"])
        else:
            documents = documents.filter(status__ne="CANCELLED")
        totals = defaultdict(lambda: [Decimal(0)]*4)
        for document in documents:
            number = getattr(document,number_field)
            for line in document.items:
                if group in {"discount","item-discount"} and not line.discount:
                    continue
                key = number
                if group in {"item","party-item","item-discount"}:
                    key = getattr(line,"item_name","") or line.product.name
                if group in {"party","party-item"}:
                    party = document.customer if source.startswith("sales") else document.supplier
                    key = party.name if group=="party" else f"{party.name} · {key}"
                if group=="category":
                    key = line.product.category.name
                if group in {"hsn","sac"}:
                    if getattr(line,"item_type","goods") != ("service" if group=="sac" else "goods"):
                        continue
                    key = getattr(line, "hsn_code", "") or "Unclassified"
                if group=="rate":
                    key = f"{line.tax_rate}%"
                row = totals[key]
                gross, tax = (line.total, line.tax_amount) if source=="purchase-orders" else (line.line_total, line.line_tax)
                row[0] += gross-tax
                row[1] += line.discount
                row[2] += tax
                row[3] += gross
        return R.success(data={"columns":[group.replace("-"," ").title(),"Net before tax","Discount","Tax","Total"],
                               "rows":[[k,*map(str,v)] for k,v in sorted(totals.items())]},request=request)
    except (TypeError,ValueError) as exc:
        return R.validation_error(message=str(exc),request=request)
