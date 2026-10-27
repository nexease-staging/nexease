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

from django.test import (
    Client,
    SimpleTestCase,
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
    BankPaymentSuggestionAPISerializer,
)
from apps.finance.repositories.bank_payment_suggestion_repository import (
    BankPaymentSuggestionRepository,
)
from apps.finance.services.bank_payment_suggestion_api_service import (
    BankPaymentSuggestionAPIService,
    BankPaymentSuggestionAPIStateError,
)
from apps.finance.services.bank_payment_suggestion_service import (
    BankPaymentSuggestionService,
)
from apps.organizations.api_context_service import (
    APIOrganizationContextService,
)


class BankPaymentSuggestionAPIV1RegressionTestCase(
    SimpleTestCase
):

    SUGGESTIONS_URL = (
        "/api/v1/bank-payment-suggestions/"
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

        self.statement = SimpleNamespace(
            id=ObjectId(),
            organization=self.organization,
            statement_number="BST-TEST000001",
        )

        self.invoice = SimpleNamespace(
            id=ObjectId(),
            organization=self.organization,
            invoice_number="INV-TEST000001",
        )

        self.vendor_bill = SimpleNamespace(
            id=ObjectId(),
            organization=self.organization,
            bill_number="BILL-TEST000001",
        )

        self.suggestion = SimpleNamespace(
            id=ObjectId(),
            organization=self.organization,
            statement=self.statement,
            line_number="1",
            suggestion_type="CUSTOMER_RECEIPT",
            invoice=self.invoice,
            vendor_bill=None,
            amount=Decimal("250.00"),
            confidence=Decimal("95.00"),
            match_reason="Amount and reference matched.",
            status="PENDING",
            created_by=self.user,
            confirmed_at=None,
            rejected_at=None,
            executed_at=None,
            payment_reference="",
            created_at=now,
            updated_at=now,
        )

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
                return_value=self.organization_context,
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
            f"{self.SUGGESTIONS_URL}"
            f"{self.suggestion.id}/"
        )

    def action_url(
        self,
        action,
    ):
        return (
            f"{self.detail_url()}"
            f"{action}/"
        )

    def generate_url(self):
        return (
            "/api/v1/bank-statements/"
            f"{self.statement.id}/lines/1/"
            "payment-suggestion/"
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
        self.assertTrue(body["success"])
        self.assertIn("data", body)
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
        self.assertFalse(body["success"])
        self.assertEqual(
            body["error"]["code"],
            expected_code,
        )
        self.assertTrue(
            body.get("request_id")
        )

        return body

    def serialized_suggestion(
        self,
        status=None,
    ):
        return {
            "id": str(self.suggestion.id),
            "line_number": "1",
            "suggestion_type": "CUSTOMER_RECEIPT",
            "amount": "250.00",
            "confidence": "95.00",
            "status": (
                status
                or
                self.suggestion.status
            ),
            "is_executed": False,
        }

    def test_collection_returns_paginated_data(
        self,
    ):
        pipeline_result = {
            "items": [self.suggestion],
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
                    "-created_at",
                    "id",
                ],
            },
        }

        with (
            patch.object(
                BankPaymentSuggestionRepository,
                "queryset_for_organization",
                return_value=object(),
            ),
            patch.object(
                APIQueryPipelineService,
                "execute",
                return_value=pipeline_result,
            ),
            patch.object(
                BankPaymentSuggestionAPISerializer,
                "serialize_many",
                return_value=[
                    self.serialized_suggestion()
                ],
            ),
        ):
            response = self.client.get(
                self.SUGGESTIONS_URL
            )

        body = self.assert_success_contract(
            response
        )
        self.assertEqual(
            body["data"][
                "bank_payment_suggestions"
            ][0]["confidence"],
            "95.00",
        )

    def test_detail_returns_suggestion(
        self,
    ):
        with (
            patch.object(
                BankPaymentSuggestionAPIService,
                "get_suggestion",
                return_value=self.suggestion,
            ),
            patch.object(
                BankPaymentSuggestionAPISerializer,
                "serialize_detail",
                return_value=(
                    self.serialized_suggestion()
                ),
            ),
        ):
            response = self.client.get(
                self.detail_url()
            )

        body = self.assert_success_contract(
            response
        )
        self.assertEqual(
            body["data"][
                "bank_payment_suggestion"
            ]["status"],
            "PENDING",
        )

    def test_generate_returns_created_suggestion(
        self,
    ):
        with (
            patch.object(
                BankPaymentSuggestionAPIService,
                "generate_suggestion",
                return_value=self.suggestion,
            ) as generate_mock,
            patch.object(
                BankPaymentSuggestionAPISerializer,
                "serialize_detail",
                return_value=(
                    self.serialized_suggestion()
                ),
            ),
        ):
            response = self.client.post(
                self.generate_url()
            )

        self.assert_success_contract(
            response,
            201,
        )
        generate_mock.assert_called_once_with(
            user=self.user,
            organization=self.organization,
            statement_id=str(self.statement.id),
            line_number="1",
        )

    def test_confirm_returns_confirmed_suggestion(
        self,
    ):
        confirmed = SimpleNamespace(
            **{
                **vars(self.suggestion),
                "status": "CONFIRMED",
                "confirmed_at": datetime.utcnow(),
            }
        )

        with (
            patch.object(
                BankPaymentSuggestionAPIService,
                "confirm_suggestion",
                return_value=confirmed,
            ),
            patch.object(
                BankPaymentSuggestionAPISerializer,
                "serialize_detail",
                return_value=(
                    self.serialized_suggestion(
                        "CONFIRMED"
                    )
                ),
            ),
        ):
            response = self.client.post(
                self.action_url("confirm")
            )

        body = self.assert_success_contract(
            response
        )
        self.assertEqual(
            body["data"][
                "bank_payment_suggestion"
            ]["status"],
            "CONFIRMED",
        )

    def test_reject_returns_rejected_suggestion(
        self,
    ):
        rejected = SimpleNamespace(
            **{
                **vars(self.suggestion),
                "status": "REJECTED",
                "rejected_at": datetime.utcnow(),
            }
        )

        with (
            patch.object(
                BankPaymentSuggestionAPIService,
                "reject_suggestion",
                return_value=rejected,
            ),
            patch.object(
                BankPaymentSuggestionAPISerializer,
                "serialize_detail",
                return_value=(
                    self.serialized_suggestion(
                        "REJECTED"
                    )
                ),
            ),
        ):
            response = self.client.post(
                self.action_url("reject")
            )

        body = self.assert_success_contract(
            response
        )
        self.assertEqual(
            body["data"][
                "bank_payment_suggestion"
            ]["status"],
            "REJECTED",
        )

    def test_execute_returns_execution_data(
        self,
    ):
        result = {
            "suggestion": self.suggestion,
            "payment": object(),
            "bank_transaction": object(),
        }

        with (
            patch.object(
                BankPaymentSuggestionAPIService,
                "execute_suggestion",
                return_value=result,
            ),
            patch.object(
                BankPaymentSuggestionAPISerializer,
                "serialize_execution",
                return_value={
                    "suggestion": {
                        "id": str(
                            self.suggestion.id
                        ),
                        "is_executed": True,
                    },
                    "payment": {
                        "payment_number": (
                            "PAY-TEST000001"
                        ),
                    },
                    "bank_transaction": {
                        "transaction_number": (
                            "BTX-TEST000001"
                        ),
                    },
                },
            ),
        ):
            response = self.client.post(
                self.action_url("execute")
            )

        body = self.assert_success_contract(
            response
        )
        self.assertTrue(
            body["data"]["execution"]
            ["suggestion"]["is_executed"]
        )

    def test_state_error_returns_422(
        self,
    ):
        with patch.object(
            BankPaymentSuggestionAPIService,
            "confirm_suggestion",
            side_effect=(
                BankPaymentSuggestionAPIStateError(
                    message=(
                        "Only pending suggestions "
                        "can be confirmed."
                    ),
                )
            ),
        ):
            response = self.client.post(
                self.action_url("confirm")
            )

        self.assert_error_contract(
            response,
            422,
            "UNPROCESSABLE_ENTITY",
        )

    def test_invalid_id_returns_400(
        self,
    ):
        response = self.client.get(
            (
                f"{self.SUGGESTIONS_URL}"
                "invalid-id/"
            )
        )

        self.assert_error_contract(
            response,
            400,
            "VALIDATION_ERROR",
        )

    def test_missing_suggestion_returns_404(
        self,
    ):
        with patch.object(
            BankPaymentSuggestionAPIService,
            "get_suggestion",
            side_effect=LookupError(
                "Payment suggestion not found."
            ),
        ):
            response = self.client.get(
                self.detail_url()
            )

        self.assert_error_contract(
            response,
            404,
            "NOT_FOUND",
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
                self.SUGGESTIONS_URL
            )

        self.assert_error_contract(
            response,
            403,
            "FORBIDDEN",
        )

    def test_collection_rejects_post(
        self,
    ):
        response = self.client.post(
            self.SUGGESTIONS_URL
        )

        self.assert_error_contract(
            response,
            405,
            "METHOD_NOT_ALLOWED",
        )

    def test_service_executes_customer_receipt(
        self,
    ):
        expected = {
            "suggestion": self.suggestion,
        }

        with (
            patch.object(
                BankPaymentSuggestionRepository,
                "get_by_id",
                return_value=self.suggestion,
            ),
            patch.object(
                BankPaymentSuggestionService,
                "execute_customer_receipt",
                return_value=expected,
            ) as execute_mock,
        ):
            result = (
                BankPaymentSuggestionAPIService
                .execute_suggestion(
                    user=self.user,
                    organization=self.organization,
                    suggestion_id=str(
                        self.suggestion.id
                    ),
                )
            )

        self.assertEqual(result, expected)
        execute_mock.assert_called_once_with(
            user=self.user,
            organization=self.organization,
            suggestion=self.suggestion,
        )

    def test_service_executes_supplier_payment(
        self,
    ):
        supplier_suggestion = SimpleNamespace(
            **{
                **vars(self.suggestion),
                "suggestion_type": (
                    "SUPPLIER_PAYMENT"
                ),
                "invoice": None,
                "vendor_bill": self.vendor_bill,
            }
        )

        expected = {
            "suggestion": supplier_suggestion,
        }

        with (
            patch.object(
                BankPaymentSuggestionRepository,
                "get_by_id",
                return_value=supplier_suggestion,
            ),
            patch.object(
                BankPaymentSuggestionService,
                "execute_supplier_payment",
                return_value=expected,
            ) as execute_mock,
        ):
            result = (
                BankPaymentSuggestionAPIService
                .execute_suggestion(
                    user=self.user,
                    organization=self.organization,
                    suggestion_id=str(
                        supplier_suggestion.id
                    ),
                )
            )

        self.assertEqual(result, expected)
        execute_mock.assert_called_once_with(
            user=self.user,
            organization=self.organization,
            suggestion=supplier_suggestion,
        )
