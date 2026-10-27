from bson import (
    ObjectId,
)

from apps.finance.repositories.chart_of_account_repository import (
    ChartOfAccountRepository,
)
from apps.finance.services.general_ledger_service import (
    GeneralLedgerService,
)
from apps.finance.services.trial_balance_service import (
    TrialBalanceService,
)


class AccountingReportAPIValidationError(
    ValueError
):

    def __init__(
        self,
        *,
        message=(
            "Accounting report "
            "validation failed."
        ),
        details=None,
    ):
        super().__init__(
            message
        )

        self.message = message
        self.details = details or {}


class AccountingReportAPIStateError(
    ValueError
):

    def __init__(
        self,
        *,
        message,
        details=None,
    ):
        super().__init__(
            message
        )

        self.message = message
        self.details = details or {}


class AccountingReportAPIService:

    TRUE_VALUES = {
        "1",
        "true",
        "yes",
        "on",
    }

    FALSE_VALUES = {
        "0",
        "false",
        "no",
        "off",
    }

    @staticmethod
    def _raise_field_error(
        field,
        message,
    ):
        raise (
            AccountingReportAPIValidationError(
                details={
                    field: [
                        message,
                    ],
                },
            )
        )

    @staticmethod
    def _normalize_identifier(
        value,
        *,
        field,
    ):
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
                AccountingReportAPIService
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
                AccountingReportAPIService
                ._raise_field_error(
                    field,
                    (
                        "This field must be an "
                        "ISO-8601 date or datetime."
                    ),
                )
            )

        normalized = value.strip()

        if not normalized:
            return None

        return normalized

    @staticmethod
    def _normalize_boolean(
        value,
        *,
        field,
        default,
    ):
        if value in (
            None,
            "",
        ):
            return default

        if isinstance(
            value,
            bool,
        ):
            return value

        if not isinstance(
            value,
            str,
        ):
            (
                AccountingReportAPIService
                ._raise_field_error(
                    field,
                    (
                        "This field must be "
                        "a boolean."
                    ),
                )
            )

        normalized = (
            value.strip().lower()
        )

        if (
            normalized
            in
            AccountingReportAPIService
            .TRUE_VALUES
        ):
            return True

        if (
            normalized
            in
            AccountingReportAPIService
            .FALSE_VALUES
        ):
            return False

        (
            AccountingReportAPIService
            ._raise_field_error(
                field,
                (
                    "Use true or false for "
                    "this field."
                ),
            )
        )

    @staticmethod
    def get_general_ledger(
        *,
        user,
        organization,
        account_id,
        start_date=None,
        end_date=None,
    ):
        normalized_id = (
            AccountingReportAPIService
            ._normalize_identifier(
                account_id,
                field="account_id",
            )
        )

        account = (
            ChartOfAccountRepository
            .get_by_id(
                organization=organization,
                account_id=normalized_id,
            )
        )

        if not account:
            raise LookupError(
                "Chart of account not found."
            )

        normalized_start_date = (
            AccountingReportAPIService
            ._normalize_optional_date(
                start_date,
                field="start_date",
            )
        )

        normalized_end_date = (
            AccountingReportAPIService
            ._normalize_optional_date(
                end_date,
                field="end_date",
            )
        )

        try:
            return (
                GeneralLedgerService
                .get_account_ledger(
                    user=user,
                    organization=organization,
                    account_id=str(
                        account.id
                    ),
                    start_date=(
                        normalized_start_date
                    ),
                    end_date=(
                        normalized_end_date
                    ),
                )
            )

        except PermissionError:
            raise

        except ValueError as exc:
            raise (
                AccountingReportAPIStateError(
                    message=str(
                        exc
                    ),
                    details={
                        "general_ledger": [
                            str(
                                exc
                            ),
                        ],
                    },
                )
            ) from exc

    @staticmethod
    def get_trial_balance(
        *,
        user,
        organization,
        as_of_date=None,
        include_zero_balances=None,
    ):
        normalized_as_of_date = (
            AccountingReportAPIService
            ._normalize_optional_date(
                as_of_date,
                field="as_of_date",
            )
        )

        include_zero = (
            AccountingReportAPIService
            ._normalize_boolean(
                include_zero_balances,
                field=(
                    "include_zero_balances"
                ),
                default=True,
            )
        )

        try:
            return (
                TrialBalanceService
                .generate_trial_balance(
                    user=user,
                    organization=organization,
                    as_of_date=(
                        normalized_as_of_date
                    ),
                    include_zero_balances=(
                        include_zero
                    ),
                )
            )

        except PermissionError:
            raise

        except ValueError as exc:
            raise (
                AccountingReportAPIStateError(
                    message=str(
                        exc
                    ),
                    details={
                        "trial_balance": [
                            str(
                                exc
                            ),
                        ],
                    },
                )
            ) from exc