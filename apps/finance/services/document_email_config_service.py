from apps.sales.repositories.invoice_repository import (
    InvoiceRepository,
)

from apps.sales.repositories.sales_order_repository import (
    SalesOrderRepository,
)

from apps.sales.repositories.credit_note_repository import (
    CreditNoteRepository,
)

from apps.sales.repositories.payment_repository import (
    PaymentRepository,
)

from apps.purchasing.repositories.purchase_order_repository import (
    PurchaseOrderRepository,
)

from apps.purchasing.repositories.vendor_bill_repository import (
    VendorBillRepository,
)

from apps.purchasing.repositories.vendor_debit_note_repository import (
    VendorDebitNoteRepository,
)

from apps.purchasing.repositories.supplier_payment_repository import (
    SupplierPaymentRepository,
)

from apps.purchasing.repositories.goods_receipt_repository import (
    GoodsReceiptRepository,
)


class DocumentEmailConfigService:

    CONFIG = {
        "INVOICE": {
            "permission":
                "invoices.read",

            "repository":
                InvoiceRepository,

            "id_argument":
                "invoice_id",

            "number_attribute":
                "invoice_number",

            "recipient_object":
                "customer",

            "recipient_email_attribute":
                "email",

            "recipient_name_attribute":
                "name",
        },

        "SALES_ORDER": {
            "permission":
                "sales_orders.read",

            "repository":
                SalesOrderRepository,

            "id_argument":
                "sales_order_id",

            "number_attribute":
                "so_number",

            "recipient_object":
                "customer",

            "recipient_email_attribute":
                "email",

            "recipient_name_attribute":
                "name",
        },

        "CREDIT_NOTE": {
            "permission":
                "credit_notes.read",

            "repository":
                CreditNoteRepository,

            "id_argument":
                "credit_note_id",

            "number_attribute":
                "credit_note_number",

            "recipient_object":
                "customer",

            "recipient_email_attribute":
                "email",

            "recipient_name_attribute":
                "name",
        },

        "CUSTOMER_PAYMENT": {
            "permission":
                "customer_payments.read",

            "repository":
                PaymentRepository,

            "id_argument":
                "payment_id",

            "number_attribute":
                "payment_number",

            "recipient_object":
                "customer",

            "recipient_email_attribute":
                "email",

            "recipient_name_attribute":
                "name",
        },

        "PURCHASE_ORDER": {
            "permission":
                "purchase_orders.read",

            "repository":
                PurchaseOrderRepository,

            "id_argument":
                "purchase_order_id",

            "number_attribute":
                "po_number",

            "recipient_object":
                "supplier",

            "recipient_email_attribute":
                "email",

            "recipient_name_attribute":
                "name",
        },

        "VENDOR_BILL": {
            "permission":
                "vendor_bills.read",

            "repository":
                VendorBillRepository,

            "id_argument":
                "bill_id",

            "number_attribute":
                "bill_number",

            "recipient_object":
                "supplier",

            "recipient_email_attribute":
                "email",

            "recipient_name_attribute":
                "name",
        },

        "VENDOR_DEBIT_NOTE": {
            "permission":
                "vendor_debit_notes.read",

            "repository":
                VendorDebitNoteRepository,

            "id_argument":
                "debit_note_id",

            "number_attribute":
                "debit_note_number",

            "recipient_object":
                "supplier",

            "recipient_email_attribute":
                "email",

            "recipient_name_attribute":
                "name",
        },

        "SUPPLIER_PAYMENT": {
            "permission":
                "supplier_payments.read",

            "repository":
                SupplierPaymentRepository,

            "id_argument":
                "payment_id",

            "number_attribute":
                "payment_number",

            "recipient_object":
                "supplier",

            "recipient_email_attribute":
                "email",

            "recipient_name_attribute":
                "name",
        },

        "GOODS_RECEIPT": {
            "permission":
                "goods_receipts.read",

            "repository":
                GoodsReceiptRepository,

            "id_argument":
                "goods_receipt_id",

            "number_attribute":
                "grn_number",

            "recipient_object":
                "supplier",

            "recipient_email_attribute":
                "email",

            "recipient_name_attribute":
                "name",
        },
    }

    @staticmethod
    def normalize_document_type(
        document_type,
    ):
        if not document_type:
            raise ValueError(
                "Document type is required."
            )

        document_type = (
            str(document_type)
            .strip()
            .upper()
        )

        if (
            document_type
            not in
            DocumentEmailConfigService
            .CONFIG
        ):
            raise ValueError(
                "Unsupported document type."
            )

        return document_type

    @staticmethod
    def get_config(
        document_type,
    ):
        document_type = (
            DocumentEmailConfigService
            .normalize_document_type(
                document_type
            )
        )

        return (
            DocumentEmailConfigService
            .CONFIG[
                document_type
            ]
        )

    @staticmethod
    def get_document(
        *,
        organization,
        document_type,
        document_id,
    ):
        document_type = (
            DocumentEmailConfigService
            .normalize_document_type(
                document_type
            )
        )

        config = (
            DocumentEmailConfigService
            .CONFIG[
                document_type
            ]
        )

        repository = (
            config[
                "repository"
            ]
        )

        id_argument = (
            config[
                "id_argument"
            ]
        )

        kwargs = {
            "organization":
                organization,

            id_argument:
                document_id,
        }

        return (
            repository
            .get_by_id(
                **kwargs
            )
        )

    @staticmethod
    def get_delivery_data(
        *,
        document_type,
        document,
    ):
        if not document:
            raise ValueError(
                "Document is required."
            )

        document_type = (
            DocumentEmailConfigService
            .normalize_document_type(
                document_type
            )
        )

        config = (
            DocumentEmailConfigService
            .CONFIG[
                document_type
            ]
        )

        document_number = getattr(
            document,
            config[
                "number_attribute"
            ],
            None,
        )

        if not document_number:
            raise ValueError(
                "Document number not found."
            )

        recipient = getattr(
            document,
            config[
                "recipient_object"
            ],
            None,
        )

        if not recipient:
            raise ValueError(
                "Document recipient "
                "not found."
            )

        recipient_email = getattr(
            recipient,
            config[
                "recipient_email_attribute"
            ],
            None,
        )

        recipient_name = getattr(
            recipient,
            config[
                "recipient_name_attribute"
            ],
            None,
        )

        if not recipient_email:
            raise ValueError(
                "Recipient email "
                "is not configured."
            )

        return {
            "document_type":
                document_type,

            "document_number":
                document_number,

            "recipient":
                recipient,

            "recipient_email":
                recipient_email,

            "recipient_name":
                recipient_name,

            "permission":
                config[
                    "permission"
                ],
        }