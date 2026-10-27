from decimal import Decimal
from mongoengine.errors import NotUniqueError

from apps.authorization.services import AuthorizationService
from apps.inventory.models import Inventory

from apps.inventory.services.stock_movement_service import (
    StockMovementService,
)
from apps.inventory.repositories.inventory_repository import (
    InventoryRepository,
)


class InventoryService:

    @staticmethod
    def _check_permission(
        user,
        permission_code,
    ):
        """
        Check whether the authenticated user
        has the required permission.
        """

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
        """
        Ensure the user belongs to the
        organization being accessed.
        """

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
    def _validate_product(
        product,
        organization,
    ):
        """
        Ensure the product belongs to
        the same organization.
        """

        if not product:
            raise ValueError(
                "Product is required."
            )

        if product.organization.id != organization.id:
            raise PermissionError(
                "Product does not belong to this organization."
            )

    @staticmethod
    def _validate_warehouse(
        warehouse,
        organization,
    ):
        """
        Ensure the warehouse belongs to
        the same organization.
        """

        if not warehouse:
            raise ValueError(
                "Warehouse is required."
            )

        if warehouse.organization.id != organization.id:
            raise PermissionError(
                "Warehouse does not belong to this organization."
            )

    @staticmethod
    def create_inventory(
        *,
        user,
        organization,
        product,
        warehouse,
        quantity=0,
        reserved_quantity=0,
    ):
        """
        Create inventory for a product
        at a specific warehouse.
        """

        InventoryService._check_permission(
            user,
            "inventory.create",
        )

        InventoryService._check_organization(
            user,
            organization,
        )

        InventoryService._validate_product(
            product,
            organization,
        )

        InventoryService._validate_warehouse(
            warehouse,
            organization,
        )

        quantity = Decimal(
            str(quantity)
        )

        reserved_quantity = Decimal(
            str(reserved_quantity)
        )

        if quantity < 0:
            raise ValueError(
                "Quantity cannot be negative."
            )

        if reserved_quantity < 0:
            raise ValueError(
                "Reserved quantity cannot be negative."
            )

        if reserved_quantity > quantity:
            raise ValueError(
                "Reserved quantity cannot exceed quantity."
            )

        existing = (
            InventoryRepository
            .get_by_product_and_warehouse(
                organization=organization,
                product=product,
                warehouse=warehouse,
            )
        )

        if existing:
            raise ValueError(
                "Inventory already exists for "
                "this product and warehouse."
            )

        try:
            inventory = InventoryRepository.create_inventory(
                organization=organization,
                product=product,
                warehouse=warehouse,
                quantity=quantity,
                reserved_quantity=reserved_quantity,
            )

        except NotUniqueError:
            raise ValueError(
                "Inventory already exists for "
                "this product and warehouse."
            )

        # Create opening-stock ledger entry only
        # when physical opening quantity is greater than zero.
        if quantity > 0:
            StockMovementService.create_movement(
                user=user,
                organization=organization,
                inventory=inventory,
                movement_type="OPENING_STOCK",
                quantity=quantity,
                quantity_before=Decimal("0"),
                quantity_after=quantity,
                reserved_before=Decimal("0"),
                reserved_after=reserved_quantity,
                reference_type="OPENING_STOCK",
                reference_id="",
                notes="Initial inventory quantity",
            )

        return inventory

    @staticmethod
    def get_inventory(
        *,
        user,
        organization,
        inventory_id,
    ):
        """
        Retrieve one inventory record.
        """

        InventoryService._check_permission(
            user,
            "inventory.read",
        )

        InventoryService._check_organization(
            user,
            organization,
        )

        inventory = InventoryRepository.get_by_id(
            organization=organization,
            inventory_id=inventory_id,
        )

        if not inventory:
            raise ValueError(
                "Inventory not found."
            )

        return inventory

    @staticmethod
    def get_inventory_by_product_and_warehouse(
        *,
        user,
        organization,
        product,
        warehouse,
    ):
        """
        Retrieve inventory for a specific
        product and warehouse.
        """

        InventoryService._check_permission(
            user,
            "inventory.read",
        )

        InventoryService._check_organization(
            user,
            organization,
        )

        InventoryService._validate_product(
            product,
            organization,
        )

        InventoryService._validate_warehouse(
            warehouse,
            organization,
        )

        inventory = (
            InventoryRepository
            .get_by_product_and_warehouse(
                organization=organization,
                product=product,
                warehouse=warehouse,
            )
        )

        if not inventory:
            raise ValueError(
                "Inventory not found."
            )

        return inventory

    @staticmethod
    def list_inventory(
        *,
        user,
        organization,
    ):
        """
        Return all inventory belonging
        to the organization.
        """

        InventoryService._check_permission(
            user,
            "inventory.read",
        )

        InventoryService._check_organization(
            user,
            organization,
        )

        return InventoryRepository.list_by_organization(
            organization=organization,
        )

    @staticmethod
    def list_inventory_by_warehouse(
        *,
        user,
        organization,
        warehouse,
    ):
        """
        Return inventory for a warehouse.
        """

        InventoryService._check_permission(
            user,
            "inventory.read",
        )

        InventoryService._check_organization(
            user,
            organization,
        )

        InventoryService._validate_warehouse(
            warehouse,
            organization,
        )

        return InventoryRepository.list_by_warehouse(
            organization=organization,
            warehouse=warehouse,
        )

    @staticmethod
    def list_inventory_by_product(
        *,
        user,
        organization,
        product,
    ):
        """
        Return inventory for a product.
        """

        InventoryService._check_permission(
            user,
            "inventory.read",
        )

        InventoryService._check_organization(
            user,
            organization,
        )

        InventoryService._validate_product(
            product,
            organization,
        )

        return InventoryRepository.list_by_product(
            organization=organization,
            product=product,
        )

    @staticmethod
    def adjust_quantity(
        *,
        user,
        organization,
        inventory_id,
        quantity_change,
        reference_type="",
        reference_id="",
        notes="",
    ):
        """
        Increase or decrease inventory quantity
        and create a stock movement record.
        """

        InventoryService._check_permission(
            user,
            "inventory.adjust",
        )

        InventoryService._check_organization(
            user,
            organization,
        )

        quantity_change = Decimal(
            str(quantity_change)
        )

        if quantity_change == 0:
            raise ValueError(
                "Quantity change cannot be zero."
            )

        inventory = InventoryRepository.get_by_id(
            organization=organization,
            inventory_id=inventory_id,
        )

        if not inventory:
            raise ValueError(
                "Inventory not found."
            )

        quantity_before = inventory.quantity
        reserved_before = inventory.reserved_quantity

        quantity_after = (
            quantity_before
            + quantity_change
        )

        if quantity_after < 0:
            raise ValueError(
                "Inventory quantity cannot become negative."
            )

        if reserved_before > quantity_after:
            raise ValueError(
                "Quantity cannot be lower than "
                "reserved quantity."
            )

        if quantity_change > 0:
            movement_type = "ADJUSTMENT_IN"
        else:
            movement_type = "ADJUSTMENT_OUT"

        try:

            inventory = (
                InventoryRepository
                .update_quantity(
                    inventory=inventory,
                    quantity=quantity_after,
                )
            )

            (
                StockMovementService
                .create_movement(
                    user=user,
                    organization=organization,
                    inventory=inventory,
                    movement_type=movement_type,
                    quantity=quantity_change,
                    quantity_before=quantity_before,
                    quantity_after=quantity_after,
                    reserved_before=reserved_before,
                    reserved_after=(
                        inventory
                        .reserved_quantity
                    ),
                    reference_type=reference_type,
                    reference_id=reference_id,
                    notes=notes,
                )
            )

        except Exception:

            # Best-effort rollback so a failed
            # ledger write does not leave the
            # inventory balance changed.
            try:

                inventory = (
                    InventoryRepository
                    .update_quantity(
                        inventory=inventory,
                        quantity=quantity_before,
                    )
                )

            except Exception:
                pass

            raise

        return inventory

    @staticmethod
    def reserve_quantity(
        *,
        user,
        organization,
        inventory_id,
        quantity,
        reference_type="",
        reference_id="",
        notes="",
    ):
        """
        Reserve inventory and record the
        reservation in the stock ledger.
        """

        InventoryService._check_permission(
            user,
            "inventory.adjust",
        )

        InventoryService._check_organization(
            user,
            organization,
        )

        quantity = Decimal(
            str(quantity)
        )

        if quantity <= 0:
            raise ValueError(
                "Reservation quantity must be greater than zero."
            )

        inventory = InventoryRepository.get_by_id(
            organization=organization,
            inventory_id=inventory_id,
        )

        if not inventory:
            raise ValueError(
                "Inventory not found."
            )

        quantity_before = inventory.quantity
        reserved_before = inventory.reserved_quantity

        available_quantity = (
            quantity_before
            - reserved_before
        )

        if quantity > available_quantity:
            raise ValueError(
                "Insufficient available inventory."
            )

        reserved_after = (
            reserved_before
            + quantity
        )

        inventory = (
            InventoryRepository
            .update_reserved_quantity(
                inventory=inventory,
                reserved_quantity=reserved_after,
            )
        )

        StockMovementService.create_movement(
            user=user,
            organization=organization,
            inventory=inventory,
            movement_type="RESERVATION",
            quantity=quantity,
            quantity_before=quantity_before,
            quantity_after=quantity_before,
            reserved_before=reserved_before,
            reserved_after=reserved_after,
            reference_type=reference_type,
            reference_id=reference_id,
            notes=notes,
        )

        return inventory

    @staticmethod
    def release_reserved_quantity(
        *,
        user,
        organization,
        inventory_id,
        quantity,
        reference_type="",
        reference_id="",
        notes="",
    ):
        """
        Release reserved inventory and
        record the movement.
        """

        InventoryService._check_permission(
            user,
            "inventory.adjust",
        )

        InventoryService._check_organization(
            user,
            organization,
        )

        quantity = Decimal(
            str(quantity)
        )

        if quantity <= 0:
            raise ValueError(
                "Release quantity must be greater than zero."
            )

        inventory = InventoryRepository.get_by_id(
            organization=organization,
            inventory_id=inventory_id,
        )

        if not inventory:
            raise ValueError(
                "Inventory not found."
            )

        quantity_before = inventory.quantity
        reserved_before = inventory.reserved_quantity

        if quantity > reserved_before:
            raise ValueError(
                "Cannot release more than reserved quantity."
            )

        reserved_after = (
            reserved_before
            - quantity
        )

        inventory = (
            InventoryRepository
            .update_reserved_quantity(
                inventory=inventory,
                reserved_quantity=reserved_after,
            )
        )

        StockMovementService.create_movement(
            user=user,
            organization=organization,
            inventory=inventory,
            movement_type="RESERVATION_RELEASE",
            quantity=-quantity,
            quantity_before=quantity_before,
            quantity_after=quantity_before,
            reserved_before=reserved_before,
            reserved_after=reserved_after,
            reference_type=reference_type,
            reference_id=reference_id,
            notes=notes,
        )

        return inventory

    @staticmethod
    def record_business_movement(
        *,
        user,
        organization,
        product,
        warehouse,
        quantity_change,
        movement_type,
        reference_type="",
        reference_id="",
        notes="",
    ):
        """
        Apply a business-driven physical stock movement.

        Examples:
        SALES_RETURN
        PURCHASE_RETURN
        """

        InventoryService._check_organization(
            user,
            organization,
        )

        allowed_types = {
            "SALES_RETURN",
            "PURCHASE_RETURN",
        }

        if movement_type not in allowed_types:
            raise ValueError(
                "Invalid business movement type."
            )

        quantity_change = Decimal(
            str(quantity_change)
        )

        if quantity_change == 0:
            raise ValueError(
                "Quantity change cannot be zero."
            )

        if (
            product.organization.id
            != organization.id
        ):
            raise PermissionError(
                "Product does not belong "
                "to this organization."
            )

        if (
            warehouse.organization.id
            != organization.id
        ):
            raise PermissionError(
                "Warehouse does not belong "
                "to this organization."
            )

        inventory = (
            InventoryRepository
            .get_by_product_and_warehouse(
                organization=organization,
                product=product,
                warehouse=warehouse,
            )
        )

        if not inventory:
            if quantity_change < 0:
                raise ValueError(
                    "Inventory does not exist "
                    "for this product and warehouse."
                )

            inventory = (
                InventoryRepository
                .create_inventory(
                    organization=organization,
                    product=product,
                    warehouse=warehouse,
                    quantity=0,
                    reserved_quantity=0,
                )
            )

        quantity_before = (
            inventory.quantity
        )

        reserved_before = (
            inventory.reserved_quantity
        )

        quantity_after = (
            quantity_before
            + quantity_change
        )

        if quantity_after < 0:
            raise ValueError(
                "Inventory quantity cannot "
                "become negative."
            )

        if (
            reserved_before
            > quantity_after
        ):
            raise ValueError(
                "Quantity cannot be lower "
                "than reserved quantity."
            )

        if (
            movement_type == "SALES_RETURN"
            and quantity_change < 0
        ):
            raise ValueError(
                "Sales return quantity "
                "must increase inventory."
            )

        if (
            movement_type == "PURCHASE_RETURN"
            and quantity_change > 0
        ):
            raise ValueError(
                "Purchase return quantity "
                "must decrease inventory."
            )

        try:
            inventory = (
                InventoryRepository
                .update_quantity(
                    inventory=inventory,
                    quantity=quantity_after,
                )
            )

            StockMovementService.create_movement(
                user=user,
                organization=organization,
                inventory=inventory,
                movement_type=movement_type,
                quantity=quantity_change,
                quantity_before=quantity_before,
                quantity_after=quantity_after,
                reserved_before=reserved_before,
                reserved_after=(
                    inventory.reserved_quantity
                ),
                reference_type=reference_type,
                reference_id=reference_id,
                notes=notes,
            )

        except Exception:
            #
            # Best-effort rollback so inventory does not
            # remain changed when movement creation fails.
            #
            try:
                InventoryRepository.update_quantity(
                    inventory=inventory,
                    quantity=quantity_before,
                )
            except Exception:
                pass

            raise

        return inventory