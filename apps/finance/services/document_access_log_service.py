from apps.finance.models import (
    DocumentAccessLog,
)


class DocumentAccessLogService:

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
            DocumentAccessLogService
            .READ_PERMISSION
        ):
            raise PermissionError(
                "Permission denied: "
                f"{DocumentAccessLogService.READ_PERMISSION}"
            )

    @staticmethod
    def _check_organization(
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
        action=None,
        document_number=None,
        user_id=None,
        limit=100,
    ):
        DocumentAccessLogService._check_permission(
            user
        )

        DocumentAccessLogService._check_organization(
            user,
            organization,
        )

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

        filters = {
            "organization":
                organization,
        }

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

        if action:
            filters[
                "action"
            ] = (
                str(
                    action
                )
                .strip()
                .upper()
            )

        if document_number:
            filters[
                "document_number"
            ] = str(
                document_number
            ).strip()

        if user_id:
            filters[
                "user"
            ] = user_id

        return list(
            DocumentAccessLog.objects(
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
        log_id,
    ):
        DocumentAccessLogService._check_permission(
            user
        )

        DocumentAccessLogService._check_organization(
            user,
            organization,
        )

        if not log_id:
            raise ValueError(
                "Document access log ID "
                "is required."
            )

        log = (
            DocumentAccessLog.objects(
                organization=organization,
                id=log_id,
            )
            .first()
        )

        return log

    @staticmethod
    def get_summary(
        *,
        user,
        organization,
        recent_limit=10,
    ):
        DocumentAccessLogService._check_permission(
            user
        )

        DocumentAccessLogService._check_organization(
            user,
            organization,
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
            DocumentAccessLog.objects(
                organization=organization,
            )
        )

        total_downloads = (
            logs.count()
        )

        # ==================================================
        # BY DOCUMENT TYPE
        # ==================================================

        by_document_type = {}

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


        # ==================================================
        # BY USER
        # ==================================================

        by_user = {}

        for log in logs:

            if log.user:

                user_id = str(
                    log.user.id
                )

                email = (
                    log.user.email
                )

            else:

                user_id = None
                email = "UNKNOWN"

            key = (
                user_id
                or "UNKNOWN"
            )

            if key not in by_user:

                by_user[key] = {
                    "user_id":
                        user_id,

                    "email":
                        email,

                    "downloads":
                        0,
                }

            by_user[
                key
            ][
                "downloads"
            ] += 1


        # ==================================================
        # BY ACTION
        # ==================================================

        by_action = {}

        for log in logs:

            action = (
                log.action
                or "UNKNOWN"
            )

            by_action[
                action
            ] = (
                by_action.get(
                    action,
                    0,
                )
                + 1
            )


        # ==================================================
        # RECENT ACTIVITY
        # ==================================================

        recent_logs = list(
            DocumentAccessLog.objects(
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
                        str(log.id),

                    "user": {
                        "id": (
                            str(
                                log.user.id
                            )
                            if log.user
                            else None
                        ),

                        "email": (
                            log.user.email
                            if log.user
                            else None
                        ),
                    },

                    "document_type":
                        log.document_type,

                    "document_id":
                        log.document_id,

                    "document_number":
                        log.document_number,

                    "action":
                        log.action,

                    "created_at": (
                        log.created_at
                        .isoformat()
                        if log.created_at
                        else None
                    ),
                }
            )


        # ==================================================
        # SORTED OUTPUT
        # ==================================================

        document_type_rows = [
            {
                "document_type":
                    document_type,

                "downloads":
                    count,
            }

            for (
                document_type,
                count,
            )
            in by_document_type.items()
        ]

        document_type_rows.sort(
            key=lambda row: (
                -row["downloads"],
                row["document_type"],
            )
        )


        user_rows = list(
            by_user.values()
        )

        user_rows.sort(
            key=lambda row: (
                -row["downloads"],
                row["email"]
                or "",
            )
        )


        action_rows = [
            {
                "action":
                    action,

                "count":
                    count,
            }

            for (
                action,
                count,
            )
            in by_action.items()
        ]

        action_rows.sort(
            key=lambda row: (
                -row["count"],
                row["action"],
            )
        )


        return {
            "total_downloads":
                total_downloads,

            "by_document_type":
                document_type_rows,

            "by_user":
                user_rows,

            "by_action":
                action_rows,

            "recent_activity":
                recent_activity,
        }