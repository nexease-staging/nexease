from io import StringIO
from types import SimpleNamespace
from unittest.mock import (
    call,
    patch,
)

from django.core.management import call_command
from django.test import SimpleTestCase


class BackgroundWorkerCommandTests(
    SimpleTestCase
):

    def run_worker(
        self,
        *,
        lease_seconds=300,
        patch_requeue=True,
    ):
        stdout = StringIO()
        stderr = StringIO()

        if patch_requeue:
            with patch(
                "apps.core.management.commands."
                "run_background_worker."
                "Command._requeue_due_retries"
            ):
                call_command(
                    "run_background_worker",
                    once=True,
                    sleep=0,
                    lease_seconds=lease_seconds,
                    stdout=stdout,
                    stderr=stderr,
                )
        else:
            call_command(
                "run_background_worker",
                once=True,
                sleep=0,
                lease_seconds=lease_seconds,
                stdout=stdout,
                stderr=stderr,
            )

        return (
            stdout.getvalue(),
            stderr.getvalue(),
        )

    # ==================================================
    # NO JOB
    # ==================================================

    @patch(
        "apps.core.management.commands."
        "run_background_worker."
        "register_core_background_jobs"
    )
    @patch(
        "apps.core.management.commands."
        "run_background_worker."
        "register_finance_background_jobs"
    )
    @patch(
        "apps.core.management.commands."
        "run_background_worker."
        "BackgroundJobService"
    )
    def test_once_exits_when_no_job_available(
        self,
        service,
        register_finance,
        register_core,
    ):
        service.claim_next_job.return_value = None

        stdout, stderr = self.run_worker()

        self.assertIn(
            "No background job available.",
            stdout,
        )

        self.assertEqual(
            stderr,
            "",
        )

        service.recover_expired_jobs.assert_called_once()

        service.claim_next_job.assert_called_once()

    # ==================================================
    # SUCCESS
    # ==================================================

    @patch(
        "apps.core.management.commands."
        "run_background_worker."
        "register_core_background_jobs"
    )
    @patch(
        "apps.core.management.commands."
        "run_background_worker."
        "register_finance_background_jobs"
    )
    @patch(
        "apps.core.management.commands."
        "run_background_worker."
        "BackgroundJobExecutor"
    )
    @patch(
        "apps.core.management.commands."
        "run_background_worker."
        "BackgroundJobService"
    )
    def test_successful_job_is_marked_succeeded(
        self,
        service,
        executor,
        register_finance,
        register_core,
    ):
        job = SimpleNamespace(
            id="job-success",
            job_type="NOTIFICATION",
            attempts=1,
            max_attempts=3,
        )

        completed_job = SimpleNamespace(
            id="job-success",
            status="SUCCEEDED",
        )

        service.claim_next_job.return_value = job

        executor.execute.return_value = {
            "notification_id":
                "notification-1",
        }

        service.mark_succeeded.return_value = (
            completed_job
        )

        stdout, stderr = self.run_worker()

        executor.execute.assert_called_once_with(
            job=job,
        )

        service.mark_succeeded.assert_called_once_with(
            job=job,
            result={
                "notification_id":
                    "notification-1",
            },
        )

        service.handle_failure.assert_not_called()

        self.assertIn(
            "Background job completed: job-success",
            stdout,
        )

        self.assertEqual(
            stderr,
            "",
        )

    # ==================================================
    # RETRYABLE FAILURE
    # ==================================================

    @patch(
        "apps.core.management.commands."
        "run_background_worker."
        "register_core_background_jobs"
    )
    @patch(
        "apps.core.management.commands."
        "run_background_worker."
        "register_finance_background_jobs"
    )
    @patch(
        "apps.core.management.commands."
        "run_background_worker."
        "BackgroundJobExecutor"
    )
    @patch(
        "apps.core.management.commands."
        "run_background_worker."
        "BackgroundJobService"
    )
    def test_handler_failure_uses_failure_service(
        self,
        service,
        executor,
        register_finance,
        register_core,
    ):
        job = SimpleNamespace(
            id="job-retry",
            job_type="DOCUMENT_EMAIL",
            attempts=1,
            max_attempts=3,
        )

        retrying_job = SimpleNamespace(
            id="job-retry",
            status="RETRYING",
        )

        error = RuntimeError(
            "Temporary delivery failure"
        )

        service.claim_next_job.return_value = job
        executor.execute.side_effect = error

        service.handle_failure.return_value = (
            retrying_job
        )

        stdout, stderr = self.run_worker()

        service.handle_failure.assert_called_once_with(
            job=job,
            error=error,
        )

        service.mark_succeeded.assert_not_called()

        self.assertIn(
            "Job status: RETRYING",
            stdout,
        )

        self.assertIn(
            "Temporary delivery failure",
            stderr,
        )

    # ==================================================
    # FINAL FAILURE
    # ==================================================

    @patch(
        "apps.core.management.commands."
        "run_background_worker."
        "register_core_background_jobs"
    )
    @patch(
        "apps.core.management.commands."
        "run_background_worker."
        "register_finance_background_jobs"
    )
    @patch(
        "apps.core.management.commands."
        "run_background_worker."
        "BackgroundJobExecutor"
    )
    @patch(
        "apps.core.management.commands."
        "run_background_worker."
        "BackgroundJobService"
    )
    def test_exhausted_failure_reports_failed_status(
        self,
        service,
        executor,
        register_finance,
        register_core,
    ):
        job = SimpleNamespace(
            id="job-failed",
            job_type="BANK_STATEMENT_IMPORT",
            attempts=3,
            max_attempts=3,
        )

        failed_job = SimpleNamespace(
            id="job-failed",
            status="FAILED",
        )

        error = ValueError(
            "Permanent import failure"
        )

        service.claim_next_job.return_value = job
        executor.execute.side_effect = error

        service.handle_failure.return_value = (
            failed_job
        )

        stdout, stderr = self.run_worker()

        service.handle_failure.assert_called_once_with(
            job=job,
            error=error,
        )

        self.assertIn(
            "Job status: FAILED",
            stdout,
        )

        self.assertIn(
            "Permanent import failure",
            stderr,
        )

    # ==================================================
    # DUE RETRIES
    # ==================================================

    @patch(
        "apps.core.management.commands."
        "run_background_worker."
        "register_core_background_jobs"
    )
    @patch(
        "apps.core.management.commands."
        "run_background_worker."
        "register_finance_background_jobs"
    )
    @patch(
        "apps.core.management.commands."
        "run_background_worker."
        "Command._requeue_due_retries"
    )
    @patch(
        "apps.core.management.commands."
        "run_background_worker."
        "BackgroundJobService"
    )
    def test_due_retries_are_requeued_before_claim(
        self,
        service,
        requeue_due_retries,
        register_finance,
        register_core,
    ):
        service.claim_next_job.return_value = None

        self.run_worker(
            patch_requeue=False,
        )

        self.assertTrue(
            requeue_due_retries.called
        )

        self.assertTrue(
            service.recover_expired_jobs.called
        )

        self.assertTrue(
            service.claim_next_job.called
        )

    # ==================================================
    # GRACEFUL SHUTDOWN
    # ==================================================

    @patch(
        "apps.core.management.commands."
        "run_background_worker."
        "register_core_background_jobs"
    )
    @patch(
        "apps.core.management.commands."
        "run_background_worker."
        "register_finance_background_jobs"
    )
    @patch(
        "apps.core.management.commands."
        "run_background_worker."
        "ShutdownStateService"
    )
    @patch(
        "apps.core.management.commands."
        "run_background_worker."
        "BackgroundJobService"
    )
    def test_shutdown_exits_before_claiming_job(
        self,
        service,
        shutdown_state,
        register_finance,
        register_core,
    ):
        shutdown_state.is_shutting_down.return_value = True

        stdout, stderr = self.run_worker()

        self.assertIn(
            "Background worker stopping gracefully.",
            stdout,
        )

        self.assertEqual(
            stderr,
            "",
        )

        service.recover_expired_jobs.assert_not_called()

        service.claim_next_job.assert_not_called()
        
    # ==================================================
    # LEASE
    # ==================================================

    def test_short_lease_is_rejected(
        self,
    ):
        with self.assertRaisesRegex(
            ValueError,
            "Lease seconds must be at least 30",
        ):
            self.run_worker(
                lease_seconds=29,
            )