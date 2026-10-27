from datetime import (
    datetime,
    timedelta,
)
from uuid import uuid4

from django.test import SimpleTestCase

from apps.accounts.models import User
from apps.core.background_job_models import (
    BackgroundJob,
)
from apps.core.repositories.background_job_repository import (
    BackgroundJobRepository,
)
from apps.organizations.models import Organization


class BackgroundJobRepositoryTests(
    SimpleTestCase
):

    def setUp(self):
        self.test_key = (
            f"repository-test-{uuid4().hex}"
        )

        self.organization = (
            Organization(
                name=(
                    "Background Job "
                    "Repository Test"
                ),
                email=(
                    f"{self.test_key}"
                    "@example.com"
                ),
            )
        )

        self.organization.save()

        self.user = User(
            organization=
                self.organization,

            email=(
                f"user-{self.test_key}"
                "@example.com"
            ),

            password="test-password",

            first_name="Repository",
            last_name="Tester",
        )

        self.user.save()

    def tearDown(self):
        BackgroundJob.objects(
            organization=
                self.organization,
        ).delete()

        User.objects(
            organization=
                self.organization,
        ).delete()

        self.organization.delete()

    def create_job(
        self,
        *,
        idempotency_key=None,
        max_attempts=3,
    ):
        return (
            BackgroundJobRepository
            .create(
                organization=
                    self.organization,

                created_by=
                    self.user,

                job_type=
                    "NOTIFICATION",

                payload={
                    "title": "Repository test",
                },

                idempotency_key=(
                    idempotency_key
                    or
                    f"{self.test_key}-job"
                ),

                max_attempts=
                    max_attempts,
            )
        )

    # ==================================================
    # CREATE / IDEMPOTENCY
    # ==================================================

    def test_duplicate_idempotency_key_returns_same_job(
        self,
    ):
        first = self.create_job(
            idempotency_key=
                f"{self.test_key}-duplicate",
        )

        second = self.create_job(
            idempotency_key=
                f"{self.test_key}-duplicate",
        )

        self.assertEqual(
            str(first.id),
            str(second.id),
        )

        count = (
            BackgroundJob.objects(
                organization=
                    self.organization,

                idempotency_key=
                    f"{self.test_key}-duplicate",
            )
            .count()
        )

        self.assertEqual(
            count,
            1,
        )

    def test_same_idempotency_key_allowed_for_other_organization(
        self,
    ):
        second_organization = (
            Organization(
                name="Second Test Organization",
                email=(
                    f"second-{self.test_key}"
                    "@example.com"
                ),
            )
        )

        second_organization.save()

        second_user = User(
            organization=
                second_organization,

            email=(
                f"second-user-{self.test_key}"
                "@example.com"
            ),

            password="test-password",

            first_name="Second",
            last_name="Tester",
        )

        second_user.save()

        try:
            key = (
                f"{self.test_key}-shared"
            )

            first = (
                BackgroundJobRepository
                .create(
                    organization=
                        self.organization,

                    created_by=
                        self.user,

                    job_type=
                        "NOTIFICATION",

                    payload={},

                    idempotency_key=
                        key,
                )
            )

            second = (
                BackgroundJobRepository
                .create(
                    organization=
                        second_organization,

                    created_by=
                        second_user,

                    job_type=
                        "NOTIFICATION",

                    payload={},

                    idempotency_key=
                        key,
                )
            )

            self.assertNotEqual(
                str(first.id),
                str(second.id),
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

    # ==================================================
    # ATOMIC CLAIM
    # ==================================================

    def test_claim_next_moves_pending_job_to_running(
        self,
    ):
        job = self.create_job(
            idempotency_key=
                f"{self.test_key}-claim",
        )

        claimed = (
            BackgroundJobRepository
            .claim_next(
                worker_id=
                    "repository-test-worker",

                lease_seconds=60,
            )
        )

        self.assertIsNotNone(
            claimed
        )

        self.assertEqual(
            str(claimed.id),
            str(job.id),
        )

        self.assertEqual(
            claimed.status,
            "RUNNING",
        )

        self.assertEqual(
            claimed.attempts,
            1,
        )

        self.assertEqual(
            claimed.worker_id,
            "repository-test-worker",
        )

        self.assertIsNotNone(
            claimed.locked_at
        )

        self.assertIsNotNone(
            claimed.lock_expires_at
        )

        self.assertIsNotNone(
            claimed.started_at
        )

    def test_claimed_job_cannot_be_claimed_twice(
        self,
    ):
        job = self.create_job(
            idempotency_key=
                f"{self.test_key}-single-claim",
        )

        first = (
            BackgroundJobRepository
            .claim_next(
                worker_id=
                    "worker-one",

                lease_seconds=60,
            )
        )

        self.assertEqual(
            str(first.id),
            str(job.id),
        )

        second = (
            BackgroundJobRepository
            .claim_next(
                worker_id=
                    "worker-two",

                lease_seconds=60,
            )
        )

        self.assertIsNone(
            second
        )

    # ==================================================
    # SUCCESS
    # ==================================================

    def test_mark_succeeded_clears_lock(
        self,
    ):
        self.create_job(
            idempotency_key=
                f"{self.test_key}-success",
        )

        job = (
            BackgroundJobRepository
            .claim_next(
                worker_id=
                    "success-worker",

                lease_seconds=60,
            )
        )

        result = (
            BackgroundJobRepository
            .mark_succeeded(
                job=job,

                result={
                    "value": "done",
                },
            )
        )

        self.assertEqual(
            result.status,
            "SUCCEEDED",
        )

        self.assertEqual(
            result.result,
            {
                "value": "done",
            },
        )

        self.assertIsNotNone(
            result.completed_at
        )

        self.assertIsNone(
            result.worker_id
        )

        self.assertIsNone(
            result.locked_at
        )

        self.assertIsNone(
            result.lock_expires_at
        )

    # ==================================================
    # RETRY
    # ==================================================

    def test_mark_retrying_preserves_attempt_count(
        self,
    ):
        self.create_job(
            idempotency_key=
                f"{self.test_key}-retrying",
        )

        job = (
            BackgroundJobRepository
            .claim_next(
                worker_id=
                    "retry-worker",

                lease_seconds=60,
            )
        )

        self.assertEqual(
            job.attempts,
            1,
        )

        available_at = (
            datetime.utcnow()
            + timedelta(seconds=30)
        )

        result = (
            BackgroundJobRepository
            .mark_retrying(
                job=job,

                error_message=
                    "temporary failure",

                available_at=
                    available_at,
            )
        )

        self.assertEqual(
            result.status,
            "RETRYING",
        )

        self.assertEqual(
            result.attempts,
            1,
        )

        self.assertEqual(
            result.last_error,
            "temporary failure",
        )

        self.assertIsNone(
            result.worker_id
        )

    def test_requeue_keeps_attempt_count(
        self,
    ):
        job = self.create_job(
            idempotency_key=
                f"{self.test_key}-requeue",
        )

        job.status = "RETRYING"
        job.attempts = 2
        job.save()

        result = (
            BackgroundJobRepository
            .requeue(
                job=job,
            )
        )

        self.assertEqual(
            result.status,
            "PENDING",
        )

        self.assertEqual(
            result.attempts,
            2,
        )

    # ==================================================
    # MANUAL RETRY
    # ==================================================

    def test_manual_retry_resets_failed_job(
        self,
    ):
        job = self.create_job(
            idempotency_key=
                f"{self.test_key}-manual",
        )

        job.status = "FAILED"
        job.attempts = 3
        job.last_error = (
            "permanent failure"
        )
        job.result = {
            "partial": True,
        }
        job.started_at = (
            datetime.utcnow()
        )
        job.completed_at = (
            datetime.utcnow()
        )
        job.worker_id = (
            "old-worker"
        )
        job.locked_at = (
            datetime.utcnow()
        )
        job.lock_expires_at = (
            datetime.utcnow()
        )

        job.save()

        result = (
            BackgroundJobRepository
            .retry_failed(
                job=job,
            )
        )

        self.assertEqual(
            result.status,
            "PENDING",
        )

        self.assertEqual(
            result.attempts,
            0,
        )

        self.assertEqual(
            result.result,
            {},
        )

        self.assertIsNone(
            result.last_error
        )

        self.assertIsNone(
            result.started_at
        )

        self.assertIsNone(
            result.completed_at
        )

        self.assertIsNone(
            result.worker_id
        )

        self.assertIsNone(
            result.locked_at
        )

        self.assertIsNone(
            result.lock_expires_at
        )

    # ==================================================
    # FAILED
    # ==================================================

    def test_mark_failed_clears_worker_lock(
        self,
    ):
        self.create_job(
            idempotency_key=
                f"{self.test_key}-failed",
        )

        job = (
            BackgroundJobRepository
            .claim_next(
                worker_id=
                    "failed-worker",

                lease_seconds=60,
            )
        )

        result = (
            BackgroundJobRepository
            .mark_failed(
                job=job,

                error_message=
                    "terminal failure",
            )
        )

        self.assertEqual(
            result.status,
            "FAILED",
        )

        self.assertEqual(
            result.last_error,
            "terminal failure",
        )

        self.assertIsNotNone(
            result.completed_at
        )

        self.assertIsNone(
            result.worker_id
        )

        self.assertIsNone(
            result.locked_at
        )

        self.assertIsNone(
            result.lock_expires_at
        )

    # ==================================================
    # EXPIRED LEASE
    # ==================================================

    def test_recover_expired_running_job(
        self,
    ):
        job = self.create_job(
            idempotency_key=
                f"{self.test_key}-expired",
        )

        job.status = "RUNNING"
        job.attempts = 1
        job.worker_id = (
            "dead-worker"
        )
        job.locked_at = (
            datetime.utcnow()
            - timedelta(minutes=10)
        )
        job.lock_expires_at = (
            datetime.utcnow()
            - timedelta(seconds=1)
        )

        job.save()

        recovered_count = (
            BackgroundJobRepository
            .recover_expired_jobs()
        )

        job.reload()

        self.assertGreaterEqual(
            recovered_count,
            1,
        )

        self.assertEqual(
            job.status,
            "PENDING",
        )

        # Expired lease recovery must
        # preserve attempts.
        self.assertEqual(
            job.attempts,
            1,
        )

        self.assertIsNone(
            job.worker_id
        )

        self.assertIsNone(
            job.locked_at
        )

        self.assertIsNone(
            job.lock_expires_at
        )