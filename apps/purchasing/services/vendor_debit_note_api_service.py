from datetime import datetime

from bson import ObjectId

from apps.purchasing.repositories.purchase_return_repository import (
    PurchaseReturnRepository,
)
from apps.purchasing.repositories.vendor_debit_note_repository import (
    VendorDebitNoteRepository,
)
from apps.purchasing.services.vendor_debit_note_service import (
    VendorDebitNoteService,
)


class VendorDebitNoteAPIValidationError(
    ValueError
):

    def __init__(
        self,
        *,
        message=(
            "Vendor debit note validation "
            "failed."
        ),
        details=None,
    ):
        super().__init__(message)

        self.message = message
        self.details = details or {}


class VendorDebitNoteAPIStateError(
    ValueError
):

    def __init__(
        self,
        *,
        message,
        details=None,
    ):
        super().__init__(message)

        self.message = message
        self.details = details or {}


class VendorDebitNoteAPIService:

    CREATE_FIELDS = {
        "purchase_return_id",
        "debit_note_date",
        "reason",
        "notes",
    }

    @staticmethod
    def _raise_field_error(
        field,
        message,
    ):
        raise (
            VendorDebitNoteAPIValidationError(
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
                VendorDebitNoteAPIValidationError(
                    details={
                        "body": [
                            (
                                "JSON body must be "
                                "an object."
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
                VendorDebitNoteAPIValidationError(
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
                VendorDebitNoteAPIService
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
            (
                VendorDebitNoteAPIService
                ._raise_field_error(
                    field,
                    (
                        "This field must be an "
                        "ISO-8601 date or datetime."
                    ),
                )
            )

        normalized = value.strip()

        if normalized.endswith("Z"):
            normalized = (
                normalized[:-1]
                +
                "+00:00"
            )

        try:
            parsed = datetime.fromisoformat(
                normalized
            )

        except ValueError:
            (
                VendorDebitNoteAPIService
                ._raise_field_error(
                    field,
                    (
                        "Enter a valid ISO-8601 "
                        "date or datetime."
                    ),
                )
            )

        if parsed.tzinfo is not None:
            parsed = parsed.replace(
                tzinfo=None,
            )

        return parsed

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
            (
                VendorDebitNoteAPIService
                ._raise_field_error(
                    field,
                    "This field must be a string.",
                )
            )

        normalized = value.strip()

        if (
            len(normalized)
            >
            maximum_length
        ):
            (
                VendorDebitNoteAPIService
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
    def validate_create_payload(
        *,
        organization,
        payload,
    ):
        (
            VendorDebitNoteAPIService
            ._validate_payload_object(
                payload
            )
        )

        (
            VendorDebitNoteAPIService
            ._validate_allowed_fields(
                payload,
                allowed_fields=(
                    VendorDebitNoteAPIService
                    .CREATE_FIELDS
                ),
            )
        )

        purchase_return_id = (
            VendorDebitNoteAPIService
            ._normalize_identifier(
                payload.get(
                    "purchase_return_id"
                ),
                field="purchase_return_id",
            )
        )

        purchase_return = (
            PurchaseReturnRepository
            .get_by_id(
                organization=organization,
                purchase_return_id=(
                    purchase_return_id
                ),
            )
        )

        if not purchase_return:
            (
                VendorDebitNoteAPIService
                ._raise_field_error(
                    "purchase_return_id",
                    (
                        "Purchase return was not "
                        "found in this organization."
                    ),
                )
            )

        if (
            purchase_return.status
            != "CONFIRMED"
        ):
            (
                VendorDebitNoteAPIService
                ._raise_field_error(
                    "purchase_return_id",
                    (
                        "Only confirmed purchase "
                        "returns can create vendor "
                        "debit notes."
                    ),
                )
            )

        existing = (
            VendorDebitNoteRepository
            .get_by_purchase_return(
                organization=organization,
                purchase_return=(
                    purchase_return
                ),
            )
        )

        if existing:
            (
                VendorDebitNoteAPIService
                ._raise_field_error(
                    "purchase_return_id",
                    (
                        "A vendor debit note already "
                        "exists for this purchase "
                        "return."
                    ),
                )
            )

        return {
            "purchase_return":
                purchase_return,
            "debit_note_date": (
                VendorDebitNoteAPIService
                ._normalize_datetime(
                    payload.get(
                        "debit_note_date"
                    ),
                    field="debit_note_date",
                )
            ),
            "reason": (
                VendorDebitNoteAPIService
                ._normalize_text(
                    payload.get(
                        "reason"
                    ),
                    field="reason",
                    maximum_length=500,
                )
            ),
            "notes": (
                VendorDebitNoteAPIService
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
    def get_debit_note(
        *,
        organization,
        debit_note_id,
    ):
        normalized_id = (
            VendorDebitNoteAPIService
            ._normalize_identifier(
                debit_note_id,
                field="debit_note_id",
            )
        )

        debit_note = (
            VendorDebitNoteRepository
            .get_by_id(
                organization=organization,
                debit_note_id=(
                    normalized_id
                ),
            )
        )

        if not debit_note:
            raise LookupError(
                "Vendor debit note not found."
            )

        return debit_note

    @staticmethod
    def create_debit_note(
        *,
        user,
        organization,
        payload,
    ):
        values = (
            VendorDebitNoteAPIService
            .validate_create_payload(
                organization=organization,
                payload=payload,
            )
        )

        try:
            return (
                VendorDebitNoteService
                .create_from_purchase_return(
                    user=user,
                    organization=organization,
                    **values,
                )
            )

        except PermissionError:
            raise

        except ValueError as exc:
            raise (
                VendorDebitNoteAPIStateError(
                    message=str(exc),
                    details={
                        "vendor_debit_note": [
                            str(exc),
                        ],
                    },
                )
            ) from exc

    @staticmethod
    def issue_debit_note(
        *,
        user,
        organization,
        debit_note_id,
    ):
        debit_note = (
            VendorDebitNoteAPIService
            .get_debit_note(
                organization=organization,
                debit_note_id=debit_note_id,
            )
        )

        try:
            return (
                VendorDebitNoteService
                .issue_debit_note(
                    user=user,
                    organization=organization,
                    debit_note=debit_note,
                )
            )

        except PermissionError:
            raise

        except ValueError as exc:
            raise (
                VendorDebitNoteAPIStateError(
                    message=str(exc),
                    details={
                        "vendor_debit_note": [
                            str(exc),
                        ],
                    },
                )
            ) from exc

    @staticmethod
    def cancel_debit_note(
        *,
        user,
        organization,
        debit_note_id,
    ):
        debit_note = (
            VendorDebitNoteAPIService
            .get_debit_note(
                organization=organization,
                debit_note_id=debit_note_id,
            )
        )

        try:
            return (
                VendorDebitNoteService
                .cancel_debit_note(
                    user=user,
                    organization=organization,
                    debit_note=debit_note,
                )
            )

        except PermissionError:
            raise

        except ValueError as exc:
            raise (
                VendorDebitNoteAPIStateError(
                    message=str(exc),
                    details={
                        "vendor_debit_note": [
                            str(exc),
                        ],
                    },
                )
            ) from exc