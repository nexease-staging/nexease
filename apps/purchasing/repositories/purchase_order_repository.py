from datetime import (
    datetime,
)

from apps.purchasing.models import (
    PurchaseOrder,
)


class PurchaseOrderRepository:

    @staticmethod
    def queryset_for_organization(
        *,
        organization,
    ):
        """
        Return the tenant-scoped Purchase Order queryset.
        """

        if not organization:
            return (
                PurchaseOrder
                .objects(
                    id=None,
                )
            )

        return (
            PurchaseOrder
            .objects(
                organization=organization,
            )
        )

    @staticmethod
    def create_purchase_order(
        *,
        organization,
        po_number,
        supplier,
        order_date,
        expected_delivery_date,
        items,
        subtotal,
        tax_amount,
        discount_amount,
        total_amount,
        notes,
        created_by,
        status="DRAFT",
    ):
        """
        Create a purchase order.
        """

        purchase_order = PurchaseOrder(
            organization=organization,
            po_number=po_number,
            supplier=supplier,
            status=status,
            order_date=order_date,
            expected_delivery_date=(
                expected_delivery_date
            ),
            items=items,
            subtotal=subtotal,
            tax_amount=tax_amount,
            discount_amount=discount_amount,
            total_amount=total_amount,
            notes=notes,
            created_by=created_by,
        )

        purchase_order.save()

        return purchase_order

    @staticmethod
    def get_by_id(
        *,
        organization,
        purchase_order_id,
    ):
        """
        Get a Purchase Order within an organization.
        """

        return (
            PurchaseOrderRepository
            .queryset_for_organization(
                organization=organization,
            )
            .filter(
                id=purchase_order_id,
            )
            .first()
        )

    @staticmethod
    def get_by_po_number(
        *,
        organization,
        po_number,
    ):
        """
        Get a Purchase Order using its PO number.
        """

        return (
            PurchaseOrderRepository
            .queryset_for_organization(
                organization=organization,
            )
            .filter(
                po_number=po_number,
            )
            .first()
        )

    @staticmethod
    def list_by_organization(
        *,
        organization,
    ):
        """
        List all Purchase Orders for an organization.
        """

        return (
            PurchaseOrderRepository
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
        """
        List Purchase Orders for a supplier.
        """

        return (
            PurchaseOrderRepository
            .queryset_for_organization(
                organization=organization,
            )
            .filter(
                supplier=supplier,
            )
            .order_by(
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
        """
        List Purchase Orders by status.
        """

        return (
            PurchaseOrderRepository
            .queryset_for_organization(
                organization=organization,
            )
            .filter(
                status=status,
            )
            .order_by(
                "-created_at",
                "-id",
            )
        )

    @staticmethod
    def update_purchase_order(
        *,
        purchase_order,
        supplier=None,
        order_date=None,
        expected_delivery_date=None,
        items=None,
        subtotal=None,
        tax_amount=None,
        discount_amount=None,
        total_amount=None,
        notes=None,
    ):
        """
        Update editable Purchase Order fields.
        """

        if supplier is not None:
            purchase_order.supplier = (
                supplier
            )

        if order_date is not None:
            purchase_order.order_date = (
                order_date
            )

        if expected_delivery_date is not None:
            (
                purchase_order
                .expected_delivery_date
            ) = expected_delivery_date

        if items is not None:
            purchase_order.items = items

        if subtotal is not None:
            purchase_order.subtotal = (
                subtotal
            )

        if tax_amount is not None:
            purchase_order.tax_amount = (
                tax_amount
            )

        if discount_amount is not None:
            (
                purchase_order
                .discount_amount
            ) = discount_amount

        if total_amount is not None:
            purchase_order.total_amount = (
                total_amount
            )

        if notes is not None:
            purchase_order.notes = notes

        purchase_order.updated_at = (
            datetime.utcnow()
        )

        purchase_order.save()

        return purchase_order

    @staticmethod
    def update_status(
        *,
        purchase_order,
        status,
        confirmed_at=None,
        cancelled_at=None,
    ):
        """
        Persist a Purchase Order status change.
        """

        purchase_order.status = status

        if confirmed_at is not None:
            purchase_order.confirmed_at = (
                confirmed_at
            )

        if cancelled_at is not None:
            purchase_order.cancelled_at = (
                cancelled_at
            )

        purchase_order.updated_at = (
            datetime.utcnow()
        )

        purchase_order.save()

        return purchase_order

    @staticmethod
    def update_received_quantities(
        *,
        purchase_order,
        items,
        status,
    ):
        """
        Persist received quantities and receipt status.
        """

        purchase_order.items = items
        purchase_order.status = status
        purchase_order.updated_at = (
            datetime.utcnow()
        )

        purchase_order.save()

        return purchase_order