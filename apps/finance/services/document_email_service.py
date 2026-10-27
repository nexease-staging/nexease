class DocumentEmailService:

    SUPPORTED_DOCUMENT_TYPES = {
        "INVOICE": "Invoice",
        "SALES_ORDER": "Sales Order",
        "CREDIT_NOTE": "Credit Note",
        "CUSTOMER_PAYMENT": "Payment Receipt",
        "PURCHASE_ORDER": "Purchase Order",
        "VENDOR_BILL": "Vendor Bill",
        "VENDOR_DEBIT_NOTE": "Vendor Debit Note",
        "SUPPLIER_PAYMENT": "Supplier Payment Receipt",
        "GOODS_RECEIPT": "Goods Receipt",
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
            DocumentEmailService
            .SUPPORTED_DOCUMENT_TYPES
        ):
            raise ValueError(
                "Unsupported document type."
            )

        return document_type

    @staticmethod
    def _normalize_recipient_name(
        recipient_name,
    ):
        if not recipient_name:
            return "Customer / Supplier"

        return str(
            recipient_name
        ).strip()

    @staticmethod
    def compose(
        *,
        organization,
        document_type,
        document_number,
        recipient_name=None,
    ):
        if not organization:
            raise ValueError(
                "Organization is required."
            )

        if not document_number:
            raise ValueError(
                "Document number is required."
            )

        document_type = (
            DocumentEmailService
            ._normalize_document_type(
                document_type
            )
        )

        recipient_name = (
            DocumentEmailService
            ._normalize_recipient_name(
                recipient_name
            )
        )

        document_label = (
            DocumentEmailService
            .SUPPORTED_DOCUMENT_TYPES[
                document_type
            ]
        )

        organization_name = (
            getattr(
                organization,
                "name",
                None,
            )
            or
            "Our Company"
        )

        organization_email = (
            getattr(
                organization,
                "email",
                None,
            )
        )

        organization_phone = (
            getattr(
                organization,
                "phone",
                None,
            )
        )

        subject = (
            f"{document_label} "
            f"{document_number} - "
            f"{organization_name}"
        )

        body_lines = [
            f"Dear {recipient_name},",
            "",
            (
                f"Please find attached your "
                f"{document_label.lower()} "
                f"{document_number}."
            ),
            "",
            (
                f"Regards,"
            ),
            organization_name,
        ]

        if organization_email:
            body_lines.append(
                f"Email: {organization_email}"
            )

        if organization_phone:
            body_lines.append(
                f"Phone: {organization_phone}"
            )

        body = "\n".join(
            body_lines
        )

        return {
            "document_type":
                document_type,

            "document_label":
                document_label,

            "document_number":
                str(document_number),

            "recipient_name":
                recipient_name,

            "subject":
                subject,

            "body":
                body,
        }