from datetime import datetime

from mongoengine.errors import (
    ValidationError,
)

from apps.purchasing.models import (
    PurchaseReturn,
)


class PurchaseReturnRepository:

    @staticmethod
    def queryset_for_organization(
        *,
        organization,
    ):
        return PurchaseReturn.objects(
            organization=organization,
        )

    @staticmethod
    def create_purchase_return(
        *,
        organization,
        return_number,
        purchase_order,
        vendor_bill,
        supplier,
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
        purchase_return = PurchaseReturn(
            organization=organization,
            return_number=return_number,
            purchase_order=purchase_order,
            vendor_bill=vendor_bill,
            supplier=supplier,
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

        purchase_return.save()

        return purchase_return

    @staticmethod
    def get_by_id(
        *,
        organization,
        purchase_return_id,
    ):
        try:
            return (
                PurchaseReturnRepository
                .queryset_for_organization(
                    organization=organization,
                )
                .filter(
                    id=purchase_return_id,
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
    def get_by_number(
        *,
        organization,
        return_number,
    ):
        return (
            PurchaseReturnRepository
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
            PurchaseReturnRepository
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
    def list_by_purchase_order(
        *,
        organization,
        purchase_order,
    ):
        return (
            PurchaseReturnRepository
            .queryset_for_organization(
                organization=organization,
            )
            .filter(
                purchase_order=purchase_order,
            )
            .order_by(
                "-return_date",
                "-created_at",
                "-id",
            )
        )

    @staticmethod
    def list_by_vendor_bill(
        *,
        organization,
        vendor_bill,
    ):
        return (
            PurchaseReturnRepository
            .queryset_for_organization(
                organization=organization,
            )
            .filter(
                vendor_bill=vendor_bill,
            )
            .order_by(
                "-return_date",
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
        return (
            PurchaseReturnRepository
            .queryset_for_organization(
                organization=organization,
            )
            .filter(
                supplier=supplier,
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
            PurchaseReturnRepository
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
        purchase_return,
        status,
        confirmed_at=None,
        cancelled_at=None,
    ):
        purchase_return.status = status

        if confirmed_at is not None:
            purchase_return.confirmed_at = (
                confirmed_at
            )

        if cancelled_at is not None:
            purchase_return.cancelled_at = (
                cancelled_at
            )

        purchase_return.updated_at = (
            datetime.utcnow()
        )

        purchase_return.save()

        return purchase_return