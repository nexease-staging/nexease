from mongoengine.errors import (
    ValidationError,
)

from apps.inventory.models import (
    StockTransfer,
)


class StockTransferRepository:

    @staticmethod
    def queryset_for_organization(
        *,
        organization,
    ):
        return StockTransfer.objects(
            organization=organization,
        )

    @staticmethod
    def create_transfer(
        *,
        organization,
        transfer_number,
        product,
        source_warehouse,
        destination_warehouse,
        source_inventory,
        destination_inventory,
        quantity,
        status,
        notes,
        created_by,
        completed_at=None,
    ):
        transfer = StockTransfer(
            organization=organization,
            transfer_number=transfer_number,
            product=product,
            source_warehouse=source_warehouse,
            destination_warehouse=destination_warehouse,
            source_inventory=source_inventory,
            destination_inventory=destination_inventory,
            quantity=quantity,
            status=status,
            notes=notes,
            created_by=created_by,
            completed_at=completed_at,
        )

        transfer.save()

        return transfer

    @staticmethod
    def get_by_id(
        *,
        organization,
        transfer_id,
    ):
        try:

            return (
                StockTransferRepository
                .queryset_for_organization(
                    organization=organization,
                )
                .filter(
                    id=transfer_id,
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
    def get_by_transfer_number(
        *,
        organization,
        transfer_number,
    ):
        return (
            StockTransferRepository
            .queryset_for_organization(
                organization=organization,
            )
            .filter(
                transfer_number=transfer_number,
            )
            .first()
        )

    @staticmethod
    def list_by_organization(
        *,
        organization,
    ):
        return (
            StockTransferRepository
            .queryset_for_organization(
                organization=organization,
            )
            .order_by(
                "-created_at",
                "-id",
            )
        )

    @staticmethod
    def list_by_product(
        *,
        organization,
        product,
    ):
        return (
            StockTransferRepository
            .queryset_for_organization(
                organization=organization,
            )
            .filter(
                product=product,
            )
            .order_by(
                "-created_at",
                "-id",
            )
        )

    @staticmethod
    def list_by_source_warehouse(
        *,
        organization,
        warehouse,
    ):
        return (
            StockTransferRepository
            .queryset_for_organization(
                organization=organization,
            )
            .filter(
                source_warehouse=warehouse,
            )
            .order_by(
                "-created_at",
                "-id",
            )
        )

    @staticmethod
    def list_by_destination_warehouse(
        *,
        organization,
        warehouse,
    ):
        return (
            StockTransferRepository
            .queryset_for_organization(
                organization=organization,
            )
            .filter(
                destination_warehouse=warehouse,
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
        return (
            StockTransferRepository
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
    def update_status(
        *,
        transfer,
        status,
        completed_at=None,
    ):
        transfer.status = status
        transfer.completed_at = completed_at

        transfer.save()

        return transfer

    @staticmethod
    def delete_transfer(
        *,
        transfer,
    ):
        if not transfer:
            return False

        transfer.delete()

        return True