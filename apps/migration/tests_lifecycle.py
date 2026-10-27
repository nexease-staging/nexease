from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase

from apps.migration.services.migration_batch_service import (
    MigrationBatchService,
)


class MigrationLifecycleTestCase(
    SimpleTestCase,
):

    def make_batch(
        self,
        *,
        status="CREATED",
        valid_rows=0,
        invalid_rows=0,
    ):
        return SimpleNamespace(
            id="batch-1",
            organization=SimpleNamespace(
                id="organization-1",
            ),
            status=status,
            upload_id=None,
            valid_rows=valid_rows,
            invalid_rows=invalid_rows,
            total_rows=(
                valid_rows
                + invalid_rows
            ),
        )

    @patch(
        "apps.migration.services."
        "migration_batch_service."
        "MigrationBatchRepository."
        "set_upload"
    )
    def test_created_can_move_to_uploaded(
        self,
        set_upload_mock,
    ):
        batch = self.make_batch(
            status="CREATED",
        )

        uploaded = SimpleNamespace(
            status="UPLOADED",
        )
        set_upload_mock.return_value = uploaded

        result = (
            MigrationBatchService
            .attach_upload(
                batch=batch,
                upload_id="upload-1",
            )
        )

        self.assertIs(
            result,
            uploaded,
        )

        set_upload_mock.assert_called_once_with(
            batch=batch,
            upload_id="upload-1",
        )

    @patch(
        "apps.migration.services."
        "migration_batch_service."
        "MigrationBatchRepository."
        "mark_validating"
    )
    def test_uploaded_can_move_to_validating(
        self,
        mark_mock,
    ):
        batch = self.make_batch(
            status="UPLOADED",
        )

        validating = SimpleNamespace(
            status="VALIDATING",
        )
        mark_mock.return_value = validating

        result = (
            MigrationBatchService
            .start_validation(
                batch=batch,
            )
        )

        self.assertIs(
            result,
            validating,
        )

        mark_mock.assert_called_once_with(
            batch=batch,
        )

    @patch(
        "apps.migration.services."
        "migration_batch_service."
        "MigrationBatchRepository."
        "mark_validated"
    )
    def test_validating_can_move_to_validated(
        self,
        mark_mock,
    ):
        batch = self.make_batch(
            status="VALIDATING",
        )

        validated = SimpleNamespace(
            status="VALIDATED",
        )
        mark_mock.return_value = validated

        validation_result = {
            "can_import": True,
        }

        result = (
            MigrationBatchService
            .complete_validation(
                batch=batch,
                total_rows=10,
                valid_rows=10,
                invalid_rows=0,
                validation_result=(
                    validation_result
                ),
            )
        )

        self.assertIs(
            result,
            validated,
        )

        mark_mock.assert_called_once_with(
            batch=batch,
            total_rows=10,
            valid_rows=10,
            invalid_rows=0,
            validation_result=(
                validation_result
            ),
        )

    @patch(
        "apps.migration.services."
        "migration_batch_service."
        "MigrationBatchRepository."
        "mark_importing"
    )
    def test_validated_can_move_to_importing(
        self,
        mark_mock,
    ):
        batch = self.make_batch(
            status="VALIDATED",
            valid_rows=10,
            invalid_rows=0,
        )

        importing = SimpleNamespace(
            status="IMPORTING",
        )
        mark_mock.return_value = importing

        result = (
            MigrationBatchService
            .start_import(
                batch=batch,
            )
        )

        self.assertIs(
            result,
            importing,
        )

        mark_mock.assert_called_once_with(
            batch=batch,
        )

    @patch(
        "apps.migration.services."
        "migration_batch_service."
        "MigrationBatchRepository."
        "mark_completed"
    )
    def test_importing_can_move_to_completed(
        self,
        mark_mock,
    ):
        batch = self.make_batch(
            status="IMPORTING",
            valid_rows=10,
        )

        completed = SimpleNamespace(
            status="COMPLETED",
        )
        mark_mock.return_value = completed

        import_result = {
            "processed": 10,
        }

        result = (
            MigrationBatchService
            .complete_import(
                batch=batch,
                imported_rows=10,
                skipped_rows=0,
                failed_rows=0,
                import_result=import_result,
            )
        )

        self.assertIs(
            result,
            completed,
        )

        mark_mock.assert_called_once_with(
            batch=batch,
            imported_rows=10,
            skipped_rows=0,
            failed_rows=0,
            import_result=import_result,
        )

    def test_validation_cannot_start_from_created(
        self,
    ):
        batch = self.make_batch(
            status="CREATED",
        )

        with self.assertRaisesRegex(
            ValueError,
            "uploaded migration",
        ):
            (
                MigrationBatchService
                .start_validation(
                    batch=batch,
                )
            )

    def test_import_cannot_start_before_validation(
        self,
    ):
        batch = self.make_batch(
            status="UPLOADED",
        )

        with self.assertRaisesRegex(
            ValueError,
            "validated migration",
        ):
            (
                MigrationBatchService
                .start_import(
                    batch=batch,
                )
            )

    def test_import_rejects_invalid_rows(
        self,
    ):
        batch = self.make_batch(
            status="VALIDATED",
            valid_rows=9,
            invalid_rows=1,
        )

        with self.assertRaisesRegex(
            ValueError,
            "contains invalid rows",
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
        "create"
    )
    def test_customer_migration_can_enter_lifecycle(
        self,
        create_mock,
    ):
        organization = SimpleNamespace(
            id="organization-1",
        )

        user = SimpleNamespace(
            id="user-1",
            organization=organization,
            is_active=True,
        )

        created = SimpleNamespace(
            id="customer-batch-1",
            organization=organization,
            created_by=user,
            source_system="GENERIC",
            migration_type="CUSTOMERS",
            status="CREATED",
        )

        create_mock.return_value = created

        result = (
            MigrationBatchService
            .create_batch(
                organization=organization,
                created_by=user,
                source_system="GENERIC",
                migration_type="CUSTOMERS",
                mapping={
                    "Customer Code": "code",
                    "Customer Name": "name",
                },
                options={
                    "skip_duplicates": True,
                },
            )
        )

        self.assertIs(
            result,
            created,
        )

        self.assertEqual(
            result.migration_type,
            "CUSTOMERS",
        )

        self.assertEqual(
            result.status,
            "CREATED",
        )

        create_mock.assert_called_once_with(
            organization=organization,
            created_by=user,
            source_system="GENERIC",
            migration_type="CUSTOMERS",
            mapping={
                "Customer Code": "code",
                "Customer Name": "name",
            },
            options={
                "skip_duplicates": True,
            },
        )

    @patch(
        "apps.migration.services."
        "migration_batch_service."
        "MigrationBatchRepository."
        "create"
    )
    def test_supplier_migration_can_enter_lifecycle(
        self,
        create_mock,
    ):
        organization = SimpleNamespace(
            id="organization-1",
        )

        user = SimpleNamespace(
            id="user-1",
            organization=organization,
            is_active=True,
        )

        created = SimpleNamespace(
            id="supplier-batch-1",
            organization=organization,
            created_by=user,
            source_system="GENERIC",
            migration_type="SUPPLIERS",
            status="CREATED",
        )

        create_mock.return_value = created

        result = (
            MigrationBatchService
            .create_batch(
                organization=organization,
                created_by=user,
                source_system="GENERIC",
                migration_type="SUPPLIERS",
                mapping={
                    "Supplier Code": "code",
                    "Supplier Name": "name",
                },
                options={
                    "skip_duplicates": True,
                },
            )
        )

        self.assertIs(
            result,
            created,
        )

        self.assertEqual(
            result.migration_type,
            "SUPPLIERS",
        )

        self.assertEqual(
            result.status,
            "CREATED",
        )

        create_mock.assert_called_once_with(
            organization=organization,
            created_by=user,
            source_system="GENERIC",
            migration_type="SUPPLIERS",
            mapping={
                "Supplier Code": "code",
                "Supplier Name": "name",
            },
            options={
                "skip_duplicates": True,
            },
        )