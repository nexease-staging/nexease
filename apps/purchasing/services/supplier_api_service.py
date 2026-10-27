from bson import (
    ObjectId,
)
from django.core.exceptions import (
    ValidationError,
)
from django.core.validators import (
    validate_email,
)
from mongoengine.errors import (
    NotUniqueError,
)

from apps.purchasing.repositories.supplier_repository import (
    SupplierRepository,
)


class SupplierAPIValidationError(
    ValueError
):

    def __init__(
        self,
        *,
        message="Validation failed.",
        details=None,
    ):
        super().__init__(
            message
        )

        self.message = message
        self.details = details or {}


class SupplierAPIStateError(
    ValueError
):

    def __init__(
        self,
        *,
        message,
        details=None,
    ):
        super().__init__(
            message
        )

        self.message = message
        self.details = details or {}


class SupplierAPIService:

    CREATE_FIELDS = {
        "code",
        "name",
        "email",
        "phone",
        "gstin",
        "address",
        "city",
        "state",
        "country",
        "pincode",
    }

    UPDATE_FIELDS = {
        "name",
        "email",
        "phone",
        "gstin",
        "address",
        "city",
        "state",
        "country",
        "pincode",
    }

    REQUIRED_CREATE_FIELDS = {
        "code",
        "name",
    }

    @staticmethod
    def _raise_field_error(
        field_name,
        message,
    ):
        raise SupplierAPIValidationError(
            details={
                field_name: [
                    message,
                ],
            },
        )

    @staticmethod
    def _validate_payload_object(
        payload,
    ):
        if not isinstance(
            payload,
            dict,
        ):
            raise SupplierAPIValidationError(
                details={
                    "body": [
                        (
                            "JSON body must be "
                            "an object."
                        ),
                    ],
                },
            )

    @staticmethod
    def _validate_allowed_fields(
        payload,
        *,
        allowed_fields,
    ):
        unknown_fields = (
            set(
                payload.keys()
            )
            -
            allowed_fields
        )

        if not unknown_fields:
            return

        raise SupplierAPIValidationError(
            message=(
                "Unsupported supplier fields "
                "were supplied."
            ),
            details={
                field_name: [
                    "This field is not supported.",
                ]
                for field_name
                in sorted(
                    unknown_fields
                )
            },
        )

    @staticmethod
    def _normalize_required_string(
        value,
        *,
        field_name,
        maximum_length,
    ):
        if not isinstance(
            value,
            str,
        ):
            SupplierAPIService._raise_field_error(
                field_name,
                (
                    f"{field_name} must be "
                    "a string."
                ),
            )

        value = value.strip()

        if not value:
            SupplierAPIService._raise_field_error(
                field_name,
                (
                    f"{field_name} is "
                    "required."
                ),
            )

        if len(value) > maximum_length:
            SupplierAPIService._raise_field_error(
                field_name,
                (
                    f"{field_name} cannot exceed "
                    f"{maximum_length} characters."
                ),
            )

        return value

    @staticmethod
    def _normalize_optional_string(
        value,
        *,
        field_name,
        maximum_length,
    ):
        if value is None:
            return ""

        if not isinstance(
            value,
            str,
        ):
            SupplierAPIService._raise_field_error(
                field_name,
                (
                    f"{field_name} must be "
                    "a string or null."
                ),
            )

        value = value.strip()

        if len(value) > maximum_length:
            SupplierAPIService._raise_field_error(
                field_name,
                (
                    f"{field_name} cannot exceed "
                    f"{maximum_length} characters."
                ),
            )

        return value

    @staticmethod
    def _normalize_email(
        value,
    ):
        email = (
            SupplierAPIService
            ._normalize_optional_string(
                value,
                field_name="email",
                maximum_length=254,
            )
            .lower()
        )

        if not email:
            return ""

        try:
            validate_email(
                email
            )

        except ValidationError:
            SupplierAPIService._raise_field_error(
                "email",
                (
                    "Enter a valid email "
                    "address."
                ),
            )

        return email

    @staticmethod
    def _normalize_supplier_id(
        supplier_id,
    ):
        if (
            not isinstance(
                supplier_id,
                str,
            )
            or
            not ObjectId.is_valid(
                supplier_id
            )
        ):
            raise SupplierAPIValidationError(
                message=(
                    "Invalid supplier identifier."
                ),
                details={
                    "supplier_id": [
                        (
                            "Supplier identifier must "
                            "be a valid ObjectId."
                        ),
                    ],
                },
            )

        return ObjectId(
            supplier_id
        )

    @staticmethod
    def validate_create_payload(
        *,
        organization,
        payload,
    ):
        SupplierAPIService._validate_payload_object(
            payload
        )

        SupplierAPIService._validate_allowed_fields(
            payload,
            allowed_fields=(
                SupplierAPIService
                .CREATE_FIELDS
            ),
        )

        missing_fields = (
            SupplierAPIService
            .REQUIRED_CREATE_FIELDS
            -
            set(
                payload.keys()
            )
        )

        if missing_fields:
            raise SupplierAPIValidationError(
                details={
                    field_name: [
                        (
                            f"{field_name} is "
                            "required."
                        ),
                    ]
                    for field_name
                    in sorted(
                        missing_fields
                    )
                },
            )

        code = (
            SupplierAPIService
            ._normalize_required_string(
                payload.get(
                    "code"
                ),
                field_name="code",
                maximum_length=50,
            )
            .upper()
        )

        name = (
            SupplierAPIService
            ._normalize_required_string(
                payload.get(
                    "name"
                ),
                field_name="name",
                maximum_length=200,
            )
        )

        if (
            SupplierRepository
            .code_exists(
                organization=organization,
                code=code,
            )
        ):
            raise SupplierAPIValidationError(
                message=(
                    "A supplier with this code "
                    "already exists."
                ),
                details={
                    "code": [
                        (
                            "Supplier code must be "
                            "unique within the current "
                            "organization."
                        ),
                    ],
                },
            )

        country = (
            SupplierAPIService
            ._normalize_optional_string(
                payload.get(
                    "country",
                    "India",
                ),
                field_name="country",
                maximum_length=100,
            )
            or
            "India"
        )

        return {
            "code":
                code,
            "name":
                name,
            "email": (
                SupplierAPIService
                ._normalize_email(
                    payload.get(
                        "email",
                        "",
                    )
                )
            ),
            "phone": (
                SupplierAPIService
                ._normalize_optional_string(
                    payload.get(
                        "phone",
                        "",
                    ),
                    field_name="phone",
                    maximum_length=30,
                )
            ),
            "gstin": (
                SupplierAPIService
                ._normalize_optional_string(
                    payload.get(
                        "gstin",
                        "",
                    ),
                    field_name="gstin",
                    maximum_length=20,
                )
                .upper()
            ),
            "address": (
                SupplierAPIService
                ._normalize_optional_string(
                    payload.get(
                        "address",
                        "",
                    ),
                    field_name="address",
                    maximum_length=500,
                )
            ),
            "city": (
                SupplierAPIService
                ._normalize_optional_string(
                    payload.get(
                        "city",
                        "",
                    ),
                    field_name="city",
                    maximum_length=100,
                )
            ),
            "state": (
                SupplierAPIService
                ._normalize_optional_string(
                    payload.get(
                        "state",
                        "",
                    ),
                    field_name="state",
                    maximum_length=100,
                )
            ),
            "country":
                country,
            "pincode": (
                SupplierAPIService
                ._normalize_optional_string(
                    payload.get(
                        "pincode",
                        "",
                    ),
                    field_name="pincode",
                    maximum_length=20,
                )
            ),
        }

    @staticmethod
    def validate_update_payload(
        *,
        payload,
    ):
        SupplierAPIService._validate_payload_object(
            payload
        )

        if not payload:
            raise SupplierAPIValidationError(
                details={
                    "body": [
                        (
                            "At least one editable "
                            "field is required."
                        ),
                    ],
                },
            )

        SupplierAPIService._validate_allowed_fields(
            payload,
            allowed_fields=(
                SupplierAPIService
                .UPDATE_FIELDS
            ),
        )

        updates = {}

        if "name" in payload:
            updates["name"] = (
                SupplierAPIService
                ._normalize_required_string(
                    payload["name"],
                    field_name="name",
                    maximum_length=200,
                )
            )

        if "email" in payload:
            updates["email"] = (
                SupplierAPIService
                ._normalize_email(
                    payload["email"]
                )
            )

        optional_fields = {
            "phone": 30,
            "gstin": 20,
            "address": 500,
            "city": 100,
            "state": 100,
            "country": 100,
            "pincode": 20,
        }

        for (
            field_name,
            maximum_length,
        ) in optional_fields.items():
            if field_name not in payload:
                continue

            value = (
                SupplierAPIService
                ._normalize_optional_string(
                    payload[field_name],
                    field_name=field_name,
                    maximum_length=maximum_length,
                )
            )

            if field_name == "gstin":
                value = value.upper()

            if (
                field_name == "country"
                and
                not value
            ):
                value = "India"

            updates[field_name] = value

        return updates

    @staticmethod
    def create_supplier(
        *,
        organization,
        payload,
    ):
        if not organization:
            raise PermissionError(
                "Organization context unavailable."
            )

        values = (
            SupplierAPIService
            .validate_create_payload(
                organization=organization,
                payload=payload,
            )
        )

        try:
            return (
                SupplierRepository
                .create_supplier(
                    organization=organization,
                    **values,
                )
            )

        except NotUniqueError:
            raise SupplierAPIValidationError(
                message=(
                    "A supplier with this code "
                    "already exists."
                ),
                details={
                    "code": [
                        (
                            "Supplier code must be "
                            "unique within the current "
                            "organization."
                        ),
                    ],
                },
            )

    @staticmethod
    def get_supplier(
        *,
        organization,
        supplier_id,
    ):
        if not organization:
            raise PermissionError(
                "Organization context unavailable."
            )

        normalized_supplier_id = (
            SupplierAPIService
            ._normalize_supplier_id(
                supplier_id
            )
        )

        supplier = (
            SupplierRepository
            .get_by_id(
                organization=organization,
                supplier_id=(
                    normalized_supplier_id
                ),
            )
        )

        if not supplier:
            raise LookupError(
                "Supplier not found."
            )

        return supplier

    @staticmethod
    def update_supplier(
        *,
        organization,
        supplier_id,
        payload,
    ):
        supplier = (
            SupplierAPIService
            .get_supplier(
                organization=organization,
                supplier_id=supplier_id,
            )
        )

        if not supplier.is_active:
            raise SupplierAPIStateError(
                message=(
                    "Inactive suppliers cannot "
                    "be updated."
                ),
                details={
                    "is_active": [
                        (
                            "Activate the supplier "
                            "before updating it."
                        ),
                    ],
                },
            )

        updates = (
            SupplierAPIService
            .validate_update_payload(
                payload=payload,
            )
        )

        return (
            SupplierRepository
            .update_supplier(
                supplier=supplier,
                **updates,
            )
        )

    @staticmethod
    def activate_supplier(
        *,
        organization,
        supplier_id,
    ):
        supplier = (
            SupplierAPIService
            .get_supplier(
                organization=organization,
                supplier_id=supplier_id,
            )
        )

        if supplier.is_active:
            return supplier

        return (
            SupplierRepository
            .set_active_status(
                supplier=supplier,
                is_active=True,
            )
        )

    @staticmethod
    def deactivate_supplier(
        *,
        organization,
        supplier_id,
    ):
        supplier = (
            SupplierAPIService
            .get_supplier(
                organization=organization,
                supplier_id=supplier_id,
            )
        )

        if not supplier.is_active:
            return supplier

        return (
            SupplierRepository
            .set_active_status(
                supplier=supplier,
                is_active=False,
            )
        )