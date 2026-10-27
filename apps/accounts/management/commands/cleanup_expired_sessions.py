from django.core.management.base import (
    BaseCommand,
)

from apps.accounts.session_backend import (
    SessionStore,
)

from apps.accounts.session_models import (
    MongoSession,
)


class Command(BaseCommand):

    help = (
        "Delete expired IMS MongoDB sessions."
    )

    def handle(
        self,
        *args,
        **options,
    ):
        before_count = (
            MongoSession.objects.count()
        )

        SessionStore.clear_expired()

        after_count = (
            MongoSession.objects.count()
        )

        deleted_count = (
            before_count
            -
            after_count
        )

        self.stdout.write(
            self.style.SUCCESS(
                (
                    "Expired session cleanup complete. "
                    f"Deleted: {deleted_count}"
                )
            )
        )