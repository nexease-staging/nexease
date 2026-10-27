from apps.finance.models import (
    DocumentDeliveryLog,
)

from apps.finance.services.document_email_config_service import (
    DocumentEmailConfigService,
)

from apps.finance.services.generic_document_email_service import (
    GenericDocumentEmailService,
)


class DocumentDeliveryRetryService:

    @staticmethod
    def retry(
        *,
        user,
        organization,
        delivery_log_id,
    ):
        if not user:
            raise ValueError(
                "User is required."
            )

        if not user.is_active:
            raise ValueError(
                "User is inactive."
            )

        if not organization:
            raise ValueError(
                "Organization is required."
            )

        if not user.organization:
            raise ValueError(
                "User has no organization."
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

        # ==================================================
        # ORIGINAL DELIVERY LOG
        # ==================================================

        delivery_log = (
            DocumentDeliveryLog.objects(
                organization=organization,
                id=delivery_log_id,
            )
            .first()
        )

        if not delivery_log:
            return None

        # ==================================================
        # CHANNEL
        # ==================================================

        if delivery_log.channel != "EMAIL":
            raise ValueError(
                "Only EMAIL deliveries "
                "can be retried here."
            )

        # ==================================================
        # DOCUMENT TYPE
        # ==================================================

        document_type = (
            DocumentEmailConfigService
            .normalize_document_type(
                delivery_log.document_type
            )
        )

        # ==================================================
        # RETRY THROUGH GENERIC SERVICE
        # ==================================================

        result = (
            GenericDocumentEmailService
            .send(
                user=user,
                organization=organization,
                document_type=document_type,
                document_id=(
                    delivery_log.document_id
                ),
            )
        )

        if result is None:
            raise ValueError(
                "Original document "
                "no longer exists."
            )

        return {
            "original_delivery":
                delivery_log,

            "retry_delivery":
                result[
                    "delivery"
                ],

            "result":
                result,
        }