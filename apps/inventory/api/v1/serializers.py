from apps.core.services.api_serialization_service import (
    APISerializationService,
)


class WarehouseAPISerializer:

    @staticmethod
    def serialize_summary(
        warehouse,
    ):
        if not warehouse:
            return None

        return {
            "id": (
                APISerializationService
                .serialize_identifier(
                    warehouse.id
                )
            ),
            "code":
                warehouse.code,
            "name":
                warehouse.name,
            "city":
                (
                    warehouse.city
                    or
                    None
                ),
            "state":
                (
                    warehouse.state
                    or
                    None
                ),
            "country":
                (
                    warehouse.country
                    or
                    None
                ),
            "is_active":
                bool(
                    warehouse.is_active
                ),
        }

    @staticmethod
    def serialize_detail(
        warehouse,
    ):
        if not warehouse:
            return None

        summary = (
            WarehouseAPISerializer
            .serialize_summary(
                warehouse
            )
        )

        return {
            **summary,
            "address":
                (
                    warehouse.address
                    or
                    None
                ),
            "pincode":
                (
                    warehouse.pincode
                    or
                    None
                ),
            "created_at": (
                APISerializationService
                .serialize_datetime(
                    warehouse.created_at
                )
            ),
            "updated_at": (
                APISerializationService
                .serialize_datetime(
                    warehouse.updated_at
                )
            ),
        }

    @staticmethod
    def serialize_many(
        warehouses,
    ):
        return [
            (
                WarehouseAPISerializer
                .serialize_summary(
                    warehouse
                )
            )
            for warehouse
            in warehouses
        ]

class InventoryAPISerializer:

    @staticmethod
    def serialize_summary(
        inventory,
    ):
        if not inventory:
            return None

        quantity = (
            inventory.quantity
        )

        reserved_quantity = (
            inventory.reserved_quantity
        )

        available_quantity = (
            quantity
            -
            reserved_quantity
        )

        return {
            "id": (
                APISerializationService
                .serialize_identifier(
                    inventory.id
                )
            ),
            "product": {
                "id": (
                    APISerializationService
                    .serialize_identifier(
                        inventory.product.id
                    )
                ),
                "sku":
                    inventory.product.sku,
                "name":
                    inventory.product.name,
                "unit":
                    inventory.product.unit,
                "is_active":
                    bool(
                        inventory.product.is_active
                    ),
            },
            "warehouse": (
                WarehouseAPISerializer
                .serialize_summary(
                    inventory.warehouse
                )
            ),
            "quantity":
                str(
                    quantity
                ),
            "reserved_quantity":
                str(
                    reserved_quantity
                ),
            "available_quantity":
                str(
                    available_quantity
                ),
        }

    @staticmethod
    def serialize_detail(
        inventory,
    ):
        if not inventory:
            return None

        summary = (
            InventoryAPISerializer
            .serialize_summary(
                inventory
            )
        )

        return {
            **summary,
            "created_at": (
                APISerializationService
                .serialize_datetime(
                    inventory.created_at
                )
            ),
            "updated_at": (
                APISerializationService
                .serialize_datetime(
                    inventory.updated_at
                )
            ),
        }

    @staticmethod
    def serialize_many(
        inventory_items,
    ):
        return [
            (
                InventoryAPISerializer
                .serialize_summary(
                    inventory
                )
            )
            for inventory
            in inventory_items
        ]

class StockMovementAPISerializer:

    @staticmethod
    def serialize_summary(
        movement,
    ):
        if not movement:
            return None

        created_by = (
            movement.created_by
        )

        return {
            "id": (
                APISerializationService
                .serialize_identifier(
                    movement.id
                )
            ),
            "inventory_id": (
                APISerializationService
                .serialize_identifier(
                    movement.inventory.id
                )
            ),
            "movement_type":
                movement.movement_type,
            "quantity":
                str(
                    movement.quantity
                ),
            "quantity_before":
                str(
                    movement.quantity_before
                ),
            "quantity_after":
                str(
                    movement.quantity_after
                ),
            "reserved_before":
                str(
                    movement.reserved_before
                ),
            "reserved_after":
                str(
                    movement.reserved_after
                ),
            "product": {
                "id": (
                    APISerializationService
                    .serialize_identifier(
                        movement.product.id
                    )
                ),
                "sku":
                    movement.product.sku,
                "name":
                    movement.product.name,
                "unit":
                    movement.product.unit,
            },
            "warehouse": (
                WarehouseAPISerializer
                .serialize_summary(
                    movement.warehouse
                )
            ),
            "reference": {
                "type":
                    (
                        movement.reference_type
                        or
                        None
                    ),
                "id":
                    (
                        movement.reference_id
                        or
                        None
                    ),
            },
            "created_by": (
                {
                    "id": (
                        APISerializationService
                        .serialize_identifier(
                            created_by.id
                        )
                    ),
                    "email":
                        created_by.email,
                }
                if created_by
                else
                None
            ),
            "created_at": (
                APISerializationService
                .serialize_datetime(
                    movement.created_at
                )
            ),
        }

    @staticmethod
    def serialize_detail(
        movement,
    ):
        if not movement:
            return None

        summary = (
            StockMovementAPISerializer
            .serialize_summary(
                movement
            )
        )

        return {
            **summary,
            "notes":
                (
                    movement.notes
                    or
                    None
                ),
        }

    @staticmethod
    def serialize_many(
        movements,
    ):
        return [
            (
                StockMovementAPISerializer
                .serialize_summary(
                    movement
                )
            )
            for movement
            in movements
        ]

class StockTransferAPISerializer:

    @staticmethod
    def serialize_summary(
        transfer,
    ):
        if not transfer:
            return None

        created_by = (
            transfer.created_by
        )

        return {
            "id": (
                APISerializationService
                .serialize_identifier(
                    transfer.id
                )
            ),
            "transfer_number":
                transfer.transfer_number,
            "product": {
                "id": (
                    APISerializationService
                    .serialize_identifier(
                        transfer.product.id
                    )
                ),
                "sku":
                    transfer.product.sku,
                "name":
                    transfer.product.name,
                "unit":
                    transfer.product.unit,
            },
            "source_warehouse": (
                WarehouseAPISerializer
                .serialize_summary(
                    transfer.source_warehouse
                )
            ),
            "destination_warehouse": (
                WarehouseAPISerializer
                .serialize_summary(
                    transfer.destination_warehouse
                )
            ),
            "quantity":
                str(
                    transfer.quantity
                ),
            "status":
                transfer.status,
            "created_by": (
                {
                    "id": (
                        APISerializationService
                        .serialize_identifier(
                            created_by.id
                        )
                    ),
                    "email":
                        created_by.email,
                }
                if created_by
                else
                None
            ),
            "created_at": (
                APISerializationService
                .serialize_datetime(
                    transfer.created_at
                )
            ),
            "completed_at": (
                APISerializationService
                .serialize_datetime(
                    transfer.completed_at
                )
            ),
        }

    @staticmethod
    def serialize_detail(
        transfer,
    ):
        if not transfer:
            return None

        summary = (
            StockTransferAPISerializer
            .serialize_summary(
                transfer
            )
        )

        return {
            **summary,
            "source_inventory_id": (
                APISerializationService
                .serialize_identifier(
                    transfer.source_inventory.id
                )
            ),
            "destination_inventory_id": (
                APISerializationService
                .serialize_identifier(
                    transfer.destination_inventory.id
                )
            ),
            "notes":
                (
                    transfer.notes
                    or
                    None
                ),
        }

    @staticmethod
    def serialize_many(
        transfers,
    ):
        return [
            (
                StockTransferAPISerializer
                .serialize_summary(
                    transfer
                )
            )
            for transfer
            in transfers
        ]