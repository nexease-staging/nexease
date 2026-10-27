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
from apps.finance.repositories.bank_transfer_repository import (
    BankTransferRepository,
)
from apps.finance.services.bank_transfer_service import (
    BankTransferService,
)


class BankTransferAPIValidationError(
    ValueError
):

    def __init__(
        self,
        *,
        message=(
            "Bank transfer validation failed."
        ),
        details=None,
    ):
        super().__init__(
            message
        )

        self.message = message
        self.details = details or {}


class BankTransferAPIStateError(
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


class BankTransferAPIService:

    CREATE_FIELDS = {
        "source_account_id",
        "destination_account_id",
        "transfer_date",
        "amount",
        "reference",
        "notes",
    }

    @staticmethod
    def _raise_field_error(
        field,
        message,
    ):
        raise (
            BankTransferAPIValidationError(
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
                BankTransferAPIValidationError(
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
                BankTransferAPIValidationError(
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
                BankTransferAPIService
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
                BankTransferAPIService
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
                BankTransferAPIService
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
                BankTransferAPIService
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
                BankTransferAPIService
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
                BankTransferAPIService
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
                BankTransferAPIService
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
                BankTransferAPIService
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
                BankTransferAPIService
                ._raise_field_error(
                    field,
                    "This field is required.",
                )
            )

        try:
            if len(
                normalized
            ) == 10:
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
                BankTransferAPIService
                ._raise_field_error(
                    field,
                    (
                        "Use an ISO-8601 date "
                        "or datetime."
                    ),
                )
            )

    @staticmethod
    def validate_create_payload(
        payload,
    ):
        (
            BankTransferAPIService
            ._validate_payload_object(
                payload
            )
        )

        (
            BankTransferAPIService
            ._validate_allowed_fields(
                payload,
                allowed_fields=(
                    BankTransferAPIService
                    .CREATE_FIELDS
                ),
            )
        )

        missing_fields = [
            field
            for field
            in (
                "source_account_id",
                "destination_account_id",
                "transfer_date",
                "amount",
            )
            if field not in payload
        ]

        if missing_fields:
            raise (
                BankTransferAPIValidationError(
                    details={
                        field: [
                            "This field is required.",
                        ]
                        for field
                        in missing_fields
                    },
                )
            )

        source_account_id = (
            BankTransferAPIService
            ._normalize_identifier(
                payload.get(
                    "source_account_id"
                ),
                field="source_account_id",
            )
        )

        destination_account_id = (
            BankTransferAPIService
            ._normalize_identifier(
                payload.get(
                    "destination_account_id"
                ),
                field="destination_account_id",
            )
        )

        if (
            source_account_id
            ==
            destination_account_id
        ):
            raise (
                BankTransferAPIValidationError(
                    details={
                        "destination_account_id": [
                            (
                                "Destination account "
                                "must be different "
                                "from source account."
                            ),
                        ],
                    },
                )
            )

        return {
            "source_account_id":
                source_account_id,
            "destination_account_id":
                destination_account_id,
            "transfer_date": (
                BankTransferAPIService
                ._normalize_datetime(
                    payload.get(
                        "transfer_date"
                    ),
                    field="transfer_date",
                )
            ),
            "amount": (
                BankTransferAPIService
                ._normalize_decimal(
                    payload.get(
                        "amount"
                    ),
                    field="amount",
                )
            ),
            "reference": (
                BankTransferAPIService
                ._normalize_optional_text(
                    payload.get(
                        "reference",
                        "",
                    ),
                    field="reference",
                    maximum_length=150,
                )
            ),
            "notes": (
                BankTransferAPIService
                ._normalize_optional_text(
                    payload.get(
                        "notes",
                        "",
                    ),
                    field="notes",
                    maximum_length=1000,
                )
            ),
        }

    @staticmethod
    def _get_transfer(
        *,
        organization,
        transfer_id,
    ):
        normalized_id = (
            BankTransferAPIService
            ._normalize_identifier(
                transfer_id,
                field="transfer_id",
            )
        )

        transfer = (
            BankTransferRepository
            .get_by_id(
                organization=organization,
                transfer_id=normalized_id,
            )
        )

        if not transfer:
            raise LookupError(
                "Bank transfer not found."
            )

        return transfer

    @staticmethod
    def create_transfer(
        *,
        user,
        organization,
        payload,
    ):
        values = (
            BankTransferAPIService
            .validate_create_payload(
                payload
            )
        )

        source_account = (
            BankAccountRepository
            .get_by_id(
                organization=organization,
                bank_account_id=(
                    values.pop(
                        "source_account_id"
                    )
                ),
            )
        )

        if not source_account:
            raise (
                BankTransferAPIValidationError(
                    details={
                        "source_account_id": [
                            (
                                "Select a valid source "
                                "bank account."
                            ),
                        ],
                    },
                )
            )

        destination_account = (
            BankAccountRepository
            .get_by_id(
                organization=organization,
                bank_account_id=(
                    values.pop(
                        "destination_account_id"
                    )
                ),
            )
        )

        if not destination_account:
            raise (
                BankTransferAPIValidationError(
                    details={
                        "destination_account_id": [
                            (
                                "Select a valid "
                                "destination bank "
                                "account."
                            ),
                        ],
                    },
                )
            )

        try:
            return (
                BankTransferService
                .create_transfer(
                    user=user,
                    organization=organization,
                    source_account=source_account,
                    destination_account=(
                        destination_account
                    ),
                    **values,
                )
            )

        except PermissionError:
            raise

        except ValueError as exc:
            raise (
                BankTransferAPIStateError(
                    message=str(
                        exc
                    ),
                )
            ) from exc

    @staticmethod
    def get_transfer(
        *,
        organization,
        transfer_id,
    ):
        return (
            BankTransferAPIService
            ._get_transfer(
                organization=organization,
                transfer_id=transfer_id,
            )
        )

    @staticmethod
    def post_transfer(
        *,
        user,
        organization,
        transfer_id,
    ):
        transfer = (
            BankTransferAPIService
            ._get_transfer(
                organization=organization,
                transfer_id=transfer_id,
            )
        )

        try:
            return (
                BankTransferService
                .post_transfer(
                    user=user,
                    organization=organization,
                    transfer=transfer,
                )
            )

        except PermissionError:
            raise

        except ValueError as exc:
            raise (
                BankTransferAPIStateError(
                    message=str(
                        exc
                    ),
                )
            ) from exc

    @staticmethod
    def cancel_transfer(
        *,
        user,
        organization,
        transfer_id,
    ):
        transfer = (
            BankTransferAPIService
            ._get_transfer(
                organization=organization,
                transfer_id=transfer_id,
            )
        )

        try:
            return (
                BankTransferService
                .cancel_transfer(
                    user=user,
                    organization=organization,
                    transfer=transfer,
                )
            )

        except PermissionError:
            raise

        except ValueError as exc:
            raise (
                BankTransferAPIStateError(
                    message=str(
                        exc
                    ),
                )
            ) from exc