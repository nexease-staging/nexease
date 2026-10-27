from datetime import datetime

from apps.sales.models import Invoice


class InvoiceRepository:

    @staticmethod
    def queryset_for_organization(
        *,
        organization,
    ):
        """
        Return a tenant-scoped Invoice queryset
        for API filtering, searching, sorting,
        and pagination.
        """

        return Invoice.objects(
            organization=organization,
        )
    @staticmethod
    def create_invoice(
        *,
        organization,
        invoice_number,
        sales_order,
        customer,
        invoice_date,
        due_date,
        items,
        subtotal,
        tax_amount,
        discount_amount,
        total_amount,
        billing_name,
        billing_address,
        billing_city,
        billing_state,
        billing_country,
        billing_pincode,
        customer_gstin,
        notes,
        created_by,
        status="DRAFT",
    ):
        invoice = Invoice(
            organization=organization,
            invoice_number=invoice_number,
            sales_order=sales_order,
            customer=customer,
            status=status,
            invoice_date=invoice_date,
            due_date=due_date,
            items=items,
            subtotal=subtotal,
            tax_amount=tax_amount,
            discount_amount=discount_amount,
            total_amount=total_amount,
            amount_paid=0,
            balance_due=total_amount,
            billing_name=billing_name,
            billing_address=billing_address,
            billing_city=billing_city,
            billing_state=billing_state,
            billing_country=billing_country,
            billing_pincode=billing_pincode,
            customer_gstin=customer_gstin,
            notes=notes,
            created_by=created_by,
        )

        invoice.save()

        return invoice

    @staticmethod
    def get_by_id(
        *,
        organization,
        invoice_id,
    ):
        return Invoice.objects(
            organization=organization,
            id=invoice_id,
        ).first()

    @staticmethod
    def get_by_invoice_number(
        *,
        organization,
        invoice_number,
    ):
        return Invoice.objects(
            organization=organization,
            invoice_number=invoice_number,
        ).first()

    @staticmethod
    def get_by_sales_order(
        *,
        organization,
        sales_order,
    ):
        return Invoice.objects(
            organization=organization,
            sales_order=sales_order,
        ).first()

    @staticmethod
    def list_by_organization(
        *,
        organization,
    ):
        return (
            InvoiceRepository
            .queryset_for_organization(
                organization=organization,
            )
            .order_by(
                "-created_at",
                "-id",
            )
        )

    @staticmethod
    def list_by_customer(
        *,
        organization,
        customer,
    ):
        return Invoice.objects(
            organization=organization,
            customer=customer,
        ).order_by(
            "-created_at"
        )

    @staticmethod
    def list_by_status(
        *,
        organization,
        status,
    ):
        return Invoice.objects(
            organization=organization,
            status=status,
        ).order_by(
            "-created_at"
        )

    @staticmethod
    def update_status(
        *,
        invoice,
        status,
        issued_at=None,
        paid_at=None,
        cancelled_at=None,
    ):
        invoice.status = status

        if issued_at is not None:
            invoice.issued_at = issued_at

        if paid_at is not None:
            invoice.paid_at = paid_at

        if cancelled_at is not None:
            invoice.cancelled_at = cancelled_at

        invoice.updated_at = (
            datetime.utcnow()
        )

        invoice.save()

        return invoice

    @staticmethod
    def update_payment_totals(
        *,
        invoice,
        amount_paid,
        balance_due,
        status,
        paid_at=None,
    ):
        invoice.amount_paid = amount_paid
        invoice.balance_due = balance_due
        invoice.status = status

        if paid_at is not None:
            invoice.paid_at = paid_at

        invoice.updated_at = (
            datetime.utcnow()
        )

        invoice.save()

        return invoice

    @staticmethod
    def list_outstanding(
        *,
        organization,
        customer=None,
    ):
        query = {
            "organization": organization,
            "status__in": [
                "ISSUED",
                "PARTIALLY_PAID",
            ],
            "balance_due__gt": 0,
        }

        if customer is not None:
            query["customer"] = customer

        return Invoice.objects(
            **query
        ).order_by(
            "due_date",
            "created_at",
        )