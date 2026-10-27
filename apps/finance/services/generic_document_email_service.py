from apps.finance.documents.pdf_security import (
    PDFSecurity,
)

from apps.finance.services.document_email_config_service import (
    DocumentEmailConfigService,
)

from apps.finance.services.document_email_delivery_service import (
    DocumentEmailDeliveryService,
)

from apps.finance.services.document_email_service import (
    DocumentEmailService,
)


class GenericDocumentEmailService:

    @staticmethod
    def send(
        *,
        user,
        organization,
        document_type,
        document_id,
        recipient_email_override=None,
        subject_override=None,
        body_override=None,
        background_job_key=None,
    ):
        # ==================================================
        # BASIC VALIDATION
        # ==================================================

        if not user:
            raise ValueError(
                "User is required."
            )

        if not organization:
            raise ValueError(
                "Organization is required."
            )

        # ==================================================
        # DOCUMENT TYPE
        # ==================================================

        document_type = (
            DocumentEmailConfigService
            .normalize_document_type(
                document_type
            )
        )

        config = (
            DocumentEmailConfigService
            .get_config(
                document_type
            )
        )

        # ==================================================
        # PERMISSION
        # ==================================================

        PDFSecurity.require_permission(
            user=user,
            permission_code=(
                config[
                    "permission"
                ]
            ),
        )

        # ==================================================
        # DOCUMENT
        # ==================================================

        document = (
            DocumentEmailConfigService
            .get_document(
                organization=organization,
                document_type=document_type,
                document_id=document_id,
            )
        )

        if not document:
            return None

        # ==================================================
        # DELIVERY DATA
        # ==================================================

        delivery_data = (
            DocumentEmailConfigService
            .get_delivery_data(
                document_type=document_type,
                document=document,
            )
        )

        # ==================================================
        # DEFAULT MESSAGE
        # ==================================================

        message_data = (
            DocumentEmailService
            .compose(
                organization=organization,
                document_type=document_type,
                document_number=(
                    delivery_data[
                        "document_number"
                    ]
                ),
                recipient_name=(
                    delivery_data[
                        "recipient_name"
                    ]
                ),
            )
        )

        # ==================================================
        # CUSTOM SUBJECT
        # ==================================================

        custom_subject_used = (
            subject_override
            is not None
        )

        if custom_subject_used:

            subject_override = (
                str(
                    subject_override
                )
                .strip()
            )

            if not subject_override:
                raise ValueError(
                    "Custom subject cannot be empty."
                )

            if len(
                subject_override
            ) > 200:
                raise ValueError(
                    "Custom subject is too long."
                )

            message_data[
                "subject"
            ] = subject_override

        # ==================================================
        # CUSTOM MESSAGE
        # ==================================================

        custom_message_used = (
            body_override
            is not None
        )

        if custom_message_used:

            body_override = (
                str(
                    body_override
                )
                .strip()
            )

            if not body_override:
                raise ValueError(
                    "Custom message cannot be empty."
                )

            if len(
                body_override
            ) > 5000:
                raise ValueError(
                    "Custom message is too long."
                )

            message_data[
                "body"
            ] = body_override

        # ==================================================
        # RECIPIENT
        # ==================================================

        recipient_email = (
            delivery_data[
                "recipient_email"
            ]
        )

        recipient_overridden = (
            recipient_email_override
            is not None
        )

        if recipient_overridden:

            recipient_email = (
                str(
                    recipient_email_override
                )
                .strip()
            )

            if not recipient_email:
                raise ValueError(
                    "Recipient email "
                    "override is invalid."
                )

        # ==================================================
        # SEND
        # ==================================================

        result = (
            DocumentEmailDeliveryService
            .send(
                user=user,
                organization=organization,
                document_type=document_type,
                document=document,
                document_id=document.id,
                background_job_key=background_job_key,

                document_number=(
                    delivery_data[
                        "document_number"
                    ]
                ),

                recipient_email=(
                    recipient_email
                ),

                recipient_name=(
                    delivery_data[
                        "recipient_name"
                    ]
                ),

                message_data=(
                    message_data
                ),

                recipient_overridden=(
                    recipient_overridden
                ),

                custom_subject=(
                    custom_subject_used
                ),

                custom_message=(
                    custom_message_used
                ),
            )
        )

        # ==================================================
        # RESULT
        # ==================================================

        return {
            "document":
                document,

            "delivery_data":
                delivery_data,

            "actual_recipient_email":
                recipient_email,

            "recipient_overridden":
                recipient_overridden,

            "custom_subject":
                custom_subject_used,

            "custom_message":
                custom_message_used,

            "delivery":
                result[
                    "delivery"
                ],

            "email":
                result[
                    "email"
                ],

            "message":
                result[
                    "message"
                ],

            "attachment":
                result[
                    "attachment"
                ],

            "sent_count":
                result[
                    "sent_count"
                ],
        }