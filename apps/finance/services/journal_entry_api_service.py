from decimal import (
    Decimal,
    InvalidOperation,
)

from bson import (
    ObjectId,
)

from apps.finance.repositories.journal_entry_repository import (
    JournalEntryRepository,
)
from apps.finance.services.journal_entry_service import (
    JournalEntryService,
)


class JournalEntryAPIValidationError(
    ValueError
):

    def __init__(
        self,
        *,
        message=(
            "Journal entry validation failed."
        ),
        details=None,
    ):
        super().__init__(
            message
        )

        self.message = message
        self.details = details or {}


class JournalEntryAPIStateError(
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


class JournalEntryAPIService:

    CREATE_FIELDS = {
        "journal_date",
        "description",
        "lines",
    }

    UPDATE_FIELDS = {
        "journal_date",
        "description",
        "lines",
    }

    REVERSAL_FIELDS = {
        "reversal_date",
        "description",
    }

    LINE_FIELDS = {
        "account_id",
        "description",
        "debit",
        "credit",
    }

    @staticmethod
    def _raise_field_error(
        field,
        message,
    ):
        raise JournalEntryAPIValidationError(
            details={
                field: [
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
            raise JournalEntryAPIValidationError(
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

        if unknown_fields:
            raise JournalEntryAPIValidationError(
                details={
                    field: [
                        (
                            "This field is not "
                            "supported."
                        ),
                    ]
                    for field
                    in sorted(
                        unknown_fields
                    )
                },
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
                JournalEntryAPIService
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
        maximum_length=None,
    ):
        if not isinstance(
            value,
            str,
        ):
            (
                JournalEntryAPIService
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
                JournalEntryAPIService
                ._raise_field_error(
                    field,
                    "This field is required.",
                )
            )

        if (
            maximum_length is not None
            and
            len(
                normalized
            )
            >
            maximum_length
        ):
            (
                JournalEntryAPIService
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
        maximum_length=None,
    ):
        if value is None:
            return ""

        if not isinstance(
            value,
            str,
        ):
            (
                JournalEntryAPIService
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
            maximum_length is not None
            and
            len(
                normalized
            )
            >
            maximum_length
        ):
            (
                JournalEntryAPIService
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
    def _normalize_date(
        value,
        *,
        field,
        required=False,
    ):
        if value in (
            None,
            "",
        ):
            if required:
                (
                    JournalEntryAPIService
                    ._raise_field_error(
                        field,
                        "This field is required.",
                    )
                )

            return None

        if not isinstance(
            value,
            str,
        ):
            (
                JournalEntryAPIService
                ._raise_field_error(
                    field,
                    (
                        "This field must be an "
                        "ISO-8601 date or datetime."
                    ),
                )
            )

        normalized = value.strip()

        if not normalized:
            if required:
                (
                    JournalEntryAPIService
                    ._raise_field_error(
                        field,
                        "This field is required.",
                    )
                )

            return None

        return normalized

    @staticmethod
    def _normalize_amount(
        value,
        *,
        field,
    ):
        if isinstance(
            value,
            bool,
        ):
            (
                JournalEntryAPIService
                ._raise_field_error(
                    field,
                    (
                        "This field must contain "
                        "a valid amount."
                    ),
                )
            )

        if value in (
            None,
            "",
        ):
            return Decimal(
                "0.00"
            )

        try:
            amount = Decimal(
                str(
                    value
                ).strip()
            )

        except (
            InvalidOperation,
            TypeError,
            ValueError,
        ):
            (
                JournalEntryAPIService
                ._raise_field_error(
                    field,
                    (
                        "This field must contain "
                        "a valid amount."
                    ),
                )
            )

        if not amount.is_finite():
            (
                JournalEntryAPIService
                ._raise_field_error(
                    field,
                    (
                        "This field must contain "
                        "a finite amount."
                    ),
                )
            )

        if amount < Decimal(
            "0"
        ):
            (
                JournalEntryAPIService
                ._raise_field_error(
                    field,
                    (
                        "This field cannot "
                        "be negative."
                    ),
                )
            )

        try:
            return amount.quantize(
                Decimal(
                    "0.01"
                )
            )

        except InvalidOperation:
            (
                JournalEntryAPIService
                ._raise_field_error(
                    field,
                    (
                        "This field contains "
                        "an invalid amount."
                    ),
                )
            )

    @staticmethod
    def _normalize_lines(
        value,
    ):
        if not isinstance(
            value,
            list,
        ):
            (
                JournalEntryAPIService
                ._raise_field_error(
                    "lines",
                    (
                        "This field must be "
                        "a list."
                    ),
                )
            )

        if len(
            value
        ) < 2:
            (
                JournalEntryAPIService
                ._raise_field_error(
                    "lines",
                    (
                        "At least two journal "
                        "lines are required."
                    ),
                )
            )

        normalized_lines = []
        line_errors = {}

        for index, line in enumerate(
            value
        ):
            prefix = (
                f"lines.{index}"
            )

            if not isinstance(
                line,
                dict,
            ):
                line_errors[
                    prefix
                ] = [
                    (
                        "Each journal line must "
                        "be an object."
                    ),
                ]
                continue

            unknown_fields = (
                set(
                    line.keys()
                )
                -
                JournalEntryAPIService
                .LINE_FIELDS
            )

            if unknown_fields:
                for field in sorted(
                    unknown_fields
                ):
                    line_errors[
                        f"{prefix}.{field}"
                    ] = [
                        (
                            "This field is not "
                            "supported."
                        ),
                    ]

                continue

            account_id = line.get(
                "account_id"
            )

            if (
                not isinstance(
                    account_id,
                    str,
                )
                or
                not ObjectId.is_valid(
                    account_id.strip()
                )
            ):
                line_errors[
                    f"{prefix}.account_id"
                ] = [
                    (
                        "This field must contain "
                        "a valid ObjectId."
                    ),
                ]
                continue

            description = line.get(
                "description",
                "",
            )

            if (
                description is not None
                and
                not isinstance(
                    description,
                    str,
                )
            ):
                line_errors[
                    f"{prefix}.description"
                ] = [
                    (
                        "This field must be "
                        "a string."
                    ),
                ]
                continue

            description = str(
                description
                or
                ""
            ).strip()

            if len(
                description
            ) > 500:
                line_errors[
                    f"{prefix}.description"
                ] = [
                    (
                        "This field must not exceed "
                        "500 characters."
                    ),
                ]
                continue

            try:
                debit = (
                    JournalEntryAPIService
                    ._normalize_amount(
                        line.get(
                            "debit",
                            "0",
                        ),
                        field=(
                            f"{prefix}.debit"
                        ),
                    )
                )

                credit = (
                    JournalEntryAPIService
                    ._normalize_amount(
                        line.get(
                            "credit",
                            "0",
                        ),
                        field=(
                            f"{prefix}.credit"
                        ),
                    )
                )

            except (
                JournalEntryAPIValidationError
            ) as exc:
                line_errors.update(
                    exc.details
                )
                continue

            if (
                debit > Decimal(
                    "0"
                )
                and
                credit > Decimal(
                    "0"
                )
            ):
                line_errors[
                    prefix
                ] = [
                    (
                        "A journal line cannot "
                        "contain both debit and "
                        "credit amounts."
                    ),
                ]
                continue

            if (
                debit == Decimal(
                    "0"
                )
                and
                credit == Decimal(
                    "0"
                )
            ):
                line_errors[
                    prefix
                ] = [
                    (
                        "A journal line must contain "
                        "either a debit or credit "
                        "amount."
                    ),
                ]
                continue

            normalized_lines.append({
                "account_id":
                    account_id.strip(),
                "description":
                    description,
                "debit":
                    debit,
                "credit":
                    credit,
            })

        if line_errors:
            raise JournalEntryAPIValidationError(
                details=line_errors,
            )

        total_debit = sum(
            (
                line[
                    "debit"
                ]
                for line
                in normalized_lines
            ),
            Decimal(
                "0.00"
            ),
        )

        total_credit = sum(
            (
                line[
                    "credit"
                ]
                for line
                in normalized_lines
            ),
            Decimal(
                "0.00"
            ),
        )

        if total_debit <= Decimal(
            "0"
        ):
            (
                JournalEntryAPIService
                ._raise_field_error(
                    "lines",
                    (
                        "Journal total debit must "
                        "be greater than zero."
                    ),
                )
            )

        if total_credit <= Decimal(
            "0"
        ):
            (
                JournalEntryAPIService
                ._raise_field_error(
                    "lines",
                    (
                        "Journal total credit must "
                        "be greater than zero."
                    ),
                )
            )

        if total_debit != total_credit:
            (
                JournalEntryAPIService
                ._raise_field_error(
                    "lines",
                    (
                        "Journal debit and credit "
                        "totals must be equal."
                    ),
                )
            )

        return normalized_lines

    @staticmethod
    def validate_create_payload(
        payload,
    ):
        (
            JournalEntryAPIService
            ._validate_payload_object(
                payload
            )
        )

        (
            JournalEntryAPIService
            ._validate_allowed_fields(
                payload,
                allowed_fields=(
                    JournalEntryAPIService
                    .CREATE_FIELDS
                ),
            )
        )

        missing_fields = [
            field
            for field
            in (
                "journal_date",
                "lines",
            )
            if field not in payload
        ]

        if missing_fields:
            raise JournalEntryAPIValidationError(
                details={
                    field: [
                        "This field is required.",
                    ]
                    for field
                    in missing_fields
                },
            )

        return {
            "journal_date": (
                JournalEntryAPIService
                ._normalize_date(
                    payload.get(
                        "journal_date"
                    ),
                    field="journal_date",
                    required=True,
                )
            ),
            "description": (
                JournalEntryAPIService
                ._normalize_optional_text(
                    payload.get(
                        "description",
                        "",
                    ),
                    field="description",
                    maximum_length=500,
                )
            ),
            "raw_lines": (
                JournalEntryAPIService
                ._normalize_lines(
                    payload.get(
                        "lines"
                    )
                )
            ),
            "source_type":
                "MANUAL",
            "source_id":
                "",
        }

    @staticmethod
    def validate_update_payload(
        payload,
    ):
        (
            JournalEntryAPIService
            ._validate_payload_object(
                payload
            )
        )

        (
            JournalEntryAPIService
            ._validate_allowed_fields(
                payload,
                allowed_fields=(
                    JournalEntryAPIService
                    .UPDATE_FIELDS
                ),
            )
        )

        if not payload:
            raise JournalEntryAPIValidationError(
                details={
                    "body": [
                        (
                            "Provide at least one "
                            "editable field."
                        ),
                    ],
                },
            )

        values = {}

        if "journal_date" in payload:
            values[
                "journal_date"
            ] = (
                JournalEntryAPIService
                ._normalize_date(
                    payload[
                        "journal_date"
                    ],
                    field="journal_date",
                    required=True,
                )
            )

        if "description" in payload:
            values[
                "description"
            ] = (
                JournalEntryAPIService
                ._normalize_optional_text(
                    payload[
                        "description"
                    ],
                    field="description",
                    maximum_length=500,
                )
            )

        if "lines" in payload:
            values[
                "raw_lines"
            ] = (
                JournalEntryAPIService
                ._normalize_lines(
                    payload[
                        "lines"
                    ]
                )
            )

        return values

    @staticmethod
    def validate_reversal_payload(
        payload,
    ):
        (
            JournalEntryAPIService
            ._validate_payload_object(
                payload
            )
        )

        (
            JournalEntryAPIService
            ._validate_allowed_fields(
                payload,
                allowed_fields=(
                    JournalEntryAPIService
                    .REVERSAL_FIELDS
                ),
            )
        )

        values = {
            "reversal_date":
                None,
            "description":
                "",
        }

        if "reversal_date" in payload:
            values[
                "reversal_date"
            ] = (
                JournalEntryAPIService
                ._normalize_date(
                    payload[
                        "reversal_date"
                    ],
                    field="reversal_date",
                )
            )

        if "description" in payload:
            values[
                "description"
            ] = (
                JournalEntryAPIService
                ._normalize_optional_text(
                    payload[
                        "description"
                    ],
                    field="description",
                    maximum_length=500,
                )
            )

        return values

    @staticmethod
    def get_journal(
        *,
        organization,
        journal_id,
    ):
        normalized_id = (
            JournalEntryAPIService
            ._normalize_identifier(
                journal_id,
                field="journal_id",
            )
        )

        journal = (
            JournalEntryRepository
            .get_by_id(
                organization=organization,
                journal_id=normalized_id,
            )
        )

        if not journal:
            raise LookupError(
                "Journal entry not found."
            )

        return journal

    @staticmethod
    def create_journal(
        *,
        user,
        organization,
        payload,
    ):
        values = (
            JournalEntryAPIService
            .validate_create_payload(
                payload
            )
        )

        try:
            return (
                JournalEntryService
                .create_journal(
                    user=user,
                    organization=organization,
                    **values,
                )
            )

        except PermissionError:
            raise

        except ValueError as exc:
            raise JournalEntryAPIStateError(
                message=str(
                    exc
                ),
                details={
                    "journal": [
                        str(
                            exc
                        ),
                    ],
                },
            ) from exc

    @staticmethod
    def update_journal(
        *,
        user,
        organization,
        journal_id,
        payload,
    ):
        journal = (
            JournalEntryAPIService
            .get_journal(
                organization=organization,
                journal_id=journal_id,
            )
        )

        values = (
            JournalEntryAPIService
            .validate_update_payload(
                payload
            )
        )

        try:
            return (
                JournalEntryService
                .update_draft(
                    user=user,
                    organization=organization,
                    journal_id=str(
                        journal.id
                    ),
                    **values,
                )
            )

        except PermissionError:
            raise

        except ValueError as exc:
            raise JournalEntryAPIStateError(
                message=str(
                    exc
                ),
                details={
                    "journal": [
                        str(
                            exc
                        ),
                    ],
                },
            ) from exc

    @staticmethod
    def post_journal(
        *,
        user,
        organization,
        journal_id,
    ):
        journal = (
            JournalEntryAPIService
            .get_journal(
                organization=organization,
                journal_id=journal_id,
            )
        )

        try:
            return (
                JournalEntryService
                .post_journal(
                    user=user,
                    organization=organization,
                    journal_id=str(
                        journal.id
                    ),
                )
            )

        except PermissionError:
            raise

        except ValueError as exc:
            raise JournalEntryAPIStateError(
                message=str(
                    exc
                ),
                details={
                    "journal": [
                        str(
                            exc
                        ),
                    ],
                },
            ) from exc

    @staticmethod
    def reverse_journal(
        *,
        user,
        organization,
        journal_id,
        payload,
    ):
        journal = (
            JournalEntryAPIService
            .get_journal(
                organization=organization,
                journal_id=journal_id,
            )
        )

        values = (
            JournalEntryAPIService
            .validate_reversal_payload(
                payload
            )
        )

        try:
            return (
                JournalEntryService
                .reverse_journal(
                    user=user,
                    organization=organization,
                    journal_id=str(
                        journal.id
                    ),
                    **values,
                )
            )

        except PermissionError:
            raise

        except ValueError as exc:
            raise JournalEntryAPIStateError(
                message=str(
                    exc
                ),
                details={
                    "journal": [
                        str(
                            exc
                        ),
                    ],
                },
            ) from exc