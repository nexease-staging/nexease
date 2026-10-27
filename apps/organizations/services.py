import re

from datetime import datetime
from zoneinfo import (
    ZoneInfo,
    ZoneInfoNotFoundError,
)

from django.core.exceptions import (
    ValidationError as DjangoValidationError,
)
from django.core.validators import (
    validate_email,
)

from apps.organizations.models import (
    Organization,
)


class OrganizationUpdateValidationError(
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

        self.details = (
            details
            or
            {}
        )


class OrganizationService:

    EDITABLE_FIELDS = {
        "business_scope",
        "name",
        "email",
        "phone",
        "address",
        "country",
        "currency",
        "timezone",
    }

    PHONE_PATTERN = re.compile(
        r"^[0-9+().\-\s]{7,30}$"
    )

    CURRENCY_PATTERN = re.compile(
        r"^[A-Z]{3,10}$"
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

            raise (
                OrganizationUpdateValidationError(
                    details={
                        field_name: [
                            (
                                f"{field_name} "
                                "must be a string."
                            )
                        ],
                    },
                )
            )

        value = value.strip()

        if not value:

            raise (
                OrganizationUpdateValidationError(
                    details={
                        field_name: [
                            (
                                f"{field_name} "
                                "is required."
                            )
                        ],
                    },
                )
            )

        if (
            len(
                value
            )
            >
            maximum_length
        ):

            raise (
                OrganizationUpdateValidationError(
                    details={
                        field_name: [
                            (
                                f"{field_name} cannot "
                                f"exceed "
                                f"{maximum_length} "
                                "characters."
                            )
                        ],
                    },
                )
            )

        return value

    @staticmethod
    def validate_update_payload(
        payload,
    ):
        if not isinstance(
            payload,
            dict,
        ):

            raise (
                OrganizationUpdateValidationError(
                    details={
                        "body": [
                            (
                                "JSON body must "
                                "be an object."
                            )
                        ],
                    },
                )
            )

        if not payload:

            raise (
                OrganizationUpdateValidationError(
                    details={
                        "body": [
                            (
                                "At least one editable "
                                "field is required."
                            )
                        ],
                    },
                )
            )

        unknown_fields = (
            set(
                payload.keys()
            )
            -
            OrganizationService
            .EDITABLE_FIELDS
        )

        if unknown_fields:

            details = {}

            for field_name in sorted(
                unknown_fields
            ):

                details[
                    field_name
                ] = [
                    "This field cannot be updated."
                ]

            raise (
                OrganizationUpdateValidationError(
                    message=(
                        "Unsupported organization "
                        "fields were supplied."
                    ),
                    details=details,
                )
            )

        updates = {}
        if "business_scope" in payload:
            from apps.business.profiles import PROFILES
            if payload["business_scope"] not in PROFILES:
                raise OrganizationUpdateValidationError(details={"business_scope":["Choose a valid business scope."]})
            updates["business_scope"] = payload["business_scope"]


        # ==================================================
        # NAME
        # ==================================================

        if "name" in payload:

            updates[
                "name"
            ] = (
                OrganizationService
                ._normalize_required_string(
                    payload[
                        "name"
                    ],
                    field_name="name",
                    maximum_length=200,
                )
            )

        # ==================================================
        # EMAIL
        # ==================================================

        if "email" in payload:

            email = (
                OrganizationService
                ._normalize_required_string(
                    payload[
                        "email"
                    ],
                    field_name="email",
                    maximum_length=254,
                )
                .lower()
            )

            try:

                validate_email(
                    email
                )

            except DjangoValidationError:

                raise (
                    OrganizationUpdateValidationError(
                        details={
                            "email": [
                                (
                                    "Enter a valid "
                                    "email address."
                                )
                            ],
                        },
                    )
                )

            updates[
                "email"
            ] = email

        # ==================================================
        # PHONE
        # ==================================================

        if "phone" in payload:

            phone = payload[
                "phone"
            ]

            if phone is None:

                updates[
                    "phone"
                ] = None

            elif not isinstance(
                phone,
                str,
            ):

                raise (
                    OrganizationUpdateValidationError(
                        details={
                            "phone": [
                                (
                                    "phone must be "
                                    "a string or null."
                                )
                            ],
                        },
                    )
                )

            else:

                phone = phone.strip()

                if not phone:

                    updates[
                        "phone"
                    ] = None

                elif not (
                    OrganizationService
                    .PHONE_PATTERN
                    .fullmatch(
                        phone
                    )
                ):

                    raise (
                        OrganizationUpdateValidationError(
                            details={
                                "phone": [
                                    (
                                        "Enter a valid "
                                        "phone number."
                                    )
                                ],
                            },
                        )
                    )

                else:

                    updates[
                        "phone"
                    ] = phone

        # ==================================================
        # ADDRESS
        # ==================================================

        if "address" in payload:

            address = payload[
                "address"
            ]

            if address is None:

                updates[
                    "address"
                ] = None

            elif not isinstance(
                address,
                str,
            ):

                raise (
                    OrganizationUpdateValidationError(
                        details={
                            "address": [
                                (
                                    "address must be "
                                    "a string or null."
                                )
                            ],
                        },
                    )
                )

            else:

                address = address.strip()

                if len(
                    address
                ) > 500:

                    raise (
                        OrganizationUpdateValidationError(
                            details={
                                "address": [
                                    (
                                        "address cannot "
                                        "exceed 500 "
                                        "characters."
                                    )
                                ],
                            },
                        )
                    )

                updates[
                    "address"
                ] = (
                    address
                    or
                    None
                )

        # ==================================================
        # COUNTRY
        # ==================================================

        if "country" in payload:

            updates[
                "country"
            ] = (
                OrganizationService
                ._normalize_required_string(
                    payload[
                        "country"
                    ],
                    field_name="country",
                    maximum_length=100,
                )
            )

        # ==================================================
        # CURRENCY
        # ==================================================

        if "currency" in payload:

            currency = (
                OrganizationService
                ._normalize_required_string(
                    payload[
                        "currency"
                    ],
                    field_name="currency",
                    maximum_length=10,
                )
                .upper()
            )

            if not (
                OrganizationService
                .CURRENCY_PATTERN
                .fullmatch(
                    currency
                )
            ):

                raise (
                    OrganizationUpdateValidationError(
                        details={
                            "currency": [
                                (
                                    "currency must contain "
                                    "3 to 10 uppercase "
                                    "letters."
                                )
                            ],
                        },
                    )
                )

            updates[
                "currency"
            ] = currency

        # ==================================================
        # TIMEZONE
        # ==================================================

        if "timezone" in payload:

            timezone_name = (
                OrganizationService
                ._normalize_required_string(
                    payload[
                        "timezone"
                    ],
                    field_name="timezone",
                    maximum_length=100,
                )
            )

            try:

                ZoneInfo(
                    timezone_name
                )

            except (
                ZoneInfoNotFoundError,
                ValueError,
            ):

                raise (
                    OrganizationUpdateValidationError(
                        details={
                            "timezone": [
                                (
                                    "Enter a valid IANA "
                                    "timezone."
                                )
                            ],
                        },
                    )
                )

            updates[
                "timezone"
            ] = timezone_name

        return updates

    @staticmethod
    def update_organization(
        *,
        organization,
        payload,
    ):
        if not organization:

            raise PermissionError(
                "Organization context unavailable."
            )

        updates = (
            OrganizationService
            .validate_update_payload(
                payload
            )
        )

        mongo_updates = {
            f"set__{field_name}":
                value
            for field_name, value
            in updates.items()
        }

        mongo_updates[
            "set__updated_at"
        ] = datetime.utcnow()

        updated_organization = (
            Organization.objects(
                id=organization.id,
                is_active=True,
            )
            .modify(
                new=True,
                **mongo_updates,
            )
        )

        if not updated_organization:

            raise LookupError(
                "Organization not found."
            )

        return updated_organization