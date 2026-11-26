"""Inventory insights: stock value, low stock with reorder suggestions, out of stock and dead stock.

GET /api/v1/business/inventory-insights/?dead_days=90&warehouse_id=<id>

All figures are organisation-scoped. Valuation uses each product's cost price; products
without a cost price are counted as "unvalued" so the total is never silently understated.
"""

from datetime import datetime, timedelta
from decimal import Decimal

from bson import ObjectId
from django.views.decorators.http import require_http_methods

from apps.core.api.decorators import api_login_required
from apps.core.services.api_response_service import APIResponseService as R
from apps.inventory.models import Inventory, StockMovement, Warehouse
from apps.products.models import Product
from apps.purchasing.models import PurchaseOrder

from .models import BusinessRecord as Record
from .views import permitted

LIST_LIMIT = 200
CENT = Decimal("0.01")


def money(value):
    return str(Decimal(value).quantize(CENT))


def qty(value):
    return str(Decimal(value).quantize(CENT))


def suggested_quantity(level, available):
    """Order enough to come back up to twice the reorder level (a simple min/max rule)."""
    target = level * 2
    return max(target - available, Decimal(0)).quantize(CENT)


def last_suppliers(org, product_ids):
    """Most recent purchase-order supplier and rate per product, newest orders first."""
    wanted = set(product_ids)
    found = {}
    if not wanted:
        return found
    orders = (
        PurchaseOrder.objects(organization=org, status__ne="CANCELLED", items__product__in=list(wanted))
        .order_by("-order_date", "-id")
        .limit(500)
    )
    for order in orders:
        for item in order.items:
            pid = item.product.id if item.product else None
            if pid in wanted and pid not in found and order.supplier:
                found[pid] = {
                    "id": str(order.supplier.id),
                    "code": order.supplier.code,
                    "name": order.supplier.name,
                    "last_rate": money(item.unit_price or 0),
                    "last_po": order.po_number,
                }
        if len(found) == len(wanted):
            break
    return found


@api_login_required
@require_http_methods(["GET"])
def insights(request):
    if not permitted(request, "inventory.read"):
        return R.forbidden(message="Inventory read permission required.", request=request)
    try:
        org = request.api_organization
        dead_days = int(request.GET.get("dead_days") or 90)
        if not 7 <= dead_days <= 730:
            raise ValueError("dead_days must be between 7 and 730.")
        warehouse = None
        if request.GET.get("warehouse_id"):
            if not ObjectId.is_valid(request.GET["warehouse_id"]):
                raise ValueError("Unknown warehouse.")
            warehouse = Warehouse.objects(organization=org, id=request.GET["warehouse_id"]).first()
            if not warehouse:
                raise ValueError("Unknown warehouse.")

        products = {p.id: p for p in Product.objects(organization=org, is_active=True, item_type="goods")}
        balances = Inventory.objects(organization=org, **({"warehouse": warehouse} if warehouse else {}))
        on_hand = {pid: Decimal(0) for pid in products}
        reserved = {pid: Decimal(0) for pid in products}
        by_warehouse = {}
        unvalued = set()
        for row in balances:
            pid = row.product.id if row.product else None
            if pid not in products:
                continue
            q = Decimal(row.quantity or 0)
            on_hand[pid] += q
            reserved[pid] += Decimal(row.reserved_quantity or 0)
            cost = products[pid].cost_price
            if q > 0 and not cost:
                unvalued.add(pid)
            w = by_warehouse.setdefault(row.warehouse.id, {"id": str(row.warehouse.id), "name": row.warehouse.name, "code": row.warehouse.code, "value": Decimal(0), "units": Decimal(0)})
            if q > 0:
                w["value"] += q * Decimal(cost or 0)
                w["units"] += q

        levels = {}
        for record in Record.objects(organization=org, kind="reorder_rule"):
            data = record.data or {}
            if data.get("enabled", True) and ObjectId.is_valid(record.key):
                levels[ObjectId(record.key)] = Decimal(str(data.get("level", "0")))

        total_value = sum((max(on_hand[pid], Decimal(0)) * Decimal(p.cost_price or 0) for pid, p in products.items()), Decimal(0))
        available = {pid: on_hand[pid] - reserved[pid] for pid in products}

        low = []
        for pid, level in levels.items():
            if pid in products and level > 0 and available[pid] <= level:
                low.append((pid, level))
        low.sort(key=lambda item: (available[item[0]] - item[1], products[item[0]].name.lower()))
        low = low[:LIST_LIMIT]
        suppliers = last_suppliers(org, [pid for pid, _ in low])

        cutoff = datetime.utcnow() - timedelta(days=dead_days)
        match = {"organization": org.id}
        if warehouse:
            match["warehouse"] = warehouse.id
        last_moved = {
            row["_id"]: row["last"]
            for row in StockMovement.objects.aggregate([{"$match": match}, {"$group": {"_id": "$product", "last": {"$max": "$created_at"}}}])
        }
        dead = [pid for pid in products if on_hand[pid] > 0 and (last_moved.get(pid) is None or last_moved[pid] < cutoff)]
        dead.sort(key=lambda pid: -(on_hand[pid] * Decimal(products[pid].cost_price or 0)))

        def item(pid):
            p = products[pid]
            return {
                "product_id": str(pid),
                "sku": p.sku,
                "name": p.name,
                "unit": p.unit,
                "cost_price": money(p.cost_price or 0),
                "on_hand": qty(on_hand[pid]),
                "reserved": qty(reserved[pid]),
                "available": qty(available[pid]),
            }

        data = {
            "as_of": datetime.utcnow().isoformat() + "Z",
            "warehouse_id": str(warehouse.id) if warehouse else None,
            "dead_days": dead_days,
            "summary": {
                "stock_value": money(total_value),
                "products": len(products),
                "in_stock": sum(1 for pid in products if available[pid] > 0),
                "out_of_stock": sum(1 for pid in products if available[pid] <= 0),
                "low_stock": len([1 for pid, level in levels.items() if pid in products and level > 0 and available[pid] <= level]),
                "dead_stock": len(dead),
                "dead_stock_value": money(sum((on_hand[pid] * Decimal(products[pid].cost_price or 0) for pid in dead), Decimal(0))),
                "unvalued_products": len(unvalued),
            },
            "by_warehouse": sorted(
                ({**w, "value": money(w["value"]), "units": qty(w["units"])} for w in by_warehouse.values()),
                key=lambda w: -Decimal(w["value"]),
            ),
            "low_stock": [
                {
                    **item(pid),
                    "reorder_level": qty(level),
                    "suggested_quantity": qty(suggested_quantity(level, available[pid])),
                    "supplier": suppliers.get(pid),
                }
                for pid, level in low
            ],
            "dead_stock": [
                {
                    **item(pid),
                    "value": money(on_hand[pid] * Decimal(products[pid].cost_price or 0)),
                    "last_movement": last_moved[pid].isoformat() + "Z" if last_moved.get(pid) else None,
                }
                for pid in dead[:LIST_LIMIT]
            ],
        }
        return R.success(data=data, request=request)
    except ValueError as exc:
        return R.validation_error(message=str(exc), request=request)
