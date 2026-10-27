from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from mongoengine.errors import NotUniqueError

from apps.authorization.services import AuthorizationService

from apps.inventory.repositories.inventory_repository import (
    InventoryRepository,
)
from apps.inventory.repositories.stock_transfer_repository import (
    StockTransferRepository,
)
from apps.inventory.services.stock_movement_service import (
    StockMovementService,
)
from apps.inventory.repositories.stock_movement_repository import (
    StockMovementRepository,
)

class StockTransferService:

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
    def _validate_product(
        product,
        organization,
    ):
        if not product:
            raise ValueError(
                "Product is required."
            )

        if product.organization.id != organization.id:
            raise PermissionError(
                "Product does not belong to this organization."
            )

        if not product.is_active:
            raise ValueError(
                "Inactive product cannot be transferred."
            )

    @staticmethod
    def _validate_warehouse(
        warehouse,
        organization,
    ):
        if not warehouse:
            raise ValueError(
                "Warehouse is required."
            )

        if warehouse.organization.id != organization.id:
            raise PermissionError(
                "Warehouse does not belong to this organization."
            )

        if not warehouse.is_active:
            raise ValueError(
                "Inactive warehouse cannot be used "
                "for stock transfer."
            )

    @staticmethod
    def _generate_transfer_number():
        """
        Generate a temporary unique transfer number.

        We can replace this later with an
        organization-specific sequence.
        """

        return (
            "TRF-"
            + uuid4().hex[:12].upper()
        )

    @staticmethod
    def transfer_stock(
        *,
        user,
        organization,
        product,
        source_warehouse,
        destination_warehouse,
        quantity,
        notes="",
    ):
        """
        Transfer physical stock from one warehouse
        to another.
        """

        StockTransferService._check_permission(
            user,
            "inventory.transfer",
        )

        StockTransferService._check_organization(
            user,
            organization,
        )

        StockTransferService._validate_product(
            product,
            organization,
        )

        StockTransferService._validate_warehouse(
            source_warehouse,
            organization,
        )

        StockTransferService._validate_warehouse(
            destination_warehouse,
            organization,
        )

        if (
            source_warehouse.id
            == destination_warehouse.id
        ):
            raise ValueError(
                "Source and destination warehouses "
                "cannot be the same."
            )

        quantity = Decimal(
            str(quantity)
        )

        if quantity <= 0:
            raise ValueError(
                "Transfer quantity must be greater than zero."
            )

        # ---------------------------------------------
        # SOURCE INVENTORY
        # ---------------------------------------------

        source_inventory = (
            InventoryRepository
            .get_by_product_and_warehouse(
                organization=organization,
                product=product,
                warehouse=source_warehouse,
            )
        )

        if not source_inventory:
            raise ValueError(
                "Source inventory not found."
            )

        available_quantity = (
            source_inventory.quantity
            - source_inventory.reserved_quantity
        )

        if quantity > available_quantity:
            raise ValueError(
                "Insufficient available inventory "
                "for transfer."
            )

        # ---------------------------------------------
        # DESTINATION INVENTORY
        # ---------------------------------------------
        destination_inventory_created = False
        destination_inventory = (
            InventoryRepository
            .get_by_product_and_warehouse(
                organization=organization,
                product=product,
                warehouse=destination_warehouse,
            )
        )

        if not destination_inventory:
            try:
                destination_inventory = (
                    InventoryRepository.create_inventory(
                        organization=organization,
                        product=product,
                        warehouse=destination_warehouse,
                        quantity=0,
                        reserved_quantity=0,
                    )
                )
                destination_inventory_created = True
            except NotUniqueError:
                destination_inventory = (
                    InventoryRepository
                    .get_by_product_and_warehouse(
                        organization=organization,
                        product=product,
                        warehouse=destination_warehouse,
                    )
                )

        # ---------------------------------------------
        # CAPTURE BEFORE VALUES
        # ---------------------------------------------

        source_quantity_before = (
            source_inventory.quantity
        )

        source_reserved_before = (
            source_inventory.reserved_quantity
        )

        destination_quantity_before = (
            destination_inventory.quantity
        )

        destination_reserved_before = (
            destination_inventory.reserved_quantity
        )

        source_quantity_after = (
            source_quantity_before
            - quantity
        )

        destination_quantity_after = (
            destination_quantity_before
            + quantity
        )

        transfer_number = (
            StockTransferService
            ._generate_transfer_number()
        )

        # ---------------------------------------------
        # COMPENSATING TRANSACTION
        # ---------------------------------------------

        transfer = None
        transfer_out_movement = None
        transfer_in_movement = None

        try:

            source_inventory = (
                InventoryRepository
                .update_quantity(
                    inventory=source_inventory,
                    quantity=source_quantity_after,
                )
            )

            destination_inventory = (
                InventoryRepository
                .update_quantity(
                    inventory=destination_inventory,
                    quantity=(
                        destination_quantity_after
                    ),
                )
            )

            transfer = (
                StockTransferRepository
                .create_transfer(
                    organization=organization,
                    transfer_number=transfer_number,
                    product=product,
                    source_warehouse=(
                        source_warehouse
                    ),
                    destination_warehouse=(
                        destination_warehouse
                    ),
                    source_inventory=(
                        source_inventory
                    ),
                    destination_inventory=(
                        destination_inventory
                    ),
                    quantity=quantity,
                    status="COMPLETED",
                    notes=notes,
                    created_by=user,
                    completed_at=datetime.utcnow(),
                )
            )

            transfer_out_movement = (
                StockMovementService
                .create_movement(
                    user=user,
                    organization=organization,
                    inventory=source_inventory,
                    movement_type="TRANSFER_OUT",
                    quantity=-quantity,
                    quantity_before=(
                        source_quantity_before
                    ),
                    quantity_after=(
                        source_quantity_after
                    ),
                    reserved_before=(
                        source_reserved_before
                    ),
                    reserved_after=(
                        source_inventory
                        .reserved_quantity
                    ),
                    reference_type=(
                        "STOCK_TRANSFER"
                    ),
                    reference_id=(
                        transfer_number
                    ),
                    notes=notes,
                )
            )

            transfer_in_movement = (
                StockMovementService
                .create_movement(
                    user=user,
                    organization=organization,
                    inventory=(
                        destination_inventory
                    ),
                    movement_type="TRANSFER_IN",
                    quantity=quantity,
                    quantity_before=(
                        destination_quantity_before
                    ),
                    quantity_after=(
                        destination_quantity_after
                    ),
                    reserved_before=(
                        destination_reserved_before
                    ),
                    reserved_after=(
                        destination_inventory
                        .reserved_quantity
                    ),
                    reference_type=(
                        "STOCK_TRANSFER"
                    ),
                    reference_id=(
                        transfer_number
                    ),
                    notes=notes,
                )
            )

        except Exception:

            # Remove any partially written
            # movement documents.
            try:
                (
                    StockMovementRepository
                    .delete_movement(
                        movement=(
                            transfer_in_movement
                        ),
                    )
                )
            except Exception:
                pass

            try:
                (
                    StockMovementRepository
                    .delete_movement(
                        movement=(
                            transfer_out_movement
                        ),
                    )
                )
            except Exception:
                pass

            # Remove an incomplete transfer.
            try:
                (
                    StockTransferRepository
                    .delete_transfer(
                        transfer=transfer,
                    )
                )
            except Exception:
                pass

            # Restore source inventory.
            try:
                (
                    InventoryRepository
                    .update_quantity(
                        inventory=source_inventory,
                        quantity=(
                            source_quantity_before
                        ),
                    )
                )
            except Exception:
                pass

            # Restore an existing destination
            # balance, or remove a balance created
            # solely for the failed transfer.
            if destination_inventory_created:

                try:
                    (
                        InventoryRepository
                        .delete_inventory(
                            inventory=(
                                destination_inventory
                            ),
                        )
                    )
                except Exception:
                    pass

            else:

                try:
                    (
                        InventoryRepository
                        .update_quantity(
                            inventory=(
                                destination_inventory
                            ),
                            quantity=(
                                destination_quantity_before
                            ),
                        )
                    )
                except Exception:
                    pass

            raise

        return transfer