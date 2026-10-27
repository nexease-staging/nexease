import socket
import time
import uuid

from apps.finance.background_jobs import (
    register_finance_background_jobs,
)
from apps.core.background_jobs import (
    register_core_background_jobs,
)
from django.core.management.base import (
    BaseCommand,
)

from apps.core.services.background_job_executor import (
    BackgroundJobExecutor,
)
from apps.core.services.background_job_service import (
    BackgroundJobService,
)
from apps.core.services.shutdown_state_service import (
    ShutdownStateService,
)
from apps.migration.background_jobs import (
    register_migration_background_jobs,
)

class Command(BaseCommand):

    help = (
        "Run the django-ims background job worker."
    )

    def add_arguments(
        self,
        parser,
    ):
        parser.add_argument(
            "--once",
            action="store_true",
            help=(
                "Process at most one available "
                "background job and exit."
            ),
        )

        parser.add_argument(
            "--sleep",
            type=float,
            default=2.0,
            help=(
                "Seconds to wait when no "
                "job is available."
            ),
        )

        parser.add_argument(
            "--lease-seconds",
            type=int,
            default=300,
            help=(
                "Job lease duration in seconds."
            ),
        )

    def handle(
        self,
        *args,
        **options,
    ):
        once = bool(
            options["once"]
        )

        sleep_seconds = float(
            options["sleep"]
        )

        lease_seconds = int(
            options["lease_seconds"]
        )

        if sleep_seconds < 0:
            raise ValueError(
                "Sleep seconds cannot be negative."
            )

        if lease_seconds < 30:
            raise ValueError(
                "Lease seconds must be at least 30."
            )

        register_finance_background_jobs()
        register_core_background_jobs()
        register_migration_background_jobs()

        worker_id = (
            self._build_worker_id()
        )

        self.stdout.write(
            self.style.SUCCESS(
                (
                    "Background worker started: "
                    f"{worker_id}"
                )
            )
        )

        while True:

            if ShutdownStateService.is_shutting_down():
                self.stdout.write(
                    self.style.WARNING(
                        "Background worker stopping gracefully."
                    )
                )
                return

            BackgroundJobService.recover_expired_jobs()

            self._requeue_due_retries()

            job = (
                BackgroundJobService
                .claim_next_job(
                    worker_id=worker_id,
                    lease_seconds=
                        lease_seconds,
                )
            )

            if job is None:
                if once:
                    self.stdout.write(
                        "No background job available."
                    )
                    return

                time.sleep(
                    sleep_seconds
                )

                continue

            self.stdout.write(
                (
                    "Processing job "
                    f"{job.id} "
                    f"({job.job_type}) "
                    f"attempt "
                    f"{job.attempts}/"
                    f"{job.max_attempts}"
                )
            )

            try:
                result = (
                    BackgroundJobExecutor
                    .execute(
                        job=job,
                    )
                )

            except Exception as exc:
                failed_job = (
                    BackgroundJobService
                    .handle_failure(
                        job=job,
                        error=exc,
                    )
                )

                self.stderr.write(
                    (
                        "Background job failed: "
                        f"{job.id} - "
                        f"{exc}"
                    )
                )

                self.stdout.write(
                    (
                        "Job status: "
                        f"{failed_job.status}"
                    )
                )

            else:
                completed_job = (
                    BackgroundJobService
                    .mark_succeeded(
                        job=job,
                        result=result
                    )
                )

                self.stdout.write(
                    self.style.SUCCESS(
                        (
                            "Background job "
                            "completed: "
                            f"{completed_job.id}"
                        )
                    )
                )

            if once:
                return

    @staticmethod
    def _build_worker_id():
        hostname = (
            socket.gethostname()
            or "unknown-host"
        )

        unique_id = (
            uuid.uuid4()
            .hex[:12]
        )

        return (
            f"{hostname}:{unique_id}"
        )

    @staticmethod
    def _requeue_due_retries():
        from datetime import datetime

        from apps.core.background_job_models import (
            BackgroundJob,
        )

        now = datetime.utcnow()

        retry_jobs = (
            BackgroundJob.objects(
                status="RETRYING",
                available_at__lte=now,
            )
            .only(
                "id",
                "status",
                "available_at",
            )
        )

        for job in retry_jobs:
            (
                BackgroundJobService
                .requeue_retrying_job(
                    job=job,
                )
            )