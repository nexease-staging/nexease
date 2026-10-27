from apps.finance.models import (
    DocumentDeliveryLog,
)


class DocumentDeliveryLogService:

    READ_PERMISSION = (
        "accounting_audit.read"
    )

    @staticmethod
    def _check_permission(
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

        if not user.has_permission(
            DocumentDeliveryLogService
            .READ_PERMISSION
        ):
            raise PermissionError(
                "Permission denied: "
                f"{DocumentDeliveryLogService.READ_PERMISSION}"
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

    @staticmethod
    def list_logs(
        *,
        user,
        organization,
        document_type=None,
        channel=None,
        status=None,
        recipient=None,
        document_number=None,
        subject=None,
        recipient_overridden=None,
        custom_subject=None,
        custom_message=None,
        limit=100,
    ):
        DocumentDeliveryLogService._check_permission(
            user
        )

        DocumentDeliveryLogService._check_organization(
            user=user,
            organization=organization,
        )

        # ==================================================
        # LIMIT
        # ==================================================

        try:

            limit = int(
                limit
            )

        except (
            TypeError,
            ValueError,
        ):

            raise ValueError(
                "Invalid limit."
            )

        if limit < 1:

            raise ValueError(
                "Limit must be greater "
                "than zero."
            )

        if limit > 500:

            limit = 500

        # ==================================================
        # BASE FILTER
        # ==================================================

        filters = {
            "organization":
                organization,
        }

        # ==================================================
        # DOCUMENT TYPE
        # ==================================================

        if document_type:

            filters[
                "document_type"
            ] = (
                str(
                    document_type
                )
                .strip()
                .upper()
            )

        # ==================================================
        # CHANNEL
        # ==================================================

        if channel:

            filters[
                "channel"
            ] = (
                str(
                    channel
                )
                .strip()
                .upper()
            )

        # ==================================================
        # STATUS
        # ==================================================

        if status:

            filters[
                "status"
            ] = (
                str(
                    status
                )
                .strip()
                .upper()
            )

        # ==================================================
        # RECIPIENT SEARCH
        # ==================================================

        if recipient:

            recipient = (
                str(
                    recipient
                )
                .strip()
            )

            if recipient:

                filters[
                    "recipient__icontains"
                ] = recipient

        # ==================================================
        # DOCUMENT NUMBER SEARCH
        # ==================================================

        if document_number:

            document_number = (
                str(
                    document_number
                )
                .strip()
            )

            if document_number:

                filters[
                    "document_number__icontains"
                ] = (
                    document_number
                )

        # ==================================================
        # SUBJECT SEARCH
        # ==================================================

        if subject:

            subject = (
                str(
                    subject
                )
                .strip()
            )

            if subject:

                filters[
                    "subject__icontains"
                ] = subject

        # ==================================================
        # BOOLEAN FILTER HELPER
        # ==================================================

        def parse_boolean(
            value,
            field_name,
        ):
            if value is None:
                return None

            if isinstance(
                value,
                bool,
            ):
                return value

            normalized = (
                str(
                    value
                )
                .strip()
                .lower()
            )

            if normalized in {
                "true",
                "1",
                "yes",
            }:
                return True

            if normalized in {
                "false",
                "0",
                "no",
            }:
                return False

            raise ValueError(
                f"Invalid {field_name} value."
            )

        # ==================================================
        # RECIPIENT OVERRIDDEN
        # ==================================================

        parsed_recipient_overridden = (
            parse_boolean(
                recipient_overridden,
                "recipient_overridden",
            )
        )

        if (
            parsed_recipient_overridden
            is not None
        ):

            filters[
                "recipient_overridden"
            ] = (
                parsed_recipient_overridden
            )

        # ==================================================
        # CUSTOM SUBJECT
        # ==================================================

        parsed_custom_subject = (
            parse_boolean(
                custom_subject,
                "custom_subject",
            )
        )

        if (
            parsed_custom_subject
            is not None
        ):

            filters[
                "custom_subject"
            ] = (
                parsed_custom_subject
            )

        # ==================================================
        # CUSTOM MESSAGE
        # ==================================================

        parsed_custom_message = (
            parse_boolean(
                custom_message,
                "custom_message",
            )
        )

        if (
            parsed_custom_message
            is not None
        ):

            filters[
                "custom_message"
            ] = (
                parsed_custom_message
            )

        # ==================================================
        # QUERY
        # ==================================================

        return list(
            DocumentDeliveryLog.objects(
                **filters
            )
            .order_by(
                "-created_at"
            )[
                :limit
            ]
        )

    @staticmethod
    def get_log_by_id(
        *,
        user,
        organization,
        delivery_log_id,
    ):
        DocumentDeliveryLogService._check_permission(
            user
        )

        DocumentDeliveryLogService._check_organization(
            user=user,
            organization=organization,
        )

        if not delivery_log_id:
            raise ValueError(
                "Delivery log ID is required."
            )

        return (
            DocumentDeliveryLog.objects(
                organization=organization,
                id=delivery_log_id,
            )
            .first()
        )

    @staticmethod
    def get_summary(
        *,
        user,
        organization,
        recent_limit=10,
    ):
        DocumentDeliveryLogService._check_permission(
            user
        )

        DocumentDeliveryLogService._check_organization(
            user=user,
            organization=organization,
        )

        try:
            recent_limit = int(
                recent_limit
            )

        except (
            TypeError,
            ValueError,
        ):
            raise ValueError(
                "Invalid recent_limit."
            )

        if recent_limit < 1:
            raise ValueError(
                "recent_limit must be greater "
                "than zero."
            )

        if recent_limit > 100:
            recent_limit = 100

        logs = (
            DocumentDeliveryLog.objects(
                organization=organization,
            )
        )

        total_deliveries = (
            logs.count()
        )

        sent_count = (
            DocumentDeliveryLog.objects(
                organization=organization,
                status="SENT",
            )
            .count()
        )

        failed_count = (
            DocumentDeliveryLog.objects(
                organization=organization,
                status="FAILED",
            )
            .count()
        )

        pending_count = (
            DocumentDeliveryLog.objects(
                organization=organization,
                status="PENDING",
            )
            .count()
        )

        email_count = (
            DocumentDeliveryLog.objects(
                organization=organization,
                channel="EMAIL",
            )
            .count()
        )

        whatsapp_count = (
            DocumentDeliveryLog.objects(
                organization=organization,
                channel="WHATSAPP",
            )
            .count()
        )

        success_rate = (
            round(
                (
                    sent_count
                    /
                    total_deliveries
                    *
                    100
                ),
                2,
            )
            if total_deliveries
            else 0.0
        )

        failure_rate = (
            round(
                (
                    failed_count
                    /
                    total_deliveries
                    *
                    100
                ),
                2,
            )
            if total_deliveries
            else 0.0
        )

        by_document_type = {}

        by_status = {}

        by_channel = {}

        for log in logs:

            document_type = (
                log.document_type
                or "UNKNOWN"
            )

            by_document_type[
                document_type
            ] = (
                by_document_type.get(
                    document_type,
                    0,
                )
                + 1
            )

            status = (
                log.status
                or "UNKNOWN"
            )

            by_status[
                status
            ] = (
                by_status.get(
                    status,
                    0,
                )
                + 1
            )

            channel = (
                log.channel
                or "UNKNOWN"
            )

            by_channel[
                channel
            ] = (
                by_channel.get(
                    channel,
                    0,
                )
                + 1
            )

        document_type_rows = [
            {
                "document_type":
                    key,

                "count":
                    value,
            }

            for (
                key,
                value,
            )
            in by_document_type.items()
        ]

        document_type_rows.sort(
            key=lambda row: (
                -row["count"],
                row["document_type"],
            )
        )

        status_rows = [
            {
                "status":
                    key,

                "count":
                    value,
            }

            for (
                key,
                value,
            )
            in by_status.items()
        ]

        status_rows.sort(
            key=lambda row: (
                -row["count"],
                row["status"],
            )
        )

        channel_rows = [
            {
                "channel":
                    key,

                "count":
                    value,
            }

            for (
                key,
                value,
            )
            in by_channel.items()
        ]

        channel_rows.sort(
            key=lambda row: (
                -row["count"],
                row["channel"],
            )
        )

        recent_logs = list(
            DocumentDeliveryLog.objects(
                organization=organization,
            )
            .order_by(
                "-created_at"
            )[
                :recent_limit
            ]
        )

        recent_activity = []

        for log in recent_logs:

            recent_activity.append(
                {
                    "id":
                        str(
                            log.id
                        ),

                    "document_type":
                        log.document_type,

                    "document_number":
                        log.document_number,

                    "channel":
                        log.channel,

                    "recipient":
                        log.recipient,

                    "status":
                        log.status,

                    "sent_at": (
                        log.sent_at
                        .isoformat()
                        if log.sent_at
                        else None
                    ),

                    "created_at": (
                        log.created_at
                        .isoformat()
                        if log.created_at
                        else None
                    ),
                }
            )

        return {
            "total_deliveries":
                total_deliveries,

            "sent":
                sent_count,

            "failed":
                failed_count,

            "pending":
                pending_count,

            "email":
                email_count,

            "whatsapp":
                whatsapp_count,

            "success_rate":
                success_rate,

            "failure_rate":
                failure_rate,

            "by_document_type":
                document_type_rows,

            "by_status":
                status_rows,

            "by_channel":
                channel_rows,

            "recent_activity":
                recent_activity,
        }