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
from apps.finance.repositories.chart_of_account_repository import (
    ChartOfAccountRepository,
)
from apps.finance.repositories.journal_entry_repository import (
    JournalEntryRepository,
)
from apps.finance.services.accounting_report_api_service import (
    AccountingReportAPIService,
    AccountingReportAPIValidationError,
)
from apps.finance.services.chart_of_account_api_service import (
    ChartOfAccountAPIService,
    ChartOfAccountAPIStateError,
    ChartOfAccountAPIValidationError,
)
from apps.finance.services.journal_entry_api_service import (
    JournalEntryAPIService,
    JournalEntryAPIStateError,
    JournalEntryAPIValidationError,
)
from apps.finance.repositories.bank_account_repository import (
    BankAccountRepository,
)
from apps.finance.repositories.bank_transaction_repository import (
    BankTransactionRepository,
)
from apps.finance.repositories.bank_transfer_repository import (
    BankTransferRepository,
)
from apps.finance.services.bank_account_api_service import (
    BankAccountAPIService,
    BankAccountAPIStateError,
    BankAccountAPIValidationError,
)
from apps.finance.services.bank_transaction_api_service import (
    BankTransactionAPIService,
    BankTransactionAPIStateError,
    BankTransactionAPIValidationError,
)
from apps.finance.services.bank_transfer_api_service import (
    BankTransferAPIService,
    BankTransferAPIStateError,
    BankTransferAPIValidationError,
)
from apps.organizations.api_context_service import (
    APIOrganizationContextService,
)


class FinanceAPIV1RegressionTestCase(
    SimpleTestCase
):

    ACCOUNTS_URL = (
        "/api/v1/chart-of-accounts/"
    )

    JOURNALS_URL = (
        "/api/v1/journal-entries/"
    )

    TRIAL_BALANCE_URL = (
        "/api/v1/trial-balance/"
    )
    BANK_ACCOUNTS_URL = (
        "/api/v1/bank-accounts/"
    )

    BANK_TRANSACTIONS_URL = (
        "/api/v1/bank-transactions/"
    )

    BANK_TRANSFERS_URL = (
        "/api/v1/bank-transfers/"
    )

    def setUp(self):
        now = datetime.utcnow()

        self.organization = (
            SimpleNamespace(
                id=ObjectId(),
                name=(
                    "Finance Regression "
                    "Organization"
                ),
                email=(
                    "finance@example.com"
                ),
                is_active=True,
                created_at=now,
                updated_at=now,
            )
        )

        self.other_organization = (
            SimpleNamespace(
                id=ObjectId(),
                name=(
                    "Other Finance "
                    "Organization"
                ),
                email=(
                    "other-finance@example.com"
                ),
                is_active=True,
                created_at=now,
                updated_at=now,
            )
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

        self.account = (
            SimpleNamespace(
                id=ObjectId(),
                organization=(
                    self.organization
                ),
                account_code="100100",
                account_name="Main Bank",
                account_type="ASSET",
                account_subtype=(
                    "CURRENT_ASSET"
                ),
                normal_balance="DEBIT",
                system_key="",
                description=(
                    "Primary operating bank."
                ),
                is_system_account=False,
                is_active=True,
                allow_manual_posting=True,
                created_by=self.user,
                created_at=now,
                updated_at=now,
            )
        )

        self.credit_account = (
            SimpleNamespace(
                id=ObjectId(),
                organization=(
                    self.organization
                ),
                account_code="300100",
                account_name=(
                    "Owner Capital"
                ),
                account_type="EQUITY",
                account_subtype="CAPITAL",
                normal_balance="CREDIT",
                system_key="",
                description="",
                is_system_account=False,
                is_active=True,
                allow_manual_posting=True,
                created_by=self.user,
                created_at=now,
                updated_at=now,
            )
        )

        self.debit_line = (
            SimpleNamespace(
                account=self.account,
                description=(
                    "Opening bank balance"
                ),
                debit=Decimal(
                    "1000.00"
                ),
                credit=Decimal(
                    "0.00"
                ),
            )
        )

        self.credit_line = (
            SimpleNamespace(
                account=(
                    self.credit_account
                ),
                description=(
                    "Opening capital"
                ),
                debit=Decimal(
                    "0.00"
                ),
                credit=Decimal(
                    "1000.00"
                ),
            )
        )

        self.journal = (
            SimpleNamespace(
                id=ObjectId(),
                organization=(
                    self.organization
                ),
                journal_number=(
                    "JE-TEST000001"
                ),
                journal_date=now,
                description=(
                    "Opening journal"
                ),
                source_type="MANUAL",
                source_id="",
                lines=[
                    self.debit_line,
                    self.credit_line,
                ],
                total_debit=Decimal(
                    "1000.00"
                ),
                total_credit=Decimal(
                    "1000.00"
                ),
                status="DRAFT",
                posted_at=None,
                reversed_at=None,
                reversal_of=None,
                reversed_by=None,
                created_by=self.user,
                created_at=now,
                updated_at=now,
            )
        )

        self.reversal = (
            SimpleNamespace(
                **{
                    **vars(
                        self.journal
                    ),
                    "id":
                        ObjectId(),
                    "journal_number":
                        "JE-REV000001",
                    "description":
                        (
                            "Reversal of "
                            "JE-TEST000001"
                        ),
                    "source_type":
                        "REVERSAL",
                    "source_id":
                        str(
                            self.journal.id
                        ),
                    "status":
                        "POSTED",
                    "posted_at":
                        now,
                    "reversal_of":
                        self.journal,
                }
            )
        )
        self.bank_account = (
            SimpleNamespace(
                id=ObjectId(),
                organization=(
                    self.organization
                ),
                account_name=(
                    "Operating Bank"
                ),
                account_type="BANK",
                bank_name="Example Bank",
                account_number="1234567890",
                ifsc_code="EXAM0001234",
                currency="INR",
                opening_balance=Decimal(
                    "1000.00"
                ),
                current_balance=Decimal(
                    "1250.00"
                ),
                is_active=True,
                created_by=self.user,
                created_at=now,
                updated_at=now,
            )
        )

        self.destination_bank_account = (
            SimpleNamespace(
                id=ObjectId(),
                organization=(
                    self.organization
                ),
                account_name=(
                    "Secondary Bank"
                ),
                account_type="BANK",
                bank_name="Second Bank",
                account_number="9876543210",
                ifsc_code="SECO0005678",
                currency="INR",
                opening_balance=Decimal(
                    "500.00"
                ),
                current_balance=Decimal(
                    "500.00"
                ),
                is_active=True,
                created_by=self.user,
                created_at=now,
                updated_at=now,
            )
        )

        self.bank_transaction = (
            SimpleNamespace(
                id=ObjectId(),
                organization=(
                    self.organization
                ),
                bank_account=(
                    self.bank_account
                ),
                transaction_number=(
                    "BTX-TEST000001"
                ),
                transaction_type="MONEY_IN",
                transaction_date=now,
                amount=Decimal(
                    "250.00"
                ),
                balance_before=Decimal(
                    "1000.00"
                ),
                balance_after=Decimal(
                    "1250.00"
                ),
                reference_type="",
                reference_id="",
                external_reference=(
                    "UTR-TEST-001"
                ),
                description=(
                    "Customer receipt"
                ),
                reconciliation_status=(
                    "UNRECONCILED"
                ),
                reconciled_at=None,
                created_by=self.user,
                created_at=now,
            )
        )

        self.bank_transfer = (
            SimpleNamespace(
                id=ObjectId(),
                organization=(
                    self.organization
                ),
                transfer_number=(
                    "TRF-TEST000001"
                ),
                source_account=(
                    self.bank_account
                ),
                destination_account=(
                    self.destination_bank_account
                ),
                transfer_date=now,
                amount=Decimal(
                    "100.00"
                ),
                status="DRAFT",
                reference="TRANSFER-001",
                notes=(
                    "Move funds to secondary bank."
                ),
                created_by=self.user,
                posted_at=None,
                cancelled_at=None,
                created_at=now,
                updated_at=now,
            )
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

    def tearDown(self):
        for patcher in reversed(
            self.patchers
        ):
            patcher.stop()

    def account_detail_url(
        self,
        account=None,
    ):
        account = (
            account
            or
            self.account
        )

        return (
            f"{self.ACCOUNTS_URL}"
            f"{account.id}/"
        )

    def account_deactivate_url(
        self,
        account=None,
    ):
        account = (
            account
            or
            self.account
        )

        return (
            f"{self.ACCOUNTS_URL}"
            f"{account.id}/deactivate/"
        )

    def journal_detail_url(
        self,
        journal=None,
    ):
        journal = (
            journal
            or
            self.journal
        )

        return (
            f"{self.JOURNALS_URL}"
            f"{journal.id}/"
        )

    def journal_post_url(
        self,
        journal=None,
    ):
        journal = (
            journal
            or
            self.journal
        )

        return (
            f"{self.JOURNALS_URL}"
            f"{journal.id}/post/"
        )

    def journal_reverse_url(
        self,
        journal=None,
    ):
        journal = (
            journal
            or
            self.journal
        )

        return (
            f"{self.JOURNALS_URL}"
            f"{journal.id}/reverse/"
        )

    def general_ledger_url(
        self,
        account=None,
    ):
        account = (
            account
            or
            self.account
        )

        return (
            "/api/v1/general-ledger/"
            f"{account.id}/"
        )

    def bank_account_detail_url(
        self,
        bank_account=None,
    ):
        bank_account = (
            bank_account
            or
            self.bank_account
        )

        return (
            f"{self.BANK_ACCOUNTS_URL}"
            f"{bank_account.id}/"
        )

    def bank_account_deactivate_url(
        self,
        bank_account=None,
    ):
        bank_account = (
            bank_account
            or
            self.bank_account
        )

        return (
            f"{self.BANK_ACCOUNTS_URL}"
            f"{bank_account.id}/deactivate/"
        )

    def bank_transaction_detail_url(
        self,
        transaction=None,
    ):
        transaction = (
            transaction
            or
            self.bank_transaction
        )

        return (
            f"{self.BANK_TRANSACTIONS_URL}"
            f"{transaction.id}/"
        )

    def bank_transaction_reconcile_url(
        self,
        transaction=None,
    ):
        transaction = (
            transaction
            or
            self.bank_transaction
        )

        return (
            f"{self.BANK_TRANSACTIONS_URL}"
            f"{transaction.id}/reconcile/"
        )

    def bank_transfer_detail_url(
        self,
        transfer=None,
    ):
        transfer = (
            transfer
            or
            self.bank_transfer
        )

        return (
            f"{self.BANK_TRANSFERS_URL}"
            f"{transfer.id}/"
        )

    def bank_transfer_post_url(
        self,
        transfer=None,
    ):
        transfer = (
            transfer
            or
            self.bank_transfer
        )

        return (
            f"{self.BANK_TRANSFERS_URL}"
            f"{transfer.id}/post/"
        )

    def bank_transfer_cancel_url(
        self,
        transfer=None,
    ):
        transfer = (
            transfer
            or
            self.bank_transfer
        )

        return (
            f"{self.BANK_TRANSFERS_URL}"
            f"{transfer.id}/cancel/"
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
            body.get(
                "request_id"
            )
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
            body.get(
                "request_id"
            )
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

    # ==================================================
    # CHART OF ACCOUNT API
    # ==================================================

    def test_account_collection_returns_paginated_data(
        self,
    ):
        pipeline_result = {
            "items": [
                self.account,
            ],
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
                    "account_code",
                    "id",
                ],
            },
        }

        with (
            patch.object(
                ChartOfAccountRepository,
                "queryset_for_organization",
                return_value=object(),
            ),
            patch.object(
                APIQueryPipelineService,
                "execute",
                return_value=pipeline_result,
            ),
        ):
            response = self.client.get(
                self.ACCOUNTS_URL
            )

        body = (
            self.assert_success_contract(
                response
            )
        )

        self.assertEqual(
            body["data"][
                "accounts"
            ][0]["account_code"],
            self.account.account_code,
        )

        self.assertEqual(
            body["data"][
                "pagination"
            ]["total_items"],
            1,
        )

    def test_account_collection_creates_account(
        self,
    ):
        payload = {
            "account_code":
                "100100",
            "account_name":
                "Main Bank",
            "account_type":
                "ASSET",
        }

        with patch.object(
            ChartOfAccountAPIService,
            "create_account",
            return_value=self.account,
        ) as create_mock:
            response = self.client.post(
                self.ACCOUNTS_URL,
                data=json.dumps(
                    payload
                ),
                content_type=(
                    "application/json"
                ),
            )

        body = (
            self.assert_success_contract(
                response,
                expected_status=201,
            )
        )

        self.assertEqual(
            body["data"][
                "account"
            ]["id"],
            str(
                self.account.id
            ),
        )

        create_mock.assert_called_once()

    def test_account_detail_returns_account(
        self,
    ):
        with patch.object(
            ChartOfAccountAPIService,
            "get_account",
            return_value=self.account,
        ):
            response = self.client.get(
                self.account_detail_url()
            )

        body = (
            self.assert_success_contract(
                response
            )
        )

        self.assertEqual(
            body["data"][
                "account"
            ]["account_name"],
            self.account.account_name,
        )

    def test_account_detail_updates_account(
        self,
    ):
        updated_account = (
            SimpleNamespace(
                **{
                    **vars(
                        self.account
                    ),
                    "account_name":
                        "Updated Bank",
                }
            )
        )

        with patch.object(
            ChartOfAccountAPIService,
            "update_account",
            return_value=updated_account,
        ):
            response = self.client.patch(
                self.account_detail_url(),
                data=json.dumps({
                    "account_name":
                        "Updated Bank",
                }),
                content_type=(
                    "application/json"
                ),
            )

        body = (
            self.assert_success_contract(
                response
            )
        )

        self.assertEqual(
            body["data"][
                "account"
            ]["account_name"],
            "Updated Bank",
        )

    def test_account_deactivation_returns_account(
        self,
    ):
        inactive_account = (
            SimpleNamespace(
                **{
                    **vars(
                        self.account
                    ),
                    "is_active":
                        False,
                }
            )
        )

        with patch.object(
            ChartOfAccountAPIService,
            "deactivate_account",
            return_value=inactive_account,
        ):
            response = self.client.post(
                self.account_deactivate_url()
            )

        body = (
            self.assert_success_contract(
                response
            )
        )

        self.assertFalse(
            body["data"][
                "account"
            ]["is_active"]
        )

    def test_account_detail_rejects_invalid_identifier(
        self,
    ):
        response = self.client.get(
            (
                f"{self.ACCOUNTS_URL}"
                "invalid-id/"
            )
        )

        body = self.assert_error_contract(
            response,
            400,
            "VALIDATION_ERROR",
        )

        self.assertIn(
            "account_id",
            body["error"][
                "details"
            ],
        )

    def test_account_detail_returns_not_found(
        self,
    ):
        with patch.object(
            ChartOfAccountRepository,
            "get_by_id",
            return_value=None,
        ):
            response = self.client.get(
                self.account_detail_url()
            )

        self.assert_error_contract(
            response,
            404,
            "NOT_FOUND",
        )

    def test_account_collection_rejects_protected_fields(
        self,
    ):
        with self.assertRaises(
            ChartOfAccountAPIValidationError
        ) as context:
            (
                ChartOfAccountAPIService
                .validate_create_payload({
                    "account_code":
                        "100100",
                    "account_name":
                        "Main Bank",
                    "account_type":
                        "ASSET",
                    "organization_id":
                        str(
                            self.organization.id
                        ),
                    "normal_balance":
                        "CREDIT",
                    "is_system_account":
                        True,
                })
            )

        self.assertIn(
            "organization_id",
            context.exception.details,
        )

        self.assertIn(
            "normal_balance",
            context.exception.details,
        )

        self.assertIn(
            "is_system_account",
            context.exception.details,
        )

    def test_account_update_rejects_immutable_fields(
        self,
    ):
        with self.assertRaises(
            ChartOfAccountAPIValidationError
        ) as context:
            (
                ChartOfAccountAPIService
                .validate_update_payload({
                    "account_code":
                        "CHANGED",
                    "account_type":
                        "LIABILITY",
                    "system_key":
                        "ACCOUNTS_PAYABLE",
                })
            )

        self.assertIn(
            "account_code",
            context.exception.details,
        )

        self.assertIn(
            "account_type",
            context.exception.details,
        )

        self.assertIn(
            "system_key",
            context.exception.details,
        )

    def test_account_create_rejects_invalid_account_type(
        self,
    ):
        with self.assertRaises(
            ChartOfAccountAPIValidationError
        ) as context:
            (
                ChartOfAccountAPIService
                .validate_create_payload({
                    "account_code":
                        "100100",
                    "account_name":
                        "Main Bank",
                    "account_type":
                        "INVALID",
                })
            )

        self.assertIn(
            "account_type",
            context.exception.details,
        )

    def test_account_collection_rejects_permission(
        self,
    ):
        with patch.object(
            AuthorizationService,
            "has_permission",
            return_value=False,
        ):
            response = self.client.get(
                self.ACCOUNTS_URL
            )

        self.assert_error_contract(
            response,
            403,
            "FORBIDDEN",
        )

    def test_account_state_error_uses_unprocessable_contract(
        self,
    ):
        with patch.object(
            ChartOfAccountAPIService,
            "create_account",
            side_effect=(
                ChartOfAccountAPIStateError(
                    message=(
                        "Account code already "
                        "exists."
                    ),
                    details={
                        "account": [
                            (
                                "Account code already "
                                "exists."
                            ),
                        ],
                    },
                )
            ),
        ):
            response = self.client.post(
                self.ACCOUNTS_URL,
                data=json.dumps({
                    "account_code":
                        "100100",
                    "account_name":
                        "Duplicate Bank",
                    "account_type":
                        "ASSET",
                }),
                content_type=(
                    "application/json"
                ),
            )

        self.assert_error_contract(
            response,
            422,
            "UNPROCESSABLE_ENTITY",
        )

    def test_account_collection_rejects_delete(
        self,
    ):
        response = self.client.delete(
            self.ACCOUNTS_URL
        )

        self.assert_error_contract(
            response,
            405,
            "METHOD_NOT_ALLOWED",
        )

    def test_account_detail_rejects_post(
        self,
    ):
        response = self.client.post(
            self.account_detail_url(),
            data=json.dumps({}),
            content_type=(
                "application/json"
            ),
        )

        self.assert_error_contract(
            response,
            405,
            "METHOD_NOT_ALLOWED",
        )

    # ==================================================
    # JOURNAL ENTRY API
    # ==================================================

    def test_journal_collection_returns_paginated_data(
        self,
    ):
        pipeline_result = {
            "items": [
                self.journal,
            ],
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
                    "-journal_date",
                    "-created_at",
                    "id",
                ],
            },
        }

        with (
            patch.object(
                JournalEntryRepository,
                "queryset_for_organization",
                return_value=object(),
            ),
            patch.object(
                APIQueryPipelineService,
                "execute",
                return_value=pipeline_result,
            ),
        ):
            response = self.client.get(
                self.JOURNALS_URL
            )

        body = (
            self.assert_success_contract(
                response
            )
        )

        self.assertEqual(
            body["data"][
                "journal_entries"
            ][0]["journal_number"],
            self.journal.journal_number,
        )

        self.assertEqual(
            body["data"][
                "pagination"
            ]["total_items"],
            1,
        )

    def test_journal_collection_creates_manual_journal(
        self,
    ):
        payload = {
            "journal_date":
                "2026-08-30",
            "description":
                "Opening journal",
            "lines": [
                {
                    "account_id":
                        str(
                            self.account.id
                        ),
                    "debit":
                        "1000.00",
                    "credit":
                        "0.00",
                },
                {
                    "account_id":
                        str(
                            self.credit_account.id
                        ),
                    "debit":
                        "0.00",
                    "credit":
                        "1000.00",
                },
            ],
        }

        with patch.object(
            JournalEntryAPIService,
            "create_journal",
            return_value=self.journal,
        ) as create_mock:
            response = self.client.post(
                self.JOURNALS_URL,
                data=json.dumps(
                    payload
                ),
                content_type=(
                    "application/json"
                ),
            )

        body = (
            self.assert_success_contract(
                response,
                expected_status=201,
            )
        )

        self.assertEqual(
            body["data"][
                "journal_entry"
            ]["source_type"],
            "MANUAL",
        )

        create_mock.assert_called_once()

    def test_journal_detail_returns_journal(
        self,
    ):
        with patch.object(
            JournalEntryAPIService,
            "get_journal",
            return_value=self.journal,
        ):
            response = self.client.get(
                self.journal_detail_url()
            )

        body = (
            self.assert_success_contract(
                response
            )
        )

        self.assertEqual(
            body["data"][
                "journal_entry"
            ]["journal_number"],
            self.journal.journal_number,
        )

        self.assertEqual(
            len(
                body["data"][
                    "journal_entry"
                ]["lines"]
            ),
            2,
        )

    def test_journal_detail_updates_draft(
        self,
    ):
        updated_journal = (
            SimpleNamespace(
                **{
                    **vars(
                        self.journal
                    ),
                    "description":
                        "Updated journal",
                }
            )
        )

        with patch.object(
            JournalEntryAPIService,
            "update_journal",
            return_value=updated_journal,
        ):
            response = self.client.patch(
                self.journal_detail_url(),
                data=json.dumps({
                    "description":
                        "Updated journal",
                }),
                content_type=(
                    "application/json"
                ),
            )

        body = (
            self.assert_success_contract(
                response
            )
        )

        self.assertEqual(
            body["data"][
                "journal_entry"
            ]["description"],
            "Updated journal",
        )

    def test_journal_post_returns_posted_journal(
        self,
    ):
        posted_journal = (
            SimpleNamespace(
                **{
                    **vars(
                        self.journal
                    ),
                    "status":
                        "POSTED",
                    "posted_at":
                        datetime.utcnow(),
                }
            )
        )

        with patch.object(
            JournalEntryAPIService,
            "post_journal",
            return_value=posted_journal,
        ):
            response = self.client.post(
                self.journal_post_url()
            )

        body = (
            self.assert_success_contract(
                response
            )
        )

        self.assertEqual(
            body["data"][
                "journal_entry"
            ]["status"],
            "POSTED",
        )

    def test_journal_reverse_returns_both_journals(
        self,
    ):
        reversed_original = (
            SimpleNamespace(
                **{
                    **vars(
                        self.journal
                    ),
                    "status":
                        "REVERSED",
                    "reversed_at":
                        datetime.utcnow(),
                    "reversed_by":
                        self.reversal,
                }
            )
        )

        with patch.object(
            JournalEntryAPIService,
            "reverse_journal",
            return_value={
                "original":
                    reversed_original,
                "reversal":
                    self.reversal,
            },
        ):
            response = self.client.post(
                self.journal_reverse_url(),
                data=json.dumps({
                    "reversal_date":
                        "2026-08-30",
                    "description":
                        "Reverse opening journal",
                }),
                content_type=(
                    "application/json"
                ),
            )

        body = (
            self.assert_success_contract(
                response,
                expected_status=201,
            )
        )

        self.assertEqual(
            body["data"][
                "original"
            ]["status"],
            "REVERSED",
        )

        self.assertEqual(
            body["data"][
                "reversal"
            ]["source_type"],
            "REVERSAL",
        )

    def test_journal_create_forces_manual_source(
        self,
    ):
        values = (
            JournalEntryAPIService
            .validate_create_payload({
                "journal_date":
                    "2026-08-30",
                "description":
                    "Manual journal",
                "lines": [
                    {
                        "account_id":
                            str(
                                self.account.id
                            ),
                        "debit":
                            "100.00",
                    },
                    {
                        "account_id":
                            str(
                                self.credit_account.id
                            ),
                        "credit":
                            "100.00",
                    },
                ],
            })
        )

        self.assertEqual(
            values[
                "source_type"
            ],
            "MANUAL",
        )

        self.assertEqual(
            values[
                "source_id"
            ],
            "",
        )

    def test_journal_create_rejects_source_metadata(
        self,
    ):
        with self.assertRaises(
            JournalEntryAPIValidationError
        ) as context:
            (
                JournalEntryAPIService
                .validate_create_payload({
                    "journal_date":
                        "2026-08-30",
                    "source_type":
                        "SALES_INVOICE",
                    "source_id":
                        str(
                            ObjectId()
                        ),
                    "lines": [
                        {
                            "account_id":
                                str(
                                    self.account.id
                                ),
                            "debit":
                                "100.00",
                        },
                        {
                            "account_id":
                                str(
                                    self.credit_account.id
                                ),
                            "credit":
                                "100.00",
                        },
                    ],
                })
            )

        self.assertIn(
            "source_type",
            context.exception.details,
        )

        self.assertIn(
            "source_id",
            context.exception.details,
        )

    def test_journal_create_rejects_unbalanced_lines(
        self,
    ):
        with self.assertRaises(
            JournalEntryAPIValidationError
        ) as context:
            (
                JournalEntryAPIService
                .validate_create_payload({
                    "journal_date":
                        "2026-08-30",
                    "lines": [
                        {
                            "account_id":
                                str(
                                    self.account.id
                                ),
                            "debit":
                                "100.00",
                        },
                        {
                            "account_id":
                                str(
                                    self.credit_account.id
                                ),
                            "credit":
                                "90.00",
                        },
                    ],
                })
            )

        self.assertIn(
            "lines",
            context.exception.details,
        )

    def test_journal_create_rejects_both_debit_and_credit(
        self,
    ):
        with self.assertRaises(
            JournalEntryAPIValidationError
        ) as context:
            (
                JournalEntryAPIService
                .validate_create_payload({
                    "journal_date":
                        "2026-08-30",
                    "lines": [
                        {
                            "account_id":
                                str(
                                    self.account.id
                                ),
                            "debit":
                                "100.00",
                            "credit":
                                "100.00",
                        },
                        {
                            "account_id":
                                str(
                                    self.credit_account.id
                                ),
                            "credit":
                                "100.00",
                        },
                    ],
                })
            )

        self.assertIn(
            "lines.0",
            context.exception.details,
        )

    def test_journal_detail_rejects_invalid_identifier(
        self,
    ):
        response = self.client.get(
            (
                f"{self.JOURNALS_URL}"
                "invalid-id/"
            )
        )

        body = self.assert_error_contract(
            response,
            400,
            "VALIDATION_ERROR",
        )

        self.assertIn(
            "journal_id",
            body["error"][
                "details"
            ],
        )

    def test_journal_detail_returns_not_found(
        self,
    ):
        with patch.object(
            JournalEntryRepository,
            "get_by_id",
            return_value=None,
        ):
            response = self.client.get(
                self.journal_detail_url()
            )

        self.assert_error_contract(
            response,
            404,
            "NOT_FOUND",
        )

    def test_journal_post_state_error_uses_unprocessable_contract(
        self,
    ):
        with patch.object(
            JournalEntryAPIService,
            "post_journal",
            side_effect=(
                JournalEntryAPIStateError(
                    message=(
                        "Journal entry is "
                        "already posted."
                    ),
                    details={
                        "journal": [
                            (
                                "Journal entry is "
                                "already posted."
                            ),
                        ],
                    },
                )
            ),
        ):
            response = self.client.post(
                self.journal_post_url()
            )

        self.assert_error_contract(
            response,
            422,
            "UNPROCESSABLE_ENTITY",
        )

    def test_journal_collection_rejects_permission(
        self,
    ):
        with patch.object(
            AuthorizationService,
            "has_permission",
            return_value=False,
        ):
            response = self.client.get(
                self.JOURNALS_URL
            )

        self.assert_error_contract(
            response,
            403,
            "FORBIDDEN",
        )

    def test_journal_collection_rejects_delete(
        self,
    ):
        response = self.client.delete(
            self.JOURNALS_URL
        )

        self.assert_error_contract(
            response,
            405,
            "METHOD_NOT_ALLOWED",
        )

    def test_journal_detail_rejects_post(
        self,
    ):
        response = self.client.post(
            self.journal_detail_url(),
            data=json.dumps({}),
            content_type=(
                "application/json"
            ),
        )

        self.assert_error_contract(
            response,
            405,
            "METHOD_NOT_ALLOWED",
        )

    def test_journal_post_rejects_get(
        self,
    ):
        response = self.client.get(
            self.journal_post_url()
        )

        self.assert_error_contract(
            response,
            405,
            "METHOD_NOT_ALLOWED",
        )

    def test_journal_reverse_rejects_get(
        self,
    ):
        response = self.client.get(
            self.journal_reverse_url()
        )

        self.assert_error_contract(
            response,
            405,
            "METHOD_NOT_ALLOWED",
        )

    # ==================================================
    # GENERAL LEDGER API
    # ==================================================

    def test_general_ledger_returns_account_movements(
        self,
    ):
        result = {
            "account":
                self.account,
            "start_date":
                None,
            "end_date":
                None,
            "opening_balance":
                Decimal(
                    "0.00"
                ),
            "entries": [
                {
                    "journal_number":
                        self.journal
                        .journal_number,
                    "journal_date":
                        self.journal
                        .journal_date,
                    "description":
                        "Opening bank balance",
                    "source_type":
                        "MANUAL",
                    "source_id":
                        "",
                    "debit":
                        Decimal(
                            "1000.00"
                        ),
                    "credit":
                        Decimal(
                            "0.00"
                        ),
                    "running_balance":
                        Decimal(
                            "1000.00"
                        ),
                },
            ],
            "total_debit":
                Decimal(
                    "1000.00"
                ),
            "total_credit":
                Decimal(
                    "0.00"
                ),
            "closing_balance":
                Decimal(
                    "1000.00"
                ),
        }

        with patch.object(
            AccountingReportAPIService,
            "get_general_ledger",
            return_value=result,
        ) as ledger_mock:
            response = self.client.get(
                self.general_ledger_url(),
                {
                    "start_date":
                        "2026-08-01",
                    "end_date":
                        "2026-08-30",
                },
            )

        body = (
            self.assert_success_contract(
                response
            )
        )

        ledger = body["data"][
            "general_ledger"
        ]

        self.assertEqual(
            ledger["account"][
                "id"
            ],
            str(
                self.account.id
            ),
        )

        self.assertEqual(
            ledger[
                "closing_balance"
            ],
            "1000.00",
        )

        self.assertEqual(
            len(
                ledger["entries"]
            ),
            1,
        )

        ledger_mock.assert_called_once_with(
            user=self.user,
            organization=(
                self.organization
            ),
            account_id=str(
                self.account.id
            ),
            start_date="2026-08-01",
            end_date="2026-08-30",
        )

    def test_general_ledger_rejects_invalid_account_id(
        self,
    ):
        response = self.client.get(
            (
                "/api/v1/general-ledger/"
                "invalid-id/"
            )
        )

        body = self.assert_error_contract(
            response,
            400,
            "VALIDATION_ERROR",
        )

        self.assertIn(
            "account_id",
            body["error"][
                "details"
            ],
        )

    def test_general_ledger_returns_not_found(
        self,
    ):
        with patch.object(
            ChartOfAccountRepository,
            "get_by_id",
            return_value=None,
        ):
            response = self.client.get(
                self.general_ledger_url()
            )

        self.assert_error_contract(
            response,
            404,
            "NOT_FOUND",
        )

    def test_general_ledger_rejects_permission(
        self,
    ):
        with patch.object(
            AuthorizationService,
            "has_permission",
            return_value=False,
        ):
            response = self.client.get(
                self.general_ledger_url()
            )

        self.assert_error_contract(
            response,
            403,
            "FORBIDDEN",
        )

    def test_general_ledger_rejects_post(
        self,
    ):
        response = self.client.post(
            self.general_ledger_url()
        )

        self.assert_error_contract(
            response,
            405,
            "METHOD_NOT_ALLOWED",
        )

    # ==================================================
    # TRIAL BALANCE API
    # ==================================================

    def test_trial_balance_returns_balanced_report(
        self,
    ):
        result = {
            "as_of_date":
                datetime(
                    2026,
                    8,
                    30,
                ),
            "rows": [
                {
                    "account":
                        self.account,
                    "total_debit":
                        Decimal(
                            "1000.00"
                        ),
                    "total_credit":
                        Decimal(
                            "0.00"
                        ),
                    "debit_balance":
                        Decimal(
                            "1000.00"
                        ),
                    "credit_balance":
                        Decimal(
                            "0.00"
                        ),
                },
                {
                    "account":
                        self.credit_account,
                    "total_debit":
                        Decimal(
                            "0.00"
                        ),
                    "total_credit":
                        Decimal(
                            "1000.00"
                        ),
                    "debit_balance":
                        Decimal(
                            "0.00"
                        ),
                    "credit_balance":
                        Decimal(
                            "1000.00"
                        ),
                },
            ],
            "total_debit_balance":
                Decimal(
                    "1000.00"
                ),
            "total_credit_balance":
                Decimal(
                    "1000.00"
                ),
            "difference":
                Decimal(
                    "0.00"
                ),
            "is_balanced":
                True,
        }

        with patch.object(
            AccountingReportAPIService,
            "get_trial_balance",
            return_value=result,
        ) as trial_balance_mock:
            response = self.client.get(
                self.TRIAL_BALANCE_URL,
                {
                    "as_of_date":
                        "2026-08-30",
                    "include_zero_balances":
                        "false",
                },
            )

        body = (
            self.assert_success_contract(
                response
            )
        )

        trial_balance = body["data"][
            "trial_balance"
        ]

        self.assertTrue(
            trial_balance[
                "is_balanced"
            ]
        )

        self.assertEqual(
            trial_balance[
                "difference"
            ],
            "0.00",
        )

        self.assertEqual(
            len(
                trial_balance[
                    "rows"
                ]
            ),
            2,
        )

        trial_balance_mock.assert_called_once_with(
            user=self.user,
            organization=(
                self.organization
            ),
            as_of_date="2026-08-30",
            include_zero_balances="false",
        )

    def test_trial_balance_boolean_parser(
        self,
    ):
        self.assertTrue(
            (
                AccountingReportAPIService
                ._normalize_boolean(
                    "true",
                    field=(
                        "include_zero_balances"
                    ),
                    default=False,
                )
            )
        )

        self.assertFalse(
            (
                AccountingReportAPIService
                ._normalize_boolean(
                    "false",
                    field=(
                        "include_zero_balances"
                    ),
                    default=True,
                )
            )
        )

    def test_trial_balance_rejects_invalid_boolean(
        self,
    ):
        with self.assertRaises(
            AccountingReportAPIValidationError
        ) as context:
            (
                AccountingReportAPIService
                ._normalize_boolean(
                    "sometimes",
                    field=(
                        "include_zero_balances"
                    ),
                    default=True,
                )
            )

        self.assertIn(
            "include_zero_balances",
            context.exception.details,
        )

    def test_trial_balance_rejects_permission(
        self,
    ):
        with patch.object(
            AuthorizationService,
            "has_permission",
            return_value=False,
        ):
            response = self.client.get(
                self.TRIAL_BALANCE_URL
            )

        self.assert_error_contract(
            response,
            403,
            "FORBIDDEN",
        )

    def test_trial_balance_rejects_post(
        self,
    ):
        response = self.client.post(
            self.TRIAL_BALANCE_URL
        )

        self.assert_error_contract(
            response,
            405,
            "METHOD_NOT_ALLOWED",
        )

    # ==================================================
    # BANK ACCOUNT API
    # ==================================================

    def test_bank_account_collection_returns_data(
        self,
    ):
        pipeline_result = {
            "items": [
                self.bank_account,
            ],
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
                    "account_name",
                    "id",
                ],
            },
        }

        with (
            patch.object(
                BankAccountRepository,
                "queryset_for_organization",
                return_value=object(),
            ),
            patch.object(
                APIQueryPipelineService,
                "execute",
                return_value=pipeline_result,
            ),
        ):
            response = self.client.get(
                self.BANK_ACCOUNTS_URL
            )

        body = self.assert_success_contract(
            response
        )

        accounts = body["data"][
            "bank_accounts"
        ]

        self.assertEqual(
            len(
                accounts
            ),
            1,
        )

        self.assertEqual(
            accounts[0][
                "account_name"
            ],
            "Operating Bank",
        )

        self.assertEqual(
            accounts[0][
                "current_balance"
            ],
            "1250.00",
        )

    def test_bank_account_create_returns_201(
        self,
    ):
        payload = {
            "account_name":
                "Operating Bank",
            "account_type":
                "BANK",
            "bank_name":
                "Example Bank",
            "account_number":
                "1234567890",
            "ifsc_code":
                "EXAM0001234",
            "currency":
                "INR",
            "opening_balance":
                "1000.00",
        }

        with patch.object(
            BankAccountAPIService,
            "create_bank_account",
            return_value=(
                self.bank_account
            ),
        ) as create_mock:
            response = self.client.post(
                self.BANK_ACCOUNTS_URL,
                data=json.dumps(
                    payload
                ),
                content_type=(
                    "application/json"
                ),
            )

        body = self.assert_success_contract(
            response,
            expected_status=201,
        )

        self.assertEqual(
            body["data"][
                "bank_account"
            ]["account_type"],
            "BANK",
        )

        create_mock.assert_called_once_with(
            user=self.user,
            organization=(
                self.organization
            ),
            payload=payload,
        )

    def test_bank_account_detail_returns_data(
        self,
    ):
        with patch.object(
            BankAccountAPIService,
            "get_bank_account",
            return_value=(
                self.bank_account
            ),
        ):
            response = self.client.get(
                self.bank_account_detail_url()
            )

        body = self.assert_success_contract(
            response
        )

        self.assertEqual(
            body["data"][
                "bank_account"
            ]["account_number"],
            "1234567890",
        )

    def test_bank_account_patch_updates_data(
        self,
    ):
        payload = {
            "account_name":
                "Updated Operating Bank",
        }

        updated = (
            SimpleNamespace(
                **{
                    **vars(
                        self.bank_account
                    ),
                    "account_name": (
                        "Updated Operating Bank"
                    ),
                }
            )
        )

        with patch.object(
            BankAccountAPIService,
            "update_bank_account",
            return_value=updated,
        ) as update_mock:
            response = self.client.patch(
                self.bank_account_detail_url(),
                data=json.dumps(
                    payload
                ),
                content_type=(
                    "application/json"
                ),
            )

        body = self.assert_success_contract(
            response
        )

        self.assertEqual(
            body["data"][
                "bank_account"
            ]["account_name"],
            "Updated Operating Bank",
        )

        update_mock.assert_called_once_with(
            user=self.user,
            organization=(
                self.organization
            ),
            bank_account_id=str(
                self.bank_account.id
            ),
            payload=payload,
        )

    def test_bank_account_deactivate_returns_data(
        self,
    ):
        inactive = (
            SimpleNamespace(
                **{
                    **vars(
                        self.bank_account
                    ),
                    "is_active":
                        False,
                }
            )
        )

        with patch.object(
            BankAccountAPIService,
            "deactivate_bank_account",
            return_value=inactive,
        ):
            response = self.client.post(
                self.bank_account_deactivate_url()
            )

        body = self.assert_success_contract(
            response
        )

        self.assertFalse(
            body["data"][
                "bank_account"
            ]["is_active"]
        )

    def test_bank_account_rejects_cash_bank_details(
        self,
    ):
        with self.assertRaises(
            BankAccountAPIValidationError
        ) as context:
            (
                BankAccountAPIService
                .validate_create_payload(
                    {
                        "account_name":
                            "Petty Cash",
                        "account_type":
                            "CASH",
                        "bank_name":
                            "Not Allowed",
                    }
                )
            )

        self.assertIn(
            "account_type",
            context.exception.details,
        )

    def test_bank_account_invalid_id_returns_400(
        self,
    ):
        response = self.client.get(
            (
                f"{self.BANK_ACCOUNTS_URL}"
                "invalid-id/"
            )
        )

        self.assert_error_contract(
            response,
            400,
            "VALIDATION_ERROR",
        )

    def test_bank_account_missing_returns_404(
        self,
    ):
        with patch.object(
            BankAccountRepository,
            "get_by_id",
            return_value=None,
        ):
            response = self.client.get(
                (
                    f"{self.BANK_ACCOUNTS_URL}"
                    f"{ObjectId()}/"
                )
            )

        self.assert_error_contract(
            response,
            404,
            "NOT_FOUND",
        )

    def test_bank_account_rejects_permission(
        self,
    ):
        with patch.object(
            AuthorizationService,
            "has_permission",
            return_value=False,
        ):
            response = self.client.get(
                self.BANK_ACCOUNTS_URL
            )

        self.assert_error_contract(
            response,
            403,
            "FORBIDDEN",
        )

    def test_bank_account_collection_rejects_put(
        self,
    ):
        response = self.client.put(
            self.BANK_ACCOUNTS_URL,
            data=json.dumps({}),
            content_type=(
                "application/json"
            ),
        )

        self.assert_error_contract(
            response,
            405,
            "METHOD_NOT_ALLOWED",
        )

    # ==================================================
    # BANK TRANSACTION API
    # ==================================================

    def test_bank_transaction_collection_returns_data(
        self,
    ):
        pipeline_result = {
            "items": [
                self.bank_transaction,
            ],
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
                    "-transaction_date",
                    "id",
                ],
            },
        }

        with (
            patch.object(
                BankTransactionRepository,
                "queryset_for_organization",
                return_value=object(),
            ),
            patch.object(
                APIQueryPipelineService,
                "execute",
                return_value=pipeline_result,
            ),
        ):
            response = self.client.get(
                self.BANK_TRANSACTIONS_URL
            )

        body = self.assert_success_contract(
            response
        )

        transactions = body["data"][
            "bank_transactions"
        ]

        self.assertEqual(
            len(
                transactions
            ),
            1,
        )

        self.assertEqual(
            transactions[0][
                "transaction_number"
            ],
            "BTX-TEST000001",
        )

        self.assertEqual(
            transactions[0][
                "balance_after"
            ],
            "1250.00",
        )

    def test_bank_transaction_create_returns_201(
        self,
    ):
        payload = {
            "bank_account_id":
                str(
                    self.bank_account.id
                ),
            "transaction_type":
                "MONEY_IN",
            "transaction_date":
                "2026-08-31",
            "amount":
                "250.00",
            "external_reference":
                "UTR-TEST-001",
            "description":
                "Customer receipt",
        }

        with patch.object(
            BankTransactionAPIService,
            "create_transaction",
            return_value=(
                self.bank_transaction
            ),
        ) as create_mock:
            response = self.client.post(
                self.BANK_TRANSACTIONS_URL,
                data=json.dumps(
                    payload
                ),
                content_type=(
                    "application/json"
                ),
            )

        body = self.assert_success_contract(
            response,
            expected_status=201,
        )

        self.assertEqual(
            body["data"][
                "bank_transaction"
            ]["transaction_type"],
            "MONEY_IN",
        )

        create_mock.assert_called_once_with(
            user=self.user,
            organization=(
                self.organization
            ),
            payload=payload,
        )

    def test_bank_transaction_detail_returns_data(
        self,
    ):
        with patch.object(
            BankTransactionAPIService,
            "get_transaction",
            return_value=(
                self.bank_transaction
            ),
        ):
            response = self.client.get(
                self.bank_transaction_detail_url()
            )

        body = self.assert_success_contract(
            response
        )

        self.assertEqual(
            body["data"][
                "bank_transaction"
            ]["amount"],
            "250.00",
        )

    def test_bank_transaction_reconcile_returns_data(
        self,
    ):
        reconciled = (
            SimpleNamespace(
                **{
                    **vars(
                        self.bank_transaction
                    ),
                    "reconciliation_status":
                        "RECONCILED",
                    "reconciled_at":
                        datetime.utcnow(),
                }
            )
        )

        with patch.object(
            BankTransactionAPIService,
            "reconcile_transaction",
            return_value=reconciled,
        ) as reconcile_mock:
            response = self.client.post(
                self.bank_transaction_reconcile_url()
            )

        body = self.assert_success_contract(
            response
        )

        self.assertEqual(
            body["data"][
                "bank_transaction"
            ]["reconciliation_status"],
            "RECONCILED",
        )

        reconcile_mock.assert_called_once_with(
            user=self.user,
            organization=(
                self.organization
            ),
            transaction_id=str(
                self.bank_transaction.id
            ),
        )

    def test_bank_transaction_rejects_system_type(
        self,
    ):
        with self.assertRaises(
            BankTransactionAPIValidationError
        ) as context:
            (
                BankTransactionAPIService
                .validate_create_payload(
                    {
                        "bank_account_id":
                            str(
                                self.bank_account.id
                            ),
                        "transaction_type":
                            "TRANSFER_IN",
                        "transaction_date":
                            "2026-08-31",
                        "amount":
                            "100.00",
                    }
                )
            )

        self.assertIn(
            "transaction_type",
            context.exception.details,
        )

    def test_bank_transaction_requires_complete_reference(
        self,
    ):
        with self.assertRaises(
            BankTransactionAPIValidationError
        ) as context:
            (
                BankTransactionAPIService
                .validate_create_payload(
                    {
                        "bank_account_id":
                            str(
                                self.bank_account.id
                            ),
                        "transaction_type":
                            "MONEY_OUT",
                        "transaction_date":
                            "2026-08-31",
                        "amount":
                            "50.00",
                        "reference_type":
                            "VENDOR_PAYMENT",
                    }
                )
            )

        self.assertIn(
            "reference_id",
            context.exception.details,
        )

    def test_bank_transaction_state_error_returns_422(
        self,
    ):
        with patch.object(
            BankTransactionAPIService,
            "reconcile_transaction",
            side_effect=(
                BankTransactionAPIStateError(
                    message=(
                        "Bank transaction is "
                        "already reconciled."
                    ),
                )
            ),
        ):
            response = self.client.post(
                self.bank_transaction_reconcile_url()
            )

        self.assert_error_contract(
            response,
            422,
            "UNPROCESSABLE_ENTITY",
        )

    def test_bank_transaction_invalid_id_returns_400(
        self,
    ):
        response = self.client.get(
            (
                f"{self.BANK_TRANSACTIONS_URL}"
                "invalid-id/"
            )
        )

        self.assert_error_contract(
            response,
            400,
            "VALIDATION_ERROR",
        )

    def test_bank_transaction_rejects_permission(
        self,
    ):
        with patch.object(
            AuthorizationService,
            "has_permission",
            return_value=False,
        ):
            response = self.client.get(
                self.BANK_TRANSACTIONS_URL
            )

        self.assert_error_contract(
            response,
            403,
            "FORBIDDEN",
        )

    def test_bank_transaction_detail_rejects_post(
        self,
    ):
        response = self.client.post(
            self.bank_transaction_detail_url()
        )

        self.assert_error_contract(
            response,
            405,
            "METHOD_NOT_ALLOWED",
        )

    # ==================================================
    # BANK TRANSFER API
    # ==================================================

    def test_bank_transfer_collection_returns_data(
        self,
    ):
        pipeline_result = {
            "items": [
                self.bank_transfer,
            ],
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
                    "-transfer_date",
                    "id",
                ],
            },
        }

        with (
            patch.object(
                BankTransferRepository,
                "queryset_for_organization",
                return_value=object(),
            ),
            patch.object(
                APIQueryPipelineService,
                "execute",
                return_value=pipeline_result,
            ),
        ):
            response = self.client.get(
                self.BANK_TRANSFERS_URL
            )

        body = self.assert_success_contract(
            response
        )

        transfers = body["data"][
            "bank_transfers"
        ]

        self.assertEqual(
            len(
                transfers
            ),
            1,
        )

        self.assertEqual(
            transfers[0][
                "transfer_number"
            ],
            "TRF-TEST000001",
        )

        self.assertEqual(
            transfers[0][
                "status"
            ],
            "DRAFT",
        )

    def test_bank_transfer_create_returns_201(
        self,
    ):
        payload = {
            "source_account_id":
                str(
                    self.bank_account.id
                ),
            "destination_account_id":
                str(
                    self.destination_bank_account.id
                ),
            "transfer_date":
                "2026-08-31",
            "amount":
                "100.00",
            "reference":
                "TRANSFER-001",
            "notes":
                "Move funds.",
        }

        with patch.object(
            BankTransferAPIService,
            "create_transfer",
            return_value=(
                self.bank_transfer
            ),
        ) as create_mock:
            response = self.client.post(
                self.BANK_TRANSFERS_URL,
                data=json.dumps(
                    payload
                ),
                content_type=(
                    "application/json"
                ),
            )

        body = self.assert_success_contract(
            response,
            expected_status=201,
        )

        self.assertEqual(
            body["data"][
                "bank_transfer"
            ]["amount"],
            "100.00",
        )

        create_mock.assert_called_once_with(
            user=self.user,
            organization=(
                self.organization
            ),
            payload=payload,
        )

    def test_bank_transfer_detail_returns_data(
        self,
    ):
        with patch.object(
            BankTransferAPIService,
            "get_transfer",
            return_value=(
                self.bank_transfer
            ),
        ):
            response = self.client.get(
                self.bank_transfer_detail_url()
            )

        body = self.assert_success_contract(
            response
        )

        self.assertEqual(
            body["data"][
                "bank_transfer"
            ]["source_account"][
                "account_name"
            ],
            "Operating Bank",
        )

        self.assertEqual(
            body["data"][
                "bank_transfer"
            ]["destination_account"][
                "account_name"
            ],
            "Secondary Bank",
        )

    def test_bank_transfer_post_returns_data(
        self,
    ):
        posted = (
            SimpleNamespace(
                **{
                    **vars(
                        self.bank_transfer
                    ),
                    "status":
                        "POSTED",
                    "posted_at":
                        datetime.utcnow(),
                }
            )
        )

        with patch.object(
            BankTransferAPIService,
            "post_transfer",
            return_value=posted,
        ) as post_mock:
            response = self.client.post(
                self.bank_transfer_post_url()
            )

        body = self.assert_success_contract(
            response
        )

        self.assertEqual(
            body["data"][
                "bank_transfer"
            ]["status"],
            "POSTED",
        )

        post_mock.assert_called_once_with(
            user=self.user,
            organization=(
                self.organization
            ),
            transfer_id=str(
                self.bank_transfer.id
            ),
        )

    def test_bank_transfer_cancel_returns_data(
        self,
    ):
        cancelled = (
            SimpleNamespace(
                **{
                    **vars(
                        self.bank_transfer
                    ),
                    "status":
                        "CANCELLED",
                    "cancelled_at":
                        datetime.utcnow(),
                }
            )
        )

        with patch.object(
            BankTransferAPIService,
            "cancel_transfer",
            return_value=cancelled,
        ):
            response = self.client.post(
                self.bank_transfer_cancel_url()
            )

        body = self.assert_success_contract(
            response
        )

        self.assertEqual(
            body["data"][
                "bank_transfer"
            ]["status"],
            "CANCELLED",
        )

    def test_bank_transfer_rejects_same_account(
        self,
    ):
        account_id = str(
            self.bank_account.id
        )

        with self.assertRaises(
            BankTransferAPIValidationError
        ) as context:
            (
                BankTransferAPIService
                .validate_create_payload(
                    {
                        "source_account_id":
                            account_id,
                        "destination_account_id":
                            account_id,
                        "transfer_date":
                            "2026-08-31",
                        "amount":
                            "100.00",
                    }
                )
            )

        self.assertIn(
            "destination_account_id",
            context.exception.details,
        )

    def test_bank_transfer_post_state_error_returns_422(
        self,
    ):
        with patch.object(
            BankTransferAPIService,
            "post_transfer",
            side_effect=(
                BankTransferAPIStateError(
                    message=(
                        "Only draft bank transfers "
                        "can be posted."
                    ),
                )
            ),
        ):
            response = self.client.post(
                self.bank_transfer_post_url()
            )

        self.assert_error_contract(
            response,
            422,
            "UNPROCESSABLE_ENTITY",
        )

    def test_bank_transfer_invalid_id_returns_400(
        self,
    ):
        response = self.client.get(
            (
                f"{self.BANK_TRANSFERS_URL}"
                "invalid-id/"
            )
        )

        self.assert_error_contract(
            response,
            400,
            "VALIDATION_ERROR",
        )

    def test_bank_transfer_rejects_permission(
        self,
    ):
        with patch.object(
            AuthorizationService,
            "has_permission",
            return_value=False,
        ):
            response = self.client.get(
                self.BANK_TRANSFERS_URL
            )

        self.assert_error_contract(
            response,
            403,
            "FORBIDDEN",
        )

    def test_bank_transfer_post_rejects_get(
        self,
    ):
        response = self.client.get(
            self.bank_transfer_post_url()
        )

        self.assert_error_contract(
            response,
            405,
            "METHOD_NOT_ALLOWED",
        )