"""Physical stock recorded by quick invoices, with explicit reversal on cancellation."""

from datetime import datetime
from decimal import Decimal
from apps.inventory.models import Inventory, StockMovement, Warehouse


def warehouse_for(org, selected=None):
    if selected:
        return selected
    warehouse = (
        Warehouse.objects(organization=org, is_active=True)
        .order_by("created_at")
        .first()
    )
    if not warehouse:
        if Warehouse.objects(organization=org).first():
            raise ValueError("Activate a warehouse before making a goods invoice.")
        warehouse = Warehouse(
            organization=org,
            name="Quick billing",
            code="QUICK-BILLING",
            address="Default warehouse created for quick invoice stock tracking.",
        ).save()
    return warehouse


def _move(invoice, user, warehouse, sign=-1):
    invoice.reload()
    """Caller holds the organization write lock. Compensate on any partial failure."""
    marker = "quick_stock_reversed" if sign == 1 else "quick_stock_applied"
    if invoice.billing_details.get(marker):
        return
    applied = []
    movements = []
    try:
        for item in invoice.items:
            if item.item_type != "goods":
                continue
            stock = Inventory.objects(
                organization=invoice.organization,
                product=item.product,
                warehouse=warehouse,
            ).first()
            if not stock:
                stock = Inventory(
                    organization=invoice.organization,
                    product=item.product,
                    warehouse=warehouse,
                ).save()
            delta = Decimal(str(item.quantity)) * sign
            # Atomic increment avoids losing independent receipts/transfers.
            after = Inventory.objects(id=stock.id).modify(
                new=True, inc__quantity=delta, set__updated_at=datetime.utcnow()
            )
            applied.append((stock.id, delta))
            before = after.quantity - delta
            movements.append(
                StockMovement(
                    organization=invoice.organization,
                    inventory=after,
                    product=item.product,
                    warehouse=warehouse,
                    movement_type="STOCK_OUT" if sign < 0 else "STOCK_IN",
                    quantity=abs(delta),
                    quantity_before=before,
                    quantity_after=after.quantity,
                    reserved_before=after.reserved_quantity,
                    reserved_after=after.reserved_quantity,
                    reference_type=(
                        "QUICK_INVOICE" if sign < 0 else "QUICK_INVOICE_CANCEL"
                    ),
                    reference_id=str(invoice.id),
                    notes="Quick invoice " + invoice.invoice_number,
                    created_by=user,
                ).save()
            )
        invoice.billing_details[marker] = True
        invoice.billing_details["quick_stock_warehouse"] = str(warehouse.id)
        invoice.save()
    except Exception:
        for sid, delta in reversed(applied):
            Inventory.objects(id=sid).update_one(inc__quantity=-delta)
        for movement in movements:
            movement.delete()
        raise


def move(invoice, user, warehouse, sign=-1):
    from mongoengine.connection import get_db
    from pymongo.errors import DuplicateKeyError

    locks = get_db().quick_invoice_stock_locks
    key = str(invoice.id)
    token = str(datetime.utcnow())
    try:
        locks.insert_one({"_id": key, "token": token})
    except DuplicateKeyError:
        raise ValueError(
            "Another stock update for this invoice is running. Retry shortly."
        )
    try:
        return _move(invoice, user, warehouse, sign)
    finally:
        locks.delete_one({"_id": key, "token": token})


def reverse(invoice, user):
    if not invoice.billing_details.get(
        "quick_stock_applied"
    ) or invoice.billing_details.get("quick_stock_reversed"):
        return
    warehouse = Warehouse.objects(
        organization=invoice.organization,
        id=invoice.billing_details["quick_stock_warehouse"],
    ).first()
    if not warehouse:
        raise ValueError(
            "The quick invoice warehouse is unavailable. Restore it before cancelling."
        )
    move(invoice, user, warehouse, 1)
