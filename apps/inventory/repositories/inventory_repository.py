from datetime import datetime

from mongoengine.errors import (
    ValidationError, SaveConditionError,
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
            ValidationError, SaveConditionError,
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
        return InventoryRepository._write_balances(inventory, quantity=quantity)

    @staticmethod
    def update_reserved_quantity(*, inventory, reserved_quantity):
        return InventoryRepository._write_balances(inventory, reserved_quantity=reserved_quantity)

    @staticmethod
    def update_balances(*, inventory, quantity, reserved_quantity):
        return InventoryRepository._write_balances(inventory, quantity=quantity, reserved_quantity=reserved_quantity)

    @staticmethod
    def _write_balances(inventory, **changes):
        # Another stock workflow may have committed since the caller calculated its delta.
        old = {key: getattr(inventory, key) for key in ("quantity", "reserved_quantity", "updated_at")}
        conditions = [
            {"$eq": [{"$ifNull": ["$" + key, 0]}, float(old[key] or 0)]}
            for key in ("quantity", "reserved_quantity")
        ]
        for key, value in changes.items():
            setattr(inventory, key, value)
        inventory.updated_at = datetime.utcnow()
        try:
            inventory.save(save_condition={"__raw__": {"$expr": {"$and": conditions}}})
        except SaveConditionError as error:
            for key, value in old.items():
                setattr(inventory, key, value)
            raise ValueError("Stock changed during this operation. Refresh the balance before retrying.") from error
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