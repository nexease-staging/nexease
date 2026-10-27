from django.conf import settings

from django.core.mail import (
    EmailMessage,
)
from apps.finance.models import (
    DocumentDeliveryLog,
)
from django.core.validators import (
    validate_email,
)

from django.core.exceptions import (
    ValidationError,
)

from apps.finance.services.document_attachment_service import (
    DocumentAttachmentService,
)

from apps.finance.services.document_delivery_service import (
    DocumentDeliveryService,
)

from apps.finance.services.document_email_service import (
    DocumentEmailService,
)


class DocumentEmailDeliveryService:

    @staticmethod
    def send(
        *,
        user,
        organization,
        document_type,
        document,
        document_id,
        document_number,
        recipient_email,
        recipient_name=None,
        message_data=None,
        recipient_overridden=False,
        custom_subject=False,
        custom_message=False,
        background_job_key=None,
    ):
        # ==================================================
        # RECIPIENT VALIDATION
        # ==================================================

        if not recipient_email:
            raise ValueError(
                "Recipient email is required."
            )

        recipient_email = (
            str(
                recipient_email
            )
            .strip()
        )

        if not recipient_email:
            raise ValueError(
                "Recipient email is required."
            )

        try:

            validate_email(
                recipient_email
            )

        except ValidationError:

            raise ValueError(
                "Invalid recipient email."
            )

        # ==================================================
        # COMPOSE EMAIL
        # ==================================================

        if message_data is None:

            message_data = (
                DocumentEmailService
                .compose(
                    organization=organization,
                    document_type=document_type,
                    document_number=document_number,
                    recipient_name=recipient_name,
                )
            )

        if background_job_key:
            existing_delivery = (
                DocumentDeliveryLog.objects(
                    organization=organization,
                    background_job_key=(
                        background_job_key
                    ),
                    channel="EMAIL",
                    status="SENT",
                )
                .first()
            )

            if existing_delivery:
                return {
                    "delivery":
                        existing_delivery,

                    "email":
                        None,

                    "message":
                        message_data,

                    "attachment":
                        None,

                    "sent_count":
                        1,
                }
            
        # ==================================================
        # GENERATE PDF ATTACHMENT
        # ==================================================

        attachment = (
            DocumentAttachmentService
            .generate(
                document_type=document_type,
                document=document,
                document_number=document_number,
            )
        )

        # ==================================================
        # CREATE DELIVERY LOG
        # ==================================================

        delivery = (
            DocumentDeliveryService
            .create_delivery(
                user=user,
                organization=organization,
                document_type=document_type,
                document_id=document_id,
                document_number=document_number,
                channel="EMAIL",
                recipient=recipient_email,

                subject=(
                    message_data[
                        "subject"
                    ]
                ),

                recipient_overridden=(
                    recipient_overridden
                ),

                custom_subject=(
                    custom_subject
                ),

                custom_message=(
                    custom_message
                ),
                background_job_key=(
                    background_job_key
                ),
            )
        )

        try:

            # ==================================================
            # CREATE EMAIL
            # ==================================================

            email = EmailMessage(
                subject=(
                    message_data[
                        "subject"
                    ]
                ),

                body=(
                    message_data[
                        "body"
                    ]
                ),

                from_email=(
                    settings.DEFAULT_FROM_EMAIL
                ),

                to=[
                    recipient_email
                ],
            )

            # ==================================================
            # ATTACH PDF
            # ==================================================

            email.attach(
                attachment[
                    "filename"
                ],

                attachment[
                    "content"
                ],

                attachment[
                    "content_type"
                ],
            )

            # ==================================================
            # SEND
            # ==================================================

            sent_count = (
                email.send(
                    using="default"
                )
            )

            if sent_count != 1:
                raise RuntimeError(
                    "Email backend did not "
                    "confirm delivery."
                )

            # ==================================================
            # MARK SENT
            # ==================================================

            DocumentDeliveryService.mark_sent(
                delivery=delivery
            )

            return {
                "delivery":
                    delivery,

                "email":
                    email,

                "message":
                    message_data,

                "attachment":
                    attachment,

                "sent_count":
                    sent_count,
            }

        except Exception:

            # ==================================================
            # MARK FAILED
            # ==================================================

            DocumentDeliveryService.mark_failed(
                delivery=delivery,
                error_message=(
                    "Email delivery failed."
                ),
            )

            raise