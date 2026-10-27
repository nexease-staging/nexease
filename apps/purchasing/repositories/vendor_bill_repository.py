from datetime import datetime

from apps.purchasing.models import (
    VendorBill,
)


class VendorBillRepository:
    @staticmethod
    def queryset_for_organization(
        *,
        organization,
    ):
        if not organization:
            return (
                VendorBill
                .objects(
                    id=None,
                )
            )

        return (
            VendorBill
            .objects(
                organization=organization,
            )
        )
    @staticmethod
    def create_vendor_bill(
        *,
        organization,
        bill_number,
        supplier_invoice_number,
        purchase_order,
        supplier,
        bill_date,
        due_date,
        items,
        subtotal,
        tax_amount,
        discount_amount,
        total_amount,
        supplier_name,
        supplier_address,
        supplier_city,
        supplier_state,
        supplier_country,
        supplier_pincode,
        supplier_gstin,
        notes,
        created_by,
        status="DRAFT",
    ):
        bill = VendorBill(
            organization=organization,
            bill_number=bill_number,
            supplier_invoice_number=(
                supplier_invoice_number
            ),
            purchase_order=purchase_order,
            supplier=supplier,
            status=status,
            bill_date=bill_date,
            due_date=due_date,
            items=items,
            subtotal=subtotal,
            tax_amount=tax_amount,
            discount_amount=discount_amount,
            total_amount=total_amount,
            amount_paid=0,
            balance_due=total_amount,
            supplier_name=supplier_name,
            supplier_address=supplier_address,
            supplier_city=supplier_city,
            supplier_state=supplier_state,
            supplier_country=supplier_country,
            supplier_pincode=supplier_pincode,
            supplier_gstin=supplier_gstin,
            notes=notes,
            created_by=created_by,
        )

        bill.save()

        return bill

    @staticmethod
    def get_by_id(
        *,
        organization,
        bill_id,
    ):
        try:
            return (
                VendorBillRepository
                .queryset_for_organization(
                    organization=organization,
                )
                .filter(
                    id=bill_id,
                )
                .first()
            )

        except (
            TypeError,
            ValueError,
        ):
            return None

    @staticmethod
    def get_by_bill_number(
        *,
        organization,
        bill_number,
    ):
        return VendorBill.objects(
            organization=organization,
            bill_number=bill_number,
        ).first()

    @staticmethod
    def get_by_supplier_invoice_number(
        *,
        organization,
        supplier,
        supplier_invoice_number,
    ):
        if not supplier_invoice_number:
            return None

        return VendorBill.objects(
            organization=organization,
            supplier=supplier,
            supplier_invoice_number=(
                supplier_invoice_number
            ),
        ).first()

    @staticmethod
    def list_by_purchase_order(
        *,
        organization,
        purchase_order,
    ):
        return VendorBill.objects(
            organization=organization,
            purchase_order=purchase_order,
        ).order_by(
            "-created_at"
        )

    @staticmethod
    def list_by_organization(
        *,
        organization,
    ):
        return (
            VendorBillRepository
            .queryset_for_organization(
                organization=organization,
            )
            .order_by(
                "-created_at",
                "-id",
            )
        )

    @staticmethod
    def list_by_supplier(
        *,
        organization,
        supplier,
    ):
        return VendorBill.objects(
            organization=organization,
            supplier=supplier,
        ).order_by(
            "-created_at"
        )

    @staticmethod
    def list_by_status(
        *,
        organization,
        status,
    ):
        return VendorBill.objects(
            organization=organization,
            status=status,
        ).order_by(
            "-created_at"
        )

    @staticmethod
    def list_outstanding(
        *,
        organization,
        supplier=None,
    ):
        query = {
            "organization": organization,
            "status__in": [
                "POSTED",
                "PARTIALLY_PAID",
            ],
            "balance_due__gt": 0,
        }

        if supplier is not None:
            query["supplier"] = supplier

        return VendorBill.objects(
            **query
        ).order_by(
            "due_date",
            "created_at",
        )

    @staticmethod
    def update_status(
        *,
        bill,
        status,
        posted_at=None,
        paid_at=None,
        cancelled_at=None,
    ):
        bill.status = status

        if posted_at is not None:
            bill.posted_at = posted_at

        if paid_at is not None:
            bill.paid_at = paid_at

        if cancelled_at is not None:
            bill.cancelled_at = cancelled_at

        bill.updated_at = (
            datetime.utcnow()
        )

        bill.save()

        return bill

    @staticmethod
    def update_payment_totals(
        *,
        bill,
        amount_paid,
        balance_due,
        status,
        paid_at=None,
    ):
        bill.amount_paid = amount_paid
        bill.balance_due = balance_due
        bill.status = status

        if paid_at is not None:
            bill.paid_at = paid_at

        bill.updated_at = (
            datetime.utcnow()
        )

        bill.save()

        return bill