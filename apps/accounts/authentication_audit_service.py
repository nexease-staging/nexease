from apps.accounts.security_audit_models import (
    AuthenticationAuditLog,
)
from datetime import (
    datetime,
    timedelta,
)

class AuthenticationAuditService:

    RETENTION_DAYS = 90

    @staticmethod
    def record(
        *,
        event_type,
        user=None,
        organization=None,
        identifier=None,
        ip_address=None,
    ):
        # ==================================================
        # ORGANIZATION FALLBACK
        # ==================================================

        if (
            organization is None
            and
            user is not None
        ):

            organization = getattr(
                user,
                "organization",
                None,
            )

        # ==================================================
        # IDENTIFIER
        # ==================================================

        if identifier is not None:

            identifier = (
                str(
                    identifier
                )
                .strip()
                .lower()
            )

        # ==================================================
        # IP
        # ==================================================

        if ip_address is not None:

            ip_address = (
                str(
                    ip_address
                )
                .strip()
            )

        # ==================================================
        # CREATE
        # ==================================================

        return AuthenticationAuditLog(
            event_type=event_type,
            user=user,
            organization=organization,
            identifier=identifier,
            ip_address=ip_address,
        ).save()

    @staticmethod
    def cleanup_old_logs():

        cutoff = (
            datetime.utcnow()
            -
            timedelta(
                days=(
                    AuthenticationAuditService
                    .RETENTION_DAYS
                )
            )
        )

        old_logs = (
            AuthenticationAuditLog.objects(
                created_at__lt=cutoff
            )
        )

        deleted_count = (
            old_logs.count()
        )

        old_logs.delete()

        return deleted_count