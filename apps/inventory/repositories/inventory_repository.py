from datetime import datetime

from mongoengine.errors import (
    ValidationError,
)

from apps.inventory.models import (
    Inventory,
)


class InventoryRepository:

    @staticmethod
    def queryset_for_organization(
        *,
        organization,
    ):
        return Inventory.objects(
            organization=organization,
        )

    @staticmethod
    def get_by_id(
        *,
        organization,
        inventory_id,
    ):
        try:

            return (
                InventoryRepository
                .queryset_for_organization(
                    organization=organization,
                )
                .filter(
                    id=inventory_id,
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
    def get_by_product_and_warehouse(
        *,
        organization,
        product,
        warehouse,
    ):
        return (
            InventoryRepository
            .queryset_for_organization(
                organization=organization,
            )
            .filter(
                product=product,
                warehouse=warehouse,
            )
            .first()
        )

    @staticmethod
    def exists_for_product_and_warehouse(
        *,
        organization,
        product,
        warehouse,
    ):
        return (
            InventoryRepository
            .get_by_product_and_warehouse(
                organization=organization,
                product=product,
                warehouse=warehouse,
            )
            is not None
        )

    @staticmethod
    def list_by_organization(
        *,
        organization,
    ):
        return (
            InventoryRepository
            .queryset_for_organization(
                organization=organization,
            )
            .order_by(
                "-updated_at",
                "-id",
            )
        )

    @staticmethod
    def list_by_warehouse(
        *,
        organization,
        warehouse,
    ):
        return (
            InventoryRepository
            .queryset_for_organization(
                organization=organization,
            )
            .filter(
                warehouse=warehouse,
            )
            .order_by(
                "-updated_at",
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
            InventoryRepository
            .queryset_for_organization(
                organization=organization,
            )
            .filter(
                product=product,
            )
            .order_by(
                "-updated_at",
                "-id",
            )
        )

    @staticmethod
    def create_inventory(
        *,
        organization,
        product,
        warehouse,
        quantity=0,
        reserved_quantity=0,
    ):
        inventory = Inventory(
            organization=organization,
            product=product,
            warehouse=warehouse,
            quantity=quantity,
            reserved_quantity=reserved_quantity,
        )

        inventory.save()

        return inventory

    @staticmethod
    def update_quantity(
        *,
        inventory,
        quantity,
    ):
        inventory.quantity = quantity
        inventory.updated_at = (
            datetime.utcnow()
        )

        inventory.save()

        return inventory

    @staticmethod
    def update_reserved_quantity(
        *,
        inventory,
        reserved_quantity,
    ):
        inventory.reserved_quantity = (
            reserved_quantity
        )

        inventory.updated_at = (
            datetime.utcnow()
        )

        inventory.save()

        return inventory

    @staticmethod
    def update_balances(
        *,
        inventory,
        quantity,
        reserved_quantity,
    ):
        inventory.quantity = quantity
        inventory.reserved_quantity = (
            reserved_quantity
        )

        inventory.updated_at = (
            datetime.utcnow()
        )

        inventory.save()

        return inventory

    @staticmethod
    def delete_inventory(
        *,
        inventory,
    ):
        if not inventory:
            return False

        inventory.delete()

        return True