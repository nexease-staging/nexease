from django.core.management.base import (
    BaseCommand,
)

from apps.accounts.login_rate_limit_service import (
    LoginRateLimitService,
)


class Command(BaseCommand):

    help = (
        "Delete stale login rate-limit records."
    )

    def handle(
        self,
        *args,
        **options,
    ):
        deleted_count = (
            LoginRateLimitService
            .cleanup_stale_attempts()
        )

        self.stdout.write(
            self.style.SUCCESS(
                (
                    "Login-attempt cleanup complete. "
                    f"Deleted: {deleted_count}"
                )
            )
        )