from datetime import datetime
from decimal import (
    Decimal,
    InvalidOperation,
)

from bson import ObjectId

from apps.finance.repositories.bank_account_repository import (
    BankAccountRepository,
)
from apps.purchasing.repositories.purchase_order_repository import (
    PurchaseOrderRepository,
)
from apps.purchasing.repositories.vendor_bill_repository import (
    VendorBillRepository,
)
from apps.purchasing.services.supplier_payment_service import (
    SupplierPaymentService,
)
from apps.purchasing.services.vendor_bill_service import (
    VendorBillService,
)


class VendorBillAPIValidationError(
    ValueError
):

    def __init__(
        self,
        *,
        message="Vendor bill validation failed.",
        details=None,
    ):
        super().__init__(message)

        self.message = message
        self.details = details or {}


class VendorBillAPIStateError(
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


class VendorBillAPIService:

    CREATE_FIELDS = {
        "purchase_order_id",
        "supplier_invoice_number",
        "bill_date",
        "due_date",
        "notes",
    }

    PAYMENT_FIELDS = {
        "amount",
        "payment_method",
        "bank_account_id",
        "payment_date",
        "reference_number",
        "notes",
    }

    PAYMENT_METHODS = {
        "CASH",
        "BANK_TRANSFER",
        "CHEQUE",
        "UPI",
        "CARD",
        "OTHER",
    }

    @staticmethod
    def _raise_field_error(
        field,
        message,
    ):
        raise VendorBillAPIValidationError(
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
            raise VendorBillAPIValidationError(
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
            raise VendorBillAPIValidationError(
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
                VendorBillAPIService
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
        required=False,
    ):
        if value in (
            None,
            "",
        ):
            if required:
                (
                    VendorBillAPIService
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
                VendorBillAPIService
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
                VendorBillAPIService
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
                VendorBillAPIService
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
                VendorBillAPIService
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
        try:
            amount = Decimal(
                str(value)
            )

        except (
            InvalidOperation,
            TypeError,
            ValueError,
        ):
            (
                VendorBillAPIService
                ._raise_field_error(
                    field,
                    "Enter a valid amount.",
                )
            )

        if amount <= 0:
            (
                VendorBillAPIService
                ._raise_field_error(
                    field,
                    (
                        "Amount must be greater "
                        "than zero."
                    ),
                )
            )

        return amount

    @staticmethod
    def validate_create_payload(
        *,
        organization,
        payload,
    ):
        (
            VendorBillAPIService
            ._validate_payload_object(
                payload
            )
        )

        (
            VendorBillAPIService
            ._validate_allowed_fields(
                payload,
                allowed_fields=(
                    VendorBillAPIService
                    .CREATE_FIELDS
                ),
            )
        )

        purchase_order_id = (
            VendorBillAPIService
            ._normalize_identifier(
                payload.get(
                    "purchase_order_id",
                ),
                field="purchase_order_id",
            )
        )

        purchase_order = (
            PurchaseOrderRepository
            .get_by_id(
                organization=organization,
                purchase_order_id=(
                    purchase_order_id
                ),
            )
        )

        if not purchase_order:
            raise LookupError(
                "Purchase order not found."
            )

        bill_date = (
            VendorBillAPIService
            ._normalize_datetime(
                payload.get(
                    "bill_date",
                ),
                field="bill_date",
                required=False,
            )
        )

        due_date = (
            VendorBillAPIService
            ._normalize_datetime(
                payload.get(
                    "due_date",
                ),
                field="due_date",
                required=False,
            )
        )

        if (
            bill_date
            and
            due_date
            and
            due_date < bill_date
        ):
            (
                VendorBillAPIService
                ._raise_field_error(
                    "due_date",
                    (
                        "Due date cannot be before "
                        "the bill date."
                    ),
                )
            )

        return {
            "purchase_order":
                purchase_order,
            "supplier_invoice_number": (
                VendorBillAPIService
                ._normalize_text(
                    payload.get(
                        "supplier_invoice_number",
                        "",
                    ),
                    field=(
                        "supplier_invoice_number"
                    ),
                    maximum_length=100,
                )
            ),
            "bill_date":
                bill_date,
            "due_date":
                due_date,
            "notes": (
                VendorBillAPIService
                ._normalize_text(
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
    def validate_payment_payload(
        *,
        organization,
        payload,
    ):
        (
            VendorBillAPIService
            ._validate_payload_object(
                payload
            )
        )

        (
            VendorBillAPIService
            ._validate_allowed_fields(
                payload,
                allowed_fields=(
                    VendorBillAPIService
                    .PAYMENT_FIELDS
                ),
            )
        )

        amount = (
            VendorBillAPIService
            ._normalize_decimal(
                payload.get("amount"),
                field="amount",
            )
        )

        payment_method = payload.get(
            "payment_method",
        )

        if not isinstance(
            payment_method,
            str,
        ):
            (
                VendorBillAPIService
                ._raise_field_error(
                    "payment_method",
                    "This field is required.",
                )
            )

        payment_method = (
            payment_method
            .strip()
            .upper()
        )

        if (
            payment_method
            not in
            VendorBillAPIService
            .PAYMENT_METHODS
        ):
            (
                VendorBillAPIService
                ._raise_field_error(
                    "payment_method",
                    (
                        "Unsupported payment "
                        "method."
                    ),
                )
            )

        bank_account_id = (
            VendorBillAPIService
            ._normalize_identifier(
                payload.get(
                    "bank_account_id",
                ),
                field="bank_account_id",
            )
        )

        bank_account = (
            BankAccountRepository
            .get_by_id(
                organization=organization,
                bank_account_id=(
                    bank_account_id
                ),
            )
        )

        if not bank_account:
            raise LookupError(
                "Bank account not found."
            )

        return {
            "amount":
                amount,
            "payment_method":
                payment_method,
            "bank_account":
                bank_account,
            "payment_date": (
                VendorBillAPIService
                ._normalize_datetime(
                    payload.get(
                        "payment_date",
                    ),
                    field="payment_date",
                    required=False,
                )
            ),
            "reference_number": (
                VendorBillAPIService
                ._normalize_text(
                    payload.get(
                        "reference_number",
                        "",
                    ),
                    field="reference_number",
                    maximum_length=100,
                )
            ),
            "notes": (
                VendorBillAPIService
                ._normalize_text(
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
    def create_vendor_bill(
        *,
        user,
        organization,
        payload,
    ):
        values = (
            VendorBillAPIService
            .validate_create_payload(
                organization=organization,
                payload=payload,
            )
        )

        try:
            return (
                VendorBillService
                .generate_from_purchase_order(
                    user=user,
                    organization=organization,
                    **values,
                )
            )

        except PermissionError:
            raise

        except ValueError as exc:
            raise VendorBillAPIStateError(
                message=str(exc),
                details={
                    "vendor_bill": [
                        str(exc),
                    ],
                },
            ) from exc

    @staticmethod
    def get_vendor_bill(
        *,
        organization,
        bill_id,
    ):
        normalized_id = (
            VendorBillAPIService
            ._normalize_identifier(
                bill_id,
                field="bill_id",
            )
        )

        bill = (
            VendorBillRepository
            .get_by_id(
                organization=organization,
                bill_id=normalized_id,
            )
        )

        if not bill:
            raise LookupError(
                "Vendor bill not found."
            )

        return bill

    @staticmethod
    def post_vendor_bill(
        *,
        user,
        organization,
        bill_id,
    ):
        bill = (
            VendorBillAPIService
            .get_vendor_bill(
                organization=organization,
                bill_id=bill_id,
            )
        )

        try:
            return (
                VendorBillService
                .post_bill(
                    user=user,
                    organization=organization,
                    bill=bill,
                )
            )

        except PermissionError:
            raise

        except ValueError as exc:
            raise VendorBillAPIStateError(
                message=str(exc),
                details={
                    "vendor_bill": [
                        str(exc),
                    ],
                },
            ) from exc

    @staticmethod
    def cancel_vendor_bill(
        *,
        user,
        organization,
        bill_id,
    ):
        bill = (
            VendorBillAPIService
            .get_vendor_bill(
                organization=organization,
                bill_id=bill_id,
            )
        )

        try:
            return (
                VendorBillService
                .cancel_bill(
                    user=user,
                    organization=organization,
                    bill=bill,
                )
            )

        except PermissionError:
            raise

        except ValueError as exc:
            raise VendorBillAPIStateError(
                message=str(exc),
                details={
                    "vendor_bill": [
                        str(exc),
                    ],
                },
            ) from exc

    @staticmethod
    def record_payment(
        *,
        user,
        organization,
        bill_id,
        payload,
    ):
        bill = (
            VendorBillAPIService
            .get_vendor_bill(
                organization=organization,
                bill_id=bill_id,
            )
        )

        values = (
            VendorBillAPIService
            .validate_payment_payload(
                organization=organization,
                payload=payload,
            )
        )

        try:
            payment = (
                SupplierPaymentService
                .record_bill_payment(
                    user=user,
                    organization=organization,
                    vendor_bill=bill,
                    **values,
                )
            )

        except PermissionError:
            raise

        except ValueError as exc:
            raise VendorBillAPIStateError(
                message=str(exc),
                details={
                    "payment": [
                        str(exc),
                    ],
                },
            ) from exc

        updated_bill = (
            VendorBillRepository
            .get_by_id(
                organization=organization,
                bill_id=bill.id,
            )
        )

        return {
            "vendor_bill":
                updated_bill,
            "payment":
                payment,
        }

    @staticmethod
    def list_active_bank_accounts(
        *,
        organization,
    ):
        return (
            BankAccountRepository
            .list_by_organization(
                organization=organization,
                is_active=True,
            )
        )

    @staticmethod
    def list_outstanding(
        *,
        organization,
    ):
        return (
            VendorBillRepository
            .list_outstanding(
                organization=organization,
            )
        )