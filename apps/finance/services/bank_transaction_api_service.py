from datetime import (
    date,
    datetime,
    time,
)
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
from apps.finance.repositories.bank_transaction_repository import (
    BankTransactionRepository,
)
from apps.finance.services.bank_transaction_service import (
    BankTransactionService,
)


class BankTransactionAPIValidationError(
    ValueError
):

    def __init__(
        self,
        *,
        message=(
            "Bank transaction validation failed."
        ),
        details=None,
    ):
        super().__init__(
            message
        )

        self.message = message
        self.details = details or {}


class BankTransactionAPIStateError(
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


class BankTransactionAPIService:

    MANUAL_TRANSACTION_TYPES = {
        "MONEY_IN",
        "MONEY_OUT",
        "BANK_CHARGE",
        "INTEREST",
        "OTHER_IN",
        "OTHER_OUT",
    }

    CREATE_FIELDS = {
        "bank_account_id",
        "transaction_type",
        "transaction_date",
        "amount",
        "reference_type",
        "reference_id",
        "external_reference",
        "description",
    }

    @staticmethod
    def _raise_field_error(
        field,
        message,
    ):
        raise (
            BankTransactionAPIValidationError(
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
                BankTransactionAPIValidationError(
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
                BankTransactionAPIValidationError(
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
                BankTransactionAPIService
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
                BankTransactionAPIService
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
                BankTransactionAPIService
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
                BankTransactionAPIService
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
                BankTransactionAPIService
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
                BankTransactionAPIService
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
                BankTransactionAPIService
                ._raise_field_error(
                    field,
                    "Enter a valid decimal amount.",
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
                BankTransactionAPIService
                ._raise_field_error(
                    field,
                    "Enter a valid decimal amount.",
                )
            )

        if (
            not normalized.is_finite()
            or
            normalized <= 0
        ):
            (
                BankTransactionAPIService
                ._raise_field_error(
                    field,
                    (
                        "Amount must be greater "
                        "than zero."
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
                BankTransactionAPIService
                ._raise_field_error(
                    field,
                    (
                        "Amount must not have more "
                        "than 2 decimal places."
                    ),
                )
            )

        return normalized

    @staticmethod
    def _normalize_datetime(
        value,
        *,
        field,
    ):
        if isinstance(
            value,
            datetime,
        ):
            return value

        if (
            isinstance(
                value,
                date,
            )
            and
            not isinstance(
                value,
                datetime,
            )
        ):
            return datetime.combine(
                value,
                time.min,
            )

        if not isinstance(
            value,
            str,
        ):
            (
                BankTransactionAPIService
                ._raise_field_error(
                    field,
                    (
                        "Use an ISO-8601 date "
                        "or datetime."
                    ),
                )
            )

        normalized = value.strip()

        if not normalized:
            (
                BankTransactionAPIService
                ._raise_field_error(
                    field,
                    "This field is required.",
                )
            )

        try:
            if (
                len(
                    normalized
                )
                ==
                10
            ):
                return datetime.combine(
                    date.fromisoformat(
                        normalized
                    ),
                    time.min,
                )

            return datetime.fromisoformat(
                normalized.replace(
                    "Z",
                    "+00:00",
                )
            )

        except ValueError:
            (
                BankTransactionAPIService
                ._raise_field_error(
                    field,
                    (
                        "Use an ISO-8601 date "
                        "or datetime."
                    ),
                )
            )

    @staticmethod
    def _normalize_transaction_type(
        value,
    ):
        normalized = (
            BankTransactionAPIService
            ._normalize_required_text(
                value,
                field="transaction_type",
                maximum_length=30,
            )
            .upper()
        )

        if (
            normalized
            not in
            BankTransactionAPIService
            .MANUAL_TRANSACTION_TYPES
        ):
            (
                BankTransactionAPIService
                ._raise_field_error(
                    "transaction_type",
                    (
                        "Select a valid manual "
                        "transaction type."
                    ),
                )
            )

        return normalized

    @staticmethod
    def validate_create_payload(
        payload,
    ):
        (
            BankTransactionAPIService
            ._validate_payload_object(
                payload
            )
        )

        (
            BankTransactionAPIService
            ._validate_allowed_fields(
                payload,
                allowed_fields=(
                    BankTransactionAPIService
                    .CREATE_FIELDS
                ),
            )
        )

        missing_fields = [
            field
            for field
            in (
                "bank_account_id",
                "transaction_type",
                "transaction_date",
                "amount",
            )
            if field not in payload
        ]

        if missing_fields:
            raise (
                BankTransactionAPIValidationError(
                    details={
                        field: [
                            "This field is required.",
                        ]
                        for field
                        in missing_fields
                    },
                )
            )

        reference_type = (
            BankTransactionAPIService
            ._normalize_optional_text(
                payload.get(
                    "reference_type",
                    "",
                ),
                field="reference_type",
                maximum_length=100,
            )
        )

        reference_id = (
            BankTransactionAPIService
            ._normalize_optional_text(
                payload.get(
                    "reference_id",
                    "",
                ),
                field="reference_id",
                maximum_length=100,
            )
        )

        if bool(
            reference_type
        ) != bool(
            reference_id
        ):
            raise (
                BankTransactionAPIValidationError(
                    details={
                        "reference_type": [
                            (
                                "Reference type and "
                                "reference ID must be "
                                "provided together."
                            ),
                        ],
                        "reference_id": [
                            (
                                "Reference type and "
                                "reference ID must be "
                                "provided together."
                            ),
                        ],
                    },
                )
            )

        return {
            "bank_account_id": (
                BankTransactionAPIService
                ._normalize_identifier(
                    payload.get(
                        "bank_account_id"
                    ),
                    field="bank_account_id",
                )
            ),
            "transaction_type": (
                BankTransactionAPIService
                ._normalize_transaction_type(
                    payload.get(
                        "transaction_type"
                    )
                )
            ),
            "transaction_date": (
                BankTransactionAPIService
                ._normalize_datetime(
                    payload.get(
                        "transaction_date"
                    ),
                    field="transaction_date",
                )
            ),
            "amount": (
                BankTransactionAPIService
                ._normalize_decimal(
                    payload.get(
                        "amount"
                    ),
                    field="amount",
                )
            ),
            "reference_type":
                reference_type,
            "reference_id":
                reference_id,
            "external_reference": (
                BankTransactionAPIService
                ._normalize_optional_text(
                    payload.get(
                        "external_reference",
                        "",
                    ),
                    field="external_reference",
                    maximum_length=150,
                )
            ),
            "description": (
                BankTransactionAPIService
                ._normalize_optional_text(
                    payload.get(
                        "description",
                        "",
                    ),
                    field="description",
                    maximum_length=1000,
                )
            ),
        }

    @staticmethod
    def _get_transaction(
        *,
        organization,
        transaction_id,
    ):
        normalized_id = (
            BankTransactionAPIService
            ._normalize_identifier(
                transaction_id,
                field="transaction_id",
            )
        )

        transaction = (
            BankTransactionRepository
            .get_by_id(
                organization=organization,
                transaction_id=normalized_id,
            )
        )

        if not transaction:
            raise LookupError(
                "Bank transaction not found."
            )

        return transaction

    @staticmethod
    def create_transaction(
        *,
        user,
        organization,
        payload,
    ):
        values = (
            BankTransactionAPIService
            .validate_create_payload(
                payload
            )
        )

        bank_account = (
            BankAccountRepository
            .get_by_id(
                organization=organization,
                bank_account_id=(
                    values.pop(
                        "bank_account_id"
                    )
                ),
            )
        )

        if not bank_account:
            raise (
                BankTransactionAPIValidationError(
                    details={
                        "bank_account_id": [
                            (
                                "Select a valid bank "
                                "account."
                            ),
                        ],
                    },
                )
            )

        try:
            return (
                BankTransactionService
                .create_transaction(
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
                BankTransactionAPIStateError(
                    message=str(
                        exc
                    ),
                )
            ) from exc

    @staticmethod
    def get_transaction(
        *,
        organization,
        transaction_id,
    ):
        return (
            BankTransactionAPIService
            ._get_transaction(
                organization=organization,
                transaction_id=transaction_id,
            )
        )

    @staticmethod
    def reconcile_transaction(
        *,
        user,
        organization,
        transaction_id,
    ):
        transaction = (
            BankTransactionAPIService
            ._get_transaction(
                organization=organization,
                transaction_id=transaction_id,
            )
        )

        try:
            return (
                BankTransactionService
                .reconcile_transaction(
                    user=user,
                    organization=organization,
                    transaction=transaction,
                )
            )

        except PermissionError:
            raise

        except ValueError as exc:
            raise (
                BankTransactionAPIStateError(
                    message=str(
                        exc
                    ),
                )
            ) from exc