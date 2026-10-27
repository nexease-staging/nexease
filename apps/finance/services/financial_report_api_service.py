from datetime import date
from bson import ObjectId

from apps.finance.repositories.bank_account_repository import (
    BankAccountRepository,
)
from apps.finance.services.cash_flow_report_service import (
    CashFlowReportService,
)
from apps.finance.services.finance_audit_service import (
    FinanceAuditService,
)
from apps.finance.services.finance_dashboard_service import (
    FinanceDashboardService,
)


class FinancialReportAPIValidationError(
    ValueError
):

    def __init__(
        self,
        *,
        message=(
            "Financial report validation "
            "failed."
        ),
        details=None,
    ):
        super().__init__(message)

        self.message = message
        self.details = details or {}


class FinancialReportAPIStateError(
    ValueError
):

    def __init__(
        self,
        *,
        message,
        details=None,
    ):
        super().__init__(message)

        self.message = message
        self.details = details or {}


class FinancialReportAPIService:

    @staticmethod
    def _raise_field_error(
        field,
        message,
    ):
        raise FinancialReportAPIValidationError(
            details={
                field: [
                    message,
                ],
            },
        )

    @staticmethod
    def _normalize_optional_date(
        value,
        *,
        field,
    ):
        if value in (
            None,
            "",
        ):
            return None

        if not isinstance(
            value,
            str,
        ):
            (
                FinancialReportAPIService
                ._raise_field_error(
                    field,
                    (
                        "This field must be an "
                        "ISO-8601 date."
                    ),
                )
            )

        normalized = value.strip()

        if not normalized:
            return None

        try:
            date.fromisoformat(
                normalized
            )
        except ValueError:
            (
                FinancialReportAPIService
                ._raise_field_error(
                    field,
                    (
                        "This field must be an "
                        "ISO-8601 date."
                    ),
                )
            )

        return normalized

    @staticmethod
    def _normalize_required_date(
        value,
        *,
        field,
    ):
        normalized = (
            FinancialReportAPIService
            ._normalize_optional_date(
                value,
                field=field,
            )
        )

        if normalized is None:
            (
                FinancialReportAPIService
                ._raise_field_error(
                    field,
                    "This field is required.",
                )
            )

        return normalized

    @staticmethod
    def _normalize_optional_identifier(
        value,
        *,
        field,
    ):
        if value in (
            None,
            "",
        ):
            return None

        if (
            not isinstance(
                value,
                str,
            )
            or
            not ObjectId.is_valid(
                value.strip()
            )
        ):
            (
                FinancialReportAPIService
                ._raise_field_error(
                    field,
                    (
                        "This field must contain "
                        "a valid ObjectId."
                    ),
                )
            )

        return value.strip()

    @staticmethod
    def get_finance_dashboard(
        *,
        user,
        organization,
    ):
        try:
            return (
                FinanceDashboardService
                .get_dashboard(
                    user=user,
                    organization=organization,
                )
            )

        except PermissionError:
            raise

        except ValueError as exc:
            raise FinancialReportAPIStateError(
                message=str(exc),
                details={
                    "finance_dashboard": [
                        str(exc),
                    ],
                },
            ) from exc

    @staticmethod
    def get_accounting_dashboard(
        *,
        user,
        organization,
        as_of_date=None,
    ):
        normalized_as_of_date = (
            FinancialReportAPIService
            ._normalize_optional_date(
                as_of_date,
                field="as_of_date",
            )
        )

        try:
            return (
                FinanceDashboardService
                .get_accounting_dashboard(
                    user=user,
                    organization=organization,
                    as_of_date=(
                        normalized_as_of_date
                    ),
                )
            )

        except PermissionError:
            raise

        except ValueError as exc:
            raise FinancialReportAPIStateError(
                message=str(exc),
                details={
                    "accounting_dashboard": [
                        str(exc),
                    ],
                },
            ) from exc

    @staticmethod
    def get_cash_flow(
        *,
        user,
        organization,
        start_date,
        end_date,
        bank_account_id=None,
    ):
        normalized_start_date = (
            FinancialReportAPIService
            ._normalize_required_date(
                start_date,
                field="start_date",
            )
        )

        normalized_end_date = (
            FinancialReportAPIService
            ._normalize_required_date(
                end_date,
                field="end_date",
            )
        )

        normalized_bank_account_id = (
            FinancialReportAPIService
            ._normalize_optional_identifier(
                bank_account_id,
                field="bank_account_id",
            )
        )

        bank_account = None

        if normalized_bank_account_id:
            bank_account = (
                BankAccountRepository
                .get_by_id(
                    organization=organization,
                    bank_account_id=(
                        normalized_bank_account_id
                    ),
                )
            )

            if not bank_account:
                raise LookupError(
                    "Bank account not found."
                )

        try:
            return (
                CashFlowReportService
                .get_cash_flow_report(
                    user=user,
                    organization=organization,
                    start_date=(
                        normalized_start_date
                    ),
                    end_date=(
                        normalized_end_date
                    ),
                    bank_account=bank_account,
                )
            )

        except PermissionError:
            raise

        except ValueError as exc:
            raise FinancialReportAPIStateError(
                message=str(exc),
                details={
                    "cash_flow": [
                        str(exc),
                    ],
                },
            ) from exc

    @staticmethod
    def get_finance_audit(
        *,
        user,
        organization,
    ):
        try:
            return (
                FinanceAuditService
                .get_audit_report(
                    user=user,
                    organization=organization,
                )
            )

        except PermissionError:
            raise

        except ValueError as exc:
            raise FinancialReportAPIStateError(
                message=str(exc),
                details={
                    "finance_audit": [
                        str(exc),
                    ],
                },
            ) from exc