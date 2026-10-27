from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

from bson import ObjectId

from django.test import (
    Client,
    SimpleTestCase,
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
from apps.finance.services.financial_report_api_service import (
    FinancialReportAPIService,
)
from apps.finance.services.main_dashboard_api_service import (
    MainDashboardAPIService,
    MainDashboardAPIValidationError,
)
from apps.organizations.api_context_service import (
    APIOrganizationContextService,
)


class FinancialReportsAPIV1Tests(
    SimpleTestCase
):
    MAIN_DASHBOARD_URL = (
        "/api/v1/dashboard/"
    )
    FINANCE_DASHBOARD_URL = (
        "/api/v1/finance-dashboard/"
    )

    ACCOUNTING_DASHBOARD_URL = (
        "/api/v1/accounting-dashboard/"
    )

    CASH_FLOW_URL = (
        "/api/v1/cash-flow/"
    )

    FINANCE_AUDIT_URL = (
        "/api/v1/finance-audit/"
    )

    def setUp(self):
        now = datetime.utcnow()

        self.organization = SimpleNamespace(
            id=ObjectId(),
            name="Financial Reports Organization",
            email="reports@example.com",
            is_active=True,
            created_at=now,
            updated_at=now,
        )

        self.user = SimpleNamespace(
            id=ObjectId(),
            organization=self.organization,
            email="admin@example.com",
            first_name="System",
            last_name="Administrator",
            is_active=True,
            is_authenticated=True,
            is_anonymous=False,
        )

        self.bank_account = SimpleNamespace(
            id=ObjectId(),
            organization=self.organization,
            account_name="Operating Bank",
            account_type="BANK",
            bank_name="Example Bank",
            account_number="1234567890",
            ifsc_code="EXAM0001234",
            currency="INR",
            opening_balance=Decimal("1000.00"),
            current_balance=Decimal("1250.00"),
            is_active=True,
            created_by=self.user,
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

    # ==================================================
    # RESPONSE CONTRACT HELPERS
    # ==================================================

    def assert_success_contract(
        self,
        response,
        status_code=200,
    ):
        self.assertEqual(
            response.status_code,
            status_code,
        )

        body = response.json()

        self.assertTrue(
            body["success"]
        )

        self.assertIn(
            "data",
            body,
        )

        return body

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
            body["success"]
        )

        self.assertEqual(
            body["error"]["code"],
            code,
        )

        return body

    def get_main_dashboard_result(
        self,
    ):
        return {
            "period": {
                "start_date":
                    "2026-01-01",
                "end_date":
                    "2026-09-03",
            },

            "kpis": {
                "total_sales":
                    "254944.00",
                "total_purchases":
                    "591250.00",
                "receivables":
                    "16000.00",
                "payables":
                    "0.00",
                "bank_balance":
                    "25000.00",
                "inventory_value":
                    "125000.00",
                "out_of_stock_items":
                    1,
            },

            "sales_trend": [
                {
                    "period": "2026-08",
                    "amount": "254944.00",
                },
            ],

            "purchase_trend": [
                {
                    "period": "2026-08",
                    "amount": "591250.00",
                },
            ],

            "cash_flow": [
                {
                    "period": "2026-08",
                    "inflow": "22344.00",
                    "outflow": "2000.00",
                    "net": "20344.00",
                },
            ],

            "receivable_aging": {
                "current":
                    "16000.00",
                "1_30":
                    "0.00",
                "31_60":
                    "0.00",
                "61_90":
                    "0.00",
                "90_plus":
                    "0.00",
            },

            "invoice_status": {
                "issued": 2,
                "partially_paid": 1,
                "paid": 4,
                "overdue": 0,
            },

            "bill_status": {
                "posted": 0,
                "partially_paid": 0,
                "paid": 3,
                "overdue": 0,
            },

            "inventory_status": {
                "in_stock": 10,
                "out_of_stock": 1,
            },

            "top_customers": [
                {
                    "customer_id":
                        str(ObjectId()),
                    "customer_name":
                        "Test Customer",
                    "amount":
                        "254944.00",
                },
            ],

            "top_suppliers": [
                {
                    "supplier_id":
                        str(ObjectId()),
                    "supplier_name":
                        "Test Supplier",
                    "amount":
                        "591250.00",
                },
            ],

            "alerts": {
                "overdue_invoices": 0,
                "overdue_bills": 0,
                "out_of_stock_items": 1,
            },

            "recent_activity": [
                {
                    "activity_type":
                        "INVOICE",
                    "reference_id":
                        str(ObjectId()),
                    "reference_number":
                        "INV-TEST-001",
                    "description":
                        "Test invoice",
                    "activity_date":
                        datetime(
                            2026,
                            9,
                            1,
                        ),
                    "amount":
                        "1000.00",
                },
            ],
        }

    # ==================================================
    # MAIN DASHBOARD
    # ==================================================

    def test_main_dashboard_returns_data(
        self,
    ):
        result = (
            self.get_main_dashboard_result()
        )

        with patch.object(
            MainDashboardAPIService,
            "get_dashboard",
            return_value=result,
        ) as service_mock:
            response = self.client.get(
                self.MAIN_DASHBOARD_URL,
                {
                    "start_date":
                        "2026-01-01",
                    "end_date":
                        "2026-09-03",
                },
            )

        body = self.assert_success_contract(
            response
        )

        dashboard = body["data"][
            "dashboard"
        ]

        self.assertEqual(
            dashboard["period"],
            {
                "start_date":
                    "2026-01-01",
                "end_date":
                    "2026-09-03",
            },
        )

        self.assertEqual(
            dashboard[
                "kpis"
            ][
                "total_sales"
            ],
            "254944.00",
        )

        self.assertEqual(
            dashboard[
                "kpis"
            ][
                "total_purchases"
            ],
            "591250.00",
        )

        self.assertEqual(
            dashboard[
                "recent_activity"
            ][0][
                "activity_date"
            ],
            "2026-09-01T00:00:00",
        )

        service_mock.assert_called_once_with(
            user=self.user,
            organization=self.organization,
            start_date="2026-01-01",
            end_date="2026-09-03",
        )


    def test_main_dashboard_default_period(
        self,
    ):
        result = (
            self.get_main_dashboard_result()
        )

        with patch.object(
            MainDashboardAPIService,
            "get_dashboard",
            return_value=result,
        ) as service_mock:
            response = self.client.get(
                self.MAIN_DASHBOARD_URL
            )

        self.assert_success_contract(
            response
        )

        service_mock.assert_called_once_with(
            user=self.user,
            organization=self.organization,
            start_date=None,
            end_date=None,
        )


    def test_main_dashboard_contract(
        self,
    ):
        result = (
            self.get_main_dashboard_result()
        )

        with patch.object(
            MainDashboardAPIService,
            "get_dashboard",
            return_value=result,
        ):
            response = self.client.get(
                self.MAIN_DASHBOARD_URL
            )

        body = self.assert_success_contract(
            response
        )

        dashboard = body["data"][
            "dashboard"
        ]

        expected_keys = {
            "period",
            "kpis",
            "sales_trend",
            "purchase_trend",
            "cash_flow",
            "receivable_aging",
            "invoice_status",
            "bill_status",
            "inventory_status",
            "top_customers",
            "top_suppliers",
            "alerts",
            "recent_activity",
        }

        self.assertEqual(
            set(
                dashboard.keys()
            ),
            expected_keys,
        )


    def test_main_dashboard_rejects_permission(
        self,
    ):
        with patch.object(
            AuthorizationService,
            "has_permission",
            return_value=False,
        ):
            response = self.client.get(
                self.MAIN_DASHBOARD_URL
            )

        self.assert_error_contract(
            response,
            403,
            "FORBIDDEN",
        )


    def test_main_dashboard_rejects_post(
        self,
    ):
        response = self.client.post(
            self.MAIN_DASHBOARD_URL
        )

        self.assert_error_contract(
            response,
            405,
            "METHOD_NOT_ALLOWED",
        )


    def test_main_dashboard_rejects_invalid_start_date(
        self,
    ):
        error = (
            MainDashboardAPIValidationError(
                message=(
                    "Invalid start_date. "
                    "Use YYYY-MM-DD."
                ),
                details={
                    "start_date":
                        "Use YYYY-MM-DD.",
                },
            )
        )

        with patch.object(
            MainDashboardAPIService,
            "get_dashboard",
            side_effect=error,
        ):
            response = self.client.get(
                self.MAIN_DASHBOARD_URL,
                {
                    "start_date":
                        "invalid-date",
                    "end_date":
                        "2026-09-03",
                },
            )

        body = self.assert_error_contract(
            response,
            400,
            "VALIDATION_ERROR",
        )

        self.assertIn(
            "start_date",
            body[
                "error"
            ][
                "details"
            ],
        )


    def test_main_dashboard_rejects_invalid_end_date(
        self,
    ):
        error = (
            MainDashboardAPIValidationError(
                message=(
                    "Invalid end_date. "
                    "Use YYYY-MM-DD."
                ),
                details={
                    "end_date":
                        "Use YYYY-MM-DD.",
                },
            )
        )

        with patch.object(
            MainDashboardAPIService,
            "get_dashboard",
            side_effect=error,
        ):
            response = self.client.get(
                self.MAIN_DASHBOARD_URL,
                {
                    "start_date":
                        "2026-01-01",
                    "end_date":
                        "invalid-date",
                },
            )

        body = self.assert_error_contract(
            response,
            400,
            "VALIDATION_ERROR",
        )

        self.assertIn(
            "end_date",
            body[
                "error"
            ][
                "details"
            ],
        )


    def test_main_dashboard_rejects_reversed_range(
        self,
    ):
        error = (
            MainDashboardAPIValidationError(
                message=(
                    "start_date cannot be "
                    "after end_date."
                ),
                details={
                    "start_date": (
                        "Must be on or before "
                        "end_date."
                    ),
                },
            )
        )

        with patch.object(
            MainDashboardAPIService,
            "get_dashboard",
            side_effect=error,
        ):
            response = self.client.get(
                self.MAIN_DASHBOARD_URL,
                {
                    "start_date":
                        "2026-09-03",
                    "end_date":
                        "2026-01-01",
                },
            )

        body = self.assert_error_contract(
            response,
            400,
            "VALIDATION_ERROR",
        )

        self.assertIn(
            "start_date",
            body[
                "error"
            ][
                "details"
            ],
        )

    # ==================================================
    # FINANCE DASHBOARD
    # ==================================================

    def test_finance_dashboard_returns_data(
        self,
    ):
        result = {
            "bank_accounts": {
                "account_count": 2,
                "total_balance": Decimal(
                    "12500.00"
                ),
                "accounts": [
                    {
                        "id": str(
                            self.bank_account.id
                        ),
                        "account_name":
                            "Operating Bank",
                        "current_balance":
                            Decimal("1250.00"),
                    },
                ],
            },
            "transactions": {
                "count": 10,
                "total_in":
                    Decimal("5000.00"),
                "total_out":
                    Decimal("2000.00"),
                "net_cash_flow":
                    Decimal("3000.00"),
            },
            "statements": {
                "count": 3,
                "unreconciled_count": 1,
            },
            "payment_suggestions": {
                "count": 4,
                "pending_count": 2,
            },
            "receivables": {
                "total_receivable":
                    Decimal("3000.00"),
            },
            "payables": {
                "total_payable":
                    Decimal("1500.00"),
            },
        }

        with patch.object(
            FinancialReportAPIService,
            "get_finance_dashboard",
            return_value=result,
        ) as service_mock:
            response = self.client.get(
                self.FINANCE_DASHBOARD_URL
            )

        body = self.assert_success_contract(
            response
        )

        dashboard = body["data"][
            "finance_dashboard"
        ]

        self.assertIn(
            "bank_accounts",
            dashboard,
        )

        self.assertIn(
            "transactions",
            dashboard,
        )

        self.assertIn(
            "receivables",
            dashboard,
        )

        service_mock.assert_called_once_with(
            user=self.user,
            organization=self.organization,
        )

    def test_finance_dashboard_rejects_permission(
        self,
    ):
        with patch.object(
            AuthorizationService,
            "has_permission",
            return_value=False,
        ):
            response = self.client.get(
                self.FINANCE_DASHBOARD_URL
            )

        self.assert_error_contract(
            response,
            403,
            "FORBIDDEN",
        )

    def test_finance_dashboard_rejects_post(
        self,
    ):
        response = self.client.post(
            self.FINANCE_DASHBOARD_URL
        )

        self.assert_error_contract(
            response,
            405,
            "METHOD_NOT_ALLOWED",
        )

    # ==================================================
    # ACCOUNTING DASHBOARD
    # ==================================================

    def test_accounting_dashboard_returns_data(
        self,
    ):
        result = {
            "as_of_date": datetime(
                2026,
                9,
                1,
            ),
            "liquidity": {
                "cash_and_bank":
                    Decimal("12500.00"),
                "current_assets":
                    Decimal("18000.00"),
                "current_liabilities":
                    Decimal("6000.00"),
            },
            "working_capital": {
                "receivables":
                    Decimal("3000.00"),
                "payables":
                    Decimal("1500.00"),
                "working_capital":
                    Decimal("12000.00"),
            },
            "profitability": {
                "revenue":
                    Decimal("20000.00"),
                "expenses":
                    Decimal("12000.00"),
                "net_profit":
                    Decimal("8000.00"),
            },
            "balance_sheet": {},
            "trial_balance": {},
            "accounting_health": {
                "is_balanced": True,
            },
        }

        with patch.object(
            FinancialReportAPIService,
            "get_accounting_dashboard",
            return_value=result,
        ) as service_mock:
            response = self.client.get(
                self.ACCOUNTING_DASHBOARD_URL,
                {
                    "as_of_date":
                        "2026-09-01",
                },
            )

        body = self.assert_success_contract(
            response
        )

        dashboard = body["data"][
            "accounting_dashboard"
        ]

        self.assertEqual(
            dashboard["as_of_date"],
            "2026-09-01T00:00:00",
        )

        self.assertIn(
            "liquidity",
            dashboard,
        )

        self.assertIn(
            "working_capital",
            dashboard,
        )

        self.assertIn(
            "profitability",
            dashboard,
        )

        service_mock.assert_called_once_with(
            user=self.user,
            organization=self.organization,
            as_of_date="2026-09-01",
        )

    def test_accounting_dashboard_rejects_permission(
        self,
    ):
        with patch.object(
            AuthorizationService,
            "has_permission",
            return_value=False,
        ):
            response = self.client.get(
                self.ACCOUNTING_DASHBOARD_URL
            )

        self.assert_error_contract(
            response,
            403,
            "FORBIDDEN",
        )

    def test_accounting_dashboard_rejects_post(
        self,
    ):
        response = self.client.post(
            self.ACCOUNTING_DASHBOARD_URL
        )

        self.assert_error_contract(
            response,
            405,
            "METHOD_NOT_ALLOWED",
        )

    # ==================================================
    # CASH FLOW
    # ==================================================

    def test_cash_flow_returns_data(
        self,
    ):
        result = {
            "start_date": datetime(
                2026,
                8,
                1,
            ),
            "end_date": datetime(
                2026,
                8,
                31,
            ),
            "bank_account": {
                "id": str(
                    self.bank_account.id
                ),
                "account_name":
                    self.bank_account.account_name,
            },
            "opening_balance":
                Decimal("1000.00"),
            "total_in":
                Decimal("5000.00"),
            "total_out":
                Decimal("2500.00"),
            "net_cash_flow":
                Decimal("2500.00"),
            "closing_balance":
                Decimal("3500.00"),
            "transaction_count": 10,
            "reconciled_count": 8,
            "unreconciled_count": 2,
            "daily_summary": [],
            "transactions": [],
        }

        with patch.object(
            FinancialReportAPIService,
            "get_cash_flow",
            return_value=result,
        ) as service_mock:
            response = self.client.get(
                self.CASH_FLOW_URL,
                {
                    "start_date":
                        "2026-08-01",
                    "end_date":
                        "2026-08-31",
                    "bank_account_id":
                        str(
                            self.bank_account.id
                        ),
                },
            )

        body = self.assert_success_contract(
            response
        )

        cash_flow = body["data"][
            "cash_flow"
        ]

        self.assertEqual(
            cash_flow["start_date"],
            "2026-08-01T00:00:00",
        )

        self.assertEqual(
            cash_flow["end_date"],
            "2026-08-31T00:00:00",
        )

        self.assertEqual(
            cash_flow["net_cash_flow"],
            "2500.00",
        )

        service_mock.assert_called_once_with(
            user=self.user,
            organization=self.organization,
            start_date="2026-08-01",
            end_date="2026-08-31",
            bank_account_id=str(
                self.bank_account.id
            ),
        )

    def test_cash_flow_rejects_invalid_date(
        self,
    ):
        response = self.client.get(
            self.CASH_FLOW_URL,
            {
                "start_date":
                    "invalid-date",
                "end_date":
                    "2026-08-31",
            },
        )

        body = self.assert_error_contract(
            response,
            400,
            "VALIDATION_ERROR",
        )

        self.assertIn(
            "start_date",
            body["error"]["details"],
        )

    def test_cash_flow_rejects_missing_start_date(
        self,
    ):
        response = self.client.get(
            self.CASH_FLOW_URL,
            {
                "end_date":
                    "2026-08-31",
            },
        )

        body = self.assert_error_contract(
            response,
            400,
            "VALIDATION_ERROR",
        )

        self.assertIn(
            "start_date",
            body["error"]["details"],
        )

    def test_cash_flow_rejects_missing_end_date(
        self,
    ):
        response = self.client.get(
            self.CASH_FLOW_URL,
            {
                "start_date":
                    "2026-08-01",
            },
        )

        body = self.assert_error_contract(
            response,
            400,
            "VALIDATION_ERROR",
        )

        self.assertIn(
            "end_date",
            body["error"]["details"],
        )

    def test_cash_flow_rejects_invalid_bank_account_id(
        self,
    ):
        response = self.client.get(
            self.CASH_FLOW_URL,
            {
                "start_date":
                    "2026-08-01",
                "end_date":
                    "2026-08-31",
                "bank_account_id":
                    "invalid-id",
            },
        )

        body = self.assert_error_contract(
            response,
            400,
            "VALIDATION_ERROR",
        )

        self.assertIn(
            "bank_account_id",
            body["error"]["details"],
        )

    def test_cash_flow_rejects_permission(
        self,
    ):
        with patch.object(
            AuthorizationService,
            "has_permission",
            return_value=False,
        ):
            response = self.client.get(
                self.CASH_FLOW_URL,
                {
                    "start_date":
                        "2026-08-01",
                    "end_date":
                        "2026-08-31",
                },
            )

        self.assert_error_contract(
            response,
            403,
            "FORBIDDEN",
        )

    def test_cash_flow_rejects_post(
        self,
    ):
        response = self.client.post(
            self.CASH_FLOW_URL
        )

        self.assert_error_contract(
            response,
            405,
            "METHOD_NOT_ALLOWED",
        )

    # ==================================================
    # FINANCE AUDIT
    # ==================================================

    def test_finance_audit_returns_data(
        self,
    ):
        result = {
            "healthy": True,
            "critical_count": 0,
            "attention_count": 0,
            "statements": [],
            "transactions": [],
            "payment_suggestions": [],
            "invoices": [],
            "vendor_bills": [],
        }

        with patch.object(
            FinancialReportAPIService,
            "get_finance_audit",
            return_value=result,
        ) as service_mock:
            response = self.client.get(
                self.FINANCE_AUDIT_URL
            )

        body = self.assert_success_contract(
            response
        )

        audit = body["data"][
            "finance_audit"
        ]

        self.assertTrue(
            audit["healthy"]
        )

        self.assertEqual(
            audit["critical_count"],
            0,
        )

        self.assertEqual(
            audit["attention_count"],
            0,
        )

        service_mock.assert_called_once_with(
            user=self.user,
            organization=self.organization,
        )

    def test_finance_audit_rejects_permission(
        self,
    ):
        with patch.object(
            AuthorizationService,
            "has_permission",
            return_value=False,
        ):
            response = self.client.get(
                self.FINANCE_AUDIT_URL
            )

        self.assert_error_contract(
            response,
            403,
            "FORBIDDEN",
        )

    def test_finance_audit_rejects_post(
        self,
    ):
        response = self.client.post(
            self.FINANCE_AUDIT_URL
        )

        self.assert_error_contract(
            response,
            405,
            "METHOD_NOT_ALLOWED",
        )