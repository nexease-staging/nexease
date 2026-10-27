from datetime import datetime
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from apps.migration.repositories.migration_batch_repository import (
    MigrationBatchRepository,
)
from apps.migration.services.migration_api_service import (
    MigrationAPIService,
    MigrationAPIValidationError,
)
from apps.migration.services.migration_batch_service import (
    MigrationBatchService,
)
from apps.migration.services.migration_import_service import (
    MigrationImportError,
    MigrationImportService,
)

class MigrationAPIServiceTestCase(
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
            organization=(
                self.organization
            ),
            is_active=True,
        )

    def make_batch(self):
        return SimpleNamespace(
            id="batch-1",
            organization=(
                self.organization
            ),
            created_by=self.user,
            source_system="ZOHO_INVENTORY",
            migration_type="PRODUCTS",
            status="CREATED",
            upload_id=None,
            job_id=None,
            mapping={
                "Product Name": "name",
            },
            options={
                "skip_duplicates": True,
            },
            total_rows=10,
            valid_rows=8,
            invalid_rows=2,
            imported_rows=0,
            skipped_rows=0,
            failed_rows=0,
            validation_result={
                "errors": [],
            },
            import_result={},
            error_summary={},
            started_at=None,
            completed_at=None,
            created_at=datetime(
                2026,
                9,
                24,
                10,
                0,
                0,
            ),
            updated_at=datetime(
                2026,
                9,
                24,
                10,
                5,
                0,
            ),
        )

    # ==============================================
    # CREATE
    # ==============================================

    @patch.object(
        MigrationBatchService,
        "create_batch",
    )
    def test_create_batch_normalizes_payload(
        self,
        create_mock,
    ):
        batch = self.make_batch()

        create_mock.return_value = batch

        result = (
            MigrationAPIService
            .create_batch(
                organization=(
                    self.organization
                ),
                created_by=self.user,
                payload={
                    "source_system":
                        " zoho_inventory ",
                    "migration_type":
                        " products ",
                    "mapping": {
                        "SKU": "sku",
                    },
                    "options": {
                        "skip_duplicates":
                            True,
                    },
                },
            )
        )

        self.assertIs(
            result,
            batch,
        )

        create_mock.assert_called_once_with(
            organization=self.organization,
            created_by=self.user,
            source_system="ZOHO_INVENTORY",
            migration_type="PRODUCTS",
            mapping={
                "SKU": "sku",
            },
            options={
                "skip_duplicates": True,
            },
        )

    def test_create_batch_rejects_non_object_payload(
        self,
    ):
        with self.assertRaises(
            MigrationAPIValidationError
        ) as context:
            (
                MigrationAPIService
                .create_batch(
                    organization=(
                        self.organization
                    ),
                    created_by=self.user,
                    payload=[],
                )
            )

        self.assertIn(
            "payload",
            context.exception.details,
        )

    def test_create_batch_rejects_unsupported_fields(
        self,
    ):
        with self.assertRaises(
            MigrationAPIValidationError
        ) as context:
            (
                MigrationAPIService
                .create_batch(
                    organization=(
                        self.organization
                    ),
                    created_by=self.user,
                    payload={
                        "source_system":
                            "GENERIC",
                        "migration_type":
                            "PRODUCTS",
                        "organization_id":
                            "other-organization",
                    },
                )
            )

        self.assertIn(
            "fields",
            context.exception.details,
        )

    def test_create_batch_rejects_invalid_source(
        self,
    ):
        with self.assertRaises(
            MigrationAPIValidationError
        ) as context:
            (
                MigrationAPIService
                .create_batch(
                    organization=(
                        self.organization
                    ),
                    created_by=self.user,
                    payload={
                        "source_system":
                            "UNKNOWN",
                        "migration_type":
                            "PRODUCTS",
                    },
                )
            )

        self.assertIn(
            "source_system",
            context.exception.details,
        )

    @patch.object(
        MigrationBatchService,
        "create_batch",
    )
    def test_create_batch_accepts_suppliers(
        self,
        create_mock,
    ):
        expected = object()
        create_mock.return_value = expected

        result = (
            MigrationAPIService
            .create_batch(
                organization=self.organization,
                created_by=self.user,
                payload={
                    "source_system":
                        "GENERIC",
                    "migration_type":
                        "SUPPLIERS",
                    "mapping": {
                        "Supplier Code":
                            "code",
                        "Supplier Name":
                            "name",
                    },
                    "options": {
                        "skip_duplicates":
                            True,
                    },
                },
            )
        )

        self.assertIs(
            result,
            expected,
        )

        create_mock.assert_called_once_with(
            organization=self.organization,
            created_by=self.user,
            source_system="GENERIC",
            migration_type="SUPPLIERS",
            mapping={
                "Supplier Code":
                    "code",
                "Supplier Name":
                    "name",
            },
            options={
                "skip_duplicates":
                    True,
            },
        )

    @patch.object(
        MigrationBatchService,
        "create_batch",
    )
    def test_create_batch_accepts_customers(
        self,
        create_mock,
    ):
        expected = object()
        create_mock.return_value = expected

        result = (
            MigrationAPIService
            .create_batch(
                organization=self.organization,
                created_by=self.user,
                payload={
                    "source_system":
                        "GENERIC",
                    "migration_type":
                        "CUSTOMERS",
                    "mapping": {
                        "Customer Code":
                            "code",
                        "Customer Name":
                            "name",
                    },
                    "options": {
                        "skip_duplicates":
                            True,
                    },
                },
            )
        )

        self.assertIs(
            result,
            expected,
        )

        create_mock.assert_called_once_with(
            organization=self.organization,
            created_by=self.user,
            source_system="GENERIC",
            migration_type="CUSTOMERS",
            mapping={
                "Customer Code":
                    "code",
                "Customer Name":
                    "name",
            },
            options={
                "skip_duplicates":
                    True,
            },
        )
    def test_create_batch_rejects_invalid_type(
        self,
    ):
        with self.assertRaises(
            MigrationAPIValidationError
        ) as context:
            (
                MigrationAPIService
                .create_batch(
                    organization=(
                        self.organization
                    ),
                    created_by=self.user,
                    payload={
                        "source_system":
                            "GENERIC",
                        "migration_type":
                            "UNKNOWN",
                    },
                )
            )

        self.assertIn(
            "migration_type",
            context.exception.details,
        )

    def test_create_batch_rejects_invalid_mapping(
        self,
    ):
        with self.assertRaises(
            MigrationAPIValidationError
        ) as context:
            (
                MigrationAPIService
                .create_batch(
                    organization=(
                        self.organization
                    ),
                    created_by=self.user,
                    payload={
                        "source_system":
                            "GENERIC",
                        "migration_type":
                            "PRODUCTS",
                        "mapping": [],
                    },
                )
            )

        self.assertIn(
            "mapping",
            context.exception.details,
        )

    @patch.object(
        MigrationBatchService,
        "create_batch",
    )
    def test_create_batch_accepts_skip_duplicates_true(
        self,
        create_mock,
    ):
        expected = object()
        create_mock.return_value = expected

        result = (
            MigrationAPIService
            .create_batch(
                organization=self.organization,
                created_by=self.user,
                payload={
                    "source_system": "GENERIC",
                    "migration_type": "PRODUCTS",
                    "options": {
                        "skip_duplicates": True,
                    },
                },
            )
        )

        self.assertIs(
            result,
            expected,
        )

        create_mock.assert_called_once()

        self.assertEqual(
            create_mock.call_args.kwargs[
                "options"
            ],
            {
                "skip_duplicates": True,
            },
        )


    @patch.object(
        MigrationBatchService,
        "create_batch",
    )
    def test_create_batch_accepts_skip_duplicates_false(
        self,
        create_mock,
    ):
        expected = object()
        create_mock.return_value = expected

        result = (
            MigrationAPIService
            .create_batch(
                organization=self.organization,
                created_by=self.user,
                payload={
                    "source_system": "GENERIC",
                    "migration_type": "PRODUCTS",
                    "options": {
                        "skip_duplicates": False,
                    },
                },
            )
        )

        self.assertIs(
            result,
            expected,
        )

        self.assertEqual(
            create_mock.call_args.kwargs[
                "options"
            ],
            {
                "skip_duplicates": False,
            },
        )


    def test_create_batch_rejects_invalid_skip_duplicates_type(
        self,
    ):
        with self.assertRaises(
            MigrationAPIValidationError
        ) as context:
            (
                MigrationAPIService
                .create_batch(
                    organization=(
                        self.organization
                    ),
                    created_by=self.user,
                    payload={
                        "source_system":
                            "GENERIC",
                        "migration_type":
                            "PRODUCTS",
                        "options": {
                            "skip_duplicates":
                                "yes",
                        },
                    },
                )
            )

        self.assertIn(
            "options",
            context.exception.details,
        )

        self.assertIn(
            "must be a boolean",
            context.exception.details[
                "options"
            ][0],
        )


    def test_create_batch_rejects_unsupported_option(
        self,
    ):
        with self.assertRaises(
            MigrationAPIValidationError
        ) as context:
            (
                MigrationAPIService
                .create_batch(
                    organization=(
                        self.organization
                    ),
                    created_by=self.user,
                    payload={
                        "source_system":
                            "GENERIC",
                        "migration_type":
                            "PRODUCTS",
                        "options": {
                            "dry_run": True,
                        },
                    },
                )
            )

        self.assertIn(
            "options",
            context.exception.details,
        )

        self.assertIn(
            "Unsupported migration option",
            context.exception.details[
                "options"
            ][0],
        )

    def test_create_batch_rejects_invalid_options(
        self,
    ):
        with self.assertRaises(
            MigrationAPIValidationError
        ) as context:
            (
                MigrationAPIService
                .create_batch(
                    organization=(
                        self.organization
                    ),
                    created_by=self.user,
                    payload={
                        "source_system":
                            "GENERIC",
                        "migration_type":
                            "PRODUCTS",
                        "options": "invalid",
                    },
                )
            )

        self.assertIn(
            "options",
            context.exception.details,
        )

    # ==============================================
    # DETAIL
    # ==============================================

    @patch.object(
        MigrationBatchService,
        "get_batch",
    )
    def test_get_batch_is_tenant_scoped(
        self,
        get_mock,
    ):
        batch = self.make_batch()

        get_mock.return_value = batch

        result = (
            MigrationAPIService
            .get_batch(
                organization=(
                    self.organization
                ),
                batch_id="batch-1",
            )
        )

        self.assertIs(
            result,
            batch,
        )

        get_mock.assert_called_once_with(
            organization=self.organization,
            batch_id="batch-1",
        )

    @patch.object(
        MigrationBatchService,
        "get_batch",
        return_value=None,
    )
    def test_get_batch_missing_raises_lookup_error(
        self,
        get_mock,
    ):
        with self.assertRaises(
            LookupError
        ):
            (
                MigrationAPIService
                .get_batch(
                    organization=(
                        self.organization
                    ),
                    batch_id="missing",
                )
            )

        get_mock.assert_called_once_with(
            organization=self.organization,
            batch_id="missing",
        )

    # ==============================================
    # LIST
    # ==============================================

    @patch.object(
        MigrationBatchRepository,
        "list_by_organization",
    )
    def test_list_batches_is_tenant_scoped(
        self,
        list_mock,
    ):
        batch = self.make_batch()

        list_mock.return_value = [
            batch,
        ]

        result = (
            MigrationAPIService
            .list_batches(
                organization=(
                    self.organization
                ),
                limit=25,
            )
        )

        self.assertEqual(
            result,
            [batch],
        )

        list_mock.assert_called_once_with(
            organization=self.organization,
            limit=25,
        )

    def test_list_batches_rejects_invalid_limit(
        self,
    ):
        invalid_values = [
            0,
            101,
            -1,
            True,
            "10",
        ]

        for value in invalid_values:
            with self.subTest(
                value=value
            ):
                with self.assertRaises(
                    MigrationAPIValidationError
                ):
                    (
                        MigrationAPIService
                        .list_batches(
                            organization=(
                                self.organization
                            ),
                            limit=value,
                        )
                    )

    # ==============================================
    # IMPORT
    # ==============================================

    def test_import_batch_requires_organization(
        self,
    ):
        with self.assertRaises(
            PermissionError
        ):
            (
                MigrationAPIService
                .import_batch(
                    organization=None,
                    batch_id="batch-1",
                )
            )

    def test_import_batch_requires_batch_id(
        self,
    ):
        with self.assertRaises(
            LookupError
        ):
            (
                MigrationAPIService
                .import_batch(
                    organization=(
                        self.organization
                    ),
                    batch_id="",
                )
            )

    @patch.object(
        MigrationBatchService,
        "get_batch",
        return_value=None,
    )
    def test_import_batch_missing_raises_lookup_error(
        self,
        get_mock,
    ):
        with self.assertRaises(
            LookupError
        ):
            (
                MigrationAPIService
                .import_batch(
                    organization=(
                        self.organization
                    ),
                    batch_id="missing",
                )
            )

        get_mock.assert_called_once_with(
            organization=self.organization,
            batch_id="missing",
        )

    @patch.object(
        MigrationImportService,
        "import_batch",
    )
    @patch.object(
        MigrationBatchService,
        "get_batch",
    )
    def test_import_batch_is_tenant_scoped(
        self,
        get_mock,
        import_mock,
    ):
        batch = self.make_batch()

        get_mock.return_value = batch

        expected_result = {
            "batch": batch,
            "import": {
                "migration_type":
                    "PRODUCTS",
                "imported_rows": 8,
                "skipped_rows": 0,
                "failed_rows": 0,
                "rows": [],
            },
        }

        import_mock.return_value = (
            expected_result
        )

        result = (
            MigrationAPIService
            .import_batch(
                organization=(
                    self.organization
                ),
                batch_id="batch-1",
            )
        )

        self.assertIs(
            result,
            expected_result,
        )

        get_mock.assert_called_once_with(
            organization=self.organization,
            batch_id="batch-1",
        )

        import_mock.assert_called_once_with(
            organization=self.organization,
            batch=batch,
        )

    @patch.object(
        MigrationImportService,
        "import_batch",
    )
    @patch.object(
        MigrationBatchService,
        "get_batch",
    )
    def test_import_batch_converts_import_error(
        self,
        get_mock,
        import_mock,
    ):
        batch = self.make_batch()

        get_mock.return_value = batch

        import_mock.side_effect = (
            MigrationImportError(
                "Migration is not ready "
                "for import."
            )
        )

        with self.assertRaises(
            MigrationAPIValidationError
        ) as context:
            (
                MigrationAPIService
                .import_batch(
                    organization=(
                        self.organization
                    ),
                    batch_id="batch-1",
                )
            )

        self.assertEqual(
            str(context.exception),
            "Migration import failed.",
        )

        self.assertIn(
            "migration",
            context.exception.details,
        )

        self.assertEqual(
            context.exception.details[
                "migration"
            ],
            [
                (
                    "Migration is not ready "
                    "for import."
                )
            ],
        )

        import_mock.assert_called_once_with(
            organization=self.organization,
            batch=batch,
        )

    # ==============================================
    # SERIALIZATION
    # ==============================================

    def test_serialize_batch_has_safe_fields(
        self,
    ):
        batch = self.make_batch()

        result = (
            MigrationAPIService
            .serialize_batch(
                batch
            )
        )

        self.assertEqual(
            result["id"],
            "batch-1",
        )

        self.assertEqual(
            result["source_system"],
            "ZOHO_INVENTORY",
        )

        self.assertEqual(
            result["migration_type"],
            "PRODUCTS",
        )

        self.assertEqual(
            result["status"],
            "CREATED",
        )

        self.assertEqual(
            result["total_rows"],
            10,
        )

        self.assertEqual(
            result["valid_rows"],
            8,
        )

        self.assertEqual(
            result["invalid_rows"],
            2,
        )

        self.assertEqual(
            result["created_by"],
            "user-1",
        )

        self.assertEqual(
            result["created_at"],
            "2026-09-24T10:00:00",
        )

        self.assertEqual(
            result["updated_at"],
            "2026-09-24T10:05:00",
        )

        self.assertNotIn(
            "organization",
            result,
        )

        self.assertNotIn(
            "_data",
            result,
        )

        self.assertNotIn(
            "_cls",
            result,
        )

    def test_serialize_none_returns_none(
        self,
    ):
        self.assertIsNone(
            MigrationAPIService
            .serialize_batch(
                None
            )
        )

    @patch.object(
        MigrationBatchRepository,
        "set_job",
    )
    @patch(
        "apps.migration.services."
        "migration_api_service."
        "BackgroundJobService.create_job"
    )
    @patch.object(
        MigrationAPIService,
        "get_batch",
    )
    def test_queue_validation_creates_job(
        self,
        get_batch_mock,
        create_job_mock,
        set_job_mock,
    ):
        batch = self.make_batch()
        job = SimpleNamespace(
            id="job-1",
        )

        get_batch_mock.return_value = batch
        create_job_mock.return_value = job

        result = (
            MigrationAPIService
            .queue_validation(
                organization=self.organization,
                created_by=self.user,
                batch_id="batch-1",
            )
        )

        get_batch_mock.assert_called_once_with(
            organization=self.organization,
            batch_id="batch-1",
        )

        create_job_mock.assert_called_once_with(
            organization=self.organization,
            created_by=self.user,
            job_type="DATA_MIGRATION_VALIDATE",
            payload={
                "batch_id": "batch-1",
            },
            idempotency_key=(
                "DATA_MIGRATION_VALIDATE:"
                "batch-1"
            ),
        )

        set_job_mock.assert_called_once_with(
            batch=batch,
            job_id="job-1",
        )

        self.assertIs(
            result["batch"],
            batch,
        )

        self.assertIs(
            result["job"],
            job,
        )


    @patch.object(
        MigrationBatchRepository,
        "set_job",
    )
    @patch(
        "apps.migration.services."
        "migration_api_service."
        "BackgroundJobService.create_job"
    )
    @patch.object(
        MigrationAPIService,
        "get_batch",
    )
    def test_queue_import_creates_job(
        self,
        get_batch_mock,
        create_job_mock,
        set_job_mock,
    ):
        batch = self.make_batch()
        job = SimpleNamespace(
            id="job-2",
        )

        get_batch_mock.return_value = batch
        create_job_mock.return_value = job

        result = (
            MigrationAPIService
            .queue_import(
                organization=self.organization,
                created_by=self.user,
                batch_id="batch-1",
            )
        )

        get_batch_mock.assert_called_once_with(
            organization=self.organization,
            batch_id="batch-1",
        )

        create_job_mock.assert_called_once_with(
            organization=self.organization,
            created_by=self.user,
            job_type="DATA_MIGRATION_IMPORT",
            payload={
                "batch_id": "batch-1",
            },
            idempotency_key=(
                "DATA_MIGRATION_IMPORT:"
                "batch-1"
            ),
        )

        set_job_mock.assert_called_once_with(
            batch=batch,
            job_id="job-2",
        )

        self.assertIs(
            result["batch"],
            batch,
        )

        self.assertIs(
            result["job"],
            job,
        )