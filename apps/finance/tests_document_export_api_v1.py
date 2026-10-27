import json

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import patch

from bson import ObjectId

from django.test import (
    Client,
    SimpleTestCase,
)

from apps.core.services.background_job_service import (
    BackgroundJobService,
)
from apps.finance.services.document_email_config_service import (
    DocumentEmailConfigService,
)

from apps.authorization.services import (
    AuthorizationService,
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
from apps.finance.services.document_api_service import (
    DocumentAPIService,
    DocumentAPIValidationError,
)
from apps.finance.services.export_api_service import (
    ExportAPIService,
    ExportAPIValidationError,
)
from apps.organizations.api_context_service import (
    APIOrganizationContextService,
)
from apps.finance.services.document_access_log_service import (
    DocumentAccessLogService,
)
from apps.finance.services.document_delivery_log_service import (
    DocumentDeliveryLogService,
)

class DocumentExportAPIV1Tests(
    SimpleTestCase
):

    def setUp(
        self,
    ):
        now = datetime.utcnow()

        self.organization = (
            SimpleNamespace(
                id=ObjectId(),
                name=(
                    "Document Export "
                    "Organization"
                ),
                email=(
                    "documents@example.com"
                ),
                is_active=True,
                created_at=now,
                updated_at=now,
            )
        )

        self.user = (
            SimpleNamespace(
                id=ObjectId(),
                organization=(
                    self.organization
                ),
                email="admin@example.com",
                first_name="System",
                last_name="Administrator",
                is_active=True,
                is_authenticated=True,
                is_anonymous=False,
            )
        )

        self.document_id = str(
            ObjectId()
        )

        self.organization_context = {
            "user":
                self.user,

            "organization":
                self.organization,
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

    def tearDown(
        self,
    ):
        for patcher in reversed(
            self.patchers
        ):
            patcher.stop()

    # ==================================================
    # HELPERS
    # ==================================================

    def document_pdf_url(
        self,
        document_type="INVOICE",
        document_id=None,
    ):
        return (
            "/api/v1/documents/"
            f"{document_type}/"
            f"{document_id or self.document_id}/"
            "pdf/"
        )

    def document_email_url(
        self,
        document_type="INVOICE",
        document_id=None,
    ):
        return (
            "/api/v1/documents/"
            f"{document_type}/"
            f"{document_id or self.document_id}/"
            "email/"
        )

    def export_url(
        self,
        resource_type="trial-balance",
    ):
        return (
            "/api/v1/exports/"
            f"{resource_type}/"
        )

    def assert_error_contract(
        self,
        response,
        status_code,
        code,
    ):
        self.assertEqual(
            response.status_code,
            status_code,
        )

        body = response.json()

        self.assertFalse(
            body[
                "success"
            ]
        )

        self.assertEqual(
            body[
                "error"
            ][
                "code"
            ],
            code,
        )

        return body

    # ==================================================
    # PDF DOWNLOAD
    # ==================================================

    def test_document_pdf_returns_pdf(
        self,
    ):
        pdf_bytes = (
            b"%PDF-1.4\n"
            b"test document\n"
        )

        result = {
            "document_type":
                "INVOICE",

            "document_id":
                self.document_id,

            "document_number":
                "INV-TEST-001",

            "filename":
                "INV-TEST-001.pdf",

            "content_type":
                "application/pdf",

            "content":
                pdf_bytes,

            "size":
                len(
                    pdf_bytes
                ),
        }

        with patch.object(
            DocumentAPIService,
            "generate_pdf",
            return_value=result,
        ) as service_mock:
            response = self.client.get(
                self.document_pdf_url()
            )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response[
                "Content-Type"
            ],
            "application/pdf",
        )

        self.assertEqual(
            response.content,
            pdf_bytes,
        )

        self.assertEqual(
            response[
                "Content-Disposition"
            ],
            (
                'attachment; filename="'
                'INV-TEST-001.pdf"'
            ),
        )

        self.assertEqual(
            response[
                "Content-Length"
            ],
            str(
                len(
                    pdf_bytes
                )
            ),
        )

        service_mock.assert_called_once_with(
            user=self.user,
            organization=self.organization,
            document_type="INVOICE",
            document_id=self.document_id,
        )

    def test_document_pdf_rejects_permission(
        self,
    ):
        with patch.object(
            AuthorizationService,
            "has_permission",
            return_value=False,
        ):
            response = self.client.get(
                self.document_pdf_url()
            )

        self.assert_error_contract(
            response,
            403,
            "FORBIDDEN",
        )

    def test_document_pdf_rejects_post(
        self,
    ):
        response = self.client.post(
            self.document_pdf_url()
        )

        self.assert_error_contract(
            response,
            405,
            "METHOD_NOT_ALLOWED",
        )

    def test_document_pdf_returns_not_found(
        self,
    ):
        with patch.object(
            DocumentAPIService,
            "generate_pdf",
            return_value=None,
        ):
            response = self.client.get(
                self.document_pdf_url()
            )

        self.assert_error_contract(
            response,
            404,
            "NOT_FOUND",
        )

    def test_document_pdf_rejects_invalid_id(
        self,
    ):
        with patch.object(
            DocumentAPIService,
            "generate_pdf",
            side_effect=(
                DocumentAPIValidationError(
                    "Invalid document ID."
                )
            ),
        ):
            response = self.client.get(
                self.document_pdf_url(
                    document_id="invalid-id"
                )
            )

        self.assert_error_contract(
            response,
            400,
            "VALIDATION_ERROR",
        )

    def test_document_pdf_rejects_unknown_type(
        self,
    ):
        response = self.client.get(
            self.document_pdf_url(
                document_type=(
                    "UNKNOWN_DOCUMENT"
                )
            )
        )

        self.assert_error_contract(
            response,
            400,
            "VALIDATION_ERROR",
        )

    # ==================================================
    # EMAIL DELIVERY
    # ==================================================

    def test_document_email_queues_document(
        self,
    ):
        document = SimpleNamespace(
            id=ObjectId(
                self.document_id
            ),
        )

        job = SimpleNamespace(
            id=ObjectId(),
            job_type="DOCUMENT_EMAIL",
            status="PENDING",
            attempts=0,
            max_attempts=3,
            created_at=datetime.utcnow(),
        )

        with (
            patch.object(
                DocumentEmailConfigService,
                "get_document",
                return_value=document,
            ),
            patch.object(
                BackgroundJobService,
                "create_job",
                return_value=job,
            ) as job_mock,
        ):
            response = self.client.post(
                self.document_email_url(),
                data=json.dumps(
                    {}
                ),
                content_type=(
                    "application/json"
                ),
            )

        self.assertEqual(
            response.status_code,
            202,
        )

        body = response.json()

        self.assertTrue(
            body["success"]
        )

        data = body["data"]

        self.assertEqual(
            data["document_type"],
            "INVOICE",
        )

        self.assertEqual(
            data["document_id"],
            self.document_id,
        )

        self.assertEqual(
            data["job"]["job_type"],
            "DOCUMENT_EMAIL",
        )

        self.assertEqual(
            data["job"]["status"],
            "PENDING",
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
            "DOCUMENT_EMAIL",
        )

        self.assertEqual(
            job_kwargs["payload"],
            {
                "document_type":
                    "INVOICE",
                "document_id":
                    self.document_id,
                "recipient_email":
                    None,
                "subject":
                    None,
                "message":
                    None,
            },
        )

        self.assertTrue(
            job_kwargs[
                "idempotency_key"
            ].startswith(
                "DOCUMENT_EMAIL:"
            )
        )

    def test_document_email_accepts_overrides(
        self,
    ):
        document = SimpleNamespace(
            id=ObjectId(
                self.document_id
            ),
        )

        job = SimpleNamespace(
            id=ObjectId(),
            job_type="DOCUMENT_EMAIL",
            status="PENDING",
            attempts=0,
            max_attempts=3,
            created_at=datetime.utcnow(),
        )

        payload = {
            "recipient_email":
                "override@example.com",
            "subject":
                "Custom subject",
            "message":
                "Custom message",
        }

        with (
            patch.object(
                DocumentEmailConfigService,
                "get_document",
                return_value=document,
            ),
            patch.object(
                BackgroundJobService,
                "create_job",
                return_value=job,
            ) as job_mock,
        ):
            response = self.client.post(
                self.document_email_url(),
                data=json.dumps(
                    payload
                ),
                content_type=(
                    "application/json"
                ),
            )

        self.assertEqual(
            response.status_code,
            202,
        )

        job_mock.assert_called_once()

        job_payload = (
            job_mock
            .call_args
            .kwargs[
                "payload"
            ]
        )

        self.assertEqual(
            job_payload[
                "recipient_email"
            ],
            "override@example.com",
        )

        self.assertEqual(
            job_payload["subject"],
            "Custom subject",
        )

        self.assertEqual(
            job_payload["message"],
            "Custom message",
        )

    def test_document_email_rejects_permission(
        self,
    ):
        with patch.object(
            AuthorizationService,
            "has_permission",
            return_value=False,
        ):
            response = self.client.post(
                self.document_email_url(),
                data=json.dumps(
                    {}
                ),
                content_type=(
                    "application/json"
                ),
            )

        self.assert_error_contract(
            response,
            403,
            "FORBIDDEN",
        )

    def test_document_email_rejects_get(
        self,
    ):
        response = self.client.get(
            self.document_email_url()
        )

        self.assert_error_contract(
            response,
            405,
            "METHOD_NOT_ALLOWED",
        )

    def test_document_email_requires_json(
        self,
    ):
        response = self.client.post(
            self.document_email_url(),
            data="recipient=test",
            content_type=(
                "application/x-www-form-urlencoded"
            ),
        )

        self.assert_error_contract(
            response,
            400,
            "VALIDATION_ERROR",
        )

    def test_document_email_rejects_invalid_json(
        self,
    ):
        response = self.client.post(
            self.document_email_url(),
            data="{invalid-json",
            content_type=(
                "application/json"
            ),
        )

        self.assert_error_contract(
            response,
            400,
            "VALIDATION_ERROR",
        )

def test_document_email_returns_not_found(
    self,
):
    with (
        patch.object(
            DocumentEmailConfigService,
            "get_document",
            return_value=None,
        ),
        patch.object(
            BackgroundJobService,
            "create_job",
        ) as job_mock,
    ):
        response = self.client.post(
            self.document_email_url(),
            data=json.dumps(
                {}
            ),
            content_type=(
                "application/json"
            ),
        )

    self.assert_error_contract(
        response,
        404,
        "NOT_FOUND",
    )

    job_mock.assert_not_called()

    # ==================================================
    # EXPORT
    # ==================================================

    def test_csv_export_returns_attachment(
        self,
    ):
        csv_bytes = (
            b"account,debit,credit\r\n"
            b"Cash,100,0\r\n"
        )

        result = {
            "resource_type":
                "TRIAL_BALANCE",

            "format":
                "csv",

            "filename":
                "trial_balance.csv",

            "content_type":
                "text/csv; charset=utf-8",

            "content":
                csv_bytes,

            "size":
                len(
                    csv_bytes
                ),
        }

        with patch.object(
            ExportAPIService,
            "export",
            return_value=result,
        ) as service_mock:
            response = self.client.get(
                (
                    self.export_url(
                        "trial-balance"
                    )
                    +
                    "?format=csv"
                )
            )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertTrue(
            response[
                "Content-Type"
            ].startswith(
                "text/csv"
            )
        )

        self.assertEqual(
            response.content,
            csv_bytes,
        )

        self.assertEqual(
            response[
                "Content-Disposition"
            ],
            (
                'attachment; filename="'
                'trial_balance.csv"'
            ),
        )

        service_mock.assert_called_once_with(
            user=self.user,
            organization=self.organization,
            resource_type=(
                "TRIAL_BALANCE"
            ),
            export_format="csv",
            parameters={},
        )

    def test_xlsx_export_returns_attachment(
        self,
    ):
        xlsx_bytes = (
            b"PK\x03\x04"
            b"fake-xlsx"
        )

        result = {
            "resource_type":
                "FINANCE_AUDIT",

            "format":
                "xlsx",

            "filename":
                "finance_audit.xlsx",

            "content_type": (
                "application/vnd."
                "openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),

            "content":
                xlsx_bytes,

            "size":
                len(
                    xlsx_bytes
                ),
        }

        with patch.object(
            ExportAPIService,
            "export",
            return_value=result,
        ):
            response = self.client.get(
                (
                    self.export_url(
                        "finance-audit"
                    )
                    +
                    "?format=xlsx"
                )
            )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.content,
            xlsx_bytes,
        )

        self.assertEqual(
            response[
                "Content-Disposition"
            ],
            (
                'attachment; filename="'
                'finance_audit.xlsx"'
            ),
        )

    def test_export_passes_query_parameters(
        self,
    ):
        csv_bytes = b"a,b\r\n1,2\r\n"

        result = {
            "resource_type":
                "CASH_FLOW",

            "format":
                "csv",

            "filename":
                "cash_flow.csv",

            "content_type":
                "text/csv; charset=utf-8",

            "content":
                csv_bytes,

            "size":
                len(
                    csv_bytes
                ),
        }

        with patch.object(
            ExportAPIService,
            "export",
            return_value=result,
        ) as service_mock:
            response = self.client.get(
                (
                    self.export_url(
                        "cash-flow"
                    )
                    +
                    "?format=csv"
                    "&start_date=2026-08-01"
                    "&end_date=2026-09-01"
                )
            )

        self.assertEqual(
            response.status_code,
            200,
        )

        service_mock.assert_called_once_with(
            user=self.user,
            organization=self.organization,
            resource_type="CASH_FLOW",
            export_format="csv",
            parameters={
                "start_date":
                    "2026-08-01",

                "end_date":
                    "2026-09-01",
            },
        )

    def test_export_rejects_permission(
        self,
    ):
        with patch.object(
            AuthorizationService,
            "has_permission",
            return_value=False,
        ):
            response = self.client.get(
                self.export_url(
                    "trial-balance"
                )
            )

        self.assert_error_contract(
            response,
            403,
            "FORBIDDEN",
        )

    def test_export_rejects_post(
        self,
    ):
        response = self.client.post(
            self.export_url(
                "trial-balance"
            )
        )

        self.assert_error_contract(
            response,
            405,
            "METHOD_NOT_ALLOWED",
        )

    def test_export_rejects_unknown_resource(
        self,
    ):
        response = self.client.get(
            self.export_url(
                "unknown-report"
            )
        )

        self.assert_error_contract(
            response,
            400,
            "VALIDATION_ERROR",
        )

    def test_export_rejects_invalid_format(
        self,
    ):
        with patch.object(
            ExportAPIService,
            "export",
            side_effect=(
                ExportAPIValidationError(
                    details={
                        "format": [
                            (
                                "Export format must "
                                "be csv or xlsx."
                            ),
                        ],
                    },
                )
            ),
        ):
            response = self.client.get(
                (
                    self.export_url(
                        "trial-balance"
                    )
                    +
                    "?format=pdf"
                )
            )

        self.assert_error_contract(
            response,
            400,
            "VALIDATION_ERROR",
        )

    # ==================================================
    # TENANT / SERVICE SECURITY
    # ==================================================

    def test_document_service_rejects_cross_tenant_context(
        self,
    ):
        other_organization = (
            SimpleNamespace(
                id=ObjectId(),
            )
        )

        with self.assertRaises(
            PermissionError
        ):
            (
                DocumentAPIService
                ._check_context(
                    user=self.user,
                    organization=(
                        other_organization
                    ),
                )
            )

    def test_document_service_accepts_matching_tenant(
        self,
    ):
        result = (
            DocumentAPIService
            ._check_context(
                user=self.user,
                organization=(
                    self.organization
                ),
            )
        )

        self.assertIsNone(
            result
        )

    def test_document_service_rejects_invalid_object_id(
        self,
    ):
        with self.assertRaises(
            DocumentAPIValidationError
        ):
            (
                DocumentAPIService
                ._normalize_document_id(
                    "not-an-object-id"
                )
            )

    def test_export_resource_permission_mapping(
        self,
    ):
        self.assertEqual(
            ExportAPIService
            .get_permission(
                "general-ledger"
            ),
            "general_ledger.read",
        )

        self.assertEqual(
            ExportAPIService
            .get_permission(
                "trial-balance"
            ),
            "trial_balance.read",
        )

        self.assertEqual(
            ExportAPIService
            .get_permission(
                "cash-flow"
            ),
            "bank_transactions.read",
        )

        self.assertEqual(
            ExportAPIService
            .get_permission(
                "finance-audit"
            ),
            "bank_transactions.read",
        )

    # ==================================================
    # DOCUMENT ACCESS LOGS
    # ==================================================

    def test_document_access_logs_returns_data(
        self,
    ):
        now = datetime.utcnow()

        log = SimpleNamespace(
            id=ObjectId(),
            user=self.user,
            document_type="INVOICE",
            document_id=str(
                ObjectId()
            ),
            document_number="INV-001",
            action="PDF_DOWNLOAD",
            created_at=now,
        )

        with patch.object(
            DocumentAccessLogService,
            "list_logs",
            return_value=[
                log,
            ],
        ) as service_mock:
            response = self.client.get(
                "/api/v1/document-access-logs/"
            )

        self.assertEqual(
            response.status_code,
            200,
        )

        body = response.json()

        self.assertTrue(
            body[
                "success"
            ]
        )

        logs = body[
            "data"
        ][
            "logs"
        ]

        self.assertEqual(
            len(
                logs
            ),
            1,
        )

        self.assertEqual(
            logs[
                0
            ][
                "document_type"
            ],
            "INVOICE",
        )

        self.assertEqual(
            logs[
                0
            ][
                "document_number"
            ],
            "INV-001",
        )

        service_mock.assert_called_once_with(
            user=self.user,
            organization=self.organization,
            document_type=None,
            action=None,
            document_number=None,
            user_id=None,
            limit=100,
        )

    def test_document_access_logs_rejects_permission(
        self,
    ):
        with patch.object(
            AuthorizationService,
            "has_permission",
            return_value=False,
        ):
            response = self.client.get(
                "/api/v1/document-access-logs/"
            )

        self.assert_error_contract(
            response,
            403,
            "FORBIDDEN",
        )

    def test_document_access_logs_rejects_post(
        self,
    ):
        response = self.client.post(
            "/api/v1/document-access-logs/"
        )

        self.assert_error_contract(
            response,
            405,
            "METHOD_NOT_ALLOWED",
        )

    def test_document_access_log_summary_returns_data(
        self,
    ):
        summary = {
            "total_downloads": 5,
            "by_document_type": {
                "INVOICE": 3,
                "PURCHASE_ORDER": 2,
            },
            "by_user": {},
            "by_action": {
                "PDF_DOWNLOAD": 5,
            },
            "recent_activity": [],
        }

        with patch.object(
            DocumentAccessLogService,
            "get_summary",
            return_value=summary,
        ) as service_mock:
            response = self.client.get(
                (
                    "/api/v1/"
                    "document-access-logs/"
                    "summary/"
                )
            )

        self.assertEqual(
            response.status_code,
            200,
        )

        body = response.json()

        self.assertTrue(
            body[
                "success"
            ]
        )

        self.assertEqual(
            body[
                "data"
            ][
                "summary"
            ][
                "total_downloads"
            ],
            5,
        )

        service_mock.assert_called_once_with(
            user=self.user,
            organization=self.organization,
        )

    # ==================================================
    # DOCUMENT DELIVERY LOGS
    # ==================================================

    def test_document_delivery_logs_returns_data(
        self,
    ):
        now = datetime.utcnow()

        log = SimpleNamespace(
            id=ObjectId(),
            document_type="INVOICE",
            document_id=str(
                ObjectId()
            ),
            document_number="INV-001",
            channel="EMAIL",
            recipient="customer@example.com",
            subject="Invoice INV-001",
            status="SENT",
            recipient_overridden=False,
            custom_subject=False,
            custom_message=False,
            error_message=None,
            sent_at=now,
            created_at=now,
            updated_at=now,
        )

        with patch.object(
            DocumentDeliveryLogService,
            "list_logs",
            return_value=[
                log,
            ],
        ) as service_mock:
            response = self.client.get(
                "/api/v1/document-delivery-logs/"
            )

        self.assertEqual(
            response.status_code,
            200,
        )

        body = response.json()

        self.assertTrue(
            body[
                "success"
            ]
        )

        logs = body[
            "data"
        ][
            "logs"
        ]

        self.assertEqual(
            len(
                logs
            ),
            1,
        )

        self.assertEqual(
            logs[
                0
            ][
                "channel"
            ],
            "EMAIL",
        )

        self.assertEqual(
            logs[
                0
            ][
                "status"
            ],
            "SENT",
        )

        service_mock.assert_called_once_with(
            user=self.user,
            organization=self.organization,
            document_type=None,
            channel=None,
            status=None,
            recipient=None,
            document_number=None,
            subject=None,
            recipient_overridden=None,
            custom_subject=None,
            custom_message=None,
            limit=100,
        )

    def test_document_delivery_logs_rejects_permission(
        self,
    ):
        with patch.object(
            AuthorizationService,
            "has_permission",
            return_value=False,
        ):
            response = self.client.get(
                "/api/v1/document-delivery-logs/"
            )

        self.assert_error_contract(
            response,
            403,
            "FORBIDDEN",
        )

    def test_document_delivery_logs_rejects_post(
        self,
    ):
        response = self.client.post(
            "/api/v1/document-delivery-logs/"
        )

        self.assert_error_contract(
            response,
            405,
            "METHOD_NOT_ALLOWED",
        )

    def test_document_delivery_log_summary_returns_data(
        self,
    ):
        summary = {
            "total_deliveries": 10,
            "sent": 8,
            "failed": 1,
            "pending": 1,
            "email": 10,
            "whatsapp": 0,
            "success_rate": 80.0,
            "failure_rate": 10.0,
            "by_document_type": {
                "INVOICE": 10,
            },
            "by_status": {
                "SENT": 8,
                "FAILED": 1,
                "PENDING": 1,
            },
            "by_channel": {
                "EMAIL": 10,
            },
            "recent_activity": [],
        }

        with patch.object(
            DocumentDeliveryLogService,
            "get_summary",
            return_value=summary,
        ) as service_mock:
            response = self.client.get(
                (
                    "/api/v1/"
                    "document-delivery-logs/"
                    "summary/"
                )
            )

        self.assertEqual(
            response.status_code,
            200,
        )

        body = response.json()

        self.assertTrue(
            body[
                "success"
            ]
        )

        self.assertEqual(
            body[
                "data"
            ][
                "summary"
            ][
                "total_deliveries"
            ],
            10,
        )

        service_mock.assert_called_once_with(
            user=self.user,
            organization=self.organization,
        )