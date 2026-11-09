"""Admin invoice amendments with amount validation, audit and delta accounting."""

from copy import deepcopy
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from uuid import uuid4
from django.views.decorators.http import require_http_methods
from mongoengine.errors import ValidationError
from apps.core.api.decorators import api_login_required
from apps.core.services.api_response_service import APIResponseService as R
from apps.sales.models import Invoice, InvoiceItem, CreditNote
from apps.products.models import Product
from apps.inventory.models import Inventory, StockMovement, Warehouse
from .views import payload, permitted
from .enhancements import is_admin
from .automation import write_lock
from .models import BusinessAudit
from .billing import tax_heads, invoice_account


def amount(value):
    try:
        d = Decimal(str(value))
    except (InvalidOperation, TypeError):
        raise ValueError("Invalid invoice amount.")
    if not d.is_finite() or d < 0 or d != d.quantize(Decimal(".01")):
        raise ValueError("Amounts must be non-negative with up to two decimal places.")
    return d


def snapshot(inv):
    return {
        "version": inv.updated_at.isoformat(timespec="milliseconds"),
        "invoice_date": inv.invoice_date.date().isoformat(),
        "due_date": inv.due_date.date().isoformat() if inv.due_date else "",
        "billing_name": inv.billing_name,
        "billing_address": inv.billing_address or "",
        "notes": inv.notes or "",
        "items": [
            {
                "product_id": str(i.product.id),
                "name": i.item_name or i.product.name,
                "quantity": str(i.quantity),
                "unit_price": str(i.unit_price),
                "tax_rate": str(i.tax_rate),
                "discount": str(i.discount),
                "description": i.description or "",
                "show_description": i.show_description,
            }
            for i in inv.items
        ],
    }


def account(org, user, key):
    if key in ("ACCOUNTS_RECEIVABLE", "SALES_REVENUE", "OUTPUT_TAX"):
        from apps.finance.services.chart_of_account_service import ChartOfAccountService

        return ChartOfAccountService.get_system_account(
            organization=org, system_key=key
        )
    return invoice_account(org, user, key)


def balances(inv):
    result = {
        "ACCOUNTS_RECEIVABLE": inv.total_amount,
        "SALES_REVENUE": Decimal(0),
        "SERVICE_REVENUE": Decimal(0),
    }
    for i in inv.items:
        result["SERVICE_REVENUE" if i.item_type == "service" else "SALES_REVENUE"] -= (
            i.line_subtotal - i.discount
        )
    if inv.billing_details.get("tax_reviewed"):
        for key, value in zip(
            ("OUTPUT_CGST", "OUTPUT_SGST", "OUTPUT_IGST"), tax_heads(inv)
        ):
            result[key] = -value
    else:
        result["OUTPUT_TAX"] = -inv.tax_amount
    return result


@api_login_required
@require_http_methods(["GET", "POST"])
@write_lock
def edit(request, invoice_id):
    if not is_admin(request.api_user) or not permitted(request, "invoices.read"):
        return R.forbidden(
            message="Only an administrator with invoice edit permission can amend invoices.",
            request=request,
        )
    try:
        org = request.api_organization
        user = request.api_user
        inv = Invoice.objects(organization=org, id=invoice_id).first()
        if not inv:
            raise ValueError("Invoice not found.")
        if inv.status not in ("DRAFT", "ISSUED", "PARTIALLY_PAID", "PAID"):
            raise ValueError("Cancelled invoices cannot be edited.")
        if inv.eway_status or (inv.einvoice or {}).get("status"):
            raise ValueError(
                "Submitted e-invoices/e-way bills require their correction workflow before editing."
            )
        if request.method == "GET":
            return R.success(data=snapshot(inv), request=request)
        raw = payload(request)
        before = snapshot(inv)
        if raw.get("version") != before["version"]:
            raise ValueError("Invoice changed. Reload it before editing.")
        if set(raw) - set(before):
            raise ValueError("Unknown invoice fields.")
        new = deepcopy(inv)
        for key in ("invoice_date", "due_date"):
            value = raw.get(key, before[key])
            setattr(new, key, datetime.fromisoformat(value) if value else None)
        if not new.invoice_date or (new.due_date and new.due_date < new.invoice_date):
            raise ValueError("Check invoice and due dates.")
        if inv.status != "DRAFT" and new.invoice_date.date() != inv.invoice_date.date():
            raise ValueError(
                "Issued invoice dates are tied to posted accounting. Use a credit/rebill correction to move the invoice date."
            )
        if inv.status != "DRAFT":
            new.invoice_date = inv.invoice_date
        for key, limit in [
            ("billing_name", 200),
            ("billing_address", 500),
            ("notes", 1000),
        ]:
            value = raw.get(key, before[key])
            if not isinstance(value, str) or len(value) > limit:
                raise ValueError("Invalid " + key)
            setattr(new, key, value.strip())
        rows = raw.get("items")
        if (
            not isinstance(rows, list)
            or not 1 <= len(rows) <= 100
            or any(not isinstance(row, dict) for row in rows)
        ):
            raise ValueError("Enter 1–100 invoice lines.")
        new.items = []
        for row in rows:
            product = Product.objects(
                organization=org, id=row.get("product_id"), is_active=True
            ).first()
            if not product:
                raise ValueError("Select an active product in this organization.")
            qty = amount(row.get("quantity"))
            price = amount(row.get("unit_price"))
            rate = amount(row.get("tax_rate"))
            discount = amount(row.get("discount", "0"))
            if qty <= 0 or rate > 100:
                raise ValueError("Quantity must be positive and tax rate at most 100%.")
            subtotal = (qty * price).quantize(Decimal(".01"), rounding=ROUND_HALF_UP)
            if discount > subtotal:
                raise ValueError("Discount exceeds line amount.")
            if (
                new.billing_details.get("supply_type") != "taxable"
                and new.billing_details.get("tax_reviewed")
                and rate
            ):
                raise ValueError("Non-taxable invoices must have zero GST.")
            existing = next((i for i in inv.items if i.product.id == product.id), None)
            tax = ((subtotal - discount) * rate / 100).quantize(
                Decimal(".01"), rounding=ROUND_HALF_UP
            )
            description = row.get("description", "")
            if not isinstance(description, str) or len(description) > 2000:
                raise ValueError("Invalid description.")
            new.items.append(
                InvoiceItem(
                    product=product,
                    item_name=str(row.get("name") or product.name)[:200],
                    item_type=existing.item_type if existing else product.item_type,
                    hsn_code=existing.hsn_code if existing else product.hsn_code,
                    unit=existing.unit if existing else product.unit,
                    quantity=qty,
                    unit_price=price,
                    tax_rate=rate,
                    discount=discount,
                    line_subtotal=subtotal,
                    line_tax=tax,
                    line_total=subtotal - discount + tax,
                    description=description,
                    show_description=bool(row.get("show_description")),
                )
            )
        if inv.sales_order:
            old_quantities = [(str(i.product.id), i.quantity) for i in inv.items]
            if old_quantities != [(str(i.product.id), i.quantity) for i in new.items]:
                raise ValueError(
                    "For a sales-order invoice, correct fulfillment before changing products or quantities. Prices, discounts and tax amounts can be amended here."
                )
        if CreditNote.objects(
            organization=org, invoice=inv, status__ne="CANCELLED"
        ).first():
            raise ValueError(
                "Resolve linked credit notes before amending invoice values."
            )
        new.subtotal = sum((i.line_subtotal for i in new.items), Decimal(0))
        new.discount_amount = sum((i.discount for i in new.items), Decimal(0))
        new.tax_amount = sum((i.line_tax for i in new.items), Decimal(0))
        new.total_amount = new.subtotal - new.discount_amount + new.tax_amount
        if new.total_amount <= 0 or new.total_amount < inv.amount_paid:
            raise ValueError(
                "Total must be positive and cannot be below payments already applied."
            )
        new.balance_due = new.total_amount - inv.amount_paid
        new.paid_at = (
            (inv.paid_at or datetime.utcnow())
            if inv.status != "DRAFT" and new.balance_due == 0
            else None
        )
        if inv.status != "DRAFT":
            new.status = (
                "PAID"
                if new.balance_due == 0
                else "PARTIALLY_PAID" if inv.amount_paid else "ISSUED"
            )
        if not new.billing_name:
            raise ValueError("Billing name is required.")
        if (
            new.billing_details.get("tax_reviewed")
            and new.billing_details.get("supply_type") != "unregistered"
        ):
            import re

            for item in new.items:
                if not re.fullmatch(
                    (
                        r"[0-9]{6}"
                        if item.item_type == "service"
                        else r"[0-9]{4}|[0-9]{6}|[0-9]{8}"
                    ),
                    item.hsn_code or "",
                ):
                    raise ValueError("Every reviewed GST line needs a valid HSN/SAC.")
        new.validate()
        journal = None
        stock_changes = []
        stock_movements = []
        saved = False
        stamp = datetime.utcnow()
        from apps.finance.services.journal_entry_service import (
            JournalEntryService as Journals,
        )

        try:
            if inv.status != "DRAFT":
                old = balances(inv)
                current = balances(new)
                lines = []
                for key in set(old) | set(current):
                    delta = current.get(key, Decimal(0)) - old.get(key, Decimal(0))
                    if delta:
                        lines.append(
                            {
                                "account": account(org, user, key),
                                "description": "Invoice amendment "
                                + inv.invoice_number,
                                "debit": max(delta, Decimal(0)),
                                "credit": max(-delta, Decimal(0)),
                            }
                        )
                if lines:
                    from apps.finance.models import JournalEntry

                    if not JournalEntry.objects(
                        organization=org,
                        source_type="SALES_INVOICE",
                        source_id=str(inv.id),
                        status="POSTED",
                    ).first():
                        raise ValueError(
                            "Original invoice accounting journal is missing. Reconcile it before changing issued amounts."
                        )
                if lines:
                    journal = Journals.create_journal(
                        user=user,
                        organization=org,
                        journal_date=datetime.utcnow(),
                        raw_lines=lines,
                        description="Amendment of " + inv.invoice_number,
                        source_type="SALES_INVOICE",
                        source_id=str(inv.id) + ":edit:" + uuid4().hex,
                    )
            if inv.billing_details.get(
                "quick_stock_applied"
            ) and not inv.billing_details.get("quick_stock_reversed"):
                warehouse = Warehouse.objects(
                    organization=org, id=inv.billing_details["quick_stock_warehouse"]
                ).first()
                if not warehouse:
                    raise ValueError("Invoice warehouse is unavailable.")
                quantities = {}
                products = {}
                for sign, items in [(1, inv.items), (-1, new.items)]:
                    for item in items:
                        if item.item_type == "goods":
                            pid = str(item.product.id)
                            products[pid] = item.product
                            quantities[pid] = (
                                quantities.get(pid, Decimal(0)) + sign * item.quantity
                            )
                for pid, delta in quantities.items():
                    if not delta:
                        continue
                    stock = Inventory.objects(
                        organization=org, product=products[pid], warehouse=warehouse
                    ).first()
                    if not stock:
                        stock = Inventory(
                            organization=org, product=products[pid], warehouse=warehouse
                        ).save()
                    after = Inventory.objects(id=stock.id).modify(
                        new=True, inc__quantity=delta
                    )
                    stock_changes.append((stock.id, delta))
                    stock_movements.append(
                        StockMovement(
                            organization=org,
                            inventory=after,
                            product=products[pid],
                            warehouse=warehouse,
                            movement_type=(
                                "ADJUSTMENT_IN" if delta > 0 else "ADJUSTMENT_OUT"
                            ),
                            quantity=abs(delta),
                            quantity_before=after.quantity - delta,
                            quantity_after=after.quantity,
                            reserved_before=after.reserved_quantity,
                            reserved_after=after.reserved_quantity,
                            reference_type="QUICK_INVOICE_EDIT",
                            reference_id=str(inv.id),
                            notes="Admin invoice amendment",
                            created_by=user,
                        ).save()
                    )
            fields = [
                "items",
                "invoice_date",
                "due_date",
                "billing_name",
                "billing_address",
                "notes",
                "subtotal",
                "discount_amount",
                "tax_amount",
                "total_amount",
                "balance_due",
                "status",
                "paid_at",
            ]
            updates = {"set__" + key: getattr(new, key) for key in fields}
            updates["set__updated_at"] = stamp
            if not Invoice.objects(
                id=inv.id, organization=org, updated_at=inv.updated_at
            ).update_one(**updates):
                raise ValueError(
                    "Invoice changed during editing. Reload before retrying."
                )
            saved = True
            new.updated_at = stamp
            if journal:
                Journals.post_journal(
                    user=user, organization=org, journal_id=str(journal.id)
                )
            BusinessAudit(
                organization=org,
                actor=user,
                kind="invoice",
                record_id=str(inv.id),
                action="financial-amendment",
                details={
                    "before": before,
                    "after": snapshot(new),
                    "journal_id": str(journal.id) if journal else None,
                },
            ).save()
        except Exception:
            if journal:
                journal.reload()
                if journal.status == "POSTED":
                    Journals.reverse_journal(
                        user=user,
                        organization=org,
                        journal_id=str(journal.id),
                        description="Invoice amendment failed; restore original values.",
                    )
                elif journal.status == "DRAFT":
                    journal.delete()
            if saved:
                restored = {"set__" + key: getattr(inv, key) for key in fields}
                restored["set__updated_at"] = inv.updated_at
                if not Invoice.objects(id=inv.id, updated_at=stamp).update_one(
                    **restored
                ):
                    raise RuntimeError(
                        "Concurrent invoice change during rollback. Administrator accounting review required."
                    )
            for sid, delta in stock_changes:
                Inventory.objects(id=sid).update_one(inc__quantity=-delta)
            for movement in stock_movements:
                movement.delete()
            raise
        return R.success(
            data={
                "id": str(inv.id),
                "total_amount": str(new.total_amount),
                "balance_due": str(new.balance_due),
            },
            message="Invoice amended and balances updated.",
            request=request,
        )
    except PermissionError as e:
        return R.forbidden(message=str(e), request=request)
    except (ValueError, TypeError, InvalidOperation, ValidationError) as e:
        return R.validation_error(message=str(e), request=request)
