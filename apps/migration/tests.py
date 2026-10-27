from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import (
    MagicMock,
    Mock,
    patch,
)

from apps.migration.services.migration_batch_service import (
    MigrationBatchService,
)
from apps.migration.repositories.migration_batch_repository import (
    MigrationBatchRepository,
)
from apps.core.background_job_models import (
    BackgroundJob,
)
from apps.core.background_upload_models import (
    BackgroundUpload,
)

class MigrationBatchServiceTestCase(
    TestCase,
):

    def setUp(self):
        self.organization = (
            SimpleNamespace(
                id="organization-1",
            )
        )

        self.user = SimpleNamespace(
            id="user-1",
            organization=self.organization,
            is_active=True,
        )

    def make_batch(
        self,
        *,
        status="CREATED",
        invalid_rows=0,
        valid_rows=0,
    ):
        return SimpleNamespace(
            id="batch-1",
            organization=self.organization,
            created_by=self.user,
            status=status,
            invalid_rows=invalid_rows,
            valid_rows=valid_rows,
        )

    # ==============================================
    # CREATE
    # ==============================================

    @patch(
        "apps.migration.services."
        "migration_batch_service."
        "MigrationBatchRepository.create"
    )
    def test_create_batch_normalizes_values(
        self,
        create_mock,
    ):
        expected = object()

        create_mock.return_value = expected

        result = (
            MigrationBatchService
            .create_batch(
                organization=(
                    self.organization
                ),
                created_by=self.user,
                source_system=(
                    " zoho_inventory "
                ),
                migration_type=(
                    " products "
                ),
            )
        )

        self.assertIs(
            result,
            expected,
        )

        create_mock.assert_called_once_with(
            organization=self.organization,
            created_by=self.user,
            source_system="ZOHO_INVENTORY",
            migration_type="PRODUCTS",
            mapping=None,
            options=None,
        )

    def test_create_batch_rejects_invalid_source(
        self,
    ):
        with self.assertRaises(
            ValueError
        ):
            (
                MigrationBatchService
                .create_batch(
                    organization=(
                        self.organization
                    ),
                    created_by=self.user,
                    source_system=(
                        "UNKNOWN_SYSTEM"
                    ),
                    migration_type=(
                        "PRODUCTS"
                    ),
                )
            )

    def test_create_batch_rejects_invalid_type(
        self,
    ):
        with self.assertRaises(
            ValueError
        ):
            (
                MigrationBatchService
                .create_batch(
                    organization=(
                        self.organization
                    ),
                    created_by=self.user,
                    source_system="GENERIC",
                    migration_type="UNKNOWN",
                )
            )

    def test_create_batch_rejects_other_tenant_user(
        self,
    ):
        other_organization = (
            SimpleNamespace(
                id="organization-2",
            )
        )

        with self.assertRaises(
            PermissionError
        ):
            (
                MigrationBatchService
                .create_batch(
                    organization=(
                        other_organization
                    ),
                    created_by=self.user,
                    source_system="GENERIC",
                    migration_type="PRODUCTS",
                )
            )

    def test_create_batch_rejects_inactive_user(
        self,
    ):
        self.user.is_active = False

        with self.assertRaises(
            ValueError
        ):
            (
                MigrationBatchService
                .create_batch(
                    organization=(
                        self.organization
                    ),
                    created_by=self.user,
                    source_system="GENERIC",
                    migration_type="PRODUCTS",
                )
            )

    # ==============================================
    # UPLOAD
    # ==============================================

    @patch(
        "apps.migration.services."
        "migration_batch_service."
        "MigrationBatchRepository.set_upload"
    )
    def test_attach_upload(
        self,
        set_upload_mock,
    ):
        batch = self.make_batch(
            status="CREATED",
        )

        expected = object()
        set_upload_mock.return_value = (
            expected
        )

        result = (
            MigrationBatchService
            .attach_upload(
                batch=batch,
                upload_id="upload-1",
            )
        )

        self.assertIs(
            result,
            expected,
        )

        set_upload_mock.assert_called_once_with(
            batch=batch,
            upload_id="upload-1",
        )

    def test_attach_upload_requires_created_state(
        self,
    ):
        batch = self.make_batch(
            status="UPLOADED",
        )

        with self.assertRaises(
            ValueError
        ):
            (
                MigrationBatchService
                .attach_upload(
                    batch=batch,
                    upload_id="upload-1",
                )
            )

    # ==============================================
    # VALIDATION
    # ==============================================

    @patch(
        "apps.migration.services."
        "migration_batch_service."
        "MigrationBatchRepository."
        "mark_validating"
    )
    def test_start_validation(
        self,
        mark_mock,
    ):
        batch = self.make_batch(
            status="UPLOADED",
        )

        expected = object()
        mark_mock.return_value = expected

        result = (
            MigrationBatchService
            .start_validation(
                batch=batch,
            )
        )

        self.assertIs(
            result,
            expected,
        )

        mark_mock.assert_called_once_with(
            batch=batch,
        )

    def test_start_validation_rejects_wrong_state(
        self,
    ):
        batch = self.make_batch(
            status="CREATED",
        )

        with self.assertRaises(
            ValueError
        ):
            (
                MigrationBatchService
                .start_validation(
                    batch=batch,
                )
            )

    @patch(
        "apps.migration.services."
        "migration_batch_service."
        "MigrationBatchRepository."
        "mark_validated"
    )
    def test_complete_validation(
        self,
        mark_mock,
    ):
        batch = self.make_batch(
            status="VALIDATING",
        )

        expected = object()
        mark_mock.return_value = expected

        result = (
            MigrationBatchService
            .complete_validation(
                batch=batch,
                total_rows=10,
                valid_rows=8,
                invalid_rows=2,
                validation_result={
                    "errors": [],
                },
            )
        )

        self.assertIs(
            result,
            expected,
        )

        mark_mock.assert_called_once_with(
            batch=batch,
            total_rows=10,
            valid_rows=8,
            invalid_rows=2,
            validation_result={
                "errors": [],
            },
        )

    def test_validation_counts_must_balance(
        self,
    ):
        batch = self.make_batch(
            status="VALIDATING",
        )

        with self.assertRaises(
            ValueError
        ):
            (
                MigrationBatchService
                .complete_validation(
                    batch=batch,
                    total_rows=10,
                    valid_rows=8,
                    invalid_rows=1,
                )
            )

    def test_validation_rejects_negative_counts(
        self,
    ):
        batch = self.make_batch(
            status="VALIDATING",
        )

        with self.assertRaises(
            ValueError
        ):
            (
                MigrationBatchService
                .complete_validation(
                    batch=batch,
                    total_rows=10,
                    valid_rows=11,
                    invalid_rows=-1,
                )
            )

    @patch(
        "apps.migration.services."
        "migration_batch_service."
        "MigrationBatchRepository."
        "mark_failed"
    )
    def test_fail_validation(
        self,
        mark_mock,
    ):
        batch = self.make_batch(
            status="VALIDATING",
        )

        expected = object()
        mark_mock.return_value = expected

        result = (
            MigrationBatchService
            .fail_validation(
                batch=batch,
                error_summary=(
                    "Validation crashed."
                ),
            )
        )

        self.assertIs(
            result,
            expected,
        )

        mark_mock.assert_called_once_with(
            batch=batch,
            error_summary={
                "message":
                    "Validation crashed.",
                "stage":
                    "VALIDATION",
            },
            expected_status=(
                "VALIDATING"
            ),
        )

    # ==============================================
    # IMPORT
    # ==============================================

    @patch(
        "apps.migration.services."
        "migration_batch_service."
        "MigrationBatchRepository."
        "mark_importing"
    )
    def test_start_import(
        self,
        mark_mock,
    ):
        batch = self.make_batch(
            status="VALIDATED",
            invalid_rows=0,
            valid_rows=10,
        )

        expected = object()
        mark_mock.return_value = expected

        result = (
            MigrationBatchService
            .start_import(
                batch=batch,
            )
        )

        self.assertIs(
            result,
            expected,
        )

        mark_mock.assert_called_once_with(
            batch=batch,
        )

    def test_start_import_rejects_invalid_rows(
        self,
    ):
        batch = self.make_batch(
            status="VALIDATED",
            invalid_rows=1,
            valid_rows=9,
        )

        with self.assertRaises(
            ValueError
        ):
            (
                MigrationBatchService
                .start_import(
                    batch=batch,
                )
            )

    def test_start_import_requires_validation(
        self,
    ):
        batch = self.make_batch(
            status="UPLOADED",
        )

        with self.assertRaises(
            ValueError
        ):
            (
                MigrationBatchService
                .start_import(
                    batch=batch,
                )
            )

    @patch(
        "apps.migration.services."
        "migration_batch_service."
        "MigrationBatchRepository."
        "mark_completed"
    )
    def test_complete_import(
        self,
        mark_mock,
    ):
        batch = self.make_batch(
            status="IMPORTING",
            valid_rows=10,
        )

        expected = object()
        mark_mock.return_value = expected

        result = (
            MigrationBatchService
            .complete_import(
                batch=batch,
                imported_rows=8,
                skipped_rows=2,
                failed_rows=0,
                import_result={
                    "processed": 10,
                },
            )
        )

        self.assertIs(
            result,
            expected,
        )

        mark_mock.assert_called_once_with(
            batch=batch,
            imported_rows=8,
            skipped_rows=2,
            failed_rows=0,
            import_result={
                "processed": 10,
            },
        )

    def test_import_counts_cannot_exceed_valid_rows(
        self,
    ):
        batch = self.make_batch(
            status="IMPORTING",
            valid_rows=10,
        )

        with self.assertRaisesRegex(
            ValueError,
            (
                "Import row counts cannot "
                "exceed validated rows."
            ),
        ):
            (
                MigrationBatchService
                .complete_import(
                    batch=batch,
                    imported_rows=8,
                    skipped_rows=2,
                    failed_rows=1,
                    import_result={
                        "processed": 11,
                    },
                )
            )

    @patch(
        "apps.migration.services."
        "migration_batch_service."
        "MigrationBatchRepository."
        "mark_failed"
    )
    def test_fail_import(
        self,
        mark_mock,
    ):
        batch = self.make_batch(
            status="IMPORTING",
        )

        expected = object()
        mark_mock.return_value = expected

        result = (
            MigrationBatchService
            .fail_import(
                batch=batch,
                error_summary=(
                    "Database connection lost."
                ),
            )
        )

        self.assertIs(
            result,
            expected,
        )

        mark_mock.assert_called_once_with(
            batch=batch,
            expected_status="IMPORTING",
            error_summary={
                "message":
                    "Database connection lost.",
                "stage":
                    "IMPORT",
            },
        )


    def test_fail_import_requires_importing_status(
        self,
    ):
        batch = self.make_batch(
            status="VALIDATED",
        )

        with self.assertRaisesRegex(
            ValueError,
            "IMPORTING status",
        ):
            (
                MigrationBatchService
                .fail_import(
                    batch=batch,
                    error_summary=(
                        "Import failed."
                    ),
                )
            )


    @patch(
        "apps.migration.services."
        "migration_batch_service."
        "MigrationBatchRepository."
        "mark_failed"
    )
    def test_fail_import_uses_default_message(
        self,
        mark_mock,
    ):
        batch = self.make_batch(
            status="IMPORTING",
        )

        expected = object()
        mark_mock.return_value = expected

        result = (
            MigrationBatchService
            .fail_import(
                batch=batch,
                error_summary="",
            )
        )

        self.assertIs(
            result,
            expected,
        )

        mark_mock.assert_called_once_with(
            batch=batch,
            error_summary={
                "message":
                    "Migration import failed.",
                "stage":
                    "IMPORT",
            },
            expected_status=(
                "IMPORTING"
            ),
        )


class MigrationBackgroundInfrastructureTestCase(
    TestCase,
):

    def test_background_upload_accepts_data_migration(
        self,
    ):
        purpose_field = (
            BackgroundUpload
            ._fields["purpose"]
        )

        self.assertIn(
            "DATA_MIGRATION",
            purpose_field.choices,
        )

    def test_background_job_accepts_validation_job(
        self,
    ):
        job_type_field = (
            BackgroundJob
            ._fields["job_type"]
        )

        self.assertIn(
            "DATA_MIGRATION_VALIDATE",
            job_type_field.choices,
        )

    def test_background_job_accepts_import_job(
        self,
    ):
        job_type_field = (
            BackgroundJob
            ._fields["job_type"]
        )

        self.assertIn(
            "DATA_MIGRATION_IMPORT",
            job_type_field.choices,
        )

class MigrationBatchRepositoryAtomicTestCase(
    TestCase,
):

    @patch(
        "apps.migration.repositories."
        "migration_batch_repository."
        "MigrationBatch.objects"
    )
    def test_mark_importing_is_atomic(
        self,
        objects_mock,
    ):
        organization = SimpleNamespace(
            id="organization-1",
        )

        batch = SimpleNamespace(
            id="batch-1",
            organization=organization,
            status="VALIDATED",
            started_at=None,
            updated_at=None,
        )

        queryset = MagicMock()

        objects_mock.return_value = queryset

        queryset.update_one.return_value = 1

        result = (
            MigrationBatchRepository
            .mark_importing(
                batch=batch,
            )
        )

        self.assertIs(
            result,
            batch,
        )

        objects_mock.assert_called_once_with(
            id="batch-1",
            organization=organization,
            status="VALIDATED",
        )

        queryset.update_one.assert_called_once()

        update_kwargs = (
            queryset
            .update_one
            .call_args
            .kwargs
        )

        self.assertEqual(
            update_kwargs[
                "set__status"
            ],
            "IMPORTING",
        )

        self.assertIn(
            "set__started_at",
            update_kwargs,
        )

        self.assertIn(
            "set__updated_at",
            update_kwargs,
        )

        self.assertEqual(
            batch.status,
            "IMPORTING",
        )

        self.assertIsNotNone(
            batch.started_at
        )

        self.assertIsNotNone(
            batch.updated_at
        )


    @patch(
        "apps.migration.repositories."
        "migration_batch_repository."
        "MigrationBatch.objects"
    )
    def test_mark_importing_rejects_lost_race(
        self,
        objects_mock,
    ):
        organization = SimpleNamespace(
            id="organization-1",
        )

        batch = SimpleNamespace(
            id="batch-1",
            organization=organization,
            status="VALIDATED",
            started_at=None,
            updated_at=None,
        )

        queryset = MagicMock()

        objects_mock.return_value = queryset

        queryset.update_one.return_value = 0

        with self.assertRaisesRegex(
            ValueError,
            (
                "Migration batch is no longer "
                "available for import."
            ),
        ):
            (
                MigrationBatchRepository
                .mark_importing(
                    batch=batch,
                )
            )

        objects_mock.assert_called_once_with(
            id="batch-1",
            organization=organization,
            status="VALIDATED",
        )

        queryset.update_one.assert_called_once()

        # Failed atomic transition must not mutate
        # the caller's in-memory object.
        self.assertEqual(
            batch.status,
            "VALIDATED",
        )

        self.assertIsNone(
            batch.started_at
        )

        self.assertIsNone(
            batch.updated_at
        )

    @patch(
        "apps.migration.repositories."
        "migration_batch_repository."
        "MigrationBatch.objects"
    )
    def test_mark_validating_is_atomic(
        self,
        objects_mock,
    ):
        organization = SimpleNamespace(
            id="organization-1",
        )

        batch = SimpleNamespace(
            id="batch-1",
            organization=organization,
            status="UPLOADED",
            updated_at=None,
        )

        queryset = MagicMock()
        objects_mock.return_value = queryset
        queryset.update_one.return_value = 1

        result = (
            MigrationBatchRepository
            .mark_validating(
                batch=batch,
            )
        )

        self.assertIs(
            result,
            batch,
        )

        objects_mock.assert_called_once_with(
            id="batch-1",
            organization=organization,
            status="UPLOADED",
        )

        update_kwargs = (
            queryset
            .update_one
            .call_args
            .kwargs
        )

        self.assertEqual(
            update_kwargs["set__status"],
            "VALIDATING",
        )

        self.assertIn(
            "set__updated_at",
            update_kwargs,
        )

        self.assertEqual(
            batch.status,
            "VALIDATING",
        )

        self.assertIsNotNone(
            batch.updated_at
        )


    @patch(
        "apps.migration.repositories."
        "migration_batch_repository."
        "MigrationBatch.objects"
    )
    def test_mark_validating_rejects_lost_race(
        self,
        objects_mock,
    ):
        organization = SimpleNamespace(
            id="organization-1",
        )

        batch = SimpleNamespace(
            id="batch-1",
            organization=organization,
            status="UPLOADED",
            updated_at=None,
        )

        queryset = MagicMock()
        objects_mock.return_value = queryset
        queryset.update_one.return_value = 0

        with self.assertRaisesRegex(
            ValueError,
            (
                "Migration batch is no longer "
                "available for validation."
            ),
        ):
            (
                MigrationBatchRepository
                .mark_validating(
                    batch=batch,
                )
            )

        self.assertEqual(
            batch.status,
            "UPLOADED",
        )

        self.assertIsNone(
            batch.updated_at
        )


    @patch(
        "apps.migration.repositories."
        "migration_batch_repository."
        "MigrationBatch.objects"
    )
    def test_mark_validated_is_atomic(
        self,
        objects_mock,
    ):
        organization = SimpleNamespace(
            id="organization-1",
        )

        batch = SimpleNamespace(
            id="batch-1",
            organization=organization,
            status="VALIDATING",
            total_rows=0,
            valid_rows=0,
            invalid_rows=0,
            validation_result={},
            updated_at=None,
        )

        queryset = MagicMock()
        objects_mock.return_value = queryset
        queryset.update_one.return_value = 1

        validation_result = {
            "rows": [],
        }

        result = (
            MigrationBatchRepository
            .mark_validated(
                batch=batch,
                total_rows=10,
                valid_rows=8,
                invalid_rows=2,
                validation_result=(
                    validation_result
                ),
            )
        )

        self.assertIs(
            result,
            batch,
        )

        objects_mock.assert_called_once_with(
            id="batch-1",
            organization=organization,
            status="VALIDATING",
        )

        update_kwargs = (
            queryset
            .update_one
            .call_args
            .kwargs
        )

        self.assertEqual(
            update_kwargs["set__status"],
            "VALIDATED",
        )

        self.assertEqual(
            update_kwargs["set__total_rows"],
            10,
        )

        self.assertEqual(
            update_kwargs["set__valid_rows"],
            8,
        )

        self.assertEqual(
            update_kwargs["set__invalid_rows"],
            2,
        )

        self.assertEqual(
            update_kwargs[
                "set__validation_result"
            ],
            validation_result,
        )

        self.assertEqual(
            batch.status,
            "VALIDATED",
        )

        self.assertEqual(
            batch.total_rows,
            10,
        )

        self.assertEqual(
            batch.valid_rows,
            8,
        )

        self.assertEqual(
            batch.invalid_rows,
            2,
        )


    @patch(
        "apps.migration.repositories."
        "migration_batch_repository."
        "MigrationBatch.objects"
    )
    def test_mark_validated_rejects_lost_race(
        self,
        objects_mock,
    ):
        organization = SimpleNamespace(
            id="organization-1",
        )

        batch = SimpleNamespace(
            id="batch-1",
            organization=organization,
            status="VALIDATING",
            total_rows=0,
            valid_rows=0,
            invalid_rows=0,
            validation_result={},
            updated_at=None,
        )

        queryset = MagicMock()
        objects_mock.return_value = queryset
        queryset.update_one.return_value = 0

        with self.assertRaisesRegex(
            ValueError,
            (
                "Migration batch is no longer "
                "available to complete validation."
            ),
        ):
            (
                MigrationBatchRepository
                .mark_validated(
                    batch=batch,
                    total_rows=10,
                    valid_rows=10,
                    invalid_rows=0,
                    validation_result={
                        "rows": [],
                    },
                )
            )

        # No in-memory mutation after losing
        # the database state-transition race.
        self.assertEqual(
            batch.status,
            "VALIDATING",
        )

        self.assertEqual(
            batch.total_rows,
            0,
        )

        self.assertEqual(
            batch.valid_rows,
            0,
        )

        self.assertEqual(
            batch.invalid_rows,
            0,
        )

        self.assertEqual(
            batch.validation_result,
            {},
        )

        self.assertIsNone(
            batch.updated_at
        )

    @patch(
        "apps.migration.repositories."
        "migration_batch_repository."
        "MigrationBatch.objects"
    )
    def test_mark_completed_is_atomic(
        self,
        objects_mock,
    ):
        organization = SimpleNamespace(
            id="organization-1",
        )

        batch = SimpleNamespace(
            id="batch-1",
            organization=organization,
            status="IMPORTING",
            imported_rows=0,
            skipped_rows=0,
            failed_rows=0,
            import_result={},
            completed_at=None,
            updated_at=None,
        )

        queryset = MagicMock()
        objects_mock.return_value = queryset
        queryset.update_one.return_value = 1

        import_result = {
            "processed": 10,
        }

        result = (
            MigrationBatchRepository
            .mark_completed(
                batch=batch,
                imported_rows=8,
                skipped_rows=2,
                failed_rows=0,
                import_result=import_result,
            )
        )

        self.assertIs(
            result,
            batch,
        )

        objects_mock.assert_called_once_with(
            id="batch-1",
            organization=organization,
            status="IMPORTING",
        )

        queryset.update_one.assert_called_once()

        update_kwargs = (
            queryset
            .update_one
            .call_args
            .kwargs
        )

        self.assertEqual(
            update_kwargs["set__status"],
            "COMPLETED",
        )

        self.assertEqual(
            update_kwargs["set__imported_rows"],
            8,
        )

        self.assertEqual(
            update_kwargs["set__skipped_rows"],
            2,
        )

        self.assertEqual(
            update_kwargs["set__failed_rows"],
            0,
        )

        self.assertEqual(
            update_kwargs["set__import_result"],
            import_result,
        )

        self.assertIn(
            "set__completed_at",
            update_kwargs,
        )

        self.assertIn(
            "set__updated_at",
            update_kwargs,
        )

        self.assertEqual(
            batch.status,
            "COMPLETED",
        )

        self.assertEqual(
            batch.imported_rows,
            8,
        )

        self.assertEqual(
            batch.skipped_rows,
            2,
        )

        self.assertEqual(
            batch.failed_rows,
            0,
        )

        self.assertEqual(
            batch.import_result,
            import_result,
        )

        self.assertIsNotNone(
            batch.completed_at,
        )

        self.assertIsNotNone(
            batch.updated_at,
        )


    @patch(
        "apps.migration.repositories."
        "migration_batch_repository."
        "MigrationBatch.objects"
    )
    def test_mark_completed_rejects_lost_race(
        self,
        objects_mock,
    ):
        organization = SimpleNamespace(
            id="organization-1",
        )

        batch = SimpleNamespace(
            id="batch-1",
            organization=organization,
            status="IMPORTING",
            imported_rows=0,
            skipped_rows=0,
            failed_rows=0,
            import_result={},
            completed_at=None,
            updated_at=None,
        )

        queryset = MagicMock()
        objects_mock.return_value = queryset
        queryset.update_one.return_value = 0

        with self.assertRaisesRegex(
            ValueError,
            (
                "Migration batch is no longer "
                "available to complete import."
            ),
        ):
            (
                MigrationBatchRepository
                .mark_completed(
                    batch=batch,
                    imported_rows=10,
                    skipped_rows=0,
                    failed_rows=0,
                    import_result={
                        "processed": 10,
                    },
                )
            )

        objects_mock.assert_called_once_with(
            id="batch-1",
            organization=organization,
            status="IMPORTING",
        )

        queryset.update_one.assert_called_once()

        # Lost race must not mutate the stale
        # in-memory batch.
        self.assertEqual(
            batch.status,
            "IMPORTING",
        )

        self.assertEqual(
            batch.imported_rows,
            0,
        )

        self.assertIsNone(
            batch.completed_at,
        )

        self.assertIsNone(
            batch.updated_at,
        )


    @patch(
        "apps.migration.repositories."
        "migration_batch_repository."
        "MigrationBatch.objects"
    )
    def test_mark_failed_from_validating_is_atomic(
        self,
        objects_mock,
    ):
        organization = SimpleNamespace(
            id="organization-1",
        )

        batch = SimpleNamespace(
            id="batch-1",
            organization=organization,
            status="VALIDATING",
            error_summary={},
            completed_at=None,
            updated_at=None,
        )

        queryset = MagicMock()
        objects_mock.return_value = queryset
        queryset.update_one.return_value = 1

        error_summary = {
            "message":
                "Validation crashed.",
            "stage":
                "VALIDATION",
        }

        result = (
            MigrationBatchRepository
            .mark_failed(
                batch=batch,
                error_summary=error_summary,
                expected_status="VALIDATING",
            )
        )

        self.assertIs(
            result,
            batch,
        )

        objects_mock.assert_called_once_with(
            id="batch-1",
            organization=organization,
            status="VALIDATING",
        )

        queryset.update_one.assert_called_once()

        update_kwargs = (
            queryset
            .update_one
            .call_args
            .kwargs
        )

        self.assertEqual(
            update_kwargs["set__status"],
            "FAILED",
        )

        self.assertEqual(
            update_kwargs["set__error_summary"],
            error_summary,
        )

        self.assertIn(
            "set__completed_at",
            update_kwargs,
        )

        self.assertIn(
            "set__updated_at",
            update_kwargs,
        )

        self.assertEqual(
            batch.status,
            "FAILED",
        )

        self.assertEqual(
            batch.error_summary,
            error_summary,
        )

        self.assertIsNotNone(
            batch.completed_at,
        )

        self.assertIsNotNone(
            batch.updated_at,
        )


    @patch(
        "apps.migration.repositories."
        "migration_batch_repository."
        "MigrationBatch.objects"
    )
    def test_mark_failed_from_importing_is_atomic(
        self,
        objects_mock,
    ):
        organization = SimpleNamespace(
            id="organization-1",
        )

        batch = SimpleNamespace(
            id="batch-1",
            organization=organization,
            status="IMPORTING",
            error_summary={},
            completed_at=None,
            updated_at=None,
        )

        queryset = MagicMock()
        objects_mock.return_value = queryset
        queryset.update_one.return_value = 1

        error_summary = {
            "message":
                "Import crashed.",
            "stage":
                "IMPORT",
        }

        result = (
            MigrationBatchRepository
            .mark_failed(
                batch=batch,
                error_summary=error_summary,
                expected_status="IMPORTING",
            )
        )

        self.assertIs(
            result,
            batch,
        )

        objects_mock.assert_called_once_with(
            id="batch-1",
            organization=organization,
            status="IMPORTING",
        )

        update_kwargs = (
            queryset
            .update_one
            .call_args
            .kwargs
        )

        self.assertEqual(
            update_kwargs["set__status"],
            "FAILED",
        )

        self.assertEqual(
            update_kwargs["set__error_summary"],
            error_summary,
        )

        self.assertEqual(
            batch.status,
            "FAILED",
        )

        self.assertEqual(
            batch.error_summary,
            error_summary,
        )


    @patch(
        "apps.migration.repositories."
        "migration_batch_repository."
        "MigrationBatch.objects"
    )
    def test_mark_failed_rejects_lost_race(
        self,
        objects_mock,
    ):
        organization = SimpleNamespace(
            id="organization-1",
        )

        batch = SimpleNamespace(
            id="batch-1",
            organization=organization,
            status="IMPORTING",
            error_summary={},
            completed_at=None,
            updated_at=None,
        )

        queryset = MagicMock()
        objects_mock.return_value = queryset
        queryset.update_one.return_value = 0

        with self.assertRaisesRegex(
            ValueError,
            (
                "Migration batch is no longer "
                "available to mark failed."
            ),
        ):
            (
                MigrationBatchRepository
                .mark_failed(
                    batch=batch,
                    error_summary={
                        "message":
                            "Import crashed.",
                        "stage":
                            "IMPORT",
                    },
                    expected_status=(
                        "IMPORTING"
                    ),
                )
            )

        objects_mock.assert_called_once_with(
            id="batch-1",
            organization=organization,
            status="IMPORTING",
        )

        queryset.update_one.assert_called_once()

        self.assertEqual(
            batch.status,
            "IMPORTING",
        )

        self.assertEqual(
            batch.error_summary,
            {},
        )

        self.assertIsNone(
            batch.completed_at,
        )

        self.assertIsNone(
            batch.updated_at,
        )

    def test_mark_failed_rejects_invalid_expected_status(
        self,
    ):
        batch = SimpleNamespace(
            id="batch-1",
            organization=SimpleNamespace(
                id="organization-1",
            ),
        )

        with self.assertRaisesRegex(
            ValueError,
            (
                "Expected migration status must "
                "be VALIDATING or IMPORTING."
            ),
        ):
            (
                MigrationBatchRepository
                .mark_failed(
                    batch=batch,
                    error_summary={},
                    expected_status=(
                        "VALIDATED"
                    ),
                )
            )