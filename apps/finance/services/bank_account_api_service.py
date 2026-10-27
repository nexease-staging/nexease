from decimal import (
    Decimal,
    InvalidOperation,
)

from bson import (
    ObjectId,
)

from apps.finance.repositories.bank_account_repository import (
    BankAccountRepository,
)
from apps.finance.services.bank_account_service import (
    BankAccountService,
)


class BankAccountAPIValidationError(
    ValueError
):

    def __init__(
        self,
        *,
        message=(
            "Bank account validation failed."
        ),
        details=None,
    ):
        super().__init__(
            message
        )

        self.message = message
        self.details = details or {}


class BankAccountAPIStateError(
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


class BankAccountAPIService:

    ACCOUNT_TYPES = {
        "BANK",
        "CASH",
    }

    CREATE_FIELDS = {
        "account_name",
        "account_type",
        "bank_name",
        "account_number",
        "ifsc_code",
        "currency",
        "opening_balance",
    }

    UPDATE_FIELDS = {
        "account_name",
        "bank_name",
        "account_number",
        "ifsc_code",
    }

    @staticmethod
    def _raise_field_error(
        field,
        message,
    ):
        raise (
            BankAccountAPIValidationError(
                details={
                    field: [
                        message,
                    ],
                },
            )
        )

    @staticmethod
    def _validate_payload_object(
        payload,
    ):
        if not isinstance(
            payload,
            dict,
        ):
            raise (
                BankAccountAPIValidationError(
                    details={
                        "body": [
                            (
                                "JSON body must "
                                "be an object."
                            ),
                        ],
                    },
                )
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

        if unknown_fields:
            raise (
                BankAccountAPIValidationError(
                    details={
                        field: [
                            (
                                "This field is "
                                "not supported."
                            ),
                        ]
                        for field
                        in sorted(
                            unknown_fields
                        )
                    },
                )
            )

    @staticmethod
    def _normalize_identifier(
        value,
        *,
        field,
    ):
        if (
            not isinstance(
                value,
                str,
            )
            or
            not ObjectId.is_valid(
                value.strip()
            )
        ):
            (
                BankAccountAPIService
                ._raise_field_error(
                    field,
                    (
                        "This field must contain "
                        "a valid ObjectId."
                    ),
                )
            )

        return value.strip()

    @staticmethod
    def _normalize_required_text(
        value,
        *,
        field,
        maximum_length,
    ):
        if not isinstance(
            value,
            str,
        ):
            (
                BankAccountAPIService
                ._raise_field_error(
                    field,
                    (
                        "This field must be "
                        "a string."
                    ),
                )
            )

        normalized = value.strip()

        if not normalized:
            (
                BankAccountAPIService
                ._raise_field_error(
                    field,
                    "This field is required.",
                )
            )

        if (
            len(
                normalized
            )
            >
            maximum_length
        ):
            (
                BankAccountAPIService
                ._raise_field_error(
                    field,
                    (
                        "This field must not exceed "
                        f"{maximum_length} characters."
                    ),
                )
            )

        return normalized

    @staticmethod
    def _normalize_optional_text(
        value,
        *,
        field,
        maximum_length,
    ):
        if value is None:
            return ""

        if not isinstance(
            value,
            str,
        ):
            (
                BankAccountAPIService
                ._raise_field_error(
                    field,
                    (
                        "This field must be "
                        "a string."
                    ),
                )
            )

        normalized = value.strip()

        if (
            len(
                normalized
            )
            >
            maximum_length
        ):
            (
                BankAccountAPIService
                ._raise_field_error(
                    field,
                    (
                        "This field must not exceed "
                        f"{maximum_length} characters."
                    ),
                )
            )

        return normalized

    @staticmethod
    def _normalize_account_type(
        value,
    ):
        normalized = (
            BankAccountAPIService
            ._normalize_required_text(
                value,
                field="account_type",
                maximum_length=20,
            )
            .upper()
        )

        if (
            normalized
            not in
            BankAccountAPIService
            .ACCOUNT_TYPES
        ):
            (
                BankAccountAPIService
                ._raise_field_error(
                    "account_type",
                    (
                        "Select BANK or CASH."
                    ),
                )
            )

        return normalized

    @staticmethod
    def _normalize_decimal(
        value,
        *,
        field,
    ):
        if isinstance(
            value,
            bool,
        ):
            (
                BankAccountAPIService
                ._raise_field_error(
                    field,
                    (
                        "This field must contain "
                        "a valid decimal amount."
                    ),
                )
            )

        try:
            normalized = Decimal(
                str(
                    value
                )
            )

        except (
            InvalidOperation,
            TypeError,
            ValueError,
        ):
            (
                BankAccountAPIService
                ._raise_field_error(
                    field,
                    (
                        "This field must contain "
                        "a valid decimal amount."
                    ),
                )
            )

        if not normalized.is_finite():
            (
                BankAccountAPIService
                ._raise_field_error(
                    field,
                    (
                        "This field must contain "
                        "a finite decimal amount."
                    ),
                )
            )

        decimal_places = (
            -normalized.as_tuple().exponent
            if normalized.as_tuple().exponent < 0
            else 0
        )

        if decimal_places > 2:
            (
                BankAccountAPIService
                ._raise_field_error(
                    field,
                    (
                        "This field must not have "
                        "more than 2 decimal places."
                    ),
                )
            )

        return normalized

    @staticmethod
    def validate_create_payload(
        payload,
    ):
        (
            BankAccountAPIService
            ._validate_payload_object(
                payload
            )
        )

        (
            BankAccountAPIService
            ._validate_allowed_fields(
                payload,
                allowed_fields=(
                    BankAccountAPIService
                    .CREATE_FIELDS
                ),
            )
        )

        missing_fields = [
            field
            for field
            in (
                "account_name",
                "account_type",
            )
            if field not in payload
        ]

        if missing_fields:
            raise (
                BankAccountAPIValidationError(
                    details={
                        field: [
                            "This field is required.",
                        ]
                        for field
                        in missing_fields
                    },
                )
            )

        account_type = (
            BankAccountAPIService
            ._normalize_account_type(
                payload.get(
                    "account_type"
                )
            )
        )

        values = {
            "account_name": (
                BankAccountAPIService
                ._normalize_required_text(
                    payload.get(
                        "account_name"
                    ),
                    field="account_name",
                    maximum_length=150,
                )
            ),
            "account_type":
                account_type,
            "bank_name": (
                BankAccountAPIService
                ._normalize_optional_text(
                    payload.get(
                        "bank_name",
                        "",
                    ),
                    field="bank_name",
                    maximum_length=150,
                )
            ),
            "account_number": (
                BankAccountAPIService
                ._normalize_optional_text(
                    payload.get(
                        "account_number",
                        "",
                    ),
                    field="account_number",
                    maximum_length=100,
                )
            ),
            "ifsc_code": (
                BankAccountAPIService
                ._normalize_optional_text(
                    payload.get(
                        "ifsc_code",
                        "",
                    ),
                    field="ifsc_code",
                    maximum_length=20,
                )
                .upper()
            ),
            "currency": (
                BankAccountAPIService
                ._normalize_required_text(
                    payload.get(
                        "currency",
                        "INR",
                    ),
                    field="currency",
                    maximum_length=10,
                )
                .upper()
            ),
            "opening_balance": (
                BankAccountAPIService
                ._normalize_decimal(
                    payload.get(
                        "opening_balance",
                        "0",
                    ),
                    field="opening_balance",
                )
            ),
        }

        if account_type == "BANK":
            if not values["bank_name"]:
                (
                    BankAccountAPIService
                    ._raise_field_error(
                        "bank_name",
                        (
                            "This field is required "
                            "for bank accounts."
                        ),
                    )
                )

            if not values["account_number"]:
                (
                    BankAccountAPIService
                    ._raise_field_error(
                        "account_number",
                        (
                            "This field is required "
                            "for bank accounts."
                        ),
                    )
                )

        if (
            account_type == "CASH"
            and
            (
                values["bank_name"]
                or
                values["account_number"]
                or
                values["ifsc_code"]
            )
        ):
            raise (
                BankAccountAPIValidationError(
                    details={
                        "account_type": [
                            (
                                "Cash accounts cannot "
                                "contain bank details."
                            ),
                        ],
                    },
                )
            )

        return values

    @staticmethod
    def validate_update_payload(
        payload,
        *,
        bank_account,
    ):
        (
            BankAccountAPIService
            ._validate_payload_object(
                payload
            )
        )

        (
            BankAccountAPIService
            ._validate_allowed_fields(
                payload,
                allowed_fields=(
                    BankAccountAPIService
                    .UPDATE_FIELDS
                ),
            )
        )

        if not payload:
            raise (
                BankAccountAPIValidationError(
                    details={
                        "body": [
                            (
                                "Provide at least one "
                                "field to update."
                            ),
                        ],
                    },
                )
            )

        values = {
            "account_name":
                bank_account.account_name,
            "bank_name":
                bank_account.bank_name,
            "account_number":
                bank_account.account_number,
            "ifsc_code":
                bank_account.ifsc_code,
        }

        if "account_name" in payload:
            values["account_name"] = (
                BankAccountAPIService
                ._normalize_required_text(
                    payload.get(
                        "account_name"
                    ),
                    field="account_name",
                    maximum_length=150,
                )
            )

        if "bank_name" in payload:
            values["bank_name"] = (
                BankAccountAPIService
                ._normalize_optional_text(
                    payload.get(
                        "bank_name"
                    ),
                    field="bank_name",
                    maximum_length=150,
                )
            )

        if "account_number" in payload:
            values["account_number"] = (
                BankAccountAPIService
                ._normalize_optional_text(
                    payload.get(
                        "account_number"
                    ),
                    field="account_number",
                    maximum_length=100,
                )
            )

        if "ifsc_code" in payload:
            values["ifsc_code"] = (
                BankAccountAPIService
                ._normalize_optional_text(
                    payload.get(
                        "ifsc_code"
                    ),
                    field="ifsc_code",
                    maximum_length=20,
                )
                .upper()
            )

        return values

    @staticmethod
    def _get_bank_account(
        *,
        organization,
        bank_account_id,
    ):
        normalized_id = (
            BankAccountAPIService
            ._normalize_identifier(
                bank_account_id,
                field="bank_account_id",
            )
        )

        bank_account = (
            BankAccountRepository
            .get_by_id(
                organization=organization,
                bank_account_id=(
                    normalized_id
                ),
            )
        )

        if not bank_account:
            raise LookupError(
                "Bank account not found."
            )

        return bank_account

    @staticmethod
    def create_bank_account(
        *,
        user,
        organization,
        payload,
    ):
        values = (
            BankAccountAPIService
            .validate_create_payload(
                payload
            )
        )

        try:
            return (
                BankAccountService
                .create_bank_account(
                    user=user,
                    organization=organization,
                    **values,
                )
            )

        except PermissionError:
            raise

        except ValueError as exc:
            raise (
                BankAccountAPIStateError(
                    message=str(
                        exc
                    ),
                )
            ) from exc

    @staticmethod
    def get_bank_account(
        *,
        organization,
        bank_account_id,
    ):
        return (
            BankAccountAPIService
            ._get_bank_account(
                organization=organization,
                bank_account_id=(
                    bank_account_id
                ),
            )
        )

    @staticmethod
    def update_bank_account(
        *,
        user,
        organization,
        bank_account_id,
        payload,
    ):
        bank_account = (
            BankAccountAPIService
            ._get_bank_account(
                organization=organization,
                bank_account_id=(
                    bank_account_id
                ),
            )
        )

        values = (
            BankAccountAPIService
            .validate_update_payload(
                payload,
                bank_account=bank_account,
            )
        )

        try:
            return (
                BankAccountService
                .update_bank_account(
                    user=user,
                    organization=organization,
                    bank_account=bank_account,
                    **values,
                )
            )

        except PermissionError:
            raise

        except ValueError as exc:
            raise (
                BankAccountAPIStateError(
                    message=str(
                        exc
                    ),
                )
            ) from exc

    @staticmethod
    def deactivate_bank_account(
        *,
        user,
        organization,
        bank_account_id,
    ):
        bank_account = (
            BankAccountAPIService
            ._get_bank_account(
                organization=organization,
                bank_account_id=(
                    bank_account_id
                ),
            )
        )

        try:
            return (
                BankAccountService
                .deactivate_bank_account(
                    user=user,
                    organization=organization,
                    bank_account=bank_account,
                )
            )

        except PermissionError:
            raise

        except ValueError as exc:
            raise (
                BankAccountAPIStateError(
                    message=str(
                        exc
                    ),
                )
            ) from exc