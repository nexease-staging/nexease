from decimal import (
    Decimal,
    InvalidOperation,
)

from apps.inventory.repositories.stock_transfer_repository import (
    StockTransferRepository,
)
from apps.inventory.repositories.warehouse_repository import (
    WarehouseRepository,
)
from apps.inventory.services.stock_transfer_service import (
    StockTransferService,
)
from apps.products.repositories.product_repository import (
    ProductRepository,
)


class StockTransferAPIValidationError(
    ValueError
):

    def __init__(
        self,
        message,
        details=None,
    ):
        super().__init__(
            message
        )

        self.message = message
        self.details = details or {}


class StockTransferAPIService:

    ALLOWED_FIELDS = {
        "product_id",
        "source_warehouse_id",
        "destination_warehouse_id",
        "quantity",
        "notes",
    }

    PROTECTED_FIELDS = {
        "id",
        "_id",
        "organization",
        "organization_id",
        "transfer_number",
        "status",
        "source_inventory",
        "source_inventory_id",
        "destination_inventory",
        "destination_inventory_id",
        "created_by",
        "created_at",
        "completed_at",
    }

    @staticmethod
    def _normalize_identifier(
        *,
        field,
        value,
    ):
        if not isinstance(
            value,
            str,
        ):
            raise StockTransferAPIValidationError(
                "Stock transfer validation failed.",
                details={
                    field: [
                        (
                            "This field must be "
                            "a string identifier."
                        )
                    ],
                },
            )

        value = value.strip()

        if not value:
            raise StockTransferAPIValidationError(
                "Stock transfer validation failed.",
                details={
                    field: [
                        "This field is required."
                    ],
                },
            )

        return value

    @staticmethod
    def _normalize_quantity(
        value,
    ):
        if isinstance(
            value,
            bool,
        ):
            raise StockTransferAPIValidationError(
                "Stock transfer validation failed.",
                details={
                    "quantity": [
                        (
                            "Quantity must be "
                            "a valid number."
                        )
                    ],
                },
            )

        try:

            quantity = Decimal(
                str(
                    value
                )
            )

        except (
            InvalidOperation,
            TypeError,
            ValueError,
        ) as exc:

            raise StockTransferAPIValidationError(
                "Stock transfer validation failed.",
                details={
                    "quantity": [
                        (
                            "Quantity must be "
                            "a valid number."
                        )
                    ],
                },
            ) from exc

        if (
            not quantity.is_finite()
            or
            quantity <= 0
        ):
            raise StockTransferAPIValidationError(
                "Stock transfer validation failed.",
                details={
                    "quantity": [
                        (
                            "Quantity must be greater "
                            "than zero."
                        )
                    ],
                },
            )

        if (
            quantity
            .as_tuple()
            .exponent
            <
            -2
        ):
            raise StockTransferAPIValidationError(
                "Stock transfer validation failed.",
                details={
                    "quantity": [
                        (
                            "Quantity cannot have "
                            "more than two decimal "
                            "places."
                        )
                    ],
                },
            )

        return quantity

    @staticmethod
    def validate_transfer_payload(
        *,
        organization,
        payload,
    ):
        if not organization:
            raise PermissionError(
                "Organization context is required."
            )

        if not isinstance(
            payload,
            dict,
        ):
            raise StockTransferAPIValidationError(
                "JSON body must be an object.",
                details={
                    "body": [
                        "Expected a JSON object."
                    ],
                },
            )

        errors = {}

        for field in payload:

            if field in (
                StockTransferAPIService
                .PROTECTED_FIELDS
            ):
                errors[field] = [
                    (
                        "This field cannot be "
                        "changed directly."
                    )
                ]

            elif field not in (
                StockTransferAPIService
                .ALLOWED_FIELDS
            ):
                errors[field] = [
                    "This field is not supported."
                ]

        required_fields = (
            "product_id",
            "source_warehouse_id",
            "destination_warehouse_id",
            "quantity",
        )

        for field in required_fields:
            if field not in payload:
                errors[field] = [
                    "This field is required."
                ]

        if errors:
            raise StockTransferAPIValidationError(
                "Stock transfer validation failed.",
                details=errors,
            )

        identifiers = {}

        for field in (
            "product_id",
            "source_warehouse_id",
            "destination_warehouse_id",
        ):

            try:

                identifiers[field] = (
                    StockTransferAPIService
                    ._normalize_identifier(
                        field=field,
                        value=payload[
                            field
                        ],
                    )
                )

            except StockTransferAPIValidationError as exc:
                errors.update(
                    exc.details
                )

        try:

            quantity = (
                StockTransferAPIService
                ._normalize_quantity(
                    payload[
                        "quantity"
                    ]
                )
            )

        except StockTransferAPIValidationError as exc:
            errors.update(
                exc.details
            )

            quantity = None

        notes = payload.get(
            "notes",
            "",
        )

        if not isinstance(
            notes,
            str,
        ):
            errors["notes"] = [
                "This field must be a string."
            ]

        else:
            notes = notes.strip()

            if len(notes) > 1000:
                errors["notes"] = [
                    (
                        "Ensure this field has no "
                        "more than 1000 characters."
                    )
                ]

        if errors:
            raise StockTransferAPIValidationError(
                "Stock transfer validation failed.",
                details=errors,
            )

        product = (
            ProductRepository
            .get_by_id(
                organization=organization,
                product_id=identifiers[
                    "product_id"
                ],
            )
        )

        if not product:
            errors["product_id"] = [
                (
                    "The selected product "
                    "does not exist."
                )
            ]

        elif not product.is_active:
            errors["product_id"] = [
                (
                    "The selected product "
                    "is inactive."
                )
            ]

        source_warehouse = (
            WarehouseRepository
            .get_by_id(
                organization=organization,
                warehouse_id=identifiers[
                    "source_warehouse_id"
                ],
            )
        )

        if not source_warehouse:
            errors["source_warehouse_id"] = [
                (
                    "The selected source warehouse "
                    "does not exist."
                )
            ]

        elif not source_warehouse.is_active:
            errors["source_warehouse_id"] = [
                (
                    "The selected source warehouse "
                    "is inactive."
                )
            ]

        destination_warehouse = (
            WarehouseRepository
            .get_by_id(
                organization=organization,
                warehouse_id=identifiers[
                    "destination_warehouse_id"
                ],
            )
        )

        if not destination_warehouse:
            errors[
                "destination_warehouse_id"
            ] = [
                (
                    "The selected destination "
                    "warehouse does not exist."
                )
            ]

        elif not destination_warehouse.is_active:
            errors[
                "destination_warehouse_id"
            ] = [
                (
                    "The selected destination "
                    "warehouse is inactive."
                )
            ]

        if (
            source_warehouse
            and
            destination_warehouse
            and
            source_warehouse.id
            ==
            destination_warehouse.id
        ):
            errors[
                "destination_warehouse_id"
            ] = [
                (
                    "Source and destination "
                    "warehouses cannot be the same."
                )
            ]

        if errors:
            raise StockTransferAPIValidationError(
                "Stock transfer validation failed.",
                details=errors,
            )

        return {
            "product":
                product,
            "source_warehouse":
                source_warehouse,
            "destination_warehouse":
                destination_warehouse,
            "quantity":
                quantity,
            "notes":
                notes,
        }

    @staticmethod
    def create_transfer(
        *,
        user,
        organization,
        payload,
    ):
        values = (
            StockTransferAPIService
            .validate_transfer_payload(
                organization=organization,
                payload=payload,
            )
        )

        try:

            return (
                StockTransferService
                .transfer_stock(
                    user=user,
                    organization=organization,
                    **values,
                )
            )

        except PermissionError:
            raise

        except ValueError as exc:
            raise StockTransferAPIValidationError(
                "Stock transfer failed.",
                details={
                    "transfer": [
                        str(
                            exc
                        )
                    ],
                },
            ) from exc

    @staticmethod
    def get_transfer(
        *,
        organization,
        transfer_id,
    ):
        transfer = (
            StockTransferRepository
            .get_by_id(
                organization=organization,
                transfer_id=transfer_id,
            )
        )

        if not transfer:
            raise LookupError(
                "Stock transfer not found."
            )

        return transfer