from mongoengine.errors import (
    ValidationError,
)

from apps.inventory.models import (
    StockMovement,
)


class StockMovementRepository:

    @staticmethod
    def queryset_for_organization(
        *,
        organization,
    ):
        return StockMovement.objects(
            organization=organization,
        )

    @staticmethod
    def create_movement(
        *,
        organization,
        inventory,
        product,
        warehouse,
        movement_type,
        quantity,
        quantity_before,
        quantity_after,
        reserved_before,
        reserved_after,
        created_by,
        reference_type="",
        reference_id="",
        notes="",
    ):
        movement = StockMovement(
            organization=organization,
            inventory=inventory,
            product=product,
            warehouse=warehouse,
            movement_type=movement_type,
            quantity=quantity,
            quantity_before=quantity_before,
            quantity_after=quantity_after,
            reserved_before=reserved_before,
            reserved_after=reserved_after,
            reference_type=reference_type,
            reference_id=reference_id,
            notes=notes,
            created_by=created_by,
        )

        movement.save()

        return movement

    @staticmethod
    def get_by_id(
        *,
        organization,
        movement_id,
    ):
        try:

            return (
                StockMovementRepository
                .queryset_for_organization(
                    organization=organization,
                )
                .filter(
                    id=movement_id,
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
    def list_by_organization(
        *,
        organization,
    ):
        return (
            StockMovementRepository
            .queryset_for_organization(
                organization=organization,
            )
            .order_by(
                "-created_at",
                "-id",
            )
        )

    @staticmethod
    def list_by_inventory(
        *,
        organization,
        inventory,
    ):
        return (
            StockMovementRepository
            .queryset_for_organization(
                organization=organization,
            )
            .filter(
                inventory=inventory,
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
            StockMovementRepository
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
    def list_by_warehouse(
        *,
        organization,
        warehouse,
    ):
        return (
            StockMovementRepository
            .queryset_for_organization(
                organization=organization,
            )
            .filter(
                warehouse=warehouse,
            )
            .order_by(
                "-created_at",
                "-id",
            )
        )

    @staticmethod
    def list_by_type(
        *,
        organization,
        movement_type,
    ):
        return (
            StockMovementRepository
            .queryset_for_organization(
                organization=organization,
            )
            .filter(
                movement_type=movement_type,
            )
            .order_by(
                "-created_at",
                "-id",
            )
        )

    @staticmethod
    def delete_movement(
        *,
        movement,
    ):
        if not movement:
            return False

        movement.delete()

        return True