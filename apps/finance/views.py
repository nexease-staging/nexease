from decimal import Decimal
import json
from apps.finance.services.bank_statement_service import (
    BankStatementService,
)
from apps.finance.services.finance_audit_service import (
    FinanceAuditService,
)

from apps.finance.services.cash_flow_report_service import (
    CashFlowReportService,
)
from apps.finance.models import (
    BankPaymentSuggestion,
)
from apps.finance.services.bank_payment_suggestion_service import (
    BankPaymentSuggestionService,
)
from apps.finance.services.bank_transaction_service import (
    BankTransactionService,
)
from bson import ObjectId
from bson.errors import InvalidId

from django.http import JsonResponse

from apps.finance.repositories.bank_account_repository import (
    BankAccountRepository,
)
from apps.finance.services.finance_dashboard_service import (
    FinanceDashboardService,
)
from apps.finance.services.bank_account_service import (
    BankAccountService,
)

from apps.finance.models import (
    BankAccount,
)

from apps.finance.services.bank_transaction_service import (
    BankTransactionService,
)
from apps.finance.models import (
    ChartOfAccount,
)

from apps.finance.services.journal_entry_service import (
    JournalEntryService,
)
from apps.finance.services.general_ledger_service import (
    GeneralLedgerService,
)

from apps.finance.services.trial_balance_service import (
    TrialBalanceService,
)
from apps.finance.services.profit_and_loss_service import (
    ProfitAndLossService,
)
from apps.finance.services.balance_sheet_service import (
    BalanceSheetService,
)
from apps.finance.services.finance_dashboard_service import (
    FinanceDashboardService,
)
from apps.finance.services.document_access_log_service import (
    DocumentAccessLogService,
)
from apps.finance.services.document_delivery_log_service import (
    DocumentDeliveryLogService,
)
from apps.finance.services.document_delivery_retry_service import (
    DocumentDeliveryRetryService,
)

def _bank_account_response(
    bank_account,
):
    return {
        "id": str(
            bank_account.id
        ),
        "account_name":
            bank_account.account_name,
        "account_type":
            bank_account.account_type,
        "bank_name":
            bank_account.bank_name,
        "account_number":
            bank_account.account_number,
        "ifsc_code":
            bank_account.ifsc_code,
        "currency":
            bank_account.currency,
        "opening_balance":
            str(
                bank_account.opening_balance
            ),
        "current_balance":
            str(
                bank_account.current_balance
            ),
        "is_active":
            bank_account.is_active,
        "created_at": (
            bank_account.created_at.isoformat()
            if bank_account.created_at
            else None
        ),
        "updated_at": (
            bank_account.updated_at.isoformat()
            if bank_account.updated_at
            else None
        ),
    }

def bank_accounts(
    request,
):
    user = request.user

    if not user.is_authenticated:
        return JsonResponse(
            {
                "error":
                    "Not authenticated."
            },
            status=401,
        )

    organization = user.organization

    if request.method == "GET":
        try:
            account_type = (
                request.GET.get(
                    "account_type"
                )
            )

            is_active_raw = (
                request.GET.get(
                    "is_active"
                )
            )

            is_active = None

            if is_active_raw is not None:
                value = (
                    is_active_raw
                    .strip()
                    .lower()
                )

                if value == "true":
                    is_active = True

                elif value == "false":
                    is_active = False

                else:
                    raise ValueError(
                        "is_active must be "
                        "true or false."
                    )

            accounts = (
                BankAccountService
                .list_bank_accounts(
                    user=user,
                    organization=organization,
                    account_type=(
                        account_type
                    ),
                    is_active=is_active,
                )
            )

            return JsonResponse(
                {
                    "count":
                        accounts.count(),
                    "bank_accounts": [
                        _bank_account_response(
                            account
                        )
                        for account
                        in accounts
                    ],
                },
                status=200,
            )

        except PermissionError as exc:
            return JsonResponse(
                {"error": str(exc)},
                status=403,
            )

        except ValueError as exc:
            return JsonResponse(
                {"error": str(exc)},
                status=400,
            )
    if request.method == "POST":
        try:
            payload = json.loads(
                request.body
            )

            account = (
                BankAccountService
                .create_bank_account(
                    user=user,
                    organization=organization,
                    account_name=(
                        payload.get(
                            "account_name"
                        )
                    ),
                    account_type=(
                        payload.get(
                            "account_type"
                        )
                    ),
                    bank_name=(
                        payload.get(
                            "bank_name",
                            "",
                        )
                    ),
                    account_number=(
                        payload.get(
                            "account_number",
                            "",
                        )
                    ),
                    ifsc_code=(
                        payload.get(
                            "ifsc_code",
                            "",
                        )
                    ),
                    currency=(
                        payload.get(
                            "currency",
                            "INR",
                        )
                    ),
                    opening_balance=(
                        payload.get(
                            "opening_balance",
                            0,
                        )
                    ),
                )
            )

            return JsonResponse(
                {
                    "message":
                        "Bank account created "
                        "successfully.",
                    "bank_account":
                        _bank_account_response(
                            account
                        ),
                },
                status=201,
            )

        except json.JSONDecodeError:
            return JsonResponse(
                {
                    "error":
                        "Invalid JSON body."
                },
                status=400,
            )

        except PermissionError as exc:
            return JsonResponse(
                {"error": str(exc)},
                status=403,
            )

        except ValueError as exc:
            return JsonResponse(
                {"error": str(exc)},
                status=400,
            )

    return JsonResponse(
        {"error": "Method not allowed."},
        status=405,
    )

def bank_account_detail(
    request,
    bank_account_id,
):
    user = request.user

    if not user.is_authenticated:
        return JsonResponse(
            {
                "error":
                    "Not authenticated."
            },
            status=401,
        )

    try:
        try:
            ObjectId(
                bank_account_id
            )

        except (
            InvalidId,
            TypeError,
        ):
            raise ValueError(
                "Invalid bank account ID."
            )

        bank_account = (
            BankAccountRepository
            .get_by_id(
                organization=(
                    user.organization
                ),
                bank_account_id=(
                    bank_account_id
                ),
            )
        )

        if not bank_account:
            return JsonResponse(
                {
                    "error":
                        "Bank account not found."
                },
                status=404,
            )

        if request.method == "GET":
            bank_account = (
                BankAccountService
                .get_bank_account(
                    user=user,
                    organization=(
                        user.organization
                    ),
                    bank_account_id=(
                        bank_account_id
                    ),
                )
            )

            return JsonResponse(
                {
                    "bank_account":
                        _bank_account_response(
                            bank_account
                        ),
                },
                status=200,
            )
        if request.method == "PUT":
            payload = json.loads(
                request.body
            )

            protected_fields = {
                "account_type",
                "currency",
                "opening_balance",
                "current_balance",
                "is_active",
            }

            supplied_protected = (
                protected_fields
                .intersection(
                    payload.keys()
                )
            )

            if supplied_protected:
                raise ValueError(
                    "Protected bank account "
                    "fields cannot be updated "
                    "through this endpoint."
                )

            bank_account = (
                BankAccountService
                .update_bank_account(
                    user=user,
                    organization=(
                        user.organization
                    ),
                    bank_account=(
                        bank_account
                    ),
                    account_name=(
                        payload.get(
                            "account_name",
                            bank_account
                            .account_name,
                        )
                    ),
                    bank_name=(
                        payload.get(
                            "bank_name",
                            bank_account
                            .bank_name,
                        )
                    ),
                    account_number=(
                        payload.get(
                            "account_number",
                            bank_account
                            .account_number,
                        )
                    ),
                    ifsc_code=(
                        payload.get(
                            "ifsc_code",
                            bank_account
                            .ifsc_code,
                        )
                    ),
                )
            )

            return JsonResponse(
                {
                    "message":
                        "Bank account updated "
                        "successfully.",
                    "bank_account":
                        _bank_account_response(
                            bank_account
                        ),
                },
                status=200,
            )

        return JsonResponse(
            {
                "error":
                    "Method not allowed."
            },
            status=405,
        )

    except json.JSONDecodeError:
        return JsonResponse(
            {
                "error":
                    "Invalid JSON body."
            },
            status=400,
        )

    except PermissionError as exc:
        return JsonResponse(
            {"error": str(exc)},
            status=403,
        )

    except ValueError as exc:
        return JsonResponse(
            {"error": str(exc)},
            status=400,
        )

def deactivate_bank_account(
    request,
    bank_account_id,
):
    user = request.user

    if not user.is_authenticated:
        return JsonResponse(
            {
                "error":
                    "Not authenticated."
            },
            status=401,
        )

    if request.method != "PUT":
        return JsonResponse(
            {
                "error":
                    "Method not allowed."
            },
            status=405,
        )

    try:
        try:
            ObjectId(
                bank_account_id
            )

        except (
            InvalidId,
            TypeError,
        ):
            raise ValueError(
                "Invalid bank account ID."
            )

        bank_account = (
            BankAccountRepository
            .get_by_id(
                organization=(
                    user.organization
                ),
                bank_account_id=(
                    bank_account_id
                ),
            )
        )

        if not bank_account:
            return JsonResponse(
                {
                    "error":
                        "Bank account not found."
                },
                status=404,
            )

        bank_account = (
            BankAccountService
            .deactivate_bank_account(
                user=user,
                organization=(
                    user.organization
                ),
                bank_account=(
                    bank_account
                ),
            )
        )

        return JsonResponse(
            {
                "message":
                    "Bank account deactivated "
                    "successfully.",
                "bank_account":
                    _bank_account_response(
                        bank_account
                    ),
            },
            status=200,
        )

    except PermissionError as exc:
        return JsonResponse(
            {"error": str(exc)},
            status=403,
        )

    except ValueError as exc:
        return JsonResponse(
            {"error": str(exc)},
            status=400,
        )

def _bank_transaction_response(
    transaction,
):
    return {
        "id": str(
            transaction.id
        ),
        "transaction_number":
            transaction.transaction_number,
        "bank_account": {
            "id": str(
                transaction.bank_account.id
            ),
            "account_name":
                transaction
                .bank_account
                .account_name,
        },
        "transaction_type":
            transaction.transaction_type,
        "transaction_date": (
            transaction
            .transaction_date
            .isoformat()
            if transaction.transaction_date
            else None
        ),
        "amount":
            str(transaction.amount),
        "balance_before":
            str(
                transaction.balance_before
            ),
        "balance_after":
            str(
                transaction.balance_after
            ),
        "reference_type":
            transaction.reference_type,
        "reference_id":
            transaction.reference_id,
        "external_reference":
            transaction.external_reference,
        "description":
            transaction.description,
        "reconciliation_status":
            transaction
            .reconciliation_status,
        "reconciled_at": (
            transaction
            .reconciled_at
            .isoformat()
            if transaction.reconciled_at
            else None
        ),
        "created_at": (
            transaction
            .created_at
            .isoformat()
            if transaction.created_at
            else None
        ),
    }

def bank_transactions(
    request,
):
    user = request.user

    if not user.is_authenticated:
        return JsonResponse(
            {"error": "Not authenticated."},
            status=401,
        )

    if request.method != "GET":
        return JsonResponse(
            {"error": "Method not allowed."},
            status=405,
        )

    try:
        bank_account = None

        bank_account_id = (
            request.GET.get(
                "bank_account_id"
            )
        )

        if bank_account_id:
            try:
                ObjectId(
                    bank_account_id
                )

            except (
                InvalidId,
                TypeError,
            ):
                raise ValueError(
                    "Invalid bank account ID."
                )

            bank_account = (
                BankAccount.objects(
                    organization=(
                        user.organization
                    ),
                    id=bank_account_id,
                ).first()
            )

            if not bank_account:
                raise ValueError(
                    "Bank account not found."
                )

        transactions = (
            BankTransactionService
            .list_transactions(
                user=user,
                organization=(
                    user.organization
                ),
                bank_account=(
                    bank_account
                ),
                transaction_type=(
                    request.GET.get(
                        "transaction_type"
                    )
                ),
                reconciliation_status=(
                    request.GET.get(
                        "reconciliation_status"
                    )
                ),
            )
        )

        return JsonResponse(
            {
                "count":
                    transactions.count(),
                "transactions": [
                    _bank_transaction_response(
                        transaction
                    )
                    for transaction
                    in transactions
                ],
            },
            status=200,
        )

    except PermissionError as exc:
        return JsonResponse(
            {"error": str(exc)},
            status=403,
        )

    except ValueError as exc:
        return JsonResponse(
            {"error": str(exc)},
            status=400,
        )


def bank_transaction_detail(
    request,
    transaction_id,
):
    user = request.user

    if not user.is_authenticated:
        return JsonResponse(
            {"error": "Not authenticated."},
            status=401,
        )

    if request.method != "GET":
        return JsonResponse(
            {"error": "Method not allowed."},
            status=405,
        )

    try:
        try:
            ObjectId(
                transaction_id
            )

        except (
            InvalidId,
            TypeError,
        ):
            raise ValueError(
                "Invalid transaction ID."
            )

        transaction = (
            BankTransactionService
            .get_transaction(
                user=user,
                organization=(
                    user.organization
                ),
                transaction_id=(
                    transaction_id
                ),
            )
        )

        return JsonResponse(
            {
                "transaction":
                    _bank_transaction_response(
                        transaction
                    ),
            },
            status=200,
        )

    except PermissionError as exc:
        return JsonResponse(
            {"error": str(exc)},
            status=403,
        )

    except ValueError as exc:
        return JsonResponse(
            {"error": str(exc)},
            status=400,
        )


def bank_account_statement(
    request,
    bank_account_id,
):
    user = request.user

    if not user.is_authenticated:
        return JsonResponse(
            {"error": "Not authenticated."},
            status=401,
        )

    if request.method != "GET":
        return JsonResponse(
            {"error": "Method not allowed."},
            status=405,
        )

    try:
        try:
            ObjectId(
                bank_account_id
            )

        except (
            InvalidId,
            TypeError,
        ):
            raise ValueError(
                "Invalid bank account ID."
            )

        bank_account = (
            BankAccount.objects(
                organization=(
                    user.organization
                ),
                id=bank_account_id,
            ).first()
        )

        if not bank_account:
            raise ValueError(
                "Bank account not found."
            )

        transactions = (
            BankTransactionService
            .list_transactions(
                user=user,
                organization=(
                    user.organization
                ),
                bank_account=(
                    bank_account
                ),
            )
        )

        return JsonResponse(
            {
                "bank_account":
                    _bank_account_response(
                        bank_account
                    ),
                "transaction_count":
                    transactions.count(),
                "transactions": [
                    _bank_transaction_response(
                        transaction
                    )
                    for transaction
                    in transactions
                ],
            },
            status=200,
        )

    except PermissionError as exc:
        return JsonResponse(
            {"error": str(exc)},
            status=403,
        )

    except ValueError as exc:
        return JsonResponse(
            {"error": str(exc)},
            status=400,
        )

def reconcile_bank_transaction(
    request,
    transaction_id,
):
    user = request.user

    if not user.is_authenticated:
        return JsonResponse(
            {
                "error":
                    "Not authenticated."
            },
            status=401,
        )

    if request.method != "PUT":
        return JsonResponse(
            {
                "error":
                    "Method not allowed."
            },
            status=405,
        )

    try:
        try:
            ObjectId(
                transaction_id
            )

        except (
            InvalidId,
            TypeError,
        ):
            raise ValueError(
                "Invalid transaction ID."
            )

        transaction = (
            BankTransactionService
            .get_transaction(
                user=user,
                organization=(
                    user.organization
                ),
                transaction_id=(
                    transaction_id
                ),
            )
        )

        transaction = (
            BankTransactionService
            .reconcile_transaction(
                user=user,
                organization=(
                    user.organization
                ),
                transaction=(
                    transaction
                ),
            )
        )

        return JsonResponse(
            {
                "message":
                    "Bank transaction reconciled "
                    "successfully.",
                "transaction":
                    _bank_transaction_response(
                        transaction
                    ),
            },
            status=200,
        )

    except PermissionError as exc:
        return JsonResponse(
            {"error": str(exc)},
            status=403,
        )

    except ValueError as exc:
        return JsonResponse(
            {"error": str(exc)},
            status=400,
        )

def _bank_statement_line_response(
    line,
):
    return {
        "line_number":
            line.line_number,
        "transaction_date": (
            line.transaction_date
            .isoformat()
            if line.transaction_date
            else None
        ),
        "value_date": (
            line.value_date.isoformat()
            if line.value_date
            else None
        ),
        "description":
            line.description,
        "external_reference":
            line.external_reference,
        "debit_amount":
            str(line.debit_amount),
        "credit_amount":
            str(line.credit_amount),
        "running_balance": (
            str(line.running_balance)
            if line.running_balance
            is not None
            else None
        ),
        "match_status":
            line.match_status,
        "matched_transaction": (
            {
                "id":
                    str(
                        line
                        .matched_transaction
                        .id
                    ),
                "transaction_number":
                    line
                    .matched_transaction
                    .transaction_number,
            }
            if line.matched_transaction
            else None
        ),
        "matched_at": (
            line.matched_at.isoformat()
            if line.matched_at
            else None
        ),
    }

def auto_match_bank_statement_line(
    request,
    statement_id,
    line_number,
):
    user = request.user

    if not user.is_authenticated:
        return JsonResponse(
            {
                "error":
                    "Not authenticated."
            },
            status=401,
        )

    if request.method != "PUT":
        return JsonResponse(
            {
                "error":
                    "Method not allowed."
            },
            status=405,
        )

    try:
        try:
            ObjectId(
                statement_id
            )

        except (
            InvalidId,
            TypeError,
        ):
            raise ValueError(
                "Invalid bank statement ID."
            )

        statement = (
            BankStatementService
            .get_statement(
                user=user,
                organization=(
                    user.organization
                ),
                statement_id=(
                    statement_id
                ),
            )
        )

        if (
            statement.status
            == "CANCELLED"
        ):
            raise ValueError(
                "Cancelled bank statements "
                "cannot be matched."
            )

        line = (
            BankStatementService
            .get_statement_line(
                statement=statement,
                line_number=line_number,
            )
        )

        result = (
            BankStatementService
            .auto_match_line(
                user=user,
                organization=(
                    user.organization
                ),
                statement=statement,
                line=line,
            )
        )

        statement.reload()

        line = (
            BankStatementService
            .get_statement_line(
                statement=statement,
                line_number=line_number,
            )
        )

        response_data = {
            "match_type":
                result["match_type"],
            "matched":
                result.get(
                    "matched",
                    False,
                ),
            "statement_status":
                statement.status,
            "line":
                _bank_statement_line_response(
                    line
                ),
        }

        if (
            result.get(
                "transaction"
            )
            is not None
        ):
            response_data[
                "transaction"
            ] = (
                _bank_transaction_response(
                    result[
                        "transaction"
                    ]
                )
            )

        if (
            "candidate_count"
            in result
        ):
            response_data[
                "candidate_count"
            ] = result[
                "candidate_count"
            ]

        return JsonResponse(
            response_data,
            status=200,
        )

    except PermissionError as exc:
        return JsonResponse(
            {"error": str(exc)},
            status=403,
        )

    except ValueError as exc:
        return JsonResponse(
            {"error": str(exc)},
            status=400,
        )


def manual_match_bank_statement_line(
    request,
    statement_id,
    line_number,
    transaction_id,
):
    user = request.user

    if not user.is_authenticated:
        return JsonResponse(
            {
                "error":
                    "Not authenticated."
            },
            status=401,
        )

    if request.method != "PUT":
        return JsonResponse(
            {
                "error":
                    "Method not allowed."
            },
            status=405,
        )

    try:
        try:
            ObjectId(
                statement_id
            )

            ObjectId(
                transaction_id
            )

        except (
            InvalidId,
            TypeError,
        ):
            raise ValueError(
                "Invalid statement or "
                "transaction ID."
            )

        statement = (
            BankStatementService
            .get_statement(
                user=user,
                organization=(
                    user.organization
                ),
                statement_id=(
                    statement_id
                ),
            )
        )

        if (
            statement.status
            == "CANCELLED"
        ):
            raise ValueError(
                "Cancelled bank statements "
                "cannot be matched."
            )

        line = (
            BankStatementService
            .get_statement_line(
                statement=statement,
                line_number=line_number,
            )
        )

        transaction = (
            BankTransactionService
            .get_transaction(
                user=user,
                organization=(
                    user.organization
                ),
                transaction_id=(
                    transaction_id
                ),
            )
        )

        (
            BankStatementService
            .apply_match(
                user=user,
                organization=(
                    user.organization
                ),
                statement=statement,
                line=line,
                transaction=(
                    transaction
                ),
            )
        )

        statement.reload()
        transaction.reload()

        line = (
            BankStatementService
            .get_statement_line(
                statement=statement,
                line_number=line_number,
            )
        )

        return JsonResponse(
            {
                "message":
                    "Statement line matched "
                    "successfully.",
                "statement_status":
                    statement.status,
                "line":
                    _bank_statement_line_response(
                        line
                    ),
                "transaction":
                    _bank_transaction_response(
                        transaction
                    ),
            },
            status=200,
        )

    except PermissionError as exc:
        return JsonResponse(
            {"error": str(exc)},
            status=403,
        )

    except ValueError as exc:
        return JsonResponse(
            {"error": str(exc)},
            status=400,
        )

def ignore_bank_statement_line(
    request,
    statement_id,
    line_number,
):
    user = request.user

    if not user.is_authenticated:
        return JsonResponse(
            {
                "error":
                    "Not authenticated."
            },
            status=401,
        )

    if request.method != "PUT":
        return JsonResponse(
            {
                "error":
                    "Method not allowed."
            },
            status=405,
        )

    try:
        try:
            ObjectId(
                statement_id
            )

        except (
            InvalidId,
            TypeError,
        ):
            raise ValueError(
                "Invalid bank statement ID."
            )

        statement = (
            BankStatementService
            .get_statement(
                user=user,
                organization=(
                    user.organization
                ),
                statement_id=(
                    statement_id
                ),
            )
        )

        line = (
            BankStatementService
            .get_statement_line(
                statement=statement,
                line_number=line_number,
            )
        )

        statement = (
            BankStatementService
            .ignore_statement_line(
                user=user,
                organization=(
                    user.organization
                ),
                statement=statement,
                line=line,
            )
        )

        statement.reload()

        line = (
            BankStatementService
            .get_statement_line(
                statement=statement,
                line_number=line_number,
            )
        )

        return JsonResponse(
            {
                "message":
                    "Statement line ignored "
                    "successfully.",
                "statement_status":
                    statement.status,
                "line":
                    _bank_statement_line_response(
                        line
                    ),
            },
            status=200,
        )

    except PermissionError as exc:
        return JsonResponse(
            {"error": str(exc)},
            status=403,
        )

    except ValueError as exc:
        return JsonResponse(
            {"error": str(exc)},
            status=400,
        )

def _bank_payment_suggestion_response(
    suggestion,
):
    return {
        "id":
            str(suggestion.id),
        "suggestion_type":
            suggestion.suggestion_type,
        "statement": {
            "id":
                str(
                    suggestion.statement.id
                ),
            "statement_number":
                suggestion.statement.statement_number,
        },
        "line_number":
            suggestion.line_number,
        "amount":
            str(suggestion.amount),
        "confidence":
            str(suggestion.confidence),
        "executed_at": (
            suggestion.executed_at.isoformat()
            if suggestion.executed_at
            else None
        ),

        "payment_reference":
            suggestion.payment_reference,
        "match_reason":
            suggestion.match_reason,
        "status":
            suggestion.status,
        "invoice": (
            {
                "id":
                    str(
                        suggestion.invoice.id
                    ),
                "invoice_number":
                    suggestion.invoice.invoice_number,
            }
            if suggestion.invoice
            else None
        ),
        "vendor_bill": (
            {
                "id":
                    str(
                        suggestion.vendor_bill.id
                    ),
                "bill_number":
                    suggestion.vendor_bill.bill_number,
            }
            if suggestion.vendor_bill
            else None
        ),
        "confirmed_at": (
            suggestion.confirmed_at.isoformat()
            if suggestion.confirmed_at
            else None
        ),
        "rejected_at": (
            suggestion.rejected_at.isoformat()
            if suggestion.rejected_at
            else None
        ),
        "created_at": (
            suggestion.created_at.isoformat()
            if suggestion.created_at
            else None
        ),
    }

def confirm_bank_payment_suggestion(
    request,
    suggestion_id,
):
    user = request.user

    if not user.is_authenticated:
        return JsonResponse(
            {"error": "Not authenticated."},
            status=401,
        )

    if request.method != "PUT":
        return JsonResponse(
            {"error": "Method not allowed."},
            status=405,
        )

    try:
        try:
            ObjectId(
                suggestion_id
            )

        except (
            InvalidId,
            TypeError,
        ):
            raise ValueError(
                "Invalid payment suggestion ID."
            )

        suggestion = (
            BankPaymentSuggestion.objects(
                organization=(
                    user.organization
                ),
                id=suggestion_id,
            ).first()
        )

        if not suggestion:
            raise ValueError(
                "Payment suggestion not found."
            )

        suggestion = (
            BankPaymentSuggestionService
            .confirm_suggestion(
                user=user,
                organization=(
                    user.organization
                ),
                suggestion=suggestion,
            )
        )

        return JsonResponse(
            {
                "message":
                    "Payment suggestion confirmed.",
                "suggestion":
                    _bank_payment_suggestion_response(
                        suggestion
                    ),
            },
            status=200,
        )

    except PermissionError as exc:
        return JsonResponse(
            {"error": str(exc)},
            status=403,
        )

    except ValueError as exc:
        return JsonResponse(
            {"error": str(exc)},
            status=400,
        )


def reject_bank_payment_suggestion(
    request,
    suggestion_id,
):
    user = request.user

    if not user.is_authenticated:
        return JsonResponse(
            {"error": "Not authenticated."},
            status=401,
        )

    if request.method != "PUT":
        return JsonResponse(
            {"error": "Method not allowed."},
            status=405,
        )

    try:
        try:
            ObjectId(
                suggestion_id
            )

        except (
            InvalidId,
            TypeError,
        ):
            raise ValueError(
                "Invalid payment suggestion ID."
            )

        suggestion = (
            BankPaymentSuggestion.objects(
                organization=(
                    user.organization
                ),
                id=suggestion_id,
            ).first()
        )

        if not suggestion:
            raise ValueError(
                "Payment suggestion not found."
            )

        suggestion = (
            BankPaymentSuggestionService
            .reject_suggestion(
                user=user,
                organization=(
                    user.organization
                ),
                suggestion=suggestion,
            )
        )

        return JsonResponse(
            {
                "message":
                    "Payment suggestion rejected.",
                "suggestion":
                    _bank_payment_suggestion_response(
                        suggestion
                    ),
            },
            status=200,
        )

    except PermissionError as exc:
        return JsonResponse(
            {"error": str(exc)},
            status=403,
        )

    except ValueError as exc:
        return JsonResponse(
            {"error": str(exc)},
            status=400,
        )

def execute_bank_payment_suggestion(
    request,
    suggestion_id,
):
    user = request.user

    if not user.is_authenticated:
        return JsonResponse(
            {
                "error":
                    "Not authenticated."
            },
            status=401,
        )

    if request.method != "PUT":
        return JsonResponse(
            {
                "error":
                    "Method not allowed."
            },
            status=405,
        )

    try:
        try:
            ObjectId(
                suggestion_id
            )

        except (
            InvalidId,
            TypeError,
        ):
            raise ValueError(
                "Invalid payment suggestion ID."
            )

        suggestion = (
            BankPaymentSuggestion.objects(
                organization=(
                    user.organization
                ),
                id=suggestion_id,
            ).first()
        )

        if not suggestion:
            raise ValueError(
                "Payment suggestion not found."
            )

        if (
            suggestion.suggestion_type
            == "CUSTOMER_RECEIPT"
        ):
            result = (
                BankPaymentSuggestionService
                .execute_customer_receipt(
                    user=user,
                    organization=(
                        user.organization
                    ),
                    suggestion=suggestion,
                )
            )

        elif (
            suggestion.suggestion_type
            == "SUPPLIER_PAYMENT"
        ):
            result = (
                BankPaymentSuggestionService
                .execute_supplier_payment(
                    user=user,
                    organization=(
                        user.organization
                    ),
                    suggestion=suggestion,
                )
            )

        else:
            raise ValueError(
                "Invalid payment suggestion type."
            )

        result = (
            BankPaymentSuggestionService
            .execute_customer_receipt(
                user=user,
                organization=(
                    user.organization
                ),
                suggestion=suggestion,
            )
        )

        suggestion = (
            result["suggestion"]
        )

        payment = (
            result["payment"]
        )

        bank_transaction = (
            result["bank_transaction"]
        )

        return JsonResponse(
            {
                "message":
                    "Payment suggestion executed "
                    "successfully.",
                "suggestion":
                    _bank_payment_suggestion_response(
                        suggestion
                    ),
                "payment": {
                    "id":
                        str(payment.id),
                    "payment_number":
                        payment.payment_number,
                    "amount":
                        str(payment.amount),
                },
                "bank_transaction":
                    _bank_transaction_response(
                        bank_transaction
                    ),
            },
            status=200,
        )

    except PermissionError as exc:
        return JsonResponse(
            {
                "error":
                    str(exc)
            },
            status=403,
        )

    except ValueError as exc:
        return JsonResponse(
            {
                "error":
                    str(exc)
            },
            status=400,
        )

def finance_dashboard(
    request,
):
    user = request.user

    if not user.is_authenticated:
        return JsonResponse(
            {
                "error":
                    "Not authenticated."
            },
            status=401,
        )

    if request.method != "GET":
        return JsonResponse(
            {
                "error":
                    "Method not allowed."
            },
            status=405,
        )

    try:
        dashboard = (
            FinanceDashboardService
            .get_dashboard(
                user=user,
                organization=(
                    user.organization
                ),
            )
        )

        return JsonResponse(
            {
                "bank_accounts": {
                    "account_count":
                        dashboard[
                            "bank_accounts"
                        ][
                            "account_count"
                        ],

                    "total_balance":
                        str(
                            dashboard[
                                "bank_accounts"
                            ][
                                "total_balance"
                            ]
                        ),

                    "accounts": [
                        {
                            **account,
                            "current_balance":
                                str(
                                    account[
                                        "current_balance"
                                    ]
                                ),
                        }
                        for account
                        in dashboard[
                            "bank_accounts"
                        ][
                            "accounts"
                        ]
                    ],
                },

                "transactions": {
                    **dashboard[
                        "transactions"
                    ],

                    "total_in":
                        str(
                            dashboard[
                                "transactions"
                            ][
                                "total_in"
                            ]
                        ),

                    "total_out":
                        str(
                            dashboard[
                                "transactions"
                            ][
                                "total_out"
                            ]
                        ),

                    "net_cash_flow":
                        str(
                            dashboard[
                                "transactions"
                            ][
                                "net_cash_flow"
                            ]
                        ),
                },

                "statements":
                    dashboard[
                        "statements"
                    ],

                "payment_suggestions":
                    dashboard[
                        "payment_suggestions"
                    ],

                "receivables": {
                    "invoice_count":
                        dashboard[
                            "receivables"
                        ][
                            "invoice_count"
                        ],

                    "total_receivable":
                        str(
                            dashboard[
                                "receivables"
                            ][
                                "total_receivable"
                            ]
                        ),
                },

                "payables": {
                    "bill_count":
                        dashboard[
                            "payables"
                        ][
                            "bill_count"
                        ],

                    "total_payable":
                        str(
                            dashboard[
                                "payables"
                            ][
                                "total_payable"
                            ]
                        ),
                },
            },
            status=200,
        )

    except PermissionError as exc:
        return JsonResponse(
            {
                "error":
                    str(exc)
            },
            status=403,
        )

    except ValueError as exc:
        return JsonResponse(
            {
                "error":
                    str(exc)
            },
            status=400,
        )

def cash_flow_report(
    request,
):
    user = request.user

    if not user.is_authenticated:
        return JsonResponse(
            {
                "error":
                    "Not authenticated."
            },
            status=401,
        )

    if request.method != "GET":
        return JsonResponse(
            {
                "error":
                    "Method not allowed."
            },
            status=405,
        )

    try:
        start_date = (
            request.GET.get(
                "start_date"
            )
        )

        end_date = (
            request.GET.get(
                "end_date"
            )
        )

        bank_account_id = (
            request.GET.get(
                "bank_account_id"
            )
        )

        bank_account = None

        if bank_account_id:
            try:
                ObjectId(
                    bank_account_id
                )

            except (
                InvalidId,
                TypeError,
            ):
                raise ValueError(
                    "Invalid bank account ID."
                )

            bank_account = (
                BankAccount.objects(
                    organization=(
                        user.organization
                    ),
                    id=(
                        bank_account_id
                    ),
                ).first()
            )

            if not bank_account:
                raise ValueError(
                    "Bank account not found."
                )

        report = (
            CashFlowReportService
            .get_cash_flow_report(
                user=user,
                organization=(
                    user.organization
                ),
                start_date=(
                    start_date
                ),
                end_date=(
                    end_date
                ),
                bank_account=(
                    bank_account
                ),
            )
        )

        return JsonResponse(
            {
                "start_date":
                    report[
                        "start_date"
                    ].isoformat(),

                "end_date":
                    report[
                        "end_date"
                    ].isoformat(),

                "bank_account":
                    report[
                        "bank_account"
                    ],

                "opening_balance":
                    str(
                        report[
                            "opening_balance"
                        ]
                    ),

                "total_in":
                    str(
                        report[
                            "total_in"
                        ]
                    ),

                "total_out":
                    str(
                        report[
                            "total_out"
                        ]
                    ),

                "net_cash_flow":
                    str(
                        report[
                            "net_cash_flow"
                        ]
                    ),

                "closing_balance":
                    str(
                        report[
                            "closing_balance"
                        ]
                    ),

                "transaction_count":
                    report[
                        "transaction_count"
                    ],

                "reconciled_count":
                    report[
                        "reconciled_count"
                    ],

                "unreconciled_count":
                    report[
                        "unreconciled_count"
                    ],

                "daily_summary": [
                    {
                        "date":
                            row["date"],

                        "money_in":
                            str(
                                row[
                                    "money_in"
                                ]
                            ),

                        "money_out":
                            str(
                                row[
                                    "money_out"
                                ]
                            ),

                        "net_cash_flow":
                            str(
                                row[
                                    "net_cash_flow"
                                ]
                            ),

                        "transaction_count":
                            row[
                                "transaction_count"
                            ],
                    }
                    for row
                    in report[
                        "daily_summary"
                    ]
                ],

                "transactions": [
                    {
                        **row,

                        "transaction_date":
                            row[
                                "transaction_date"
                            ].isoformat(),

                        "amount":
                            str(
                                row[
                                    "amount"
                                ]
                            ),

                        "signed_amount":
                            str(
                                row[
                                    "signed_amount"
                                ]
                            ),
                    }
                    for row
                    in report[
                        "transactions"
                    ]
                ],
            },
            status=200,
        )

    except PermissionError as exc:
        return JsonResponse(
            {
                "error":
                    str(exc)
            },
            status=403,
        )

    except ValueError as exc:
        return JsonResponse(
            {
                "error":
                    str(exc)
            },
            status=400,
        )

def finance_audit_report(
    request,
):
    user = request.user

    if not user.is_authenticated:
        return JsonResponse(
            {
                "error":
                    "Not authenticated."
            },
            status=401,
        )

    if request.method != "GET":
        return JsonResponse(
            {
                "error":
                    "Method not allowed."
            },
            status=405,
        )

    try:
        audit = (
            FinanceAuditService
            .get_audit_report(
                user=user,
                organization=(
                    user.organization
                ),
            )
        )

        statement_exceptions = (
            audit[
                "statement_exceptions"
            ]
        )

        transaction_exceptions = (
            audit[
                "transaction_exceptions"
            ]
        )

        suggestion_exceptions = (
            audit[
                "suggestion_exceptions"
            ]
        )

        return JsonResponse(
            {
                "healthy":
                    audit["healthy"],

                "critical_exception_count":
                    audit[
                        "critical_exception_count"
                    ],

                "attention_count":
                    audit[
                        "attention_count"
                    ],

                "statement_exceptions": {
                    "unmatched_lines": [
                        {
                            **row,

                            "transaction_date": (
                                row[
                                    "transaction_date"
                                ].isoformat()
                                if row[
                                    "transaction_date"
                                ]
                                else None
                            ),

                            "debit_amount":
                                str(
                                    row[
                                        "debit_amount"
                                    ]
                                ),

                            "credit_amount":
                                str(
                                    row[
                                        "credit_amount"
                                    ]
                                ),
                        }
                        for row
                        in statement_exceptions[
                            "unmatched_lines"
                        ]
                    ],

                    "invalid_matched_lines":
                        statement_exceptions[
                            "invalid_matched_lines"
                        ],

                    "stale_unresolved_links":
                        statement_exceptions[
                            "stale_unresolved_links"
                        ],
                },

                "transaction_exceptions": {
                    "unreconciled_transactions": [
                        {
                            **row,

                            "transaction_date": (
                                row[
                                    "transaction_date"
                                ].isoformat()
                                if row[
                                    "transaction_date"
                                ]
                                else None
                            ),

                            "amount":
                                str(
                                    row[
                                        "amount"
                                    ]
                                ),
                        }
                        for row
                        in transaction_exceptions[
                            "unreconciled_transactions"
                        ]
                    ],

                    "duplicate_matches":
                        transaction_exceptions[
                            "duplicate_matches"
                        ],
                },

                "suggestion_exceptions": {
                    key: [
                        {
                            **row,

                            "amount":
                                str(
                                    row[
                                        "amount"
                                    ]
                                ),

                            "confidence":
                                str(
                                    row[
                                        "confidence"
                                    ]
                                ),

                            "executed_at": (
                                row[
                                    "executed_at"
                                ].isoformat()
                                if row[
                                    "executed_at"
                                ]
                                else None
                            ),
                        }
                        for row
                        in rows
                    ]
                    for key, rows
                    in suggestion_exceptions.items()
                },

                "invoice_exceptions":
                    audit[
                        "invoice_exceptions"
                    ],

                "vendor_bill_exceptions":
                    audit[
                        "vendor_bill_exceptions"
                    ],
            },
            status=200,
        )

    except PermissionError as exc:
        return JsonResponse(
            {
                "error":
                    str(exc)
            },
            status=403,
        )

    except ValueError as exc:
        return JsonResponse(
            {
                "error":
                    str(exc)
            },
            status=400,
        )


def _journal_entry_response(
    journal,
):
    return {
        "id":
            str(journal.id),

        "journal_number":
            journal.journal_number,

        "journal_date":
            (
                journal.journal_date.isoformat()
                if journal.journal_date
                else None
            ),

        "description":
            journal.description,

        "source_type":
            journal.source_type,

        "source_id":
            journal.source_id,

        "status":
            journal.status,

        "total_debit":
            str(
                journal.total_debit
            ),

        "total_credit":
            str(
                journal.total_credit
            ),

        "lines": [
            {
                "account": {
                    "id":
                        str(
                            line.account.id
                        ),

                    "account_code":
                        line.account
                        .account_code,

                    "account_name":
                        line.account
                        .account_name,

                    "account_type":
                        line.account
                        .account_type,
                },

                "description":
                    line.description,

                "debit":
                    str(
                        line.debit
                    ),

                "credit":
                    str(
                        line.credit
                    ),
            }
            for line
            in journal.lines
        ],

        "posted_at": (
            journal.posted_at
            .isoformat()
            if journal.posted_at
            else None
        ),

        "reversed_at": (
            journal.reversed_at
            .isoformat()
            if journal.reversed_at
            else None
        ),

        "reversal_of": (
            str(
                journal.reversal_of.id
            )
            if journal.reversal_of
            else None
        ),

        "reversed_by": (
            str(
                journal.reversed_by.id
            )
            if journal.reversed_by
            else None
        ),

        "created_at": (
            journal.created_at
            .isoformat()
            if journal.created_at
            else None
        ),

        "updated_at": (
            journal.updated_at
            .isoformat()
            if journal.updated_at
            else None
        ),
    }


def journal_entries(
    request,
):
    user = request.user

    if not user.is_authenticated:
        return JsonResponse(
            {
                "error":
                    "Not authenticated."
            },
            status=401,
        )

    organization = (
        user.organization
    )

    try:
        if request.method == "GET":

            status_filter = (
                request.GET.get(
                    "status"
                )
            )

            source_type = (
                request.GET.get(
                    "source_type"
                )
            )

            journals = (
                JournalEntryService
                .list_journals(
                    user=user,
                    organization=organization,
                    status=status_filter,
                    source_type=source_type,
                )
            )

            return JsonResponse(
                {
                    "count":
                        journals.count(),

                    "journals": [
                        _journal_entry_response(
                            journal
                        )
                        for journal
                        in journals
                    ],
                },
                status=200,
            )

        if request.method == "POST":

            try:
                body = json.loads(
                    request.body
                    or "{}"
                )

            except json.JSONDecodeError:
                raise ValueError(
                    "Invalid JSON body."
                )

            raw_lines = (
                body.get(
                    "lines",
                    []
                )
            )

            prepared_lines = []

            for raw_line in raw_lines:

                account_id = (
                    raw_line.get(
                        "account_id"
                    )
                )

                if not account_id:
                    raise ValueError(
                        "account_id is required "
                        "for each journal line."
                    )

                try:
                    ObjectId(
                        account_id
                    )

                except (
                    InvalidId,
                    TypeError,
                ):
                    raise ValueError(
                        "Invalid account ID."
                    )

                account = (
                    ChartOfAccount.objects(
                        organization=organization,
                        id=account_id,
                    )
                    .first()
                )

                if not account:
                    raise ValueError(
                        "Chart of account not found."
                    )

                prepared_lines.append(
                    {
                        "account":
                            account,

                        "description":
                            raw_line.get(
                                "description",
                                "",
                            ),

                        "debit":
                            raw_line.get(
                                "debit",
                                "0.00",
                            ),

                        "credit":
                            raw_line.get(
                                "credit",
                                "0.00",
                            ),
                    }
                )

            journal = (
                JournalEntryService
                .create_journal(
                    user=user,
                    organization=organization,
                    journal_date=(
                        body.get(
                            "journal_date"
                        )
                        or None
                    ),
                    description=(
                        body.get(
                            "description",
                            ""
                        )
                    ),
                    source_type=(
                        body.get(
                            "source_type",
                            "MANUAL"
                        )
                    ),
                    source_id=(
                        body.get(
                            "source_id",
                            ""
                        )
                    ),
                    raw_lines=(
                        prepared_lines
                    ),
                )
            )

            return JsonResponse(
                {
                    "message":
                        "Journal entry created.",

                    "journal":
                        _journal_entry_response(
                            journal
                        ),
                },
                status=201,
            )

        return JsonResponse(
            {
                "error":
                    "Method not allowed."
            },
            status=405,
        )

    except PermissionError as exc:
        return JsonResponse(
            {
                "error":
                    str(exc)
            },
            status=403,
        )

    except ValueError as exc:
        return JsonResponse(
            {
                "error":
                    str(exc)
            },
            status=400,
        )

def journal_entry_detail(
    request,
    journal_id,
):
    user = request.user

    if not user.is_authenticated:
        return JsonResponse(
            {
                "error":
                    "Not authenticated."
            },
            status=401,
        )

    organization = (
        user.organization
    )

    try:
        try:
            ObjectId(
                journal_id
            )

        except (
            InvalidId,
            TypeError,
        ):
            raise ValueError(
                "Invalid journal ID."
            )

        if request.method == "GET":

            journal = (
                JournalEntryService
                .get_journal(
                    user=user,
                    organization=organization,
                    journal_id=journal_id,
                )
            )

            return JsonResponse(
                {
                    "journal":
                        _journal_entry_response(
                            journal
                        )
                },
                status=200,
            )

        if request.method == "PUT":

            try:
                body = json.loads(
                    request.body
                    or "{}"
                )

            except json.JSONDecodeError:
                raise ValueError(
                    "Invalid JSON body."
                )

            prepared_lines = None

            if "lines" in body:

                prepared_lines = []

                for raw_line in (
                    body.get(
                        "lines",
                        []
                    )
                ):

                    account_id = (
                        raw_line.get(
                            "account_id"
                        )
                    )

                    if not account_id:
                        raise ValueError(
                            "account_id is required "
                            "for each journal line."
                        )

                    try:
                        ObjectId(
                            account_id
                        )

                    except (
                        InvalidId,
                        TypeError,
                    ):
                        raise ValueError(
                            "Invalid account ID."
                        )

                    account = (
                        ChartOfAccount.objects(
                            organization=organization,
                            id=account_id,
                        )
                        .first()
                    )

                    if not account:
                        raise ValueError(
                            "Chart of account "
                            "not found."
                        )

                    prepared_lines.append(
                        {
                            "account":
                                account,

                            "description":
                                raw_line.get(
                                    "description",
                                    "",
                                ),

                            "debit":
                                raw_line.get(
                                    "debit",
                                    "0.00",
                                ),

                            "credit":
                                raw_line.get(
                                    "credit",
                                    "0.00",
                                ),
                        }
                    )

            journal = (
                JournalEntryService
                .update_draft(
                    user=user,
                    organization=organization,
                    journal_id=journal_id,
                    journal_date=(
                        body.get(
                            "journal_date"
                        )
                        if (
                            "journal_date"
                            in body
                        )
                        else None
                    ),
                    raw_lines=(
                        prepared_lines
                    ),
                    description=(
                        body.get(
                            "description"
                        )
                        if (
                            "description"
                            in body
                        )
                        else None
                    ),
                )
            )

            return JsonResponse(
                {
                    "message":
                        "Journal entry updated.",

                    "journal":
                        _journal_entry_response(
                            journal
                        ),
                },
                status=200,
            )

        return JsonResponse(
            {
                "error":
                    "Method not allowed."
            },
            status=405,
        )

    except PermissionError as exc:
        return JsonResponse(
            {
                "error":
                    str(exc)
            },
            status=403,
        )

    except ValueError as exc:
        return JsonResponse(
            {
                "error":
                    str(exc)
            },
            status=400,
        )

def post_journal_entry(
    request,
    journal_id,
):
    user = request.user

    if not user.is_authenticated:
        return JsonResponse(
            {
                "error":
                    "Not authenticated."
            },
            status=401,
        )

    if request.method != "PUT":
        return JsonResponse(
            {
                "error":
                    "Method not allowed."
            },
            status=405,
        )

    try:
        try:
            ObjectId(
                journal_id
            )

        except (
            InvalidId,
            TypeError,
        ):
            raise ValueError(
                "Invalid journal ID."
            )

        journal = (
            JournalEntryService
            .post_journal(
                user=user,
                organization=(
                    user.organization
                ),
                journal_id=journal_id,
            )
        )

        return JsonResponse(
            {
                "message":
                    "Journal entry posted.",

                "journal":
                    _journal_entry_response(
                        journal
                    ),
            },
            status=200,
        )

    except PermissionError as exc:
        return JsonResponse(
            {
                "error":
                    str(exc)
            },
            status=403,
        )

    except ValueError as exc:
        return JsonResponse(
            {
                "error":
                    str(exc)
            },
            status=400,
        )

def reverse_journal_entry(
    request,
    journal_id,
):
    user = request.user

    if not user.is_authenticated:
        return JsonResponse(
            {
                "error":
                    "Not authenticated."
            },
            status=401,
        )

    if request.method != "PUT":
        return JsonResponse(
            {
                "error":
                    "Method not allowed."
            },
            status=405,
        )

    try:
        try:
            ObjectId(
                journal_id
            )

        except (
            InvalidId,
            TypeError,
        ):
            raise ValueError(
                "Invalid journal ID."
            )

        try:
            body = json.loads(
                request.body
                or "{}"
            )

        except json.JSONDecodeError:
            raise ValueError(
                "Invalid JSON body."
            )

        result = (
            JournalEntryService
            .reverse_journal(
                user=user,
                organization=(
                    user.organization
                ),
                journal_id=(
                    journal_id
                ),
                reversal_date=(
                    body.get(
                        "reversal_date"
                    )
                ),
                description=(
                    body.get(
                        "description",
                        ""
                    )
                ),
            )
        )

        return JsonResponse(
            {
                "message":
                    "Journal entry reversed.",

                "original":
                    _journal_entry_response(
                        result[
                            "original"
                        ]
                    ),

                "reversal":
                    _journal_entry_response(
                        result[
                            "reversal"
                        ]
                    ),
            },
            status=200,
        )

    except PermissionError as exc:
        return JsonResponse(
            {
                "error":
                    str(exc)
            },
            status=403,
        )

    except ValueError as exc:
        return JsonResponse(
            {
                "error":
                    str(exc)
            },
            status=400,
        )

def general_ledger_detail(
    request,
    account_id,
):
    user = request.user

    if not user.is_authenticated:
        return JsonResponse(
            {
                "error":
                    "Not authenticated."
            },
            status=401,
        )

    if request.method != "GET":
        return JsonResponse(
            {
                "error":
                    "Method not allowed."
            },
            status=405,
        )

    organization = (
        user.organization
    )

    try:

        try:
            ObjectId(
                account_id
            )

        except (
            InvalidId,
            TypeError,
        ):
            raise ValueError(
                "Invalid account ID."
            )

        start_date = (
            request.GET.get(
                "start_date"
            )
        )

        end_date = (
            request.GET.get(
                "end_date"
            )
        )

        ledger = (
            GeneralLedgerService
            .get_account_ledger(
                user=user,
                organization=organization,
                account_id=account_id,
                start_date=start_date,
                end_date=end_date,
            )
        )

        account = (
            ledger["account"]
        )

        return JsonResponse(
            {
                "account": {
                    "id":
                        str(
                            account.id
                        ),

                    "account_code":
                        account.account_code,

                    "account_name":
                        account.account_name,

                    "account_type":
                        account.account_type,

                    "account_subtype":
                        account.account_subtype,

                    "normal_balance":
                        account.normal_balance,

                    "system_key":
                        account.system_key,

                    "is_active":
                        account.is_active,
                },

                "period": {
                    "start_date": (
                        ledger[
                            "start_date"
                        ].isoformat()
                        if ledger[
                            "start_date"
                        ]
                        else None
                    ),

                    "end_date": (
                        ledger[
                            "end_date"
                        ].isoformat()
                        if ledger[
                            "end_date"
                        ]
                        else None
                    ),
                },

                "opening_balance":
                    str(
                        ledger[
                            "opening_balance"
                        ]
                    ),

                "total_debit":
                    str(
                        ledger[
                            "total_debit"
                        ]
                    ),

                "total_credit":
                    str(
                        ledger[
                            "total_credit"
                        ]
                    ),

                "closing_balance":
                    str(
                        ledger[
                            "closing_balance"
                        ]
                    ),

                "entry_count":
                    len(
                        ledger[
                            "entries"
                        ]
                    ),

                "entries": [
                    {
                        "journal_number":
                            entry[
                                "journal_number"
                            ],

                        "journal_date": (
                            entry[
                                "journal_date"
                            ].isoformat()
                            if entry[
                                "journal_date"
                            ]
                            else None
                        ),

                        "description":
                            entry[
                                "description"
                            ],

                        "source_type":
                            entry[
                                "source_type"
                            ],

                        "source_id":
                            entry[
                                "source_id"
                            ],

                        "debit":
                            str(
                                entry[
                                    "debit"
                                ]
                            ),

                        "credit":
                            str(
                                entry[
                                    "credit"
                                ]
                            ),

                        "running_balance":
                            str(
                                entry[
                                    "running_balance"
                                ]
                            ),
                    }
                    for entry
                    in ledger[
                        "entries"
                    ]
                ],
            },
            status=200,
        )

    except PermissionError as exc:

        return JsonResponse(
            {
                "error":
                    str(exc)
            },
            status=403,
        )

    except ValueError as exc:

        return JsonResponse(
            {
                "error":
                    str(exc)
            },
            status=400,
        )

def trial_balance_report(
    request,
):
    user = request.user

    if not user.is_authenticated:
        return JsonResponse(
            {
                "error":
                    "Not authenticated."
            },
            status=401,
        )

    if request.method != "GET":
        return JsonResponse(
            {
                "error":
                    "Method not allowed."
            },
            status=405,
        )

    organization = (
        user.organization
    )

    try:

        as_of_date = (
            request.GET.get(
                "as_of_date"
            )
        )

        include_zero_raw = (
            request.GET.get(
                "include_zero_balances",
                "true",
            )
        )

        include_zero_raw = str(
            include_zero_raw
        ).strip().lower()

        if include_zero_raw in {
            "true",
            "1",
            "yes",
            "y",
        }:
            include_zero_balances = True

        elif include_zero_raw in {
            "false",
            "0",
            "no",
            "n",
        }:
            include_zero_balances = False

        else:
            raise ValueError(
                "include_zero_balances must "
                "be true or false."
            )

        trial_balance = (
            TrialBalanceService
            .generate_trial_balance(
                user=user,
                organization=organization,
                as_of_date=as_of_date,
                include_zero_balances=(
                    include_zero_balances
                ),
            )
        )

        return JsonResponse(
            {
                "as_of_date": (
                    trial_balance[
                        "as_of_date"
                    ].isoformat()
                    if trial_balance[
                        "as_of_date"
                    ]
                    else None
                ),

                "include_zero_balances":
                    include_zero_balances,

                "account_count":
                    len(
                        trial_balance[
                            "rows"
                        ]
                    ),

                "rows": [
                    {
                        "account": {
                            "id":
                                str(
                                    row[
                                        "account"
                                    ].id
                                ),

                            "account_code":
                                row[
                                    "account_code"
                                ],

                            "account_name":
                                row[
                                    "account_name"
                                ],

                            "account_type":
                                row[
                                    "account_type"
                                ],

                            "normal_balance":
                                row[
                                    "normal_balance"
                                ],
                        },

                        "total_debit":
                            str(
                                row[
                                    "total_debit"
                                ]
                            ),

                        "total_credit":
                            str(
                                row[
                                    "total_credit"
                                ]
                            ),

                        "debit_balance":
                            str(
                                row[
                                    "debit_balance"
                                ]
                            ),

                        "credit_balance":
                            str(
                                row[
                                    "credit_balance"
                                ]
                            ),
                    }
                    for row
                    in trial_balance[
                        "rows"
                    ]
                ],

                "total_debit_balance":
                    str(
                        trial_balance[
                            "total_debit_balance"
                        ]
                    ),

                "total_credit_balance":
                    str(
                        trial_balance[
                            "total_credit_balance"
                        ]
                    ),

                "difference":
                    str(
                        trial_balance[
                            "difference"
                        ]
                    ),

                "is_balanced":
                    trial_balance[
                        "is_balanced"
                    ],
            },
            status=200,
        )

    except PermissionError as exc:

        return JsonResponse(
            {
                "error":
                    str(exc)
            },
            status=403,
        )

    except ValueError as exc:

        return JsonResponse(
            {
                "error":
                    str(exc)
            },
            status=400,
        )

def profit_and_loss_report(
    request,
):
    user = request.user

    if not user.is_authenticated:
        return JsonResponse(
            {
                "error":
                    "Not authenticated."
            },
            status=401,
        )

    if request.method != "GET":
        return JsonResponse(
            {
                "error":
                    "Method not allowed."
            },
            status=405,
        )

    organization = (
        user.organization
    )

    try:

        start_date = (
            request.GET.get(
                "start_date"
            )
        )

        end_date = (
            request.GET.get(
                "end_date"
            )
        )

        include_zero_raw = (
            request.GET.get(
                "include_zero_balances",
                "false",
            )
        )

        include_zero_raw = str(
            include_zero_raw
        ).strip().lower()

        if include_zero_raw in {
            "true",
            "1",
            "yes",
            "y",
        }:
            include_zero_balances = True

        elif include_zero_raw in {
            "false",
            "0",
            "no",
            "n",
        }:
            include_zero_balances = False

        else:
            raise ValueError(
                "include_zero_balances must "
                "be true or false."
            )

        report = (
            ProfitAndLossService
            .generate_profit_and_loss(
                user=user,
                organization=organization,
                start_date=start_date,
                end_date=end_date,
                include_zero_balances=(
                    include_zero_balances
                ),
            )
        )

        def serialize_row(
            row,
        ):
            return {
                "account": {
                    "id":
                        str(
                            row[
                                "account"
                            ].id
                        ),

                    "account_code":
                        row[
                            "account_code"
                        ],

                    "account_name":
                        row[
                            "account_name"
                        ],

                    "system_key":
                        row[
                            "system_key"
                        ],
                },

                "debit":
                    str(
                        row[
                            "debit"
                        ]
                    ),

                "credit":
                    str(
                        row[
                            "credit"
                        ]
                    ),

                "balance":
                    str(
                        row[
                            "balance"
                        ]
                    ),
            }

        return JsonResponse(
            {
                "period": {
                    "start_date": (
                        report[
                            "start_date"
                        ].isoformat()
                        if report[
                            "start_date"
                        ]
                        else None
                    ),

                    "end_date": (
                        report[
                            "end_date"
                        ].isoformat()
                        if report[
                            "end_date"
                        ]
                        else None
                    ),
                },

                "include_zero_balances":
                    include_zero_balances,

                "revenue": {
                    "rows": [
                        serialize_row(
                            row
                        )
                        for row
                        in report[
                            "revenue_rows"
                        ]
                    ],

                    "total":
                        str(
                            report[
                                "total_revenue"
                            ]
                        ),
                },

                "cost_of_goods_sold": {
                    "rows": [
                        serialize_row(
                            row
                        )
                        for row
                        in report[
                            "cogs_rows"
                        ]
                    ],

                    "total":
                        str(
                            report[
                                "total_cogs"
                            ]
                        ),
                },

                "gross_profit":
                    str(
                        report[
                            "gross_profit"
                        ]
                    ),

                "operating_expenses": {
                    "rows": [
                        serialize_row(
                            row
                        )
                        for row
                        in report[
                            "operating_expense_rows"
                        ]
                    ],

                    "total":
                        str(
                            report[
                                "total_operating_expenses"
                            ]
                        ),
                },

                "net_profit":
                    str(
                        report[
                            "net_profit"
                        ]
                    ),

                "is_profit":
                    report[
                        "is_profit"
                    ],
            },
            status=200,
        )

    except PermissionError as exc:

        return JsonResponse(
            {
                "error":
                    str(exc)
            },
            status=403,
        )

    except ValueError as exc:

        return JsonResponse(
            {
                "error":
                    str(exc)
            },
            status=400,
        )

def balance_sheet_report(
    request,
):
    user = request.user

    if not user.is_authenticated:
        return JsonResponse(
            {
                "error":
                    "Not authenticated."
            },
            status=401,
        )

    if request.method != "GET":
        return JsonResponse(
            {
                "error":
                    "Method not allowed."
            },
            status=405,
        )

    organization = (
        user.organization
    )

    try:

        as_of_date = (
            request.GET.get(
                "as_of_date"
            )
        )

        include_zero_raw = (
            request.GET.get(
                "include_zero_balances",
                "false",
            )
        )

        include_zero_raw = str(
            include_zero_raw
        ).strip().lower()

        if include_zero_raw in {
            "true",
            "1",
            "yes",
            "y",
        }:
            include_zero_balances = True

        elif include_zero_raw in {
            "false",
            "0",
            "no",
            "n",
        }:
            include_zero_balances = False

        else:
            raise ValueError(
                "include_zero_balances must "
                "be true or false."
            )

        report = (
            BalanceSheetService
            .generate_balance_sheet(
                user=user,
                organization=organization,
                as_of_date=as_of_date,
                include_zero_balances=(
                    include_zero_balances
                ),
            )
        )

        def serialize_row(
            row,
        ):
            return {
                "account": {
                    "id":
                        str(
                            row[
                                "account"
                            ].id
                        ),

                    "account_code":
                        row[
                            "account_code"
                        ],

                    "account_name":
                        row[
                            "account_name"
                        ],

                    "system_key":
                        row[
                            "system_key"
                        ],
                },

                "debit":
                    str(
                        row[
                            "debit"
                        ]
                    ),

                "credit":
                    str(
                        row[
                            "credit"
                        ]
                    ),

                "balance":
                    str(
                        row[
                            "balance"
                        ]
                    ),
            }

        return JsonResponse(
            {
                "as_of_date": (
                    report[
                        "as_of_date"
                    ].isoformat()
                    if report[
                        "as_of_date"
                    ]
                    else None
                ),

                "include_zero_balances":
                    include_zero_balances,

                "assets": {
                    "rows": [
                        serialize_row(
                            row
                        )
                        for row
                        in report[
                            "asset_rows"
                        ]
                    ],

                    "total":
                        str(
                            report[
                                "total_assets"
                            ]
                        ),
                },

                "liabilities": {
                    "rows": [
                        serialize_row(
                            row
                        )
                        for row
                        in report[
                            "liability_rows"
                        ]
                    ],

                    "total":
                        str(
                            report[
                                "total_liabilities"
                            ]
                        ),
                },

                "equity": {
                    "rows": [
                        serialize_row(
                            row
                        )
                        for row
                        in report[
                            "equity_rows"
                        ]
                    ],

                    "equity_account_balance":
                        str(
                            report[
                                "equity_account_balance"
                            ]
                        ),

                    "current_earnings":
                        str(
                            report[
                                "current_earnings"
                            ]
                        ),

                    "total":
                        str(
                            report[
                                "total_equity"
                            ]
                        ),
                },

                "total_liabilities_and_equity":
                    str(
                        report[
                            "total_liabilities_and_equity"
                        ]
                    ),

                "difference":
                    str(
                        report[
                            "difference"
                        ]
                    ),

                "is_balanced":
                    report[
                        "is_balanced"
                    ],
            },
            status=200,
        )

    except PermissionError as exc:

        return JsonResponse(
            {
                "error":
                    str(exc)
            },
            status=403,
        )

    except ValueError as exc:

        return JsonResponse(
            {
                "error":
                    str(exc)
            },
            status=400,
        )

def accounting_dashboard(
    request,
):
    user = request.user

    if not user.is_authenticated:
        return JsonResponse(
            {
                "error":
                    "Not authenticated."
            },
            status=401,
        )

    if request.method != "GET":
        return JsonResponse(
            {
                "error":
                    "Method not allowed."
            },
            status=405,
        )

    try:

        as_of_date = (
            request.GET.get(
                "as_of_date"
            )
        )

        dashboard = (
            FinanceDashboardService
            .get_accounting_dashboard(
                user=user,
                organization=(
                    user.organization
                ),
                as_of_date=as_of_date,
            )
        )

        def decimal_dict(
            data,
        ):
            return {
                key: (
                    str(value)
                    if isinstance(
                        value,
                        Decimal,
                    )
                    else value
                )
                for key, value
                in data.items()
            }

        return JsonResponse(
            {
                "as_of_date": (
                    dashboard[
                        "as_of_date"
                    ].isoformat()
                    if dashboard[
                        "as_of_date"
                    ]
                    else None
                ),

                "liquidity":
                    decimal_dict(
                        dashboard[
                            "liquidity"
                        ]
                    ),

                "working_capital":
                    decimal_dict(
                        dashboard[
                            "working_capital"
                        ]
                    ),

                "profitability":
                    decimal_dict(
                        dashboard[
                            "profitability"
                        ]
                    ),

                "balance_sheet":
                    decimal_dict(
                        dashboard[
                            "balance_sheet"
                        ]
                    ),

                "trial_balance":
                    decimal_dict(
                        dashboard[
                            "trial_balance"
                        ]
                    ),

                "accounting_health":
                    dashboard[
                        "accounting_health"
                    ],
            },
            status=200,
        )

    except PermissionError as exc:

        return JsonResponse(
            {
                "error":
                    str(exc)
            },
            status=403,
        )

    except ValueError as exc:

        return JsonResponse(
            {
                "error":
                    str(exc)
            },
            status=400,
        )

def document_access_logs(
    request,
):
    user = request.user

    if not user.is_authenticated:
        return JsonResponse(
            {
                "error":
                    "Not authenticated."
            },
            status=401,
        )

    if request.method != "GET":
        return JsonResponse(
            {
                "error":
                    "Method not allowed."
            },
            status=405,
        )

    organization = (
        user.organization
    )

    document_type = (
        request.GET.get(
            "document_type"
        )
    )

    action = (
        request.GET.get(
            "action"
        )
    )

    document_number = (
        request.GET.get(
            "document_number"
        )
    )

    user_id = (
        request.GET.get(
            "user_id"
        )
    )

    limit = (
        request.GET.get(
            "limit",
            100,
        )
    )

    if user_id:
        try:
            ObjectId(
                user_id
            )

        except (
            InvalidId,
            TypeError,
        ):
            return JsonResponse(
                {
                    "error":
                        "Invalid user ID."
                },
                status=400,
            )

    try:
        logs = (
            DocumentAccessLogService
            .list_logs(
                user=user,
                organization=organization,
                document_type=(
                    document_type
                ),
                action=action,
                document_number=(
                    document_number
                ),
                user_id=user_id,
                limit=limit,
            )
        )

    except PermissionError as exc:
        return JsonResponse(
            {
                "error":
                    str(exc)
            },
            status=403,
        )

    except ValueError as exc:
        return JsonResponse(
            {
                "error":
                    str(exc)
            },
            status=400,
        )

    data = []

    for log in logs:
        data.append(
            {
                "id":
                    str(log.id),

                "user": {
                    "id":
                        str(log.user.id),

                    "email":
                        log.user.email,
                },

                "document_type":
                    log.document_type,

                "document_id":
                    log.document_id,

                "document_number":
                    log.document_number,

                "action":
                    log.action,

                "created_at": (
                    log.created_at
                    .isoformat()
                    if log.created_at
                    else None
                ),
            }
        )

    return JsonResponse(
        {
            "count":
                len(data),

            "document_access_logs":
                data,
        },
        status=200,
    )

def document_access_log_detail(
    request,
    log_id,
):
    user = request.user

    # ==================================================
    # AUTHENTICATION
    # ==================================================

    if not user.is_authenticated:
        return JsonResponse(
            {
                "error":
                    "Not authenticated."
            },
            status=401,
        )

    # ==================================================
    # METHOD PROTECTION
    # ==================================================

    if request.method != "GET":
        return JsonResponse(
            {
                "error":
                    "Method not allowed."
            },
            status=405,
        )

    # ==================================================
    # OBJECT ID VALIDATION
    # ==================================================

    try:
        ObjectId(
            log_id
        )

    except (
        InvalidId,
        TypeError,
    ):
        return JsonResponse(
            {
                "error":
                    "Invalid document access "
                    "log ID."
            },
            status=400,
        )

    organization = (
        user.organization
    )

    # ==================================================
    # LOG LOOKUP
    # ==================================================

    try:
        log = (
            DocumentAccessLogService
            .get_log_by_id(
                user=user,
                organization=organization,
                log_id=log_id,
            )
        )

    except PermissionError as exc:
        return JsonResponse(
            {
                "error":
                    str(exc)
            },
            status=403,
        )

    except ValueError as exc:
        return JsonResponse(
            {
                "error":
                    str(exc)
            },
            status=400,
        )

    # ==================================================
    # NOT FOUND
    # ==================================================

    if not log:
        return JsonResponse(
            {
                "error":
                    "Document access log "
                    "not found."
            },
            status=404,
        )

    # ==================================================
    # RESPONSE
    # ==================================================

    return JsonResponse(
        {
            "id":
                str(log.id),

            "user": {
                "id":
                    str(log.user.id),

                "email":
                    log.user.email,
            },

            "document_type":
                log.document_type,

            "document_id":
                log.document_id,

            "document_number":
                log.document_number,

            "action":
                log.action,

            "created_at": (
                log.created_at.isoformat()
                if log.created_at
                else None
            ),
        },
        status=200,
    )

def document_access_log_summary(
    request,
):
    user = request.user

    # ==================================================
    # AUTHENTICATION
    # ==================================================

    if not user.is_authenticated:
        return JsonResponse(
            {
                "error":
                    "Not authenticated."
            },
            status=401,
        )

    # ==================================================
    # METHOD
    # ==================================================

    if request.method != "GET":
        return JsonResponse(
            {
                "error":
                    "Method not allowed."
            },
            status=405,
        )

    organization = (
        user.organization
    )

    recent_limit = (
        request.GET.get(
            "recent_limit",
            10,
        )
    )

    # ==================================================
    # SUMMARY
    # ==================================================

    try:
        summary = (
            DocumentAccessLogService
            .get_summary(
                user=user,
                organization=organization,
                recent_limit=recent_limit,
            )
        )

    except PermissionError as exc:
        return JsonResponse(
            {
                "error":
                    str(exc)
            },
            status=403,
        )

    except ValueError as exc:
        return JsonResponse(
            {
                "error":
                    str(exc)
            },
            status=400,
        )

    return JsonResponse(
        summary,
        status=200,
    )

def document_delivery_logs(
    request,
):
    user = request.user

    if not user.is_authenticated:
        return JsonResponse(
            {
                "error":
                    "Not authenticated."
            },
            status=401,
        )

    if request.method != "GET":
        return JsonResponse(
            {
                "error":
                    "Method not allowed."
            },
            status=405,
        )

    organization = (
        user.organization
    )

    document_type = (
        request.GET.get(
            "document_type"
        )
    )

    channel = (
        request.GET.get(
            "channel"
        )
    )

    status_filter = (
        request.GET.get(
            "status"
        )
    )

    recipient = (
        request.GET.get(
            "recipient"
        )
    )

    document_number = (
        request.GET.get(
            "document_number"
        )
    )

    limit = (
        request.GET.get(
            "limit",
            100,
        )
    )
    subject = (
        request.GET.get(
            "subject"
        )
    )

    recipient_overridden = (
        request.GET.get(
            "recipient_overridden"
        )
    )

    custom_subject = (
        request.GET.get(
            "custom_subject"
        )
    )

    custom_message = (
        request.GET.get(
            "custom_message"
        )
    )
    try:

        logs = (
            DocumentDeliveryLogService
            .list_logs(
                user=user,
                organization=organization,
                document_type=document_type,
                channel=channel,
                status=status_filter,
                recipient=recipient,
                document_number=(
                    document_number
                ),
                subject=subject,
                recipient_overridden=(
                    recipient_overridden
                ),
                custom_subject=(
                    custom_subject
                ),
                custom_message=(
                    custom_message
                ),
                limit=limit,
            )
        )

    except PermissionError as exc:

        return JsonResponse(
            {
                "error":
                    str(exc)
            },
            status=403,
        )

    except ValueError as exc:

        return JsonResponse(
            {
                "error":
                    str(exc)
            },
            status=400,
        )

    data = []

    for log in logs:

        data.append(
            {
                "id":
                    str(
                        log.id
                    ),

                "user": {
                    "id": (
                        str(
                            log.user.id
                        )
                        if log.user
                        else None
                    ),

                    "email": (
                        log.user.email
                        if log.user
                        else None
                    ),
                },

                "document_type":
                    log.document_type,

                "document_id":
                    log.document_id,

                "document_number":
                    log.document_number,

                "channel":
                    log.channel,

                "recipient":
                    log.recipient,

                "subject":
                    log.subject,

                "recipient_overridden":
                    log.recipient_overridden,

                "custom_subject":
                    log.custom_subject,

                "custom_message":
                    log.custom_message,
                    
                "subject":
                    log.subject,

                "recipient_overridden":
                    log.recipient_overridden,

                "custom_subject":
                    log.custom_subject,

                "custom_message":
                    log.custom_message,

                "status":
                    log.status,

                "error_message":
                    log.error_message,

                "sent_at": (
                    log.sent_at
                    .isoformat()
                    if log.sent_at
                    else None
                ),

                "created_at": (
                    log.created_at
                    .isoformat()
                    if log.created_at
                    else None
                ),
            }
        )

    return JsonResponse(
        {
            "count":
                len(
                    data
                ),

            "document_delivery_logs":
                data,
        },
        status=200,
    )

def document_delivery_log_detail(
    request,
    delivery_log_id,
):
    user = request.user

    if not user.is_authenticated:
        return JsonResponse(
            {
                "error":
                    "Not authenticated."
            },
            status=401,
        )

    if request.method != "GET":
        return JsonResponse(
            {
                "error":
                    "Method not allowed."
            },
            status=405,
        )

    try:

        ObjectId(
            delivery_log_id
        )

    except (
        InvalidId,
        TypeError,
    ):

        return JsonResponse(
            {
                "error":
                    "Invalid delivery log ID."
            },
            status=400,
        )

    organization = (
        user.organization
    )

    try:

        log = (
            DocumentDeliveryLogService
            .get_log_by_id(
                user=user,
                organization=organization,
                delivery_log_id=(
                    delivery_log_id
                ),
            )
        )

    except PermissionError as exc:

        return JsonResponse(
            {
                "error":
                    str(exc)
            },
            status=403,
        )

    except ValueError as exc:

        return JsonResponse(
            {
                "error":
                    str(exc)
            },
            status=400,
        )

    if not log:

        return JsonResponse(
            {
                "error":
                    "Delivery log not found."
            },
            status=404,
        )

    return JsonResponse(
        {
            "id":
                str(
                    log.id
                ),

            "user": {
                "id": (
                    str(
                        log.user.id
                    )
                    if log.user
                    else None
                ),

                "email": (
                    log.user.email
                    if log.user
                    else None
                ),
            },

            "document_type":
                log.document_type,

            "document_id":
                log.document_id,

            "document_number":
                log.document_number,

            "channel":
                log.channel,

            "recipient":
                log.recipient,

            "subject":
                log.subject,

            "recipient_overridden":
                log.recipient_overridden,

            "custom_subject":
                log.custom_subject,

            "custom_message":
                log.custom_message,
                
            "status":
                log.status,

            "error_message":
                log.error_message,

            "sent_at": (
                log.sent_at.isoformat()
                if log.sent_at
                else None
            ),

            "created_at": (
                log.created_at.isoformat()
                if log.created_at
                else None
            ),

            "updated_at": (
                log.updated_at.isoformat()
                if log.updated_at
                else None
            ),
        },
        status=200,
    )

def document_delivery_retry(
    request,
    delivery_log_id,
):
    user = request.user

    # ==================================================
    # AUTHENTICATION
    # ==================================================

    if not user.is_authenticated:
        return JsonResponse(
            {
                "error":
                    "Not authenticated."
            },
            status=401,
        )

    # ==================================================
    # METHOD
    # ==================================================

    if request.method != "POST":
        return JsonResponse(
            {
                "error":
                    "Method not allowed."
            },
            status=405,
        )

    # ==================================================
    # OBJECT ID
    # ==================================================

    try:

        ObjectId(
            delivery_log_id
        )

    except (
        InvalidId,
        TypeError,
    ):

        return JsonResponse(
            {
                "error":
                    "Invalid delivery log ID."
            },
            status=400,
        )

    organization = (
        user.organization
    )

    # ==================================================
    # AUDIT PERMISSION
    # ==================================================

    try:

        if not user.has_permission(
            "accounting_audit.read"
        ):
            raise PermissionError(
                "Permission denied: "
                "accounting_audit.read"
            )

        # ==================================================
        # RETRY
        # ==================================================

        result = (
            DocumentDeliveryRetryService
            .retry(
                user=user,
                organization=organization,
                delivery_log_id=(
                    delivery_log_id
                ),
            )
        )

        if result is None:

            return JsonResponse(
                {
                    "error":
                        "Delivery log not found."
                },
                status=404,
            )

        original_delivery = (
            result[
                "original_delivery"
            ]
        )

        retry_delivery = (
            result[
                "retry_delivery"
            ]
        )

        retry_delivery.reload()

        return JsonResponse(
            {
                "message":
                    "Delivery retry completed.",

                "original_delivery": {
                    "id":
                        str(
                            original_delivery.id
                        ),

                    "status":
                        original_delivery.status,

                    "document_type":
                        original_delivery.document_type,

                    "document_number":
                        original_delivery.document_number,

                    "recipient":
                        original_delivery.recipient,
                },

                "retry_delivery": {
                    "id":
                        str(
                            retry_delivery.id
                        ),

                    "status":
                        retry_delivery.status,

                    "channel":
                        retry_delivery.channel,

                    "recipient":
                        retry_delivery.recipient,

                    "sent_at": (
                        retry_delivery.sent_at
                        .isoformat()
                        if retry_delivery.sent_at
                        else None
                    ),
                },
            },
            status=200,
        )

    except PermissionError as exc:

        return JsonResponse(
            {
                "error":
                    str(exc)
            },
            status=403,
        )

    except ValueError as exc:

        return JsonResponse(
            {
                "error":
                    str(exc)
            },
            status=400,
        )

    except Exception:

        return JsonResponse(
            {
                "error":
                    "Delivery retry failed."
            },
            status=500,
        )

def document_delivery_summary(
    request,
):
    user = request.user

    if not user.is_authenticated:
        return JsonResponse(
            {
                "error":
                    "Not authenticated."
            },
            status=401,
        )

    if request.method != "GET":
        return JsonResponse(
            {
                "error":
                    "Method not allowed."
            },
            status=405,
        )

    organization = (
        user.organization
    )

    recent_limit = (
        request.GET.get(
            "recent_limit",
            10,
        )
    )

    try:

        summary = (
            DocumentDeliveryLogService
            .get_summary(
                user=user,
                organization=organization,
                recent_limit=recent_limit,
            )
        )

        return JsonResponse(
            summary,
            status=200,
        )

    except PermissionError as exc:

        return JsonResponse(
            {
                "error":
                    str(exc)
            },
            status=403,
        )

    except ValueError as exc:

        return JsonResponse(
            {
                "error":
                    str(exc)
            },
            status=400,
        )