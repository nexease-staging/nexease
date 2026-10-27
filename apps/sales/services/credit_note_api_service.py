from datetime import (
    datetime,
)

from bson import (
    ObjectId,
)

from apps.sales.repositories.credit_note_repository import (
    CreditNoteRepository,
)
from apps.sales.repositories.sales_return_repository import (
    SalesReturnRepository,
)
from apps.sales.services.credit_note_service import (
    CreditNoteService,
)


class CreditNoteAPIValidationError(
    ValueError
):

    def __init__(
        self,
        *,
        message="Credit note validation failed.",
        details=None,
    ):
        super().__init__(
            message
        )

        self.message = message
        self.details = details or {}


class CreditNoteAPIStateError(
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


class CreditNoteAPIService:

    CREATE_FIELDS = {
        "sales_return_id",
        "credit_note_date",
        "reason",
        "notes",
    }

    @staticmethod
    def _raise_field_error(
        field,
        message,
    ):
        raise CreditNoteAPIValidationError(
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
            raise CreditNoteAPIValidationError(
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
    ):
        unknown_fields = (
            set(
                payload.keys()
            )
            -
            CreditNoteAPIService
            .CREATE_FIELDS
        )

        if unknown_fields:
            raise CreditNoteAPIValidationError(
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
            CreditNoteAPIService._raise_field_error(
                field,
                (
                    "This field must contain a "
                    "valid ObjectId."
                ),
            )

        return value.strip()

    @staticmethod
    def _normalize_datetime(
        value,
        *,
        field,
    ):
        if value in (
            None,
            "",
        ):
            return None

        if not isinstance(
            value,
            str,
        ):
            CreditNoteAPIService._raise_field_error(
                field,
                (
                    "This field must be an "
                    "ISO-8601 date or datetime."
                ),
            )

        normalized = value.strip()

        if normalized.endswith(
            "Z"
        ):
            normalized = (
                normalized[:-1]
                +
                "+00:00"
            )

        try:
            return datetime.fromisoformat(
                normalized
            )

        except ValueError:
            CreditNoteAPIService._raise_field_error(
                field,
                (
                    "Enter a valid ISO-8601 "
                    "date or datetime."
                ),
            )

    @staticmethod
    def _normalize_text(
        value,
        *,
        field,
        maximum_length,
    ):
        if value in (
            None,
            "",
        ):
            return ""

        if not isinstance(
            value,
            str,
        ):
            CreditNoteAPIService._raise_field_error(
                field,
                "This field must be text.",
            )

        normalized = value.strip()

        if (
            len(
                normalized
            )
            >
            maximum_length
        ):
            CreditNoteAPIService._raise_field_error(
                field,
                (
                    "Ensure this field has no "
                    f"more than {maximum_length} "
                    "characters."
                ),
            )

        return normalized

    @staticmethod
    def validate_create_payload(
        *,
        organization,
        payload,
    ):
        CreditNoteAPIService._validate_payload_object(
            payload
        )

        CreditNoteAPIService._validate_allowed_fields(
            payload
        )

        sales_return_id = (
            CreditNoteAPIService
            ._normalize_identifier(
                payload.get(
                    "sales_return_id"
                ),
                field="sales_return_id",
            )
        )

        sales_return = (
            SalesReturnRepository
            .get_by_id(
                organization=organization,
                return_id=sales_return_id,
            )
        )

        if not sales_return:
            CreditNoteAPIService._raise_field_error(
                "sales_return_id",
                "Sales return was not found.",
            )

        return {
            "sales_return":
                sales_return,
            "credit_note_date": (
                CreditNoteAPIService
                ._normalize_datetime(
                    payload.get(
                        "credit_note_date"
                    ),
                    field="credit_note_date",
                )
            ),
            "reason": (
                CreditNoteAPIService
                ._normalize_text(
                    payload.get(
                        "reason"
                    ),
                    field="reason",
                    maximum_length=500,
                )
            ),
            "notes": (
                CreditNoteAPIService
                ._normalize_text(
                    payload.get(
                        "notes"
                    ),
                    field="notes",
                    maximum_length=1000,
                )
            ),
        }

    @staticmethod
    def get_credit_note(
        *,
        organization,
        credit_note_id,
    ):
        normalized_id = (
            CreditNoteAPIService
            ._normalize_identifier(
                credit_note_id,
                field="credit_note_id",
            )
        )

        credit_note = (
            CreditNoteRepository
            .get_by_id(
                organization=organization,
                credit_note_id=normalized_id,
            )
        )

        if not credit_note:
            raise LookupError(
                "Credit note not found."
            )

        return credit_note

    @staticmethod
    def create_credit_note(
        *,
        user,
        organization,
        payload,
    ):
        values = (
            CreditNoteAPIService
            .validate_create_payload(
                organization=organization,
                payload=payload,
            )
        )

        try:
            return (
                CreditNoteService
                .create_from_sales_return(
                    user=user,
                    organization=organization,
                    **values,
                )
            )

        except PermissionError:
            raise

        except ValueError as exc:
            raise CreditNoteAPIStateError(
                message=str(
                    exc
                ),
                details={
                    "credit_note": [
                        str(
                            exc
                        ),
                    ],
                },
            ) from exc

    @staticmethod
    def issue_credit_note(
        *,
        user,
        organization,
        credit_note_id,
    ):
        credit_note = (
            CreditNoteAPIService
            .get_credit_note(
                organization=organization,
                credit_note_id=credit_note_id,
            )
        )

        try:
            return (
                CreditNoteService
                .issue_credit_note(
                    user=user,
                    organization=organization,
                    credit_note=credit_note,
                )
            )

        except PermissionError:
            raise

        except ValueError as exc:
            raise CreditNoteAPIStateError(
                message=str(
                    exc
                ),
                details={
                    "credit_note": [
                        str(
                            exc
                        ),
                    ],
                },
            ) from exc

    @staticmethod
    def cancel_credit_note(
        *,
        user,
        organization,
        credit_note_id,
    ):
        credit_note = (
            CreditNoteAPIService
            .get_credit_note(
                organization=organization,
                credit_note_id=credit_note_id,
            )
        )

        try:
            return (
                CreditNoteService
                .cancel_credit_note(
                    user=user,
                    organization=organization,
                    credit_note=credit_note,
                )
            )

        except PermissionError:
            raise

        except ValueError as exc:
            raise CreditNoteAPIStateError(
                message=str(
                    exc
                ),
                details={
                    "credit_note": [
                        str(
                            exc
                        ),
                    ],
                },
            ) from exc