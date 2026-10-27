from datetime import (
    datetime,
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
from apps.sales.repositories.invoice_repository import (
    InvoiceRepository,
)
from apps.sales.repositories.sales_order_repository import (
    SalesOrderRepository,
)
from apps.sales.services.invoice_service import (
    InvoiceService,
)
from apps.sales.services.payment_service import (
    PaymentService,
)


class InvoiceAPIValidationError(
    ValueError
):

    def __init__(
        self,
        *,
        message="Invoice validation failed.",
        details=None,
    ):
        super().__init__(
            message
        )

        self.message = message
        self.details = details or {}


class InvoiceAPIStateError(
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


class InvoiceAPIService:

    CREATE_FIELDS = {
        "sales_order_id",
        "invoice_date",
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
        "UPI",
        "CHEQUE",
        "CARD",
        "OTHER",
    }

    @staticmethod
    def _raise_field_error(
        field,
        message,
    ):
        raise InvoiceAPIValidationError(
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
            raise InvoiceAPIValidationError(
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
            raise InvoiceAPIValidationError(
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
            InvoiceAPIService._raise_field_error(
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
        required=False,
    ):
        if value in (
            None,
            "",
        ):
            if required:
                InvoiceAPIService._raise_field_error(
                    field,
                    "This field is required.",
                )

            return None

        if not isinstance(
            value,
            str,
        ):
            InvoiceAPIService._raise_field_error(
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

        except ValueError as exc:
            raise InvoiceAPIValidationError(
                details={
                    field: [
                        (
                            "Enter a valid ISO-8601 "
                            "date or datetime."
                        ),
                    ],
                },
            ) from exc

    @staticmethod
    def _normalize_decimal(
        value,
        *,
        field,
        positive=False,
    ):
        if isinstance(
            value,
            bool,
        ):
            InvoiceAPIService._raise_field_error(
                field,
                "Enter a valid number.",
            )

        try:
            decimal_value = Decimal(
                str(
                    value
                )
            )

        except (
            InvalidOperation,
            TypeError,
            ValueError,
        ) as exc:
            raise InvoiceAPIValidationError(
                details={
                    field: [
                        "Enter a valid number.",
                    ],
                },
            ) from exc

        if not decimal_value.is_finite():
            InvoiceAPIService._raise_field_error(
                field,
                "Enter a finite number.",
            )

        if (
            decimal_value
            .as_tuple()
            .exponent
            <
            -2
        ):
            InvoiceAPIService._raise_field_error(
                field,
                (
                    "This value cannot have more "
                    "than two decimal places."
                ),
            )

        if (
            positive
            and
            decimal_value <= 0
        ):
            InvoiceAPIService._raise_field_error(
                field,
                (
                    "This value must be greater "
                    "than zero."
                ),
            )

        return decimal_value

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
            InvoiceAPIService._raise_field_error(
                field,
                (
                    "This field must be a "
                    "string or null."
                ),
            )

        value = value.strip()

        if len(value) > maximum_length:
            InvoiceAPIService._raise_field_error(
                field,
                (
                    f"This field cannot exceed "
                    f"{maximum_length} characters."
                ),
            )

        return value

    @staticmethod
    def _resolve_sales_order(
        *,
        organization,
        sales_order_id,
    ):
        normalized_id = (
            InvoiceAPIService
            ._normalize_identifier(
                sales_order_id,
                field="sales_order_id",
            )
        )

        sales_order = (
            SalesOrderRepository
            .get_by_id(
                organization=organization,
                sales_order_id=normalized_id,
            )
        )

        if not sales_order:
            InvoiceAPIService._raise_field_error(
                "sales_order_id",
                (
                    "The selected Sales Order "
                    "does not exist."
                ),
            )

        return sales_order

    @staticmethod
    def _resolve_bank_account(
        *,
        organization,
        bank_account_id,
    ):
        normalized_id = (
            InvoiceAPIService
            ._normalize_identifier(
                bank_account_id,
                field="bank_account_id",
            )
        )

        bank_account = (
            BankAccountRepository
            .get_by_id(
                organization=organization,
                bank_account_id=normalized_id,
            )
        )

        if not bank_account:
            InvoiceAPIService._raise_field_error(
                "bank_account_id",
                (
                    "The selected bank account "
                    "does not exist."
                ),
            )

        if not bank_account.is_active:
            InvoiceAPIService._raise_field_error(
                "bank_account_id",
                (
                    "The selected bank account "
                    "is inactive."
                ),
            )

        return bank_account

    @staticmethod
    def get_invoice(
        *,
        organization,
        invoice_id,
    ):
        normalized_id = (
            InvoiceAPIService
            ._normalize_identifier(
                invoice_id,
                field="invoice_id",
            )
        )

        invoice = (
            InvoiceRepository
            .get_by_id(
                organization=organization,
                invoice_id=normalized_id,
            )
        )

        if not invoice:
            raise LookupError(
                "Invoice not found."
            )

        return invoice

    @staticmethod
    def validate_create_payload(
        *,
        organization,
        payload,
    ):
        InvoiceAPIService._validate_payload_object(
            payload
        )

        InvoiceAPIService._validate_allowed_fields(
            payload,
            allowed_fields=(
                InvoiceAPIService
                .CREATE_FIELDS
            ),
        )

        if "sales_order_id" not in payload:
            InvoiceAPIService._raise_field_error(
                "sales_order_id",
                "This field is required.",
            )

        sales_order = (
            InvoiceAPIService
            ._resolve_sales_order(
                organization=organization,
                sales_order_id=payload.get(
                    "sales_order_id"
                ),
            )
        )

        invoice_date = (
            InvoiceAPIService
            ._normalize_datetime(
                payload.get(
                    "invoice_date"
                ),
                field="invoice_date",
            )
        )

        due_date = (
            InvoiceAPIService
            ._normalize_datetime(
                payload.get(
                    "due_date"
                ),
                field="due_date",
            )
        )

        if (
            invoice_date
            and
            due_date
            and
            due_date < invoice_date
        ):
            InvoiceAPIService._raise_field_error(
                "due_date",
                (
                    "Due date cannot be "
                    "before invoice date."
                ),
            )

        return {
            "sales_order":
                sales_order,
            "invoice_date":
                invoice_date,
            "due_date":
                due_date,
            "notes": (
                InvoiceAPIService
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
    def validate_payment_payload(
        *,
        organization,
        payload,
    ):
        InvoiceAPIService._validate_payload_object(
            payload
        )

        InvoiceAPIService._validate_allowed_fields(
            payload,
            allowed_fields=(
                InvoiceAPIService
                .PAYMENT_FIELDS
            ),
        )

        required_fields = {
            "amount",
            "payment_method",
            "bank_account_id",
        }

        missing_fields = (
            required_fields
            -
            set(
                payload.keys()
            )
        )

        if missing_fields:
            raise InvoiceAPIValidationError(
                details={
                    field: [
                        "This field is required.",
                    ]
                    for field
                    in sorted(
                        missing_fields
                    )
                },
            )

        payment_method = payload.get(
            "payment_method"
        )

        if not isinstance(
            payment_method,
            str,
        ):
            InvoiceAPIService._raise_field_error(
                "payment_method",
                (
                    "Payment method must "
                    "be a string."
                ),
            )

        payment_method = (
            payment_method
            .strip()
            .upper()
        )

        if payment_method not in (
            InvoiceAPIService
            .PAYMENT_METHODS
        ):
            InvoiceAPIService._raise_field_error(
                "payment_method",
                (
                    "Select a valid payment "
                    "method."
                ),
            )

        return {
            "amount": (
                InvoiceAPIService
                ._normalize_decimal(
                    payload.get(
                        "amount"
                    ),
                    field="amount",
                    positive=True,
                )
            ),
            "payment_method":
                payment_method,
            "bank_account": (
                InvoiceAPIService
                ._resolve_bank_account(
                    organization=organization,
                    bank_account_id=payload.get(
                        "bank_account_id"
                    ),
                )
            ),
            "payment_date": (
                InvoiceAPIService
                ._normalize_datetime(
                    payload.get(
                        "payment_date"
                    ),
                    field="payment_date",
                )
            ),
            "reference_number": (
                InvoiceAPIService
                ._normalize_optional_text(
                    payload.get(
                        "reference_number",
                        "",
                    ),
                    field="reference_number",
                    maximum_length=100,
                )
            ),
            "notes": (
                InvoiceAPIService
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
    def list_active_bank_accounts(
        *,
        organization,
    ):
        if not organization:
            raise PermissionError(
                (
                    "Organization context "
                    "is unavailable."
                )
            )

        return (
            BankAccountRepository
            .list_by_organization(
                organization=organization,
                is_active=True,
            )
        )

    @staticmethod
    def create_invoice(
        *,
        user,
        organization,
        payload,
    ):
        values = (
            InvoiceAPIService
            .validate_create_payload(
                organization=organization,
                payload=payload,
            )
        )

        try:
            return (
                InvoiceService
                .generate_from_sales_order(
                    user=user,
                    organization=organization,
                    **values,
                )
            )

        except PermissionError:
            raise

        except ValueError as exc:
            raise InvoiceAPIStateError(
                message=str(
                    exc
                ),
                details={
                    "invoice": [
                        str(
                            exc
                        ),
                    ],
                },
            ) from exc

    @staticmethod
    def issue_invoice(
        *,
        user,
        organization,
        invoice_id,
    ):
        InvoiceAPIService.get_invoice(
            organization=organization,
            invoice_id=invoice_id,
        )

        try:
            return (
                InvoiceService
                .issue_invoice(
                    user=user,
                    organization=organization,
                    invoice_id=invoice_id,
                )
            )

        except PermissionError:
            raise

        except ValueError as exc:
            raise InvoiceAPIStateError(
                message=str(
                    exc
                ),
                details={
                    "invoice": [
                        str(
                            exc
                        ),
                    ],
                },
            ) from exc

    @staticmethod
    def cancel_invoice(
        *,
        user,
        organization,
        invoice_id,
    ):
        InvoiceAPIService.get_invoice(
            organization=organization,
            invoice_id=invoice_id,
        )

        try:
            return (
                InvoiceService
                .cancel_invoice(
                    user=user,
                    organization=organization,
                    invoice_id=invoice_id,
                )
            )

        except PermissionError:
            raise

        except ValueError as exc:
            raise InvoiceAPIStateError(
                message=str(
                    exc
                ),
                details={
                    "invoice": [
                        str(
                            exc
                        ),
                    ],
                },
            ) from exc

    @staticmethod
    def record_payment(
        *,
        user,
        organization,
        invoice_id,
        payload,
    ):
        invoice = (
            InvoiceAPIService
            .get_invoice(
                organization=organization,
                invoice_id=invoice_id,
            )
        )

        values = (
            InvoiceAPIService
            .validate_payment_payload(
                organization=organization,
                payload=payload,
            )
        )

        try:
            payment = (
                PaymentService
                .record_invoice_payment(
                    user=user,
                    organization=organization,
                    invoice=invoice,
                    **values,
                )
            )

        except PermissionError:
            raise

        except ValueError as exc:
            raise InvoiceAPIStateError(
                message=str(
                    exc
                ),
                details={
                    "payment": [
                        str(
                            exc
                        ),
                    ],
                },
            ) from exc

        return {
            "invoice":
                invoice,
            "payment":
                payment,
        }