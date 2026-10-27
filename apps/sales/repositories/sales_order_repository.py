from datetime import datetime

from apps.sales.models import SalesOrder


class SalesOrderRepository:

    @staticmethod
    def queryset_for_organization(
        *,
        organization,
    ):
        """
        Return the tenant-scoped Sales Order queryset
        used by API filtering, searching, sorting,
        and pagination.
        """

        return SalesOrder.objects(
            organization=organization,
        )
    @staticmethod
    def create_sales_order(
        *,
        organization,
        so_number,
        customer,
        warehouse,
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
        Create a sales order.
        """

        sales_order = SalesOrder(
            organization=organization,
            so_number=so_number,
            customer=customer,
            warehouse=warehouse,
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

        sales_order.save()

        return sales_order

    @staticmethod
    def get_by_id(
        *,
        organization,
        sales_order_id,
    ):
        """
        Get a sales order within an organization.
        """

        return SalesOrder.objects(
            organization=organization,
            id=sales_order_id,
        ).first()

    @staticmethod
    def get_by_so_number(
        *,
        organization,
        so_number,
    ):
        """
        Get a sales order by SO number.
        """

        return SalesOrder.objects(
            organization=organization,
            so_number=so_number,
        ).first()

    @staticmethod
    def list_by_organization(
        *,
        organization,
    ):
        """
        List all sales orders for an organization.
        """

        return (
            SalesOrderRepository
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
        """
        List sales orders for a customer.
        """

        return SalesOrder.objects(
            organization=organization,
            customer=customer,
        ).order_by(
            "-created_at"
        )

    @staticmethod
    def list_by_warehouse(
        *,
        organization,
        warehouse,
    ):
        """
        List sales orders for a warehouse.
        """

        return SalesOrder.objects(
            organization=organization,
            warehouse=warehouse,
        ).order_by(
            "-created_at"
        )

    @staticmethod
    def list_by_status(
        *,
        organization,
        status,
    ):
        """
        List sales orders by status.
        """

        return SalesOrder.objects(
            organization=organization,
            status=status,
        ).order_by(
            "-created_at"
        )

    @staticmethod
    def update_sales_order(
        *,
        sales_order,
        customer=None,
        warehouse=None,
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
        Update editable sales-order fields.

        Rules about which statuses can be edited
        belong in the service layer.
        """

        if customer is not None:
            sales_order.customer = customer

        if warehouse is not None:
            sales_order.warehouse = warehouse

        if order_date is not None:
            sales_order.order_date = (
                order_date
            )

        if expected_delivery_date is not None:
            sales_order.expected_delivery_date = (
                expected_delivery_date
            )

        if items is not None:
            sales_order.items = items

        if subtotal is not None:
            sales_order.subtotal = subtotal

        if tax_amount is not None:
            sales_order.tax_amount = (
                tax_amount
            )

        if discount_amount is not None:
            sales_order.discount_amount = (
                discount_amount
            )

        if total_amount is not None:
            sales_order.total_amount = (
                total_amount
            )

        if notes is not None:
            sales_order.notes = notes

        sales_order.updated_at = (
            datetime.utcnow()
        )

        sales_order.save()

        return sales_order

    @staticmethod
    def update_status(
        *,
        sales_order,
        status,
        confirmed_at=None,
        fulfilled_at=None,
        cancelled_at=None,
    ):
        """
        Persist a sales-order status transition.
        """

        sales_order.status = status

        if confirmed_at is not None:
            sales_order.confirmed_at = (
                confirmed_at
            )

        if fulfilled_at is not None:
            sales_order.fulfilled_at = (
                fulfilled_at
            )

        if cancelled_at is not None:
            sales_order.cancelled_at = (
                cancelled_at
            )

        sales_order.updated_at = (
            datetime.utcnow()
        )

        sales_order.save()

        return sales_order

    @staticmethod
    def update_fulfilled_quantities(
        *,
        sales_order,
        items,
        status,
        fulfilled_at=None,
    ):
        """
        Persist item fulfilment quantities
        and the resulting order status.
        """

        sales_order.items = items
        sales_order.status = status

        if fulfilled_at is not None:
            sales_order.fulfilled_at = (
                fulfilled_at
            )

        sales_order.updated_at = (
            datetime.utcnow()
        )

        sales_order.save()

        return sales_order