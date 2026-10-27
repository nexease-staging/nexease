from datetime import (
    datetime,
    timedelta,
)
from types import SimpleNamespace
from unittest.mock import (
    Mock,
    patch,
)

from bson import ObjectId
from django.test import SimpleTestCase

from apps.core.repositories.background_job_repository import (
    BackgroundJobRepository,
)
from apps.core.services.background_job_executor import (
    BackgroundJobExecutor,
)
from apps.core.services.background_job_service import (
    BackgroundJobService,
)
from apps.core.services.notification_service import (
    NotificationService,
)


class BackgroundJobServiceTests(
    SimpleTestCase
):

    def setUp(self):
        self.organization = SimpleNamespace(
            id=ObjectId(),
        )

        self.user = SimpleNamespace(
            id=ObjectId(),
            organization=self.organization,
            is_active=True,
        )

        self.job = SimpleNamespace(
            id=ObjectId(),
            organization=self.organization,
            created_by=self.user,
            job_type="NOTIFICATION",
            status="RUNNING",
            attempts=1,
            max_attempts=3,
            available_at=datetime.utcnow(),
            started_at=datetime.utcnow(),
            completed_at=None,
            result={},
            last_error=None,
        )

    # ==================================================
    # CREATE / IDEMPOTENCY CONTRACT
    # ==================================================

    @patch.object(
        BackgroundJobRepository,
        "create",
    )
    def test_create_job_passes_normalized_contract(
        self,
        create_mock,
    ):
        expected_job = object()

        create_mock.return_value = (
            expected_job
        )

        result = (
            BackgroundJobService
            .create_job(
                organization=
                    self.organization,

                created_by=
                    self.user,

                job_type=
                    " notification ",

                payload={
                    "message": "Test",
                },

                idempotency_key=
                    " test-key ",

                max_attempts=4,
            )
        )

        self.assertIs(
            result,
            expected_job,
        )

        create_mock.assert_called_once_with(
            organization=
                self.organization,

            created_by=
                self.user,

            job_type=
                "NOTIFICATION",

            payload={
                "message": "Test",
            },

            idempotency_key=
                "test-key",

            max_attempts=4,
        )

    def test_create_job_rejects_invalid_type(
        self,
    ):
        with self.assertRaisesRegex(
            ValueError,
            "Invalid background job type",
        ):
            (
                BackgroundJobService
                .create_job(
                    organization=
                        self.organization,

                    created_by=
                        self.user,

                    job_type="UNKNOWN",

                    payload={},

                    idempotency_key=
                        "test-key",
                )
            )

    def test_create_job_rejects_non_dict_payload(
        self,
    ):
        with self.assertRaisesRegex(
            ValueError,
            "must be a dictionary",
        ):
            (
                BackgroundJobService
                .create_job(
                    organization=
                        self.organization,

                    created_by=
                        self.user,

                    job_type=
                        "NOTIFICATION",

                    payload="invalid",

                    idempotency_key=
                        "test-key",
                )
            )

    # ==================================================
    # CLAIM
    # ==================================================

    @patch.object(
        BackgroundJobRepository,
        "claim_next",
    )
    def test_claim_next_job_delegates_to_atomic_repository(
        self,
        claim_mock,
    ):
        expected_job = object()

        claim_mock.return_value = (
            expected_job
        )

        result = (
            BackgroundJobService
            .claim_next_job(
                worker_id=
                    "worker-test",

                lease_seconds=60,
            )
        )

        self.assertIs(
            result,
            expected_job,
        )

        claim_mock.assert_called_once_with(
            worker_id="worker-test",
            lease_seconds=60,
        )

    def test_claim_next_job_rejects_short_lease(
        self,
    ):
        with self.assertRaisesRegex(
            ValueError,
            "at least 30",
        ):
            (
                BackgroundJobService
                .claim_next_job(
                    worker_id=
                        "worker-test",

                    lease_seconds=10,
                )
            )

    # ==================================================
    # AUTOMATIC FAILURE / RETRY
    # ==================================================

    @patch.object(
        BackgroundJobRepository,
        "mark_retrying",
    )
    def test_failure_schedules_retry_before_max_attempts(
        self,
        retry_mock,
    ):
        retry_mock.side_effect = (
            lambda **kwargs:
                kwargs["job"]
        )

        before = datetime.utcnow()

        result = (
            BackgroundJobService
            .handle_failure(
                job=self.job,
                error=RuntimeError(
                    "temporary failure"
                ),
            )
        )

        after = datetime.utcnow()

        self.assertIs(
            result,
            self.job,
        )

        retry_mock.assert_called_once()

        call = (
            retry_mock.call_args.kwargs
        )

        self.assertIs(
            call["job"],
            self.job,
        )

        self.assertEqual(
            call["error_message"],
            "temporary failure",
        )

        expected_minimum = (
            before
            + timedelta(seconds=30)
        )

        expected_maximum = (
            after
            + timedelta(seconds=30)
        )

        self.assertGreaterEqual(
            call["available_at"],
            expected_minimum,
        )

        self.assertLessEqual(
            call["available_at"],
            expected_maximum,
        )

        # Automatic retry must not reset
        # the attempt counter.
        self.assertEqual(
            self.job.attempts,
            1,
        )

    @patch.object(
        BackgroundJobRepository,
        "mark_retrying",
    )
    def test_second_failure_uses_120_second_delay(
        self,
        retry_mock,
    ):
        self.job.attempts = 2

        retry_mock.side_effect = (
            lambda **kwargs:
                kwargs["job"]
        )

        before = datetime.utcnow()

        (
            BackgroundJobService
            .handle_failure(
                job=self.job,
                error="second failure",
            )
        )

        after = datetime.utcnow()

        available_at = (
            retry_mock
            .call_args
            .kwargs[
                "available_at"
            ]
        )

        self.assertGreaterEqual(
            available_at,
            before
            + timedelta(seconds=120),
        )

        self.assertLessEqual(
            available_at,
            after
            + timedelta(seconds=120),
        )

    @patch.object(
        BackgroundJobRepository,
        "mark_failed",
    )
    def test_failure_exhaustion_marks_job_failed(
        self,
        failed_mock,
    ):
        self.job.attempts = 3
        self.job.max_attempts = 3

        failed_mock.side_effect = (
            lambda **kwargs:
                kwargs["job"]
        )

        result = (
            BackgroundJobService
            .handle_failure(
                job=self.job,
                error=RuntimeError(
                    "permanent failure"
                ),
            )
        )

        self.assertIs(
            result,
            self.job,
        )

        failed_mock.assert_called_once_with(
            job=self.job,
            error_message=
                "permanent failure",
        )

    # ==================================================
    # RETRYING -> PENDING
    # ==================================================

    @patch.object(
        BackgroundJobRepository,
        "requeue",
    )
    def test_retrying_job_requeues_when_due(
        self,
        requeue_mock,
    ):
        self.job.status = "RETRYING"

        self.job.available_at = (
            datetime.utcnow()
            - timedelta(seconds=1)
        )

        requeue_mock.return_value = (
            self.job
        )

        result = (
            BackgroundJobService
            .requeue_retrying_job(
                job=self.job,
            )
        )

        self.assertIs(
            result,
            self.job,
        )

        requeue_mock.assert_called_once_with(
            job=self.job,
        )

    @patch.object(
        BackgroundJobRepository,
        "requeue",
    )
    def test_retrying_job_waits_until_available(
        self,
        requeue_mock,
    ):
        self.job.status = "RETRYING"

        self.job.available_at = (
            datetime.utcnow()
            + timedelta(minutes=5)
        )

        result = (
            BackgroundJobService
            .requeue_retrying_job(
                job=self.job,
            )
        )

        self.assertIs(
            result,
            self.job,
        )

        requeue_mock.assert_not_called()

    # ==================================================
    # MANUAL RETRY
    # ==================================================

    @patch.object(
        BackgroundJobRepository,
        "retry_failed",
    )
    def test_manual_retry_accepts_owned_failed_job(
        self,
        retry_mock,
    ):
        self.job.status = "FAILED"

        retry_mock.return_value = (
            self.job
        )

        result = (
            BackgroundJobService
            .retry_failed_job(
                user=self.user,
                job=self.job,
            )
        )

        self.assertIs(
            result,
            self.job,
        )

        retry_mock.assert_called_once_with(
            job=self.job,
        )

    def test_manual_retry_rejects_non_failed_job(
        self,
    ):
        self.job.status = "SUCCEEDED"

        with self.assertRaisesRegex(
            ValueError,
            "Only a failed background job",
        ):
            (
                BackgroundJobService
                .retry_failed_job(
                    user=self.user,
                    job=self.job,
                )
            )

    def test_manual_retry_rejects_other_organization(
        self,
    ):
        self.job.status = "FAILED"

        other_organization = (
            SimpleNamespace(
                id=ObjectId(),
            )
        )

        other_user = SimpleNamespace(
            id=ObjectId(),
            organization=
                other_organization,
            is_active=True,
        )

        with self.assertRaisesRegex(
            PermissionError,
            "does not belong to this organization",
        ):
            (
                BackgroundJobService
                .retry_failed_job(
                    user=other_user,
                    job=self.job,
                )
            )

    def test_manual_retry_rejects_other_creator(
        self,
    ):
        self.job.status = "FAILED"

        other_user = SimpleNamespace(
            id=ObjectId(),
            organization=
                self.organization,
            is_active=True,
        )

        with self.assertRaisesRegex(
            PermissionError,
            "does not belong to this user",
        ):
            (
                BackgroundJobService
                .retry_failed_job(
                    user=other_user,
                    job=self.job,
                )
            )

    # ==================================================
    # EXPIRED JOB RECOVERY
    # ==================================================

    @patch.object(
        BackgroundJobRepository,
        "recover_expired_jobs",
    )
    def test_recover_expired_jobs_delegates_to_repository(
        self,
        recover_mock,
    ):
        recover_mock.return_value = 2

        result = (
            BackgroundJobService
            .recover_expired_jobs()
        )

        self.assertEqual(
            result,
            2,
        )

        recover_mock.assert_called_once_with()


class BackgroundJobExecutorTests(
    SimpleTestCase
):

    def tearDown(self):
        BackgroundJobExecutor.clear()

    def test_execute_registered_handler(
        self,
    ):
        handler = Mock(
            return_value={
                "ok": True,
            }
        )

        BackgroundJobExecutor.register(
            "NOTIFICATION",
            handler,
        )

        job = SimpleNamespace(
            job_type="NOTIFICATION",
        )

        result = (
            BackgroundJobExecutor
            .execute(
                job=job,
            )
        )

        self.assertEqual(
            result,
            {
                "ok": True,
            },
        )

        handler.assert_called_once_with(
            job=job,
        )

    def test_duplicate_handler_registration_rejected(
        self,
    ):
        handler = Mock()

        BackgroundJobExecutor.register(
            "NOTIFICATION",
            handler,
        )

        with self.assertRaisesRegex(
            ValueError,
            "already registered",
        ):
            (
                BackgroundJobExecutor
                .register(
                    "NOTIFICATION",
                    handler,
                )
            )

    def test_missing_handler_rejected(
        self,
    ):
        job = SimpleNamespace(
            job_type="NOTIFICATION",
        )

        with self.assertRaisesRegex(
            ValueError,
            "No background job handler",
        ):
            (
                BackgroundJobExecutor
                .execute(
                    job=job,
                )
            )


class NotificationIdempotencyTests(
    SimpleTestCase
):

    def setUp(self):
        self.organization = (
            SimpleNamespace(
                id=ObjectId(),
            )
        )

        self.recipient = (
            SimpleNamespace(
                id=ObjectId(),
                organization=
                    self.organization,
                is_active=True,
            )
        )

    @patch(
        "apps.core.services."
        "notification_service."
        "NotificationRepository.create"
    )
    @patch(
        "apps.core.services."
        "notification_service."
        "NotificationRepository."
        "get_by_background_job_key"
    )
    def test_notification_replay_returns_existing_notification(
        self,
        get_existing_mock,
        create_mock,
    ):
        existing = SimpleNamespace(
            id=ObjectId(),
        )

        get_existing_mock.return_value = (
            existing
        )

        result = (
            NotificationService
            .create_notification(
                organization=
                    self.organization,

                recipient=
                    self.recipient,

                notification_type=
                    "SYSTEM",

                title="Test",
                message="Test message",

                background_job_key=
                    "notification-job-1",
            )
        )

        self.assertIs(
            result,
            existing,
        )

        create_mock.assert_not_called()

        get_existing_mock.assert_called_once_with(
            organization=
                self.organization,

            background_job_key=
                "notification-job-1",
        )