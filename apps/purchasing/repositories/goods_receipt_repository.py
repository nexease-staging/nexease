from apps.purchasing.models import GoodsReceipt


class GoodsReceiptRepository:

    @staticmethod
    def create_goods_receipt(
        *,
        organization,
        grn_number,
        purchase_order,
        supplier,
        warehouse,
        items,
        notes,
        received_by,
    ):
        """
        Create a goods receipt record.
        """

        goods_receipt = GoodsReceipt(
            organization=organization,
            grn_number=grn_number,
            purchase_order=purchase_order,
            supplier=supplier,
            warehouse=warehouse,
            items=items,
            notes=notes,
            received_by=received_by,
        )

        goods_receipt.save()

        return goods_receipt

    @staticmethod
    def get_by_id(
        *,
        organization,
        goods_receipt_id,
    ):
        """
        Get one GRN within an organization.
        """

        return GoodsReceipt.objects(
            organization=organization,
            id=goods_receipt_id,
        ).first()

    @staticmethod
    def get_by_grn_number(
        *,
        organization,
        grn_number,
    ):
        """
        Get a GRN by its unique GRN number.
        """

        return GoodsReceipt.objects(
            organization=organization,
            grn_number=grn_number,
        ).first()

    @staticmethod
    def list_by_organization(
        *,
        organization,
    ):
        """
        List all GRNs for an organization.
        """

        return GoodsReceipt.objects(
            organization=organization,
        ).order_by(
            "-created_at"
        )

    @staticmethod
    def list_by_purchase_order(
        *,
        organization,
        purchase_order,
    ):
        """
        List all GRNs against a purchase order.
        """

        return GoodsReceipt.objects(
            organization=organization,
            purchase_order=purchase_order,
        ).order_by(
            "-created_at"
        )

    @staticmethod
    def list_by_supplier(
        *,
        organization,
        supplier,
    ):
        """
        List all GRNs for a supplier.
        """

        return GoodsReceipt.objects(
            organization=organization,
            supplier=supplier,
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
        List all GRNs received into a warehouse.
        """

        return GoodsReceipt.objects(
            organization=organization,
            warehouse=warehouse,
        ).order_by(
            "-created_at"
        )