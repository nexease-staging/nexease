from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import (
    patch,
)

from apps.migration.services.migration_preview_service import (
    MigrationPreviewError,
    MigrationPreviewService,
)


class MigrationPreviewServiceTestCase(
    TestCase,
):

    def setUp(self):
        self.organization = (
            SimpleNamespace(
                id="organization-1",
            )
        )

        self.batch = SimpleNamespace(
            organization=self.organization,
            status="UPLOADED",
            upload_id="upload-1",
            migration_type="PRODUCTS",
            mapping={
                "sku": "Item Code",
                "name": "Item Name",
                "category": "Group",
                "unit": "UOM",
            },
        )

        self.upload = SimpleNamespace(
            organization=self.organization,
            purpose="DATA_MIGRATION",
            status="AVAILABLE",
            filename="products.csv",
            content=b"file-content",
        )

    # ==================================================
    # SUCCESS
    # ==================================================

    @patch(
        "apps.migration.services."
        "migration_preview_service."
        "MigrationBatchService.complete_validation"
    )
    @patch(
        "apps.migration.services."
        "migration_preview_service."
        "MigrationRowValidationService.validate_rows"
    )
    @patch(
        "apps.migration.services."
        "migration_preview_service."
        "MigrationBatchService.start_validation"
    )
    @patch(
        "apps.migration.services."
        "migration_preview_service."
        "MigrationMappingService.apply_mapping"
    )
    @patch(
        "apps.migration.services."
        "migration_preview_service."
        "MigrationMappingService.validate_mapping"
    )
    @patch(
        "apps.migration.services."
        "migration_preview_service."
        "MigrationFileParser.read_rows"
    )
    @patch(
        "apps.migration.services."
        "migration_preview_service."
        "BackgroundUploadRepository.get_by_id"
    )
    def test_validate_batch_success(
        self,
        get_upload_mock,
        read_rows_mock,
        validate_mapping_mock,
        apply_mapping_mock,
        start_validation_mock,
        validate_rows_mock,
        complete_validation_mock,
    ):
        get_upload_mock.return_value = (
            self.upload
        )

        read_rows_mock.return_value = {
            "columns": [
                "Item Code",
                "Item Name",
                "Group",
                "UOM",
            ],
            "rows": [
                {
                    "Item Code": "ITEM-001",
                    "Item Name": "Keyboard",
                    "Group": "Electronics",
                    "UOM": "PCS",
                },
            ],
            "total_rows": 1,
            "sheet_name": None,
        }

        validate_mapping_mock.return_value = {
            "valid": True,
            "errors": [],
        }

        mapped_rows = [
            {
                "sku": "ITEM-001",
                "name": "Keyboard",
                "category": "Electronics",
                "unit": "PCS",
            },
        ]

        apply_mapping_mock.return_value = (
            mapped_rows
        )

        validation_rows = [
            {
                "row_number": 2,
                "valid": True,
                "errors": [],
                "normalized": {
                    "sku": "ITEM-001",
                },
            },
        ]

        validate_rows_mock.return_value = {
            "migration_type": "PRODUCTS",
            "total_rows": 1,
            "valid_rows": 1,
            "invalid_rows": 0,
            "can_import": True,
            "rows": validation_rows,
        }

        result = (
            MigrationPreviewService
            .validate_batch(
                batch=self.batch,
                organization=self.organization,
            )
        )

        self.assertTrue(
            result["can_import"]
        )

        self.assertEqual(
            result["total_rows"],
            1,
        )

        get_upload_mock.assert_called_once_with(
            organization=self.organization,
            upload_id="upload-1",
        )

        apply_mapping_mock.assert_called_once_with(
            rows=read_rows_mock
            .return_value["rows"],
            mapping=self.batch.mapping,
        )

        validate_rows_mock.assert_called_once_with(
            organization=self.organization,
            migration_type="PRODUCTS",
            rows=mapped_rows,
            skip_duplicates=False,
        )

        start_validation_mock.assert_called_once_with(
            batch=self.batch,
        )

        complete_validation_mock.assert_called_once()

    # ==================================================
    # TENANT / UPLOAD SAFETY
    # ==================================================

    def test_rejects_wrong_organization(
        self,
    ):
        other_organization = (
            SimpleNamespace(
                id="organization-2",
            )
        )

        with self.assertRaises(
            MigrationPreviewError
        ):
            (
                MigrationPreviewService
                .validate_batch(
                    batch=self.batch,
                    organization=(
                        other_organization
                    ),
                )
            )

    def test_requires_uploaded_status(
        self,
    ):
        self.batch.status = "VALIDATED"

        with self.assertRaises(
            MigrationPreviewError
        ):
            (
                MigrationPreviewService
                .validate_batch(
                    batch=self.batch,
                    organization=(
                        self.organization
                    ),
                )
            )

    @patch(
        "apps.migration.services."
        "migration_preview_service."
        "BackgroundUploadRepository.get_by_id"
    )
    def test_upload_lookup_is_tenant_scoped(
        self,
        get_upload_mock,
    ):
        get_upload_mock.return_value = None

        with self.assertRaises(
            MigrationPreviewError
        ):
            (
                MigrationPreviewService
                .validate_batch(
                    batch=self.batch,
                    organization=(
                        self.organization
                    ),
                )
            )

        get_upload_mock.assert_called_once_with(
            organization=self.organization,
            upload_id="upload-1",
        )

    @patch(
        "apps.migration.services."
        "migration_preview_service."
        "BackgroundUploadRepository.get_by_id"
    )
    def test_rejects_wrong_upload_purpose(
        self,
        get_upload_mock,
    ):
        self.upload.purpose = (
            "BANK_STATEMENT_IMPORT"
        )

        get_upload_mock.return_value = (
            self.upload
        )

        with self.assertRaises(
            MigrationPreviewError
        ):
            (
                MigrationPreviewService
                .validate_batch(
                    batch=self.batch,
                    organization=(
                        self.organization
                    ),
                )
            )

    @patch(
        "apps.migration.services."
        "migration_preview_service."
        "BackgroundUploadRepository.get_by_id"
    )
    def test_rejects_consumed_upload(
        self,
        get_upload_mock,
    ):
        self.upload.status = "CONSUMED"

        get_upload_mock.return_value = (
            self.upload
        )

        with self.assertRaises(
            MigrationPreviewError
        ):
            (
                MigrationPreviewService
                .validate_batch(
                    batch=self.batch,
                    organization=(
                        self.organization
                    ),
                )
            )

    # ==================================================
    # MAPPING
    # ==================================================

    @patch(
        "apps.migration.services."
        "migration_preview_service."
        "MigrationMappingService.validate_mapping"
    )
    @patch(
        "apps.migration.services."
        "migration_preview_service."
        "MigrationFileParser.read_rows"
    )
    @patch(
        "apps.migration.services."
        "migration_preview_service."
        "BackgroundUploadRepository.get_by_id"
    )
    def test_invalid_mapping_rejected_before_validation(
        self,
        get_upload_mock,
        read_rows_mock,
        validate_mapping_mock,
    ):
        get_upload_mock.return_value = (
            self.upload
        )

        read_rows_mock.return_value = {
            "columns": [
                "Item Code",
            ],
            "rows": [],
            "total_rows": 0,
            "sheet_name": None,
        }

        validate_mapping_mock.return_value = {
            "valid": False,
            "errors": [
                {
                    "code":
                        "REQUIRED_MAPPING_MISSING",
                },
            ],
        }

        with self.assertRaises(
            MigrationPreviewError
        ):
            (
                MigrationPreviewService
                .validate_batch(
                    batch=self.batch,
                    organization=(
                        self.organization
                    ),
                )
            )

    # ==================================================
    # FAILURE RECOVERY
    # ==================================================

    @patch(
        "apps.migration.services."
        "migration_preview_service."
        "MigrationBatchService.fail_validation"
    )
    @patch(
        "apps.migration.services."
        "migration_preview_service."
        "MigrationRowValidationService.validate_rows"
    )
    @patch(
        "apps.migration.services."
        "migration_preview_service."
        "MigrationBatchService.start_validation"
    )
    @patch(
        "apps.migration.services."
        "migration_preview_service."
        "MigrationMappingService.apply_mapping"
    )
    @patch(
        "apps.migration.services."
        "migration_preview_service."
        "MigrationMappingService.validate_mapping"
    )
    @patch(
        "apps.migration.services."
        "migration_preview_service."
        "MigrationFileParser.read_rows"
    )
    @patch(
        "apps.migration.services."
        "migration_preview_service."
        "BackgroundUploadRepository.get_by_id"
    )
    def test_validator_exception_marks_batch_failed(
        self,
        get_upload_mock,
        read_rows_mock,
        validate_mapping_mock,
        apply_mapping_mock,
        start_validation_mock,
        validate_rows_mock,
        fail_validation_mock,
    ):
        get_upload_mock.return_value = (
            self.upload
        )

        read_rows_mock.return_value = {
            "columns": [
                "Item Code",
                "Item Name",
                "Group",
                "UOM",
            ],
            "rows": [],
            "total_rows": 0,
            "sheet_name": None,
        }

        validate_mapping_mock.return_value = {
            "valid": True,
            "errors": [],
        }

        apply_mapping_mock.return_value = []

        validate_rows_mock.side_effect = (
            RuntimeError(
                "Unexpected validator failure."
            )
        )

        with self.assertRaises(
            RuntimeError
        ):
            (
                MigrationPreviewService
                .validate_batch(
                    batch=self.batch,
                    organization=(
                        self.organization
                    ),
                )
            )

        start_validation_mock.assert_called_once_with(
            batch=self.batch,
        )

        fail_validation_mock.assert_called_once_with(
            batch=self.batch,
            error_summary=(
                "Unexpected validator failure."
            ),
        )

    @patch(
        "apps.migration.services."
        "migration_preview_service."
        "MigrationBatchService.complete_validation"
    )
    @patch(
        "apps.migration.services."
        "migration_preview_service."
        "MigrationRowValidationService.validate_rows"
    )
    @patch(
        "apps.migration.services."
        "migration_preview_service."
        "MigrationBatchService.start_validation"
    )
    @patch(
        "apps.migration.services."
        "migration_preview_service."
        "MigrationMappingService.apply_mapping"
    )
    @patch(
        "apps.migration.services."
        "migration_preview_service."
        "MigrationMappingService.validate_mapping"
    )
    @patch(
        "apps.migration.services."
        "migration_preview_service."
        "MigrationFileParser.read_rows"
    )
    @patch(
        "apps.migration.services."
        "migration_preview_service."
        "BackgroundUploadRepository.get_by_id"
    )
    def test_validate_batch_forwards_skip_duplicates(
        self,
        get_upload_mock,
        read_rows_mock,
        validate_mapping_mock,
        apply_mapping_mock,
        start_validation_mock,
        validate_rows_mock,
        complete_validation_mock,
    ):
        self.batch.options = {
            "skip_duplicates": True,
        }

        get_upload_mock.return_value = (
            self.upload
        )

        read_rows_mock.return_value = {
            "columns": [
                "Item Code",
                "Item Name",
                "Group",
                "UOM",
            ],
            "rows": [
                {
                    "Item Code": "ITEM-001",
                    "Item Name": "Keyboard",
                    "Group": "Electronics",
                    "UOM": "PCS",
                },
            ],
            "total_rows": 1,
            "sheet_name": None,
        }

        validate_mapping_mock.return_value = {
            "valid": True,
            "errors": [],
        }

        mapped_rows = [
            {
                "sku": "ITEM-001",
                "name": "Keyboard",
                "category": "Electronics",
                "unit": "PCS",
            },
        ]

        apply_mapping_mock.return_value = (
            mapped_rows
        )

        validation_rows = [
            {
                "row_number": 2,
                "valid": True,
                "skipped": True,
                "errors": [
                    {
                        "code":
                            "ALREADY_EXISTS",
                    },
                ],
                "normalized": {
                    "sku": "ITEM-001",
                },
            },
        ]

        validate_rows_mock.return_value = {
            "migration_type": "PRODUCTS",
            "total_rows": 1,
            "valid_rows": 1,
            "invalid_rows": 0,
            "can_import": True,
            "rows": validation_rows,
        }

        result = (
            MigrationPreviewService
            .validate_batch(
                batch=self.batch,
                organization=(
                    self.organization
                ),
            )
        )

        self.assertTrue(
            result["can_import"]
        )

        validate_rows_mock.assert_called_once_with(
            organization=self.organization,
            migration_type="PRODUCTS",
            rows=mapped_rows,
            skip_duplicates=True,
        )