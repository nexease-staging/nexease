import json

from datetime import (
    datetime,
)
from decimal import (
    Decimal,
)
from types import (
    SimpleNamespace,
)
from unittest.mock import (
    patch,
)

from bson import (
    ObjectId,
)

from django.core.files.uploadedfile import (
    SimpleUploadedFile,
)
from django.test import (
    Client,
    SimpleTestCase,
)

from apps.core.services.background_job_service import (
    BackgroundJobService,
)
from apps.core.services.background_upload_service import (
    BackgroundUploadService,
)

from apps.authorization.services import (
    AuthorizationService,
)
from apps.core.services.api_query_pipeline_service import (
    APIQueryPipelineService,
)
from apps.core.services.api_rate_limit_service import (
    APIRateLimitService,
)
from apps.core.services.application_logging_service import (
    ApplicationLoggingService,
)
from apps.core.services.mongodb_error_logging_service import (
    MongoDBErrorLoggingService,
)
from apps.finance.api.v1.serializers import (
    BankStatementAPISerializer,
)
from apps.finance.importers.bank_statement_parser import (
    BankStatementParser,
)
from apps.finance.repositories.bank_statement_repository import (
    BankStatementRepository,
)
from apps.finance.services.bank_statement_api_service import (
    BankStatementAPIService,
    BankStatementAPIStateError,
)
from apps.organizations.api_context_service import (
    APIOrganizationContextService,
)


class BankStatementAPIV1RegressionTestCase(
    SimpleTestCase
):

    STATEMENTS_URL = (
        "/api/v1/bank-statements/"
    )

    def setUp(self):
        now = datetime.utcnow()

        self.organization = SimpleNamespace(
            id=ObjectId(),
            name="Test Organization",
        )

        self.user = SimpleNamespace(
            id=ObjectId(),
            organization=self.organization,
            email="admin@example.com",
            first_name="Test",
            last_name="Admin",
            is_active=True,
        )

        self.bank_account = SimpleNamespace(
            id=ObjectId(),
            organization=self.organization,
            account_name="Operating Bank",
        )

        self.statement = SimpleNamespace(
            id=ObjectId(),
            organization=self.organization,
            statement_number="BST-TEST000001",
            bank_account=self.bank_account,
            statement_start_date=now,
            statement_end_date=now,
            opening_balance=Decimal("1000.00"),
            closing_balance=Decimal("1250.00"),
            source_filename="statement.csv",
            source_type="CSV",
            status="IMPORTED",
            lines=[],
            created_by=self.user,
            reconciled_at=None,
            cancelled_at=None,
            created_at=now,
            updated_at=now,
        )

        self.line = SimpleNamespace(
            line_number=1,
            transaction_date=now,
            value_date=now,
            description="Customer receipt",
            external_reference="UTR-TEST-001",
            debit_amount=Decimal("0.00"),
            credit_amount=Decimal("250.00"),
            running_balance=Decimal("1250.00"),
            match_status="UNMATCHED",
            matched_transaction=None,
            matched_at=None,
        )

        self.statement.lines = [
            self.line,
        ]

        self.organization_context = {
            "user": self.user,
            "organization": self.organization,
        }

        self.patchers = [
            patch.object(
                ApplicationLoggingService,
                "log",
                return_value=None,
            ),
            patch.object(
                MongoDBErrorLoggingService,
                "log_exception",
                return_value=None,
            ),
            patch.object(
                APIOrganizationContextService,
                "resolve",
                return_value=(
                    self.organization_context
                ),
            ),
            patch.object(
                AuthorizationService,
                "has_permission",
                return_value=True,
            ),
            patch.object(
                APIRateLimitService,
                "check",
                return_value={
                    "allowed": True,
                },
            ),
            patch.object(
                APIRateLimitService,
                "add_headers",
                side_effect=(
                    lambda response, result:
                    response
                ),
            ),
        ]

        for patcher in self.patchers:
            patcher.start()

        self.client = Client(
            raise_request_exception=False
        )

    def tearDown(self):
        for patcher in reversed(
            self.patchers
        ):
            patcher.stop()

    def detail_url(self):
        return (
            f"{self.STATEMENTS_URL}"
            f"{self.statement.id}/"
        )

    def cancel_url(self):
        return (
            f"{self.detail_url()}cancel/"
        )

    def line_url(
        self,
        action,
    ):
        return (
            f"{self.detail_url()}lines/"
            f"{self.line.line_number}/"
            f"{action}/"
        )

    def assert_success_contract(
        self,
        response,
        expected_status=200,
    ):
        body = response.json()

        self.assertEqual(
            response.status_code,
            expected_status,
        )
        self.assertTrue(
            body["success"]
        )
        self.assertIn(
            "data",
            body,
        )
        self.assertTrue(
            body.get("request_id")
        )
        self.assertEqual(
            response.headers.get(
                "X-Request-ID"
            ),
            body["request_id"],
        )
        self.assertEqual(
            response.headers.get(
                "Cache-Control"
            ),
            "no-store",
        )

        return body

    def assert_error_contract(
        self,
        response,
        expected_status,
        expected_code,
    ):
        body = response.json()

        self.assertEqual(
            response.status_code,
            expected_status,
        )
        self.assertFalse(
            body["success"]
        )
        self.assertEqual(
            body["error"]["code"],
            expected_code,
        )
        self.assertTrue(
            body.get("request_id")
        )

        return body

    def test_collection_returns_paginated_data(
        self,
    ):
        pipeline_result = {
            "items": [self.statement],
            "pagination": {
                "page": 1,
                "page_size": 25,
                "total_items": 1,
                "total_pages": 1,
                "has_next": False,
                "has_previous": False,
            },
            "query": {
                "filters": {},
                "search": None,
                "sort": [
                    "-statement_end_date",
                    "id",
                ],
            },
        }

        with (
            patch.object(
                BankStatementRepository,
                "queryset_for_organization",
                return_value=object(),
            ),
            patch.object(
                APIQueryPipelineService,
                "execute",
                return_value=pipeline_result,
            ),
            patch.object(
                BankStatementAPISerializer,
                "serialize_many",
                return_value=[
                    {
                        "id": str(self.statement.id),
                        "statement_number": (
                            self.statement.statement_number
                        ),
                    },
                ],
            ),
        ):
            response = self.client.get(
                self.STATEMENTS_URL
            )

        body = self.assert_success_contract(
            response
        )

        self.assertEqual(
            body["data"]["bank_statements"][0][
                "statement_number"
            ],
            "BST-TEST000001",
        )

    def test_import_csv_queues_background_job(
        self,
    ):
        upload_file = SimpleUploadedFile(
            "statement.csv",
            (
                b"date,description,debit,credit\n"
                b"2026-08-10,Customer payment,0,250\n"
            ),
            content_type="text/csv",
        )

        stored_upload = SimpleNamespace(
            id=ObjectId(),
        )

        now = datetime.utcnow()

        job = SimpleNamespace(
            id=ObjectId(),
            job_type="BANK_STATEMENT_IMPORT",
            status="PENDING",
            attempts=0,
            max_attempts=3,
            created_at=now,
        )

        with (
            patch.object(
                BackgroundUploadService,
                "store_bank_statement",
                return_value=stored_upload,
            ) as upload_mock,
            patch.object(
                BackgroundJobService,
                "create_job",
                return_value=job,
            ) as job_mock,
        ):
            response = self.client.post(
                self.STATEMENTS_URL,
                data={
                    "file": upload_file,
                    "bank_account_id": str(
                        self.bank_account.id
                    ),
                    "statement_start_date":
                        "2026-08-01",
                    "statement_end_date":
                        "2026-08-31",
                    "opening_balance":
                        "1000.00",
                    "closing_balance":
                        "1250.00",
                },
            )

        body = self.assert_success_contract(
            response,
            202,
        )

        self.assertEqual(
            body["data"]["job"]["id"],
            str(job.id),
        )

        self.assertEqual(
            body["data"]["job"]["job_type"],
            "BANK_STATEMENT_IMPORT",
        )

        self.assertEqual(
            body["data"]["job"]["status"],
            "PENDING",
        )

        upload_mock.assert_called_once()

        upload_kwargs = (
            upload_mock.call_args.kwargs
        )

        self.assertIs(
            upload_kwargs["organization"],
            self.organization,
        )

        self.assertIs(
            upload_kwargs["uploaded_by"],
            self.user,
        )

        job_mock.assert_called_once()

        job_kwargs = (
            job_mock.call_args.kwargs
        )

        self.assertIs(
            job_kwargs["organization"],
            self.organization,
        )

        self.assertIs(
            job_kwargs["created_by"],
            self.user,
        )

        self.assertEqual(
            job_kwargs["job_type"],
            "BANK_STATEMENT_IMPORT",
        )

        self.assertEqual(
            job_kwargs["payload"],
            {
                "upload_id":
                    str(stored_upload.id),
                "bank_account_id":
                    str(self.bank_account.id),
                "statement_start_date":
                    "2026-08-01",
                "statement_end_date":
                    "2026-08-31",
                "opening_balance":
                    "1000.00",
                "closing_balance":
                    "1250.00",
            },
        )

        self.assertEqual(
            job_kwargs["idempotency_key"],
            (
                "BANK_STATEMENT_IMPORT:"
                f"{stored_upload.id}"
            ),
        )

    def test_detail_returns_statement(
        self,
    ):
        with (
            patch.object(
                BankStatementAPIService,
                "get_statement",
                return_value=self.statement,
            ),
            patch.object(
                BankStatementAPISerializer,
                "serialize_detail",
                return_value={
                    "id": str(self.statement.id),
                    "status": "IMPORTED",
                },
            ),
        ):
            response = self.client.get(
                self.detail_url()
            )

        body = self.assert_success_contract(
            response
        )
        self.assertEqual(
            body["data"]["bank_statement"][
                "status"
            ],
            "IMPORTED",
        )

    def test_cancel_returns_cancelled_statement(
        self,
    ):
        cancelled = SimpleNamespace(
            **{
                **vars(self.statement),
                "status": "CANCELLED",
                "cancelled_at": datetime.utcnow(),
            }
        )

        with (
            patch.object(
                BankStatementAPIService,
                "cancel_statement",
                return_value=cancelled,
            ),
            patch.object(
                BankStatementAPISerializer,
                "serialize_detail",
                return_value={
                    "id": str(cancelled.id),
                    "status": "CANCELLED",
                },
            ),
        ):
            response = self.client.post(
                self.cancel_url()
            )

        body = self.assert_success_contract(
            response
        )
        self.assertEqual(
            body["data"]["bank_statement"][
                "status"
            ],
            "CANCELLED",
        )

    def test_auto_match_returns_updated_line(
        self,
    ):
        result = {
            "statement": self.statement,
            "line": self.line,
        }

        with (
            patch.object(
                BankStatementAPIService,
                "auto_match_line",
                return_value=result,
            ) as match_mock,
            patch.object(
                BankStatementAPISerializer,
                "serialize_summary",
                return_value={
                    "id": str(self.statement.id),
                },
            ),
            patch.object(
                BankStatementAPISerializer,
                "serialize_line",
                return_value={
                    "line_number": 1,
                    "match_status": "MATCHED",
                },
            ),
        ):
            response = self.client.post(
                self.line_url("auto-match")
            )

        body = self.assert_success_contract(
            response
        )
        self.assertEqual(
            body["data"]["line"][
                "match_status"
            ],
            "MATCHED",
        )
        match_mock.assert_called_once_with(
            user=self.user,
            organization=self.organization,
            statement_id=str(self.statement.id),
            line_number="1",
            date_tolerance_days=2,
        )

    def test_manual_match_passes_transaction_id(
        self,
    ):
        transaction_id = str(ObjectId())
        result = {
            "statement": self.statement,
            "line": self.line,
            "transaction": None,
        }

        with (
            patch.object(
                BankStatementAPIService,
                "match_line",
                return_value=result,
            ) as match_mock,
            patch.object(
                BankStatementAPISerializer,
                "serialize_summary",
                return_value={
                    "id": str(self.statement.id),
                },
            ),
            patch.object(
                BankStatementAPISerializer,
                "serialize_line",
                return_value={
                    "line_number": 1,
                    "match_status": "MATCHED",
                },
            ),
        ):
            response = self.client.post(
                self.line_url("match"),
                data=json.dumps(
                    {
                        "transaction_id": transaction_id,
                    }
                ),
                content_type="application/json",
            )

        self.assert_success_contract(response)
        match_mock.assert_called_once_with(
            user=self.user,
            organization=self.organization,
            statement_id=str(self.statement.id),
            line_number="1",
            transaction_id=transaction_id,
        )

    def test_ignore_returns_ignored_line(
        self,
    ):
        result = {
            "statement": self.statement,
            "line": self.line,
        }

        with (
            patch.object(
                BankStatementAPIService,
                "ignore_line",
                return_value=result,
            ),
            patch.object(
                BankStatementAPISerializer,
                "serialize_summary",
                return_value={
                    "id": str(self.statement.id),
                },
            ),
            patch.object(
                BankStatementAPISerializer,
                "serialize_line",
                return_value={
                    "line_number": 1,
                    "match_status": "IGNORED",
                },
            ),
        ):
            response = self.client.post(
                self.line_url("ignore")
            )

        body = self.assert_success_contract(
            response
        )
        self.assertEqual(
            body["data"]["line"][
                "match_status"
            ],
            "IGNORED",
        )

    def test_cancel_state_error_returns_422(
        self,
    ):
        with patch.object(
            BankStatementAPIService,
            "cancel_statement",
            side_effect=(
                BankStatementAPIStateError(
                    message=(
                        "Reconciled statements cannot "
                        "be cancelled."
                    ),
                )
            ),
        ):
            response = self.client.post(
                self.cancel_url()
            )

        self.assert_error_contract(
            response,
            422,
            "UNPROCESSABLE_ENTITY",
        )

    def test_invalid_statement_id_returns_400(
        self,
    ):
        response = self.client.get(
            (
                f"{self.STATEMENTS_URL}"
                "invalid-id/"
            )
        )

        self.assert_error_contract(
            response,
            400,
            "VALIDATION_ERROR",
        )

    def test_collection_rejects_permission(
        self,
    ):
        with patch.object(
            AuthorizationService,
            "has_permission",
            return_value=False,
        ):
            response = self.client.get(
                self.STATEMENTS_URL
            )

        self.assert_error_contract(
            response,
            403,
            "FORBIDDEN",
        )

    def test_collection_rejects_put(
        self,
    ):
        response = self.client.put(
            self.STATEMENTS_URL,
            data=json.dumps({}),
            content_type="application/json",
        )

        self.assert_error_contract(
            response,
            405,
            "METHOD_NOT_ALLOWED",
        )

