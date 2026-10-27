from concurrent.futures import (
    ThreadPoolExecutor,
)
from datetime import (
    datetime,
    timedelta,
)
from apps.core.notification_models import (
    Notification,
)
from apps.core.services.notification_service import (
    NotificationService,
)
from apps.core.repositories.background_job_repository import (
    BackgroundJobRepository,
)
from threading import Barrier
from uuid import uuid4

from django.test import SimpleTestCase

from apps.accounts.models import User
from apps.core.background_job_models import (
    BackgroundJob,
)
from apps.core.services.background_job_service import (
    BackgroundJobService,
)
from apps.organizations.models import Organization


class Day53BackgroundJobConcurrencyTests(
    SimpleTestCase,
):

    def setUp(self):
        self.test_key = uuid4().hex

        self.organization = Organization(
            name=(
                "Day 53 Concurrency "
                f"{self.test_key}"
            ),
            email=(
                f"day53-concurrency-"
                f"{self.test_key}"
                "@example.com"
            ),
        )
        self.organization.save()

        self.user = User(
            organization=self.organization,
            email=(
                f"day53-concurrency-user-"
                f"{self.test_key}"
                "@example.com"
            ),
            password="day53-test-password",
            first_name="Day",
            last_name="FiftyThree",
            is_active=True,
        )
        self.user.save()

    def tearDown(self):
        BackgroundJob.objects(
            organization=self.organization,
        ).delete()

        Notification.objects(
            organization=self.organization,
        ).delete()

        User.objects(
            organization=self.organization,
        ).delete()

        self.organization.delete()

    def _create_job(
        self,
        suffix,
    ):
        return (
            BackgroundJobService
            .create_job(
                organization=
                    self.organization,
                created_by=
                    self.user,
                job_type="NOTIFICATION",
                payload={
                    "test": suffix,
                },
                idempotency_key=(
                    f"day53-concurrency-"
                    f"{self.test_key}-"
                    f"{suffix}"
                ),
            )
        )

    # ==========================================
    # TWO WORKERS / ONE JOB
    # ==========================================

    def test_two_workers_cannot_claim_same_job(
        self,
    ):
        job = self._create_job(
            "single-job"
        )

        barrier = Barrier(2)

        def claim(
            worker_id,
        ):
            barrier.wait()

            claimed = (
                BackgroundJobService
                .claim_next_job(
                    worker_id=worker_id,
                    lease_seconds=300,
                )
            )

            return (
                str(claimed.id)
                if claimed
                else None
            )

        with ThreadPoolExecutor(
            max_workers=2,
        ) as executor:
            results = list(
                executor.map(
                    claim,
                    [
                        "day53-worker-a",
                        "day53-worker-b",
                    ],
                )
            )

        winners = [
            result
            for result in results
            if result is not None
        ]

        self.assertEqual(
            len(winners),
            1,
        )

        self.assertEqual(
            winners[0],
            str(job.id),
        )

        job.reload()

        self.assertEqual(
            job.status,
            "RUNNING",
        )

        self.assertEqual(
            job.attempts,
            1,
        )

        self.assertIn(
            job.worker_id,
            {
                "day53-worker-a",
                "day53-worker-b",
            },
        )

        self.assertIsNotNone(
            job.locked_at
        )

        self.assertIsNotNone(
            job.lock_expires_at
        )

    # ==========================================
    # MANY WORKERS / ONE JOB
    # ==========================================

    def test_many_workers_still_produce_one_winner(
        self,
    ):
        job = self._create_job(
            "many-workers-one-job"
        )

        worker_count = 8
        barrier = Barrier(
            worker_count
        )

        def claim(
            worker_number,
        ):
            barrier.wait()

            claimed = (
                BackgroundJobService
                .claim_next_job(
                    worker_id=(
                        "day53-many-worker-"
                        f"{worker_number}"
                    ),
                    lease_seconds=300,
                )
            )

            return (
                str(claimed.id)
                if claimed
                else None
            )

        with ThreadPoolExecutor(
            max_workers=worker_count,
        ) as executor:
            results = list(
                executor.map(
                    claim,
                    range(worker_count),
                )
            )

        winners = [
            result
            for result in results
            if result is not None
        ]

        self.assertEqual(
            winners,
            [
                str(job.id),
            ],
        )

        job.reload()

        self.assertEqual(
            job.status,
            "RUNNING",
        )

        self.assertEqual(
            job.attempts,
            1,
        )

    # ==========================================
    # MANY WORKERS / MANY JOBS
    # ==========================================

    def test_concurrent_workers_claim_each_job_at_most_once(
        self,
    ):
        jobs = [
            self._create_job(
                f"multi-job-{index}"
            )
            for index in range(5)
        ]

        worker_count = 10
        barrier = Barrier(
            worker_count
        )

        def claim(
            worker_number,
        ):
            barrier.wait()

            claimed = (
                BackgroundJobService
                .claim_next_job(
                    worker_id=(
                        "day53-pool-worker-"
                        f"{worker_number}"
                    ),
                    lease_seconds=300,
                )
            )

            return (
                str(claimed.id)
                if claimed
                else None
            )

        with ThreadPoolExecutor(
            max_workers=worker_count,
        ) as executor:
            results = list(
                executor.map(
                    claim,
                    range(worker_count),
                )
            )

        claimed_ids = [
            result
            for result in results
            if result is not None
        ]

        expected_ids = {
            str(job.id)
            for job in jobs
        }

        self.assertEqual(
            len(claimed_ids),
            5,
        )

        self.assertEqual(
            len(set(claimed_ids)),
            5,
        )

        self.assertEqual(
            set(claimed_ids),
            expected_ids,
        )

        for job in jobs:
            job.reload()

            self.assertEqual(
                job.status,
                "RUNNING",
            )

            self.assertEqual(
                job.attempts,
                1,
            )

    # ==========================================
    # CONCURRENT IDEMPOTENT CREATION
    # ==========================================

    def test_concurrent_duplicate_idempotency_key_creates_one_job(
        self,
    ):
        worker_count = 8

        barrier = Barrier(
            worker_count
        )

        idempotency_key = (
            f"day53-idempotent-"
            f"{self.test_key}"
        )

        def create_job(
            worker_number,
        ):
            barrier.wait()

            job = (
                BackgroundJobService
                .create_job(
                    organization=
                        self.organization,
                    created_by=
                        self.user,
                    job_type="NOTIFICATION",
                    payload={
                        "worker":
                            worker_number,
                    },
                    idempotency_key=
                        idempotency_key,
                )
            )

            return str(
                job.id
            )

        with ThreadPoolExecutor(
            max_workers=worker_count,
        ) as executor:
            results = list(
                executor.map(
                    create_job,
                    range(worker_count),
                )
            )

        self.assertEqual(
            len(results),
            worker_count,
        )

        self.assertEqual(
            len(
                set(results)
            ),
            1,
        )

        jobs = (
            BackgroundJob.objects(
                organization=
                    self.organization,
                idempotency_key=
                    idempotency_key,
            )
        )

        self.assertEqual(
            jobs.count(),
            1,
        )

    def test_same_idempotency_key_is_still_isolated_by_organization(
        self,
    ):
        second_organization = (
            Organization(
                name=(
                    "Day 53 Concurrent "
                    "Second Organization "
                    f"{self.test_key}"
                ),
                email=(
                    f"day53-second-org-"
                    f"{self.test_key}"
                    "@example.com"
                ),
            )
        )
        second_organization.save()

        second_user = User(
            organization=
                second_organization,
            email=(
                f"day53-second-user-"
                f"{self.test_key}"
                "@example.com"
            ),
            password=
                "day53-test-password",
            first_name="Day",
            last_name="FiftyThree",
            is_active=True,
        )
        second_user.save()

        idempotency_key = (
            f"day53-cross-org-key-"
            f"{self.test_key}"
        )

        barrier = Barrier(2)

        def create_for_org(
            args,
        ):
            organization, user = args

            barrier.wait()

            job = (
                BackgroundJobService
                .create_job(
                    organization=
                        organization,
                    created_by=
                        user,
                    job_type=
                        "NOTIFICATION",
                    payload={
                        "test":
                            "cross-org-key",
                    },
                    idempotency_key=
                        idempotency_key,
                )
            )

            return str(
                job.id
            )

        try:
            with ThreadPoolExecutor(
                max_workers=2,
            ) as executor:
                results = list(
                    executor.map(
                        create_for_org,
                        [
                            (
                                self.organization,
                                self.user,
                            ),
                            (
                                second_organization,
                                second_user,
                            ),
                        ],
                    )
                )

            self.assertEqual(
                len(results),
                2,
            )

            self.assertEqual(
                len(
                    set(results)
                ),
                2,
            )

            self.assertEqual(
                BackgroundJob.objects(
                    idempotency_key=
                        idempotency_key,
                ).count(),
                2,
            )

            self.assertEqual(
                BackgroundJob.objects(
                    organization=
                        self.organization,
                    idempotency_key=
                        idempotency_key,
                ).count(),
                1,
            )

            self.assertEqual(
                BackgroundJob.objects(
                    organization=
                        second_organization,
                    idempotency_key=
                        idempotency_key,
                ).count(),
                1,
            )

        finally:
            BackgroundJob.objects(
                organization=
                    second_organization,
            ).delete()

            User.objects(
                organization=
                    second_organization,
            ).delete()

            second_organization.delete()

    def test_repository_duplicate_recovery_returns_existing_job(
        self,
    ):
        idempotency_key = (
            f"day53-repository-duplicate-"
            f"{self.test_key}"
        )

        original = (
            BackgroundJobRepository
            .create(
                organization=
                    self.organization,
                created_by=
                    self.user,
                job_type=
                    "NOTIFICATION",
                payload={
                    "source":
                        "original",
                },
                idempotency_key=
                    idempotency_key,
                max_attempts=3,
            )
        )

        duplicate = (
            BackgroundJobRepository
            .create(
                organization=
                    self.organization,
                created_by=
                    self.user,
                job_type=
                    "NOTIFICATION",
                payload={
                    "source":
                        "duplicate",
                },
                idempotency_key=
                    idempotency_key,
                max_attempts=3,
            )
        )

        self.assertEqual(
            str(original.id),
            str(duplicate.id),
        )

        self.assertEqual(
            BackgroundJob.objects(
                organization=
                    self.organization,
                idempotency_key=
                    idempotency_key,
            ).count(),
            1,
        )

    # ==========================================
    # CONCURRENT NOTIFICATION IDEMPOTENCY
    # ==========================================

    def test_concurrent_duplicate_notification_key_creates_one_notification(
        self,
    ):
        worker_count = 8

        barrier = Barrier(
            worker_count
        )

        background_job_key = (
            f"day53-notification-"
            f"{self.test_key}"
        )

        def create_notification(
            worker_number,
        ):
            barrier.wait()

            notification = (
                NotificationService
                .create_notification(
                    organization=
                        self.organization,
                    recipient=
                        self.user,
                    notification_type=
                        "SYSTEM",
                    title=(
                        "Concurrent "
                        "notification"
                    ),
                    message=(
                        "Created by worker "
                        f"{worker_number}."
                    ),
                    severity="INFO",
                    background_job_key=
                        background_job_key,
                )
            )

            return str(
                notification.id
            )

        with ThreadPoolExecutor(
            max_workers=worker_count,
        ) as executor:
            results = list(
                executor.map(
                    create_notification,
                    range(worker_count),
                )
            )

        self.assertEqual(
            len(results),
            worker_count,
        )

        self.assertEqual(
            len(
                set(results)
            ),
            1,
        )

        notifications = (
            Notification.objects(
                organization=
                    self.organization,
                background_job_key=
                    background_job_key,
            )
        )

        self.assertEqual(
            notifications.count(),
            1,
        )

    # ==========================================
    # CRASH / LEASE RECOVERY
    # ==========================================

    def test_expired_running_job_is_recovered_without_resetting_attempts(
        self,
    ):
        job = self._create_job(
            "expired-running-job"
        )

        claimed = (
            BackgroundJobService
            .claim_next_job(
                worker_id=
                    "day53-crashed-worker",
                lease_seconds=300,
            )
        )

        self.assertIsNotNone(
            claimed
        )

        self.assertEqual(
            str(claimed.id),
            str(job.id),
        )

        claimed.reload()

        self.assertEqual(
            claimed.status,
            "RUNNING",
        )

        self.assertEqual(
            claimed.attempts,
            1,
        )

        claimed.lock_expires_at = (
            datetime.utcnow()
            - timedelta(
                seconds=1
            )
        )
        claimed.save()

        recovered_count = (
            BackgroundJobService
            .recover_expired_jobs()
        )

        self.assertEqual(
            recovered_count,
            1,
        )

        claimed.reload()

        self.assertEqual(
            claimed.status,
            "PENDING",
        )

        self.assertEqual(
            claimed.attempts,
            1,
        )

        self.assertIsNone(
            claimed.worker_id
        )

        self.assertIsNone(
            claimed.locked_at
        )

        self.assertIsNone(
            claimed.lock_expires_at
        )

    def test_recovered_job_can_be_claimed_by_new_worker_and_attempt_increments_once(
        self,
    ):
        job = self._create_job(
            "recover-and-reclaim"
        )

        first_claim = (
            BackgroundJobService
            .claim_next_job(
                worker_id=
                    "day53-worker-before-crash",
                lease_seconds=300,
            )
        )

        self.assertEqual(
            str(first_claim.id),
            str(job.id),
        )

        first_claim.reload()

        self.assertEqual(
            first_claim.attempts,
            1,
        )

        first_claim.lock_expires_at = (
            datetime.utcnow()
            - timedelta(
                seconds=1
            )
        )
        first_claim.save()

        recovered_count = (
            BackgroundJobService
            .recover_expired_jobs()
        )

        self.assertEqual(
            recovered_count,
            1,
        )

        second_claim = (
            BackgroundJobService
            .claim_next_job(
                worker_id=
                    "day53-worker-after-crash",
                lease_seconds=300,
            )
        )

        self.assertIsNotNone(
            second_claim
        )

        self.assertEqual(
            str(second_claim.id),
            str(job.id),
        )

        second_claim.reload()

        self.assertEqual(
            second_claim.status,
            "RUNNING",
        )

        self.assertEqual(
            second_claim.attempts,
            2,
        )

        self.assertEqual(
            second_claim.worker_id,
            "day53-worker-after-crash",
        )

    # ==========================================
    # RETRY ATTEMPT PRESERVATION
    # ==========================================

    def test_automatic_retry_preserves_attempt_count_before_next_claim(
        self,
    ):
        job = self._create_job(
            "automatic-retry"
        )

        claimed = (
            BackgroundJobService
            .claim_next_job(
                worker_id=
                    "day53-failing-worker",
                lease_seconds=300,
            )
        )

        self.assertEqual(
            str(claimed.id),
            str(job.id),
        )

        self.assertEqual(
            claimed.attempts,
            1,
        )

        retrying = (
            BackgroundJobService
            .handle_failure(
                job=claimed,
                error=(
                    "Day 53 simulated "
                    "worker failure."
                ),
            )
        )

        retrying.reload()

        self.assertEqual(
            retrying.status,
            "RETRYING",
        )

        self.assertEqual(
            retrying.attempts,
            1,
        )

        self.assertIsNotNone(
            retrying.available_at
        )

        # Make the scheduled retry due now.
        retrying.available_at = (
            datetime.utcnow()
            - timedelta(
                seconds=1
            )
        )
        retrying.save()

        requeued = (
            BackgroundJobService
            .requeue_retrying_job(
                job=retrying,
            )
        )

        requeued.reload()

        self.assertEqual(
            requeued.status,
            "PENDING",
        )

        self.assertEqual(
            requeued.attempts,
            1,
        )

        second_claim = (
            BackgroundJobService
            .claim_next_job(
                worker_id=
                    "day53-retry-worker",
                lease_seconds=300,
            )
        )

        self.assertIsNotNone(
            second_claim
        )

        self.assertEqual(
            str(second_claim.id),
            str(job.id),
        )

        second_claim.reload()

        self.assertEqual(
            second_claim.status,
            "RUNNING",
        )

        self.assertEqual(
            second_claim.attempts,
            2,
        )