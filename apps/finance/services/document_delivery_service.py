from datetime import datetime

from apps.finance.models import (
    DocumentDeliveryLog,
)


class DocumentDeliveryService:

    VALID_CHANNELS = {
        "EMAIL",
        "WHATSAPP",
    }

    @staticmethod
    def _check_user(
        user,
    ):
        if not user:
            raise ValueError(
                "User is required."
            )

        if not user.is_active:
            raise ValueError(
                "User is inactive."
            )

        if not user.organization:
            raise ValueError(
                "User has no organization."
            )

    @staticmethod
    def _check_organization(
        *,
        user,
        organization,
    ):
        if not organization:
            raise ValueError(
                "Organization is required."
            )

        if (
            str(user.organization.id)
            !=
            str(organization.id)
        ):
            raise PermissionError(
                "User does not belong "
                "to this organization."
            )

    @staticmethod
    def _normalize_channel(
        channel,
    ):
        if not channel:
            raise ValueError(
                "Delivery channel is required."
            )

        normalized_channel = (
            str(channel)
            .strip()
            .upper()
        )

        if (
            normalized_channel
            not in
            DocumentDeliveryService
            .VALID_CHANNELS
        ):
            raise ValueError(
                "Invalid delivery channel."
            )

        return normalized_channel

    @staticmethod
    def _normalize_recipient(
        recipient,
    ):
        if not recipient:
            raise ValueError(
                "Recipient is required."
            )

        recipient = str(
            recipient
        ).strip()

        if not recipient:
            raise ValueError(
                "Recipient is required."
            )

        return recipient

    @staticmethod
    def create_delivery(
        *,
        user,
        organization,
        document_type,
        document_id,
        document_number,
        channel,
        recipient,
        subject=None,
        recipient_overridden=False,
        custom_subject=False,
        custom_message=False,
        background_job_key=None,
    ):
        DocumentDeliveryService._check_user(
            user
        )

        DocumentDeliveryService._check_organization(
            user=user,
            organization=organization,
        )

        if not document_type:
            raise ValueError(
                "Document type is required."
            )

        if not document_id:
            raise ValueError(
                "Document ID is required."
            )

        if not document_number:
            raise ValueError(
                "Document number is required."
            )

        channel = (
            DocumentDeliveryService
            ._normalize_channel(
                channel
            )
        )

        recipient = (
            DocumentDeliveryService
            ._normalize_recipient(
                recipient
            )
        )

        delivery = DocumentDeliveryLog(
            organization=organization,
            user=user,

            document_type=(
                str(
                    document_type
                )
                .strip()
                .upper()
            ),

            document_id=str(
                document_id
            ),

            document_number=(
                str(
                    document_number
                )
                .strip()
            ),

            channel=channel,

            recipient=recipient,

            subject=subject,

            recipient_overridden=bool(
                recipient_overridden
            ),

            custom_subject=bool(
                custom_subject
            ),

            custom_message=bool(
                custom_message
            ),

            background_job_key=(
                background_job_key
            ),

            status="PENDING",

            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        delivery.save()

        return delivery

    @staticmethod
    def mark_sent(
        *,
        delivery,
    ):
        if not delivery:
            raise ValueError(
                "Delivery is required."
            )

        if delivery.status == "SENT":
            return delivery

        delivery.status = "SENT"

        delivery.error_message = None

        delivery.sent_at = (
            datetime.utcnow()
        )

        delivery.updated_at = (
            datetime.utcnow()
        )

        delivery.save()

        return delivery

    @staticmethod
    def mark_failed(
        *,
        delivery,
        error_message=None,
    ):
        if not delivery:
            raise ValueError(
                "Delivery is required."
            )

        delivery.status = "FAILED"

        delivery.sent_at = None

        delivery.error_message = (
            str(
                error_message
            )[:500]
            if error_message
            else
            "Delivery failed."
        )

        delivery.updated_at = (
            datetime.utcnow()
        )

        delivery.save()

        return delivery