from decimal import (
    Decimal,
    InvalidOperation,
)

from apps.inventory.repositories.inventory_repository import (
    InventoryRepository,
)
from apps.inventory.repositories.warehouse_repository import (
    WarehouseRepository,
)
from apps.inventory.services.inventory_service import (
    InventoryService,
)
from apps.products.repositories.product_repository import (
    ProductRepository,
)


class InventoryAPIValidationError(
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


class InventoryAPIService:

    CREATE_FIELDS = {
        "product_id",
        "warehouse_id",
        "quantity",
    }

    PROTECTED_FIELDS = {
        "id",
        "_id",
        "organization",
        "organization_id",
        "product",
        "warehouse",
        "reserved_quantity",
        "available_quantity",
        "created_at",
        "updated_at",
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
            raise InventoryAPIValidationError(
                "Inventory validation failed.",
                details={
                    field: [
                        (
                            "This field must be "
                            "a string identifier."
                        )
                    ],
                },
            )

        normalized = value.strip()

        if not normalized:
            raise InventoryAPIValidationError(
                "Inventory validation failed.",
                details={
                    field: [
                        "This field is required."
                    ],
                },
            )

        return normalized

    @staticmethod
    def _normalize_quantity(
        value,
    ):
        if isinstance(
            value,
            bool,
        ):
            raise InventoryAPIValidationError(
                "Inventory validation failed.",
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

            raise InventoryAPIValidationError(
                "Inventory validation failed.",
                details={
                    "quantity": [
                        (
                            "Quantity must be "
                            "a valid number."
                        )
                    ],
                },
            ) from exc

        if not quantity.is_finite():
            raise InventoryAPIValidationError(
                "Inventory validation failed.",
                details={
                    "quantity": [
                        (
                            "Quantity must be "
                            "a finite number."
                        )
                    ],
                },
            )

        if quantity < 0:
            raise InventoryAPIValidationError(
                "Inventory validation failed.",
                details={
                    "quantity": [
                        (
                            "Quantity cannot "
                            "be negative."
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
            raise InventoryAPIValidationError(
                "Inventory validation failed.",
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
    def validate_create_payload(
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
            raise InventoryAPIValidationError(
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
                InventoryAPIService
                .PROTECTED_FIELDS
            ):
                errors[field] = [
                    (
                        "This field cannot be "
                        "changed directly."
                    )
                ]

            elif field not in (
                InventoryAPIService
                .CREATE_FIELDS
            ):
                errors[field] = [
                    "This field is not supported."
                ]

        for required_field in (
            "product_id",
            "warehouse_id",
        ):
            if required_field not in payload:
                errors[required_field] = [
                    "This field is required."
                ]

        if errors:
            raise InventoryAPIValidationError(
                "Inventory validation failed.",
                details=errors,
            )

        try:

            product_id = (
                InventoryAPIService
                ._normalize_identifier(
                    field="product_id",
                    value=payload[
                        "product_id"
                    ],
                )
            )

        except InventoryAPIValidationError as exc:
            errors.update(
                exc.details
            )

            product_id = None

        try:

            warehouse_id = (
                InventoryAPIService
                ._normalize_identifier(
                    field="warehouse_id",
                    value=payload[
                        "warehouse_id"
                    ],
                )
            )

        except InventoryAPIValidationError as exc:
            errors.update(
                exc.details
            )

            warehouse_id = None

        try:

            quantity = (
                InventoryAPIService
                ._normalize_quantity(
                    payload.get(
                        "quantity",
                        0,
                    )
                )
            )

        except InventoryAPIValidationError as exc:
            errors.update(
                exc.details
            )

            quantity = None

        if errors:
            raise InventoryAPIValidationError(
                "Inventory validation failed.",
                details=errors,
            )

        product = (
            ProductRepository
            .get_by_id(
                organization=organization,
                product_id=product_id,
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

        warehouse = (
            WarehouseRepository
            .get_by_id(
                organization=organization,
                warehouse_id=warehouse_id,
            )
        )

        if not warehouse:
            errors["warehouse_id"] = [
                (
                    "The selected warehouse "
                    "does not exist."
                )
            ]

        elif not warehouse.is_active:
            errors["warehouse_id"] = [
                (
                    "The selected warehouse "
                    "is inactive."
                )
            ]

        if (
            product
            and
            warehouse
            and
            InventoryRepository
            .exists_for_product_and_warehouse(
                organization=organization,
                product=product,
                warehouse=warehouse,
            )
        ):
            errors["inventory"] = [
                (
                    "Inventory already exists "
                    "for this product and warehouse."
                )
            ]

        if errors:
            raise InventoryAPIValidationError(
                "Inventory validation failed.",
                details=errors,
            )

        return {
            "product":
                product,
            "warehouse":
                warehouse,
            "quantity":
                quantity,
        }

    @staticmethod
    def create_inventory(
        *,
        user,
        organization,
        payload,
    ):
        values = (
            InventoryAPIService
            .validate_create_payload(
                organization=organization,
                payload=payload,
            )
        )

        try:

            return (
                InventoryService
                .create_inventory(
                    user=user,
                    organization=organization,
                    product=values[
                        "product"
                    ],
                    warehouse=values[
                        "warehouse"
                    ],
                    quantity=values[
                        "quantity"
                    ],
                    reserved_quantity=(
                        Decimal("0")
                    ),
                )
            )

        except PermissionError:
            raise

        except ValueError as exc:
            raise InventoryAPIValidationError(
                "Inventory validation failed.",
                details={
                    "inventory": [
                        str(
                            exc
                        )
                    ],
                },
            ) from exc

    @staticmethod
    def get_inventory(
        *,
        organization,
        inventory_id,
    ):
        inventory = (
            InventoryRepository
            .get_by_id(
                organization=organization,
                inventory_id=inventory_id,
            )
        )

        if not inventory:
            raise LookupError(
                "Inventory not found."
            )

        return inventory

    @staticmethod
    def _normalize_quantity_change(
        value,
    ):
        if isinstance(
            value,
            bool,
        ):
            raise InventoryAPIValidationError(
                "Inventory adjustment validation failed.",
                details={
                    "quantity_change": [
                        (
                            "Quantity change must "
                            "be a valid number."
                        )
                    ],
                },
            )

        try:

            quantity_change = Decimal(
                str(
                    value
                )
            )

        except (
            InvalidOperation,
            TypeError,
            ValueError,
        ) as exc:

            raise InventoryAPIValidationError(
                "Inventory adjustment validation failed.",
                details={
                    "quantity_change": [
                        (
                            "Quantity change must "
                            "be a valid number."
                        )
                    ],
                },
            ) from exc

        if not quantity_change.is_finite():
            raise InventoryAPIValidationError(
                "Inventory adjustment validation failed.",
                details={
                    "quantity_change": [
                        (
                            "Quantity change must "
                            "be a finite number."
                        )
                    ],
                },
            )

        if quantity_change == 0:
            raise InventoryAPIValidationError(
                "Inventory adjustment validation failed.",
                details={
                    "quantity_change": [
                        (
                            "Quantity change cannot "
                            "be zero."
                        )
                    ],
                },
            )

        if (
            quantity_change
            .as_tuple()
            .exponent
            <
            -2
        ):
            raise InventoryAPIValidationError(
                "Inventory adjustment validation failed.",
                details={
                    "quantity_change": [
                        (
                            "Quantity change cannot "
                            "have more than two "
                            "decimal places."
                        )
                    ],
                },
            )

        return quantity_change

    @staticmethod
    def _normalize_optional_text(
        *,
        field,
        value,
        maximum_length,
    ):
        if not isinstance(
            value,
            str,
        ):
            raise InventoryAPIValidationError(
                "Inventory adjustment validation failed.",
                details={
                    field: [
                        "This field must be a string."
                    ],
                },
            )

        normalized = value.strip()

        if len(normalized) > maximum_length:
            raise InventoryAPIValidationError(
                "Inventory adjustment validation failed.",
                details={
                    field: [
                        (
                            "Ensure this field has no "
                            f"more than {maximum_length} "
                            "characters."
                        )
                    ],
                },
            )

        return normalized

    @staticmethod
    def validate_adjustment_payload(
        *,
        payload,
    ):
        if not isinstance(
            payload,
            dict,
        ):
            raise InventoryAPIValidationError(
                "JSON body must be an object.",
                details={
                    "body": [
                        "Expected a JSON object."
                    ],
                },
            )

        allowed_fields = {
            "quantity_change",
            "reference_type",
            "reference_id",
            "notes",
        }

        protected_fields = {
            "id",
            "_id",
            "organization",
            "organization_id",
            "inventory_id",
            "product",
            "product_id",
            "warehouse",
            "warehouse_id",
            "quantity",
            "reserved_quantity",
            "available_quantity",
            "created_at",
            "updated_at",
        }

        errors = {}

        for field in payload:

            if field in protected_fields:
                errors[field] = [
                    (
                        "This field cannot be "
                        "changed directly."
                    )
                ]

            elif field not in allowed_fields:
                errors[field] = [
                    "This field is not supported."
                ]

        if "quantity_change" not in payload:
            errors["quantity_change"] = [
                "This field is required."
            ]

        if errors:
            raise InventoryAPIValidationError(
                "Inventory adjustment validation failed.",
                details=errors,
            )

        try:

            quantity_change = (
                InventoryAPIService
                ._normalize_quantity_change(
                    payload[
                        "quantity_change"
                    ]
                )
            )

        except InventoryAPIValidationError as exc:
            errors.update(
                exc.details
            )

            quantity_change = None

        normalized_text = {}

        text_rules = {
            "reference_type": 100,
            "reference_id": 100,
            "notes": 1000,
        }

        for (
            field,
            maximum_length,
        ) in text_rules.items():

            try:

                normalized_text[field] = (
                    InventoryAPIService
                    ._normalize_optional_text(
                        field=field,
                        value=payload.get(
                            field,
                            "",
                        ),
                        maximum_length=(
                            maximum_length
                        ),
                    )
                )

            except InventoryAPIValidationError as exc:
                errors.update(
                    exc.details
                )

        if errors:
            raise InventoryAPIValidationError(
                "Inventory adjustment validation failed.",
                details=errors,
            )

        return {
            "quantity_change":
                quantity_change,
            **normalized_text,
        }

    @staticmethod
    def adjust_inventory(
        *,
        user,
        organization,
        inventory_id,
        payload,
    ):
        inventory = (
            InventoryAPIService
            .get_inventory(
                organization=organization,
                inventory_id=inventory_id,
            )
        )

        values = (
            InventoryAPIService
            .validate_adjustment_payload(
                payload=payload,
            )
        )

        try:

            return (
                InventoryService
                .adjust_quantity(
                    user=user,
                    organization=organization,
                    inventory_id=inventory_id,
                    quantity_change=values[
                        "quantity_change"
                    ],
                    reference_type=values[
                        "reference_type"
                    ],
                    reference_id=values[
                        "reference_id"
                    ],
                    notes=values[
                        "notes"
                    ],
                )
            )

        except PermissionError:
            raise

        except ValueError as exc:
            raise InventoryAPIValidationError(
                "Inventory adjustment failed.",
                details={
                    "quantity_change": [
                        str(
                            exc
                        )
                    ],
                },
            ) from exc