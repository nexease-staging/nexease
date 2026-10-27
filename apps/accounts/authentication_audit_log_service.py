from apps.accounts.security_audit_models import (
    AuthenticationAuditLog,
)


class AuthenticationAuditLogService:

    @staticmethod
    def list_logs(
        *,
        user,
        organization,
        event_type=None,
        identifier=None,
        ip_address=None,
        limit=100,
    ):
        # ==================================================
        # AUTHENTICATION
        # ==================================================

        if not user:
            raise PermissionError(
                "Not authenticated."
            )

        if not user.is_active:
            raise PermissionError(
                "Not authenticated."
            )

        # ==================================================
        # ORGANIZATION
        # ==================================================

        if not organization:
            raise PermissionError(
                "Organization not found."
            )

        user_organization = getattr(
            user,
            "organization",
            None,
        )

        if not user_organization:

            raise PermissionError(
                "Organization not found."
            )

        if (
            str(
                user_organization.id
            )
            !=
            str(
                organization.id
            )
        ):
            raise PermissionError(
                "Organization access denied."
            )

        # ==================================================
        # PERMISSION
        # ==================================================

        if not user.has_permission(
            "accounting_audit.read"
        ):
            raise PermissionError(
                "Permission denied."
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
                "Limit must be greater than zero."
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
        # EVENT TYPE
        # ==================================================

        if event_type:

            event_type = (
                str(
                    event_type
                )
                .strip()
                .upper()
            )

            allowed_event_types = {
                "LOGIN_SUCCESS",
                "LOGIN_FAILED",
                "LOGIN_BLOCKED",
                "LOGOUT",
                "LOGOUT_ALL",
            }

            if (
                event_type
                not in
                allowed_event_types
            ):

                raise ValueError(
                    "Invalid event type."
                )

            filters[
                "event_type"
            ] = event_type

        # ==================================================
        # IDENTIFIER
        # ==================================================

        if identifier:

            identifier = (
                str(
                    identifier
                )
                .strip()
                .lower()
            )

            if identifier:

                filters[
                    "identifier__icontains"
                ] = identifier

        # ==================================================
        # IP
        # ==================================================

        if ip_address:

            ip_address = (
                str(
                    ip_address
                )
                .strip()
            )

            if ip_address:

                filters[
                    "ip_address__icontains"
                ] = ip_address

        # ==================================================
        # QUERY
        # ==================================================

        return list(
            AuthenticationAuditLog.objects(
                **filters
            )
            .order_by(
                "-created_at"
            )[
                :limit
            ]
        )