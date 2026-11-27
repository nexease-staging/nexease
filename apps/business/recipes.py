"""Item recipes: the bill of materials for an item and whether it is made to order.

A made-to-order item (a custom almirah, a fabricated gate, a printed banner) is never kept as finished
stock. Selling it uses up its raw materials instead:

* sales orders skip the finished-stock reservation and dispatch for it, the same way they treat services;
* quick and direct invoices take its recipe's raw materials out of stock (and put them back if the invoice
  is cancelled or edited), using the recipe as it was on the day of the invoice;
* invoices raised from a production job take nothing, because the job already used the materials.
"""

from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

from bson import ObjectId
from django.views.decorators.http import require_http_methods
from mongoengine.connection import get_db

from apps.core.api.decorators import api_login_required
from apps.core.services.api_response_service import APIResponseService as R
from apps.products.models import Product
from .views import payload, permitted

MAX_MATERIALS = 60


def _col():
    return get_db().product_recipes


def _oid(value):
    if isinstance(value, ObjectId):
        return value
    if not isinstance(value, str) or not ObjectId.is_valid(value):
        raise ValueError("Select a valid item.")
    return ObjectId(value)


def quantity(value, label, positive=True, places=3):
    try:
        n = Decimal(str(value).strip())
    except (InvalidOperation, AttributeError):
        raise ValueError(f"Enter a number for {label}.")
    if not n.is_finite() or n < 0 or (positive and n == 0):
        raise ValueError(f"Enter a {'positive ' if positive else ''}number for {label}.")
    if n != n.quantize(Decimal(1).scaleb(-places)):
        raise ValueError(f"Use up to {places} decimals for {label}.")
    if n > Decimal("100000000"):
        raise ValueError(f"{label.capitalize()} is too large.")
    return n


def recipe(org_id, product_id):
    return _col().find_one({"organization": _oid(org_id), "product": _oid(product_id)})


def made_to_order_ids(org_id, product_ids):
    ids = [_oid(p) for p in product_ids if p]
    if not ids:
        return set()
    rows = _col().find({"organization": _oid(org_id), "product": {"$in": ids}, "made_to_order": True}, {"product": 1})
    return {str(r["product"]) for r in rows}


def stockless(product):
    """Services and made-to-order items are never reserved or dispatched as finished stock."""
    if product is None or getattr(product, "item_type", "goods") == "service":
        return True
    org = getattr(product.organization, "id", product.organization)
    return bool(made_to_order_ids(org, [product.id]))


def snapshot(org_id, items):
    """Recipe materials for each made-to-order line, frozen when the invoice moves stock."""
    ids = {str(i.product.id) for i in items if getattr(i, "item_type", "goods") == "goods" and i.product}
    mto = made_to_order_ids(org_id, ids)
    frozen = {}
    for pid in mto:
        row = recipe(org_id, pid)
        frozen[pid] = [dict(product=m["product"], per_unit=m["per_unit"]) for m in (row or {}).get("materials", [])]
    return frozen


def expand(org_id, items, frozen):
    """Stock lines for invoice items: goods move themselves, made-to-order items move their materials.

    Returns [(Product, quantity, made_for_product_id or None)]. Lines without a product reference and
    services are skipped. A made-to-order item without materials moves nothing.
    """
    out = []
    cache = {}

    def load(pid):
        if pid not in cache:
            cache[pid] = Product.objects(organization=org_id, id=_oid(pid)).first()
        return cache[pid]

    for item in items:
        if getattr(item, "item_type", "goods") != "goods" or not item.product:
            continue
        pid = str(item.product.id)
        qty = Decimal(str(item.quantity))
        if pid in frozen:
            for m in frozen[pid]:
                raw = load(m["product"])
                if raw is not None:
                    out.append((raw, qty * Decimal(str(m["per_unit"])), pid))
        else:
            out.append((item.product, qty, None))
    return out


def _materials(org, product, rows):
    if not isinstance(rows, list) or len(rows) > MAX_MATERIALS:
        raise ValueError(f"Add up to {MAX_MATERIALS} raw materials.")
    clean, seen = [], set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("Invalid raw material line.")
        raw = Product.objects(organization=org, id=_oid(row.get("product")), is_active=True).first()
        if not raw or raw.item_type == "service":
            raise ValueError("Raw materials must be active stock items.")
        if raw.id == product.id:
            raise ValueError("An item cannot be a raw material of itself.")
        if str(raw.id) in seen:
            raise ValueError(f"{raw.name} is listed twice. Combine the quantities into one line.")
        if made_to_order_ids(org.id, [raw.id]):
            raise ValueError(f"{raw.name} is made to order, so it can't be a raw material. Use its own raw materials instead.")
        seen.add(str(raw.id))
        clean.append(dict(product=str(raw.id), name=raw.name, unit=raw.unit,
                          per_unit=f"{quantity(row.get('per_unit'), raw.name + ' per unit'):f}"))
    return clean


def public(org_id, row, product=None):
    product = product or Product.objects(organization=org_id, id=row["product"]).first()
    raws = {str(p.id): p for p in Product.objects(organization=org_id, id__in=[_oid(m["product"]) for m in row.get("materials", [])])}
    stock = _on_hand(org_id, list(raws))
    materials, cost, makeable = [], Decimal(0), None
    for m in row.get("materials", []):
        p = raws.get(m["product"])
        rate = Decimal(str(p.cost_price or 0)) if p else Decimal(0)
        per = Decimal(m["per_unit"])
        have = stock.get(m["product"], Decimal(0))
        cost += rate * per
        can = int(have // per) if per else 0
        makeable = can if makeable is None else min(makeable, can)
        materials.append(dict(product=m["product"], name=p.name if p else m.get("name", "Removed item"), unit=p.unit if p else m.get("unit", ""),
                              per_unit=m["per_unit"], rate=f"{rate:.2f}", on_hand=f"{have.normalize():f}", active=bool(p and p.is_active)))
    labour = Decimal(str(row.get("labour_per_unit", "0")))
    return dict(
        product=str(row["product"]),
        name=product.name if product else "Removed item",
        sku=product.sku if product else "",
        unit=product.unit if product else "",
        selling_price=f"{Decimal(str(product.selling_price or 0)):.2f}" if product else "0.00",
        made_to_order=bool(row.get("made_to_order")),
        materials=materials,
        labour_per_unit=f"{labour:.2f}",
        material_cost=f"{cost:.2f}",
        unit_cost=f"{cost + labour:.2f}",
        can_make=max(0, makeable) if makeable is not None else None,
        notes=row.get("notes", ""),
        updated_at=row.get("updated_at").isoformat() if row.get("updated_at") else None,
    )


def _on_hand(org_id, product_ids):
    if not product_ids:
        return {}
    pipeline = [
        {"$match": {"organization": _oid(org_id), "product": {"$in": [_oid(p) for p in product_ids]}}},
        {"$group": {"_id": "$product", "qty": {"$sum": "$quantity"}, "held": {"$sum": "$reserved_quantity"}}},
    ]
    return {str(r["_id"]): Decimal(str(r["qty"] or 0)) - Decimal(str(r.get("held") or 0)) for r in get_db().inventory.aggregate(pipeline)}


@api_login_required
@require_http_methods(["GET", "POST", "DELETE"])
def recipes(request, product_id=None):
    org = request.api_organization
    if not (permitted(request, "manufacturing.read") or permitted(request, "products.read")):
        return R.forbidden(message="Manufacturing or item access required.", request=request)
    try:
        if request.method == "GET":
            if product_id:
                product = Product.objects(organization=org, id=_oid(product_id)).first()
                if not product:
                    return R.not_found(message="Item not found.", request=request)
                row = recipe(org.id, product.id) or dict(product=product.id, made_to_order=False, materials=[])
                return R.success(data=public(org.id, row, product), request=request)
            query = {"organization": org.id}
            if request.GET.get("made_to_order") == "1":
                query["made_to_order"] = True
            rows = list(_col().find(query).sort("updated_at", -1).limit(500))
            products = {p.id: p for p in Product.objects(organization=org, id__in=[r["product"] for r in rows])}
            search = (request.GET.get("search") or "").strip().lower()[:60]
            data = [public(org.id, r, products.get(r["product"])) for r in rows]
            if search:
                data = [d for d in data if search in d["name"].lower() or search in d["sku"].lower()]
            return R.success(data={"rows": data, "count": len(data)}, request=request)
        if not permitted(request, "manufacturing.manage"):
            return R.forbidden(message="Manufacturing permission required to change recipes.", request=request)
        product = Product.objects(organization=org, id=_oid(product_id)).first() if product_id else None
        if not product or product.item_type == "service":
            raise ValueError("Recipes are for stock items. Select a goods item.")
        if request.method == "DELETE":
            _col().delete_one({"organization": org.id, "product": product.id})
            return R.success(data={"deleted": True}, request=request)
        data = payload(request)
        mto = bool(data.get("made_to_order"))
        materials = _materials(org, product, data.get("materials", []))
        if mto and not materials:
            raise ValueError("Add the raw materials used for one unit, so selling it uses them up.")
        labour = quantity(data.get("labour_per_unit", "0") or "0", "labour per unit", positive=False, places=2)
        notes = str(data.get("notes", ""))[:1000]
        now = datetime.now(timezone.utc)
        _col().update_one(
            {"organization": org.id, "product": product.id},
            {"$set": dict(made_to_order=mto, materials=materials, labour_per_unit=f"{labour:.2f}", notes=notes, updated_at=now, updated_by=request.api_user.id),
             "$setOnInsert": dict(created_at=now)},
            upsert=True,
        )
        return R.success(data=public(org.id, recipe(org.id, product.id), product), request=request)
    except ValueError as exc:
        return R.validation_error(message=str(exc), request=request)
