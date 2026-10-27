from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase

from apps.core.repositories.background_upload_repository import (
    BackgroundUploadRepository,
)
from apps.core.services.background_upload_service import (
    BackgroundUploadService,
)
from apps.migration.services.migration_api_service import (
    MigrationAPIService,
)
from apps.migration.services.migration_batch_service import (
    MigrationBatchService,
)
from apps.migration.services.migration_file_parser import (
    MigrationFileParser,
    MigrationFileParserError,
)


class MigrationUploadServiceTestCase(
    SimpleTestCase
):

    def setUp(self):
        self.organization = SimpleNamespace(
            id="organization-1",
        )

        self.user = SimpleNamespace(
            id="user-1",
            organization=self.organization,
            is_active=True,
        )

        self.batch = SimpleNamespace(
            id="batch-1",
            organization=self.organization,
            created_by=self.user,
            status="CREATED",
            upload_id=None,
        )

        self.upload = SimpleNamespace(
            id="upload-1",
            organization=self.organization,
            uploaded_by=self.user,
            filename="products.csv",
            content=(
                b"SKU,Name\n"
                b"P-001,Keyboard\n"
            ),
            status="AVAILABLE",
        )

        self.uploaded_file = (
            SimpleNamespace(
                name="products.csv",
                size=len(
                    self.upload.content
                ),
            )
        )

    @patch.object(
        MigrationBatchService,
        "attach_upload",
    )
    @patch.object(
        MigrationFileParser,
        "parse",
    )
    @patch.object(
        BackgroundUploadService,
        "create_data_migration_upload",
    )
    def test_successful_upload_is_attached(
        self,
        create_upload_mock,
        parse_mock,
        attach_mock,
    ):
        create_upload_mock.return_value = (
            self.upload
        )

        parse_mock.return_value = {
            "extension": ".csv",
            "columns": [
                "SKU",
                "Name",
            ],
            "total_rows": 1,
            "sample_rows": [
                {
                    "SKU": "P-001",
                    "Name": "Keyboard",
                }
            ],
        }

        uploaded_batch = SimpleNamespace(
            **{
                **self.batch.__dict__,
                "status": "UPLOADED",
                "upload_id": self.upload.id,
            }
        )

        attach_mock.return_value = (
            uploaded_batch
        )

        # Adapt only these arguments if your
        # current upload_file signature differs.
        result = MigrationAPIService.upload_file(
            user=self.user,
            batch=self.batch,
            uploaded_file=self.uploaded_file,
        )

        create_upload_mock.assert_called_once()

        parse_mock.assert_called_once_with(
            filename="products.csv",
            content=self.upload.content,
        )

        attach_mock.assert_called_once()

        self.assertIsNotNone(result)


    @patch.object(
        BackgroundUploadRepository,
        "mark_failed",
    )
    @patch.object(
        MigrationBatchService,
        "attach_upload",
    )
    @patch.object(
        MigrationFileParser,
        "parse",
    )
    @patch.object(
        BackgroundUploadService,
        "create_data_migration_upload",
    )
    def test_parser_failure_marks_upload_failed(
        self,
        create_upload_mock,
        parse_mock,
        attach_mock,
        mark_failed_mock,
    ):
        create_upload_mock.return_value = (
            self.upload
        )

        parse_mock.side_effect = (
            MigrationFileParserError(
                "Migration file is empty."
            )
        )

        with self.assertRaises(
            MigrationFileParserError
        ):
            MigrationAPIService.upload_file(
                user=self.user,
                batch=self.batch,
                uploaded_file=self.uploaded_file,
            )

        mark_failed_mock.assert_called_once_with(
            upload=self.upload,
        )

        attach_mock.assert_not_called()

        self.assertEqual(
            self.batch.status,
            "CREATED",
        )

        self.assertIsNone(
            self.batch.upload_id
        )


    @patch.object(
        BackgroundUploadRepository,
        "mark_failed",
    )
    @patch.object(
        MigrationBatchService,
        "attach_upload",
    )
    @patch.object(
        MigrationFileParser,
        "parse",
    )
    @patch.object(
        BackgroundUploadService,
        "create_data_migration_upload",
    )
    def test_attach_failure_marks_upload_failed(
        self,
        create_upload_mock,
        parse_mock,
        attach_mock,
        mark_failed_mock,
    ):
        create_upload_mock.return_value = (
            self.upload
        )

        parse_mock.return_value = {
            "extension": ".csv",
            "columns": ["SKU"],
            "total_rows": 1,
            "sample_rows": [
                {
                    "SKU": "P-001",
                }
            ],
        }

        attach_mock.side_effect = ValueError(
            "Unable to attach migration upload."
        )

        with self.assertRaisesRegex(
            ValueError,
            "Unable to attach migration upload",
        ):
            MigrationAPIService.upload_file(
                user=self.user,
                batch=self.batch,
                uploaded_file=self.uploaded_file,
            )

        mark_failed_mock.assert_called_once_with(
            upload=self.upload,
        )