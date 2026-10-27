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

from apps.sales.repositories.customer_repository import (
    CustomerRepository,
)


class CustomerAPIValidationError(
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


class CustomerAPIStateError(
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


class CustomerAPIService:

    CREATE_FIELDS = {
        "code",
        "name",
        "email",
        "phone",
        "gstin",
        "billing_address",
        "shipping_address",
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
        "billing_address",
        "shipping_address",
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
        raise CustomerAPIValidationError(
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
            raise CustomerAPIValidationError(
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

        raise CustomerAPIValidationError(
            message=(
                "Unsupported customer fields "
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
            CustomerAPIService._raise_field_error(
                field_name,
                (
                    f"{field_name} must be "
                    "a string."
                ),
            )

        value = value.strip()

        if not value:
            CustomerAPIService._raise_field_error(
                field_name,
                (
                    f"{field_name} is "
                    "required."
                ),
            )

        if len(value) > maximum_length:
            CustomerAPIService._raise_field_error(
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
            CustomerAPIService._raise_field_error(
                field_name,
                (
                    f"{field_name} must be "
                    "a string or null."
                ),
            )

        value = value.strip()

        if len(value) > maximum_length:
            CustomerAPIService._raise_field_error(
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
            CustomerAPIService
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
            CustomerAPIService._raise_field_error(
                "email",
                (
                    "Enter a valid email "
                    "address."
                ),
            )

        return email

    @staticmethod
    def _normalize_customer_id(
        customer_id,
    ):
        if (
            not isinstance(
                customer_id,
                str,
            )
            or
            not ObjectId.is_valid(
                customer_id
            )
        ):
            raise CustomerAPIValidationError(
                message=(
                    "Invalid customer identifier."
                ),
                details={
                    "customer_id": [
                        (
                            "Customer identifier must "
                            "be a valid ObjectId."
                        ),
                    ],
                },
            )

        return ObjectId(
            customer_id
        )

    @staticmethod
    def validate_create_payload(
        *,
        organization,
        payload,
    ):
        CustomerAPIService._validate_payload_object(
            payload
        )

        CustomerAPIService._validate_allowed_fields(
            payload,
            allowed_fields=(
                CustomerAPIService
                .CREATE_FIELDS
            ),
        )

        missing_fields = (
            CustomerAPIService
            .REQUIRED_CREATE_FIELDS
            -
            set(
                payload.keys()
            )
        )

        if missing_fields:
            raise CustomerAPIValidationError(
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
            CustomerAPIService
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
            CustomerAPIService
            ._normalize_required_string(
                payload.get(
                    "name"
                ),
                field_name="name",
                maximum_length=200,
            )
        )

        if (
            CustomerRepository
            .code_exists(
                organization=organization,
                code=code,
            )
        ):
            raise CustomerAPIValidationError(
                message=(
                    "A customer with this code "
                    "already exists."
                ),
                details={
                    "code": [
                        (
                            "Customer code must be "
                            "unique within the current "
                            "organization."
                        ),
                    ],
                },
            )

        country = (
            CustomerAPIService
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
                CustomerAPIService
                ._normalize_email(
                    payload.get(
                        "email",
                        "",
                    )
                )
            ),
            "phone": (
                CustomerAPIService
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
                CustomerAPIService
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
            "billing_address": (
                CustomerAPIService
                ._normalize_optional_string(
                    payload.get(
                        "billing_address",
                        "",
                    ),
                    field_name=(
                        "billing_address"
                    ),
                    maximum_length=500,
                )
            ),
            "shipping_address": (
                CustomerAPIService
                ._normalize_optional_string(
                    payload.get(
                        "shipping_address",
                        "",
                    ),
                    field_name=(
                        "shipping_address"
                    ),
                    maximum_length=500,
                )
            ),
            "city": (
                CustomerAPIService
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
                CustomerAPIService
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
                CustomerAPIService
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
        CustomerAPIService._validate_payload_object(
            payload
        )

        if not payload:
            raise CustomerAPIValidationError(
                details={
                    "body": [
                        (
                            "At least one editable "
                            "field is required."
                        ),
                    ],
                },
            )

        CustomerAPIService._validate_allowed_fields(
            payload,
            allowed_fields=(
                CustomerAPIService
                .UPDATE_FIELDS
            ),
        )

        updates = {}

        if "name" in payload:
            updates["name"] = (
                CustomerAPIService
                ._normalize_required_string(
                    payload["name"],
                    field_name="name",
                    maximum_length=200,
                )
            )

        if "email" in payload:
            updates["email"] = (
                CustomerAPIService
                ._normalize_email(
                    payload["email"]
                )
            )

        optional_fields = {
            "phone": 30,
            "gstin": 20,
            "billing_address": 500,
            "shipping_address": 500,
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
                CustomerAPIService
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
    def create_customer(
        *,
        organization,
        payload,
    ):
        if not organization:
            raise PermissionError(
                "Organization context unavailable."
            )

        values = (
            CustomerAPIService
            .validate_create_payload(
                organization=organization,
                payload=payload,
            )
        )

        try:
            return (
                CustomerRepository
                .create_customer(
                    organization=organization,
                    **values,
                )
            )

        except NotUniqueError:
            raise CustomerAPIValidationError(
                message=(
                    "A customer with this code "
                    "already exists."
                ),
                details={
                    "code": [
                        (
                            "Customer code must be "
                            "unique within the current "
                            "organization."
                        ),
                    ],
                },
            )

    @staticmethod
    def get_customer(
        *,
        organization,
        customer_id,
    ):
        if not organization:
            raise PermissionError(
                "Organization context unavailable."
            )

        normalized_customer_id = (
            CustomerAPIService
            ._normalize_customer_id(
                customer_id
            )
        )

        customer = (
            CustomerRepository
            .get_by_id(
                organization=organization,
                customer_id=(
                    normalized_customer_id
                ),
            )
        )

        if not customer:
            raise LookupError(
                "Customer not found."
            )

        return customer

    @staticmethod
    def update_customer(
        *,
        organization,
        customer_id,
        payload,
    ):
        customer = (
            CustomerAPIService
            .get_customer(
                organization=organization,
                customer_id=customer_id,
            )
        )

        if not customer.is_active:
            raise CustomerAPIStateError(
                message=(
                    "Inactive customers cannot "
                    "be updated."
                ),
                details={
                    "is_active": [
                        (
                            "Activate the customer "
                            "before updating it."
                        ),
                    ],
                },
            )

        updates = (
            CustomerAPIService
            .validate_update_payload(
                payload=payload,
            )
        )

        return (
            CustomerRepository
            .update_customer(
                customer=customer,
                **updates,
            )
        )

    @staticmethod
    def activate_customer(
        *,
        organization,
        customer_id,
    ):
        customer = (
            CustomerAPIService
            .get_customer(
                organization=organization,
                customer_id=customer_id,
            )
        )

        if customer.is_active:
            return customer

        return (
            CustomerRepository
            .set_active_status(
                customer=customer,
                is_active=True,
            )
        )

    @staticmethod
    def deactivate_customer(
        *,
        organization,
        customer_id,
    ):
        customer = (
            CustomerAPIService
            .get_customer(
                organization=organization,
                customer_id=customer_id,
            )
        )

        if not customer.is_active:
            return customer

        return (
            CustomerRepository
            .set_active_status(
                customer=customer,
                is_active=False,
            )
        )