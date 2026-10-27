from apps.finance.documents.invoice_pdf import (
    InvoicePDF,
)

from apps.finance.documents.sales_order_pdf import (
    SalesOrderPDF,
)

from apps.finance.documents.credit_note_pdf import (
    CreditNotePDF,
)

from apps.finance.documents.customer_payment_receipt_pdf import (
    CustomerPaymentReceiptPDF,
)

from apps.finance.documents.purchase_order_pdf import (
    PurchaseOrderPDF,
)

from apps.finance.documents.vendor_bill_pdf import (
    VendorBillPDF,
)

from apps.finance.documents.vendor_debit_note_pdf import (
    VendorDebitNotePDF,
)

from apps.finance.documents.supplier_payment_receipt_pdf import (
    SupplierPaymentReceiptPDF,
)

from apps.finance.documents.goods_receipt_pdf import (
    GoodsReceiptPDF,
)


class DocumentAttachmentService:

    GENERATORS = {
        "INVOICE": {
            "generator": InvoicePDF,
            "argument": "invoice",
        },

        "SALES_ORDER": {
            "generator": SalesOrderPDF,
            "argument": "sales_order",
        },

        "CREDIT_NOTE": {
            "generator": CreditNotePDF,
            "argument": "credit_note",
        },

        "CUSTOMER_PAYMENT": {
            "generator":
                CustomerPaymentReceiptPDF,

            "argument":
                "payment",
        },

        "PURCHASE_ORDER": {
            "generator": PurchaseOrderPDF,
            "argument": "purchase_order",
        },

        "VENDOR_BILL": {
            "generator": VendorBillPDF,
            "argument": "vendor_bill",
        },

        "VENDOR_DEBIT_NOTE": {
            "generator":
                VendorDebitNotePDF,

            "argument":
                "debit_note",
        },

        "SUPPLIER_PAYMENT": {
            "generator":
                SupplierPaymentReceiptPDF,

            "argument":
                "payment",
        },

        "GOODS_RECEIPT": {
            "generator":
                GoodsReceiptPDF,

            "argument":
                "goods_receipt",
        },
    }

    @staticmethod
    def _normalize_document_type(
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
            DocumentAttachmentService
            .GENERATORS
        ):
            raise ValueError(
                "Unsupported document type."
            )

        return document_type

    @staticmethod
    def generate(
        *,
        document_type,
        document,
        document_number,
    ):
        if not document:
            raise ValueError(
                "Document is required."
            )

        if not document_number:
            raise ValueError(
                "Document number is required."
            )

        document_type = (
            DocumentAttachmentService
            ._normalize_document_type(
                document_type
            )
        )

        configuration = (
            DocumentAttachmentService
            .GENERATORS[
                document_type
            ]
        )

        generator = (
            configuration[
                "generator"
            ]
        )

        argument_name = (
            configuration[
                "argument"
            ]
        )

        generator_kwargs = {
            argument_name:
                document
        }

        pdf_bytes = (
            generator.generate(
                **generator_kwargs
            )
        )

        if not isinstance(
            pdf_bytes,
            bytes,
        ):
            raise ValueError(
                "PDF generator did not "
                "return bytes."
            )

        if not pdf_bytes.startswith(
            b"%PDF"
        ):
            raise ValueError(
                "Generated attachment "
                "is not a valid PDF."
            )

        filename = (
            f"{document_number}.pdf"
        )

        return {
            "document_type":
                document_type,

            "filename":
                filename,

            "content_type":
                "application/pdf",

            "content":
                pdf_bytes,

            "size":
                len(
                    pdf_bytes
                ),
        }