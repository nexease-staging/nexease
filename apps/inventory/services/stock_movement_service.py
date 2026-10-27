from decimal import Decimal

from apps.authorization.services import AuthorizationService

from apps.inventory.repositories.stock_movement_repository import (
    StockMovementRepository,
)


class StockMovementService:

    VALID_MOVEMENT_TYPES = {
        "OPENING_STOCK",
        "STOCK_IN",
        "STOCK_OUT",
        "ADJUSTMENT_IN",
        "ADJUSTMENT_OUT",
        "RESERVATION",
        "RESERVATION_RELEASE",
        "TRANSFER_OUT",
        "TRANSFER_IN",
        "SALES_RETURN",
        "PURCHASE_RETURN",
    }

    @staticmethod
    def _check_permission(
        user,
        permission_code,
    ):
        if not user:
            raise ValueError(
                "User is required."
            )

        if not user.is_active:
            raise ValueError(
                "User is inactive."
            )

        if not AuthorizationService.has_permission(
            user,
            permission_code,
        ):
            raise PermissionError(
                f"Permission denied: {permission_code}"
            )

    @staticmethod
    def _check_organization(
        user,
        organization,
    ):
        if not organization:
            raise ValueError(
                "Organization is required."
            )

        if not user.organization:
            raise ValueError(
                "User has no organization."
            )

        if user.organization.id != organization.id:
            raise PermissionError(
                "User does not belong to this organization."
            )

    @staticmethod
    def create_movement(
        *,
        user,
        organization,
        inventory,
        movement_type,
        quantity,
        quantity_before,
        quantity_after,
        reserved_before,
        reserved_after,
        reference_type="",
        reference_id="",
        notes="",
    ):
        """
        Create an immutable stock movement record.
        """

        StockMovementService._check_permission(
            user,
            "inventory.adjust",
        )

        StockMovementService._check_organization(
            user,
            organization,
        )

        if not inventory:
            raise ValueError(
                "Inventory is required."
            )

        if inventory.organization.id != organization.id:
            raise PermissionError(
                "Inventory does not belong to this organization."
            )

        if inventory.product.organization.id != organization.id:
            raise PermissionError(
                "Product does not belong to this organization."
            )

        if inventory.warehouse.organization.id != organization.id:
            raise PermissionError(
                "Warehouse does not belong to this organization."
            )

        if movement_type not in (
            StockMovementService.VALID_MOVEMENT_TYPES
        ):
            raise ValueError(
                "Invalid stock movement type."
            )

        quantity = Decimal(
            str(quantity)
        )

        quantity_before = Decimal(
            str(quantity_before)
        )

        quantity_after = Decimal(
            str(quantity_after)
        )

        reserved_before = Decimal(
            str(reserved_before)
        )

        reserved_after = Decimal(
            str(reserved_after)
        )

        if quantity == 0:
            raise ValueError(
                "Movement quantity cannot be zero."
            )

        if quantity_before < 0:
            raise ValueError(
                "Quantity before cannot be negative."
            )

        if quantity_after < 0:
            raise ValueError(
                "Quantity after cannot be negative."
            )

        if reserved_before < 0:
            raise ValueError(
                "Reserved quantity before cannot be negative."
            )

        if reserved_after < 0:
            raise ValueError(
                "Reserved quantity after cannot be negative."
            )

        if reserved_before > quantity_before:
            raise ValueError(
                "Reserved quantity before cannot exceed quantity before."
            )

        if reserved_after > quantity_after:
            raise ValueError(
                "Reserved quantity after cannot exceed quantity after."
            )

        return StockMovementRepository.create_movement(
            organization=organization,
            inventory=inventory,
            product=inventory.product,
            warehouse=inventory.warehouse,
            movement_type=movement_type,
            quantity=quantity,
            quantity_before=quantity_before,
            quantity_after=quantity_after,
            reserved_before=reserved_before,
            reserved_after=reserved_after,
            created_by=user,
            reference_type=reference_type.strip(),
            reference_id=reference_id.strip(),
            notes=notes.strip(),
        )

    @staticmethod
    def get_movement(
        *,
        user,
        organization,
        movement_id,
    ):
        StockMovementService._check_permission(
            user,
            "inventory.read",
        )

        StockMovementService._check_organization(
            user,
            organization,
        )

        movement = StockMovementRepository.get_by_id(
            organization=organization,
            movement_id=movement_id,
        )

        if not movement:
            raise ValueError(
                "Stock movement not found."
            )

        return movement

    @staticmethod
    def list_movements(
        *,
        user,
        organization,
    ):
        StockMovementService._check_permission(
            user,
            "inventory.read",
        )

        StockMovementService._check_organization(
            user,
            organization,
        )

        return (
            StockMovementRepository
            .list_by_organization(
                organization=organization,
            )
        )

    @staticmethod
    def list_inventory_movements(
        *,
        user,
        organization,
        inventory,
    ):
        StockMovementService._check_permission(
            user,
            "inventory.read",
        )

        StockMovementService._check_organization(
            user,
            organization,
        )

        if not inventory:
            raise ValueError(
                "Inventory is required."
            )

        if inventory.organization.id != organization.id:
            raise PermissionError(
                "Inventory does not belong to this organization."
            )

        return (
            StockMovementRepository
            .list_by_inventory(
                organization=organization,
                inventory=inventory,
            )
        )

    @staticmethod
    def list_product_movements(
        *,
        user,
        organization,
        product,
    ):
        StockMovementService._check_permission(
            user,
            "inventory.read",
        )

        StockMovementService._check_organization(
            user,
            organization,
        )

        if not product:
            raise ValueError(
                "Product is required."
            )

        if product.organization.id != organization.id:
            raise PermissionError(
                "Product does not belong to this organization."
            )

        return StockMovementRepository.list_by_product(
            organization=organization,
            product=product,
        )

    @staticmethod
    def list_warehouse_movements(
        *,
        user,
        organization,
        warehouse,
    ):
        StockMovementService._check_permission(
            user,
            "inventory.read",
        )

        StockMovementService._check_organization(
            user,
            organization,
        )

        if not warehouse:
            raise ValueError(
                "Warehouse is required."
            )

        if warehouse.organization.id != organization.id:
            raise PermissionError(
                "Warehouse does not belong to this organization."
            )

        return StockMovementRepository.list_by_warehouse(
            organization=organization,
            warehouse=warehouse,
        )

    @staticmethod
    def list_movements_by_type(
        *,
        user,
        organization,
        movement_type,
    ):
        StockMovementService._check_permission(
            user,
            "inventory.read",
        )

        StockMovementService._check_organization(
            user,
            organization,
        )

        if movement_type not in (
            StockMovementService.VALID_MOVEMENT_TYPES
        ):
            raise ValueError(
                "Invalid stock movement type."
            )

        return StockMovementRepository.list_by_type(
            organization=organization,
            movement_type=movement_type,
        )