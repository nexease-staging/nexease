from mongoengine.errors import (
    ValidationError,
)

from apps.sales.models import (
    SalesReturn,
)


class SalesReturnRepository:

    @staticmethod
    def queryset_for_organization(
        *,
        organization,
    ):
        return SalesReturn.objects(
            organization=organization,
        )

    @staticmethod
    def create_return(
        *,
        organization,
        return_number,
        sales_order,
        invoice,
        customer,
        warehouse,
        return_date,
        items,
        subtotal,
        tax_amount,
        discount_amount,
        total_amount,
        reason,
        notes,
        created_by,
        status="DRAFT",
    ):
        sales_return = SalesReturn(
            organization=organization,
            return_number=return_number,
            sales_order=sales_order,
            invoice=invoice,
            customer=customer,
            warehouse=warehouse,
            status=status,
            return_date=return_date,
            items=items,
            subtotal=subtotal,
            tax_amount=tax_amount,
            discount_amount=discount_amount,
            total_amount=total_amount,
            reason=reason,
            notes=notes,
            created_by=created_by,
        )

        sales_return.save()

        return sales_return

    @staticmethod
    def get_by_id(
        *,
        organization,
        return_id,
    ):
        try:
            return (
                SalesReturnRepository
                .queryset_for_organization(
                    organization=organization,
                )
                .filter(
                    id=return_id,
                )
                .first()
            )

        except (
            ValidationError,
            TypeError,
            ValueError,
        ):
            return None

    @staticmethod
    def get_by_return_number(
        *,
        organization,
        return_number,
    ):
        return (
            SalesReturnRepository
            .queryset_for_organization(
                organization=organization,
            )
            .filter(
                return_number=return_number,
            )
            .first()
        )

    @staticmethod
    def list_by_organization(
        *,
        organization,
    ):
        return (
            SalesReturnRepository
            .queryset_for_organization(
                organization=organization,
            )
            .order_by(
                "-return_date",
                "-created_at",
                "-id",
            )
        )

    @staticmethod
    def list_by_invoice(
        *,
        organization,
        invoice,
    ):
        return (
            SalesReturnRepository
            .queryset_for_organization(
                organization=organization,
            )
            .filter(
                invoice=invoice,
            )
            .order_by(
                "-return_date",
                "-created_at",
                "-id",
            )
        )

    @staticmethod
    def list_confirmed_by_invoice(
        *,
        organization,
        invoice,
    ):
        return (
            SalesReturnRepository
            .queryset_for_organization(
                organization=organization,
            )
            .filter(
                invoice=invoice,
                status="CONFIRMED",
            )
            .order_by(
                "-return_date",
                "-created_at",
                "-id",
            )
        )

    @staticmethod
    def list_by_sales_order(
        *,
        organization,
        sales_order,
    ):
        return (
            SalesReturnRepository
            .queryset_for_organization(
                organization=organization,
            )
            .filter(
                sales_order=sales_order,
            )
            .order_by(
                "-return_date",
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
        return (
            SalesReturnRepository
            .queryset_for_organization(
                organization=organization,
            )
            .filter(
                customer=customer,
            )
            .order_by(
                "-return_date",
                "-created_at",
                "-id",
            )
        )

    @staticmethod
    def list_by_status(
        *,
        organization,
        status,
    ):
        return (
            SalesReturnRepository
            .queryset_for_organization(
                organization=organization,
            )
            .filter(
                status=status,
            )
            .order_by(
                "-return_date",
                "-created_at",
                "-id",
            )
        )

    @staticmethod
    def update_status(
        *,
        sales_return,
        status,
        confirmed_at=None,
        cancelled_at=None,
    ):
        sales_return.status = status

        if confirmed_at is not None:
            sales_return.confirmed_at = (
                confirmed_at
            )

        if cancelled_at is not None:
            sales_return.cancelled_at = (
                cancelled_at
            )

        sales_return.save()

        return sales_return