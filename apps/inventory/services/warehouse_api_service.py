from mongoengine.errors import (
    NotUniqueError,
)

from apps.inventory.repositories.warehouse_repository import (
    WarehouseRepository,
)


class WarehouseAPIValidationError(
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


class WarehouseAPIService:

    ALLOWED_FIELDS = {
        "name",
        "code",
        "address",
        "city",
        "state",
        "country",
        "pincode",
    }

    PROTECTED_FIELDS = {
        "id",
        "_id",
        "organization",
        "organization_id",
        "is_active",
        "created_at",
        "updated_at",
    }

    FIELD_LIMITS = {
        "name": 150,
        "code": 50,
        "address": 500,
        "city": 100,
        "state": 100,
        "country": 100,
        "pincode": 20,
    }

    @staticmethod
    def _normalize_text(
        *,
        field,
        value,
        required=False,
    ):
        if not isinstance(
            value,
            str,
        ):
            raise WarehouseAPIValidationError(
                "Warehouse validation failed.",
                details={
                    field: [
                        "This field must be a string."
                    ],
                },
            )

        normalized = value.strip()

        if required and not normalized:
            raise WarehouseAPIValidationError(
                "Warehouse validation failed.",
                details={
                    field: [
                        "This field is required."
                    ],
                },
            )

        maximum_length = (
            WarehouseAPIService
            .FIELD_LIMITS[
                field
            ]
        )

        if len(normalized) > maximum_length:
            raise WarehouseAPIValidationError(
                "Warehouse validation failed.",
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

        if field == "code":
            normalized = (
                normalized.upper()
            )

        return normalized

    @staticmethod
    def _validate_payload_fields(
        payload,
    ):
        if not isinstance(
            payload,
            dict,
        ):
            raise WarehouseAPIValidationError(
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
                WarehouseAPIService
                .PROTECTED_FIELDS
            ):
                errors[field] = [
                    (
                        "This field cannot be "
                        "changed directly."
                    )
                ]

            elif field not in (
                WarehouseAPIService
                .ALLOWED_FIELDS
            ):
                errors[field] = [
                    "This field is not supported."
                ]

        if errors:
            raise WarehouseAPIValidationError(
                "Warehouse validation failed.",
                details=errors,
            )

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

        (
            WarehouseAPIService
            ._validate_payload_fields(
                payload
            )
        )

        errors = {}

        for required_field in (
            "name",
            "code",
        ):
            if required_field not in payload:
                errors[required_field] = [
                    "This field is required."
                ]

        if errors:
            raise WarehouseAPIValidationError(
                "Warehouse validation failed.",
                details=errors,
            )

        values = {}

        for field in (
            WarehouseAPIService
            .ALLOWED_FIELDS
        ):
            if field not in payload:
                continue

            try:
                values[field] = (
                    WarehouseAPIService
                    ._normalize_text(
                        field=field,
                        value=payload[field],
                        required=(
                            field
                            in {
                                "name",
                                "code",
                            }
                        ),
                    )
                )

            except WarehouseAPIValidationError as exc:
                errors.update(
                    exc.details
                )

        if errors:
            raise WarehouseAPIValidationError(
                "Warehouse validation failed.",
                details=errors,
            )

        values.setdefault(
            "address",
            "",
        )
        values.setdefault(
            "city",
            "",
        )
        values.setdefault(
            "state",
            "",
        )
        values.setdefault(
            "country",
            "India",
        )
        values.setdefault(
            "pincode",
            "",
        )

        if (
            WarehouseRepository
            .code_exists(
                organization=organization,
                code=values["code"],
            )
        ):
            errors["code"] = [
                (
                    "A warehouse with this code "
                    "already exists."
                )
            ]

        if (
            WarehouseRepository
            .name_exists(
                organization=organization,
                name=values["name"],
            )
        ):
            errors["name"] = [
                (
                    "A warehouse with this name "
                    "already exists."
                )
            ]

        if errors:
            raise WarehouseAPIValidationError(
                "Warehouse validation failed.",
                details=errors,
            )

        return values

    @staticmethod
    def validate_update_payload(
        *,
        organization,
        warehouse,
        payload,
    ):
        if not organization:
            raise PermissionError(
                "Organization context is required."
            )

        if not warehouse:
            raise LookupError(
                "Warehouse not found."
            )

        (
            WarehouseAPIService
            ._validate_payload_fields(
                payload
            )
        )

        if not payload:
            raise WarehouseAPIValidationError(
                "Warehouse validation failed.",
                details={
                    "body": [
                        (
                            "Provide at least one "
                            "field to update."
                        )
                    ],
                },
            )

        values = {
            "name":
                warehouse.name,
            "code":
                warehouse.code,
            "address":
                warehouse.address,
            "city":
                warehouse.city,
            "state":
                warehouse.state,
            "country":
                warehouse.country,
            "pincode":
                warehouse.pincode,
        }

        errors = {}

        for field, value in payload.items():

            try:
                values[field] = (
                    WarehouseAPIService
                    ._normalize_text(
                        field=field,
                        value=value,
                        required=(
                            field
                            in {
                                "name",
                                "code",
                            }
                        ),
                    )
                )

            except WarehouseAPIValidationError as exc:
                errors.update(
                    exc.details
                )

        if errors:
            raise WarehouseAPIValidationError(
                "Warehouse validation failed.",
                details=errors,
            )

        if (
            WarehouseRepository
            .code_exists(
                organization=organization,
                code=values["code"],
                exclude_warehouse_id=(
                    warehouse.id
                ),
            )
        ):
            errors["code"] = [
                (
                    "A warehouse with this code "
                    "already exists."
                )
            ]

        if (
            WarehouseRepository
            .name_exists(
                organization=organization,
                name=values["name"],
                exclude_warehouse_id=(
                    warehouse.id
                ),
            )
        ):
            errors["name"] = [
                (
                    "A warehouse with this name "
                    "already exists."
                )
            ]

        if errors:
            raise WarehouseAPIValidationError(
                "Warehouse validation failed.",
                details=errors,
            )

        return values

    @staticmethod
    def create_warehouse(
        *,
        organization,
        payload,
    ):
        values = (
            WarehouseAPIService
            .validate_create_payload(
                organization=organization,
                payload=payload,
            )
        )

        try:
            return (
                WarehouseRepository
                .create_warehouse(
                    organization=organization,
                    **values,
                )
            )

        except NotUniqueError as exc:
            raise WarehouseAPIValidationError(
                "Warehouse validation failed.",
                details={
                    "warehouse": [
                        (
                            "A warehouse with this "
                            "name or code already exists."
                        )
                    ],
                },
            ) from exc

    @staticmethod
    def get_warehouse(
        *,
        organization,
        warehouse_id,
    ):
        warehouse = (
            WarehouseRepository
            .get_by_id(
                organization=organization,
                warehouse_id=warehouse_id,
            )
        )

        if not warehouse:
            raise LookupError(
                "Warehouse not found."
            )

        return warehouse

    @staticmethod
    def update_warehouse(
        *,
        organization,
        warehouse_id,
        payload,
    ):
        warehouse = (
            WarehouseAPIService
            .get_warehouse(
                organization=organization,
                warehouse_id=warehouse_id,
            )
        )

        values = (
            WarehouseAPIService
            .validate_update_payload(
                organization=organization,
                warehouse=warehouse,
                payload=payload,
            )
        )

        try:
            return (
                WarehouseRepository
                .update_warehouse(
                    warehouse=warehouse,
                    **values,
                )
            )

        except NotUniqueError as exc:
            raise WarehouseAPIValidationError(
                "Warehouse validation failed.",
                details={
                    "warehouse": [
                        (
                            "A warehouse with this "
                            "name or code already exists."
                        )
                    ],
                },
            ) from exc

    @staticmethod
    def activate_warehouse(
        *,
        organization,
        warehouse_id,
    ):
        warehouse = (
            WarehouseAPIService
            .get_warehouse(
                organization=organization,
                warehouse_id=warehouse_id,
            )
        )

        if warehouse.is_active:
            return warehouse

        return (
            WarehouseRepository
            .activate(
                organization=organization,
                warehouse_id=warehouse_id,
            )
        )

    @staticmethod
    def deactivate_warehouse(
        *,
        organization,
        warehouse_id,
    ):
        warehouse = (
            WarehouseAPIService
            .get_warehouse(
                organization=organization,
                warehouse_id=warehouse_id,
            )
        )

        if not warehouse.is_active:
            return warehouse

        return (
            WarehouseRepository
            .deactivate(
                organization=organization,
                warehouse_id=warehouse_id,
            )
        )