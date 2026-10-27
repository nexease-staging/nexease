from apps.authorization.services import (
    AuthorizationService,
)
from apps.core.api.decorators import (
    api_login_required,
    api_rate_limit,
)
from apps.core.services.api_response_service import (
    APIResponseService,
)
from apps.finance.api.v1.serializers import (
    AccountingDashboardAPISerializer,
    CashFlowReportAPISerializer,
    FinanceAuditAPISerializer,
    FinanceDashboardAPISerializer,
    GeneralLedgerAPISerializer,
    TrialBalanceAPISerializer,
)
from apps.finance.services.financial_report_api_service import (
    FinancialReportAPIService,
    FinancialReportAPIStateError,
    FinancialReportAPIValidationError,
)
from apps.finance.services.accounting_report_api_service import (
    AccountingReportAPIService,
    AccountingReportAPIStateError,
    AccountingReportAPIValidationError,
)


@api_login_required
@api_rate_limit(
    scope="general_ledger.read",
    limit=120,
    window_seconds=60,
)
def general_ledger_api(
    request,
    account_id,
):
    if request.method != "GET":
        return (
            APIResponseService
            .method_not_allowed(
                message=(
                    "Use GET to retrieve the "
                    "general ledger."
                ),
                request=request,
            )
        )

    if not (
        AuthorizationService
        .has_permission(
            request.api_user,
            "general_ledger.read",
        )
    ):
        return (
            APIResponseService
            .forbidden(
                message="Permission denied.",
                request=request,
            )
        )

    try:
        result = (
            AccountingReportAPIService
            .get_general_ledger(
                user=request.api_user,
                organization=(
                    request.api_organization
                ),
                account_id=account_id,
                start_date=(
                    request.GET.get(
                        "start_date"
                    )
                ),
                end_date=(
                    request.GET.get(
                        "end_date"
                    )
                ),
            )
        )

    except (
        AccountingReportAPIValidationError
    ) as exc:
        return (
            APIResponseService
            .validation_error(
                message=exc.message,
                details=exc.details,
                request=request,
            )
        )

    except LookupError:
        return (
            APIResponseService
            .not_found(
                message=(
                    "Chart of account not found."
                ),
                request=request,
            )
        )

    except (
        AccountingReportAPIStateError
    ) as exc:
        return (
            APIResponseService
            .unprocessable_entity(
                message=exc.message,
                details=exc.details,
                request=request,
            )
        )

    except PermissionError:
        return (
            APIResponseService
            .forbidden(
                message="Permission denied.",
                request=request,
            )
        )

    return (
        APIResponseService
        .success(
            data={
                "general_ledger": (
                    GeneralLedgerAPISerializer
                    .serialize(
                        result
                    )
                ),
            },
            request=request,
        )
    )


@api_login_required
@api_rate_limit(
    scope="trial_balance.read",
    limit=120,
    window_seconds=60,
)
def trial_balance_api(
    request,
):
    if request.method != "GET":
        return (
            APIResponseService
            .method_not_allowed(
                message=(
                    "Use GET to generate the "
                    "trial balance."
                ),
                request=request,
            )
        )

    if not (
        AuthorizationService
        .has_permission(
            request.api_user,
            "trial_balance.read",
        )
    ):
        return (
            APIResponseService
            .forbidden(
                message="Permission denied.",
                request=request,
            )
        )

    try:
        result = (
            AccountingReportAPIService
            .get_trial_balance(
                user=request.api_user,
                organization=(
                    request.api_organization
                ),
                as_of_date=(
                    request.GET.get(
                        "as_of_date"
                    )
                ),
                include_zero_balances=(
                    request.GET.get(
                        "include_zero_balances"
                    )
                ),
            )
        )

    except (
        AccountingReportAPIValidationError
    ) as exc:
        return (
            APIResponseService
            .validation_error(
                message=exc.message,
                details=exc.details,
                request=request,
            )
        )

    except (
        AccountingReportAPIStateError
    ) as exc:
        return (
            APIResponseService
            .unprocessable_entity(
                message=exc.message,
                details=exc.details,
                request=request,
            )
        )

    except PermissionError:
        return (
            APIResponseService
            .forbidden(
                message="Permission denied.",
                request=request,
            )
        )

    return (
        APIResponseService
        .success(
            data={
                "trial_balance": (
                    TrialBalanceAPISerializer
                    .serialize(
                        result
                    )
                ),
            },
            request=request,
        )
    )

@api_login_required
@api_rate_limit(
    scope="bank_accounts.read",
    limit=120,
    window_seconds=60,
)
def finance_dashboard_api(
    request,
):
    if request.method != "GET":
        return (
            APIResponseService
            .method_not_allowed(
                message=(
                    "Use GET to retrieve the "
                    "finance dashboard."
                ),
                request=request,
            )
        )

    if not (
        AuthorizationService
        .has_permission(
            request.api_user,
            "bank_accounts.read",
        )
    ):
        return (
            APIResponseService
            .forbidden(
                message="Permission denied.",
                request=request,
            )
        )

    try:
        result = (
            FinancialReportAPIService
            .get_finance_dashboard(
                user=request.api_user,
                organization=(
                    request.api_organization
                ),
            )
        )

    except FinancialReportAPIStateError as exc:
        return (
            APIResponseService
            .unprocessable_entity(
                message=exc.message,
                details=exc.details,
                request=request,
            )
        )

    except PermissionError:
        return (
            APIResponseService
            .forbidden(
                message="Permission denied.",
                request=request,
            )
        )

    return (
        APIResponseService
        .success(
            data={
                "finance_dashboard": (
                    FinanceDashboardAPISerializer
                    .serialize(
                        result
                    )
                ),
            },
            request=request,
        )
    )


@api_login_required
@api_rate_limit(
    scope="accounting_reports.read",
    limit=120,
    window_seconds=60,
)
def accounting_dashboard_api(
    request,
):
    if request.method != "GET":
        return (
            APIResponseService
            .method_not_allowed(
                message=(
                    "Use GET to retrieve the "
                    "accounting dashboard."
                ),
                request=request,
            )
        )

    if not (
        AuthorizationService
        .has_permission(
            request.api_user,
            "accounting_reports.read",
        )
    ):
        return (
            APIResponseService
            .forbidden(
                message="Permission denied.",
                request=request,
            )
        )

    try:
        result = (
            FinancialReportAPIService
            .get_accounting_dashboard(
                user=request.api_user,
                organization=(
                    request.api_organization
                ),
                as_of_date=(
                    request.GET.get(
                        "as_of_date"
                    )
                ),
            )
        )

    except FinancialReportAPIValidationError as exc:
        return (
            APIResponseService
            .validation_error(
                message=exc.message,
                details=exc.details,
                request=request,
            )
        )

    except FinancialReportAPIStateError as exc:
        return (
            APIResponseService
            .unprocessable_entity(
                message=exc.message,
                details=exc.details,
                request=request,
            )
        )

    except PermissionError:
        return (
            APIResponseService
            .forbidden(
                message="Permission denied.",
                request=request,
            )
        )

    return (
        APIResponseService
        .success(
            data={
                "accounting_dashboard": (
                    AccountingDashboardAPISerializer
                    .serialize(
                        result
                    )
                ),
            },
            request=request,
        )
    )


@api_login_required
@api_rate_limit(
    scope="bank_transactions.read",
    limit=120,
    window_seconds=60,
)
def cash_flow_report_api(
    request,
):
    if request.method != "GET":
        return (
            APIResponseService
            .method_not_allowed(
                message=(
                    "Use GET to retrieve the "
                    "cash-flow report."
                ),
                request=request,
            )
        )

    if not (
        AuthorizationService
        .has_permission(
            request.api_user,
            "bank_transactions.read",
        )
    ):
        return (
            APIResponseService
            .forbidden(
                message="Permission denied.",
                request=request,
            )
        )

    try:
        result = (
            FinancialReportAPIService
            .get_cash_flow(
                user=request.api_user,
                organization=(
                    request.api_organization
                ),
                start_date=(
                    request.GET.get(
                        "start_date"
                    )
                ),
                end_date=(
                    request.GET.get(
                        "end_date"
                    )
                ),
                bank_account_id=(
                    request.GET.get(
                        "bank_account_id"
                    )
                ),
            )
        )

    except FinancialReportAPIValidationError as exc:
        return (
            APIResponseService
            .validation_error(
                message=exc.message,
                details=exc.details,
                request=request,
            )
        )

    except LookupError:
        return (
            APIResponseService
            .not_found(
                message="Bank account not found.",
                request=request,
            )
        )

    except FinancialReportAPIStateError as exc:
        return (
            APIResponseService
            .unprocessable_entity(
                message=exc.message,
                details=exc.details,
                request=request,
            )
        )

    except PermissionError:
        return (
            APIResponseService
            .forbidden(
                message="Permission denied.",
                request=request,
            )
        )

    return (
        APIResponseService
        .success(
            data={
                "cash_flow": (
                    CashFlowReportAPISerializer
                    .serialize(
                        result
                    )
                ),
            },
            request=request,
        )
    )


@api_login_required
@api_rate_limit(
    scope="bank_transactions.read",
    limit=120,
    window_seconds=60,
)
def finance_audit_api(
    request,
):
    if request.method != "GET":
        return (
            APIResponseService
            .method_not_allowed(
                message=(
                    "Use GET to retrieve the "
                    "finance audit report."
                ),
                request=request,
            )
        )

    if not (
        AuthorizationService
        .has_permission(
            request.api_user,
            "bank_transactions.read",
        )
    ):
        return (
            APIResponseService
            .forbidden(
                message="Permission denied.",
                request=request,
            )
        )

    try:
        result = (
            FinancialReportAPIService
            .get_finance_audit(
                user=request.api_user,
                organization=(
                    request.api_organization
                ),
            )
        )

    except FinancialReportAPIStateError as exc:
        return (
            APIResponseService
            .unprocessable_entity(
                message=exc.message,
                details=exc.details,
                request=request,
            )
        )

    except PermissionError:
        return (
            APIResponseService
            .forbidden(
                message="Permission denied.",
                request=request,
            )
        )

    return (
        APIResponseService
        .success(
            data={
                "finance_audit": (
                    FinanceAuditAPISerializer
                    .serialize(
                        result
                    )
                ),
            },
            request=request,
        )
    )