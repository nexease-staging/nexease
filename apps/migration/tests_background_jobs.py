from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from apps.core.services.background_job_executor import (
    BackgroundJobExecutor,
)
from apps.migration.background_jobs import (
    _get_batch_id,
    execute_migration_import,
    execute_migration_validation,
    register_migration_background_jobs,
)

class MigrationBackgroundJobsTestCase(
    TestCase,
):

    def setUp(self):
        self.organization = (
            SimpleNamespace(
                id="organization-1",
            )
        )

        self.job = SimpleNamespace(
            organization=self.organization,
            payload={
                "batch_id": "batch-1",
            },
        )

    # ==============================================
    # PAYLOAD
    # ==============================================

    def test_get_batch_id(
        self,
    ):
        result = _get_batch_id(
            job=self.job,
        )

        self.assertEqual(
            result,
            "batch-1",
        )

    def test_get_batch_id_rejects_missing_id(
        self,
    ):
        job = SimpleNamespace(
            organization=self.organization,
            payload={},
        )

        with self.assertRaisesRegex(
            ValueError,
            "Migration batch ID is required",
        ):
            _get_batch_id(
                job=job,
            )

    # ==============================================
    # VALIDATION JOB
    # ==============================================

    @patch(
        "apps.migration.background_jobs."
        "MigrationAPIService.validate_batch"
    )
    def test_validation_job(
        self,
        validate_mock,
    ):
        batch = SimpleNamespace(
            id="batch-1",
            status="VALIDATED",
            migration_type="PRODUCTS",
        )

        validate_mock.return_value = {
            "batch": batch,
            "validation": {
                "total_rows": 10,
                "valid_rows": 8,
                "invalid_rows": 2,
                "can_import": False,
            },
        }

        result = (
            execute_migration_validation(
                job=self.job,
            )
        )

        validate_mock.assert_called_once_with(
            organization=self.organization,
            batch_id="batch-1",
        )

        self.assertEqual(
            result,
            {
                "batch_id": "batch-1",
                "status": "VALIDATED",
                "migration_type": "PRODUCTS",
                "total_rows": 10,
                "valid_rows": 8,
                "invalid_rows": 2,
                "can_import": False,
            },
        )

    # ==============================================
    # IMPORT JOB
    # ==============================================

    @patch(
        "apps.migration.background_jobs."
        "MigrationAPIService.import_batch"
    )
    def test_import_job(
        self,
        import_mock,
    ):
        expected = {
            "batch_id": "batch-1",
            "status": "COMPLETED",
            "imported_rows": 8,
            "skipped_rows": 2,
            "failed_rows": 0,
        }

        import_mock.return_value = expected

        result = (
            execute_migration_import(
                job=self.job,
            )
        )

        import_mock.assert_called_once_with(
            organization=self.organization,
            batch_id="batch-1",
        )

        self.assertIs(
            result,
            expected,
        )

    @patch(
        "apps.migration.background_jobs."
        "MigrationAPIService.import_batch"
    )
    def test_import_job_rejects_invalid_result(
        self,
        import_mock,
    ):
        import_mock.return_value = None

        with self.assertRaisesRegex(
            ValueError,
            "invalid result",
        ):
            execute_migration_import(
                job=self.job,
            )

    def test_register_migration_background_jobs(
        self,
    ):
        register_migration_background_jobs()

        registered = (
            BackgroundJobExecutor
            .registered_job_types()
        )

        self.assertIn(
            "DATA_MIGRATION_VALIDATE",
            registered,
        )

        self.assertIn(
            "DATA_MIGRATION_IMPORT",
            registered,
        )

        # Registration must remain idempotent.
        register_migration_background_jobs()

        registered_again = (
            BackgroundJobExecutor
            .registered_job_types()
        )

        self.assertEqual(
            registered,
            registered_again,
        )


    @patch(
        "apps.migration.background_jobs."
        "MigrationAPIService.validate_batch"
    )
    def test_executor_dispatches_validation_job(
        self,
        validate_mock,
    ):
        register_migration_background_jobs()

        batch = SimpleNamespace(
            id="batch-1",
            status="VALIDATED",
            migration_type="PRODUCTS",
        )

        validate_mock.return_value = {
            "batch": batch,
            "validation": {
                "total_rows": 1,
                "valid_rows": 1,
                "invalid_rows": 0,
                "can_import": True,
            },
        }

        job = SimpleNamespace(
            job_type=(
                "DATA_MIGRATION_VALIDATE"
            ),
            organization=self.organization,
            payload={
                "batch_id": "batch-1",
            },
        )

        result = (
            BackgroundJobExecutor
            .execute(
                job=job,
            )
        )

        validate_mock.assert_called_once_with(
            organization=self.organization,
            batch_id="batch-1",
        )

        self.assertEqual(
            result["batch_id"],
            "batch-1",
        )

        self.assertEqual(
            result["status"],
            "VALIDATED",
        )

        self.assertTrue(
            result["can_import"]
        )