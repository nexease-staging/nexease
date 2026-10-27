from django.core.management.base import (
    BaseCommand,
)

from apps.accounts.authentication_audit_service import (
    AuthenticationAuditService,
)


class Command(BaseCommand):

    help = (
        "Delete old authentication audit logs."
    )

    def handle(
        self,
        *args,
        **options,
    ):
        deleted_count = (
            AuthenticationAuditService
            .cleanup_old_logs()
        )

        self.stdout.write(
            self.style.SUCCESS(
                (
                    "Authentication audit cleanup complete. "
                    f"Deleted: {deleted_count}"
                )
            )
        )