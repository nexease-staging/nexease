from datetime import datetime
from decimal import Decimal

from apps.authorization.services import (
    AuthorizationService,
)

from apps.finance.models import (
    ChartOfAccount,
    JournalEntry,
)


class TrialBalanceService:

    @staticmethod
    def _check_permission(
        user,
        permission_code,
    ):
        if not user:
            raise ValueError(
                "User is required."
            )

        if not user.is_active:
            raise ValueError(
                "User is inactive."
            )

        if not AuthorizationService.has_permission(
            user,
            permission_code,
        ):
            raise PermissionError(
                f"Permission denied: "
                f"{permission_code}"
            )

    @staticmethod
    def _check_organization(
        user,
        organization,
    ):
        if not organization:
            raise ValueError(
                "Organization is required."
            )

        if not user.organization:
            raise ValueError(
                "User has no organization."
            )

        if (
            user.organization.id
            != organization.id
        ):
            raise PermissionError(
                "User does not belong "
                "to this organization."
            )

    @staticmethod
    def _parse_as_of_date(
        value,
    ):
        if value is None:
            return None

        if isinstance(
            value,
            datetime,
        ):
            return value

        value = str(
            value
        ).strip()

        if not value:
            return None

        for date_format in (
            "%Y-%m-%d",
            "%Y-%m-%dT%H:%M:%S",
        ):
            try:
                return datetime.strptime(
                    value,
                    date_format,
                )

            except ValueError:
                pass

        raise ValueError(
            "Invalid as_of_date. "
            "Use YYYY-MM-DD or "
            "YYYY-MM-DDTHH:MM:SS."
        )

    @staticmethod
    def generate_trial_balance(
        *,
        user,
        organization,
        as_of_date=None,
        include_zero_balances=True,
    ):
        """
        Generate an organization-wide
        trial balance from posted journals.
        """

        TrialBalanceService._check_permission(
            user,
            "trial_balance.read",
        )

        TrialBalanceService._check_organization(
            user,
            organization,
        )

        as_of_date = (
            TrialBalanceService
            ._parse_as_of_date(
                as_of_date
            )
        )

        # ==================================================
        # CHART OF ACCOUNTS
        # ==================================================

        accounts = list(
            ChartOfAccount.objects(
                organization=organization,
            ).order_by(
                "account_code"
            )
        )

        # ==================================================
        # JOURNAL QUERY
        # ==================================================

        journal_query = {
            "organization":
                organization,

            "status__in": [
                "POSTED",
                "REVERSED",
            ],
        }

        if as_of_date:
            journal_query[
                "journal_date__lte"
            ] = as_of_date

        journals = list(
            JournalEntry.objects(
                **journal_query
            ).order_by(
                "journal_date",
                "created_at",
            )
        )

        # ==================================================
        # RAW ACCOUNT TOTALS
        # ==================================================

        account_totals = {
            str(account.id): {
                "account":
                    account,

                "total_debit":
                    Decimal("0.00"),

                "total_credit":
                    Decimal("0.00"),
            }
            for account
            in accounts
        }

        for journal in journals:

            for line in journal.lines:

                if not line.account:
                    continue

                account_id = str(
                    line.account.id
                )

                if (
                    account_id
                    not in account_totals
                ):
                    continue

                account_totals[
                    account_id
                ][
                    "total_debit"
                ] += (
                    line.debit
                )

                account_totals[
                    account_id
                ][
                    "total_credit"
                ] += (
                    line.credit
                )

        # ==================================================
        # BUILD TRIAL BALANCE ROWS
        # ==================================================

        rows = []

        total_debit_balance = (
            Decimal("0.00")
        )

        total_credit_balance = (
            Decimal("0.00")
        )

        for account in accounts:

            totals = (
                account_totals[
                    str(account.id)
                ]
            )

            debit_total = (
                totals[
                    "total_debit"
                ]
            )

            credit_total = (
                totals[
                    "total_credit"
                ]
            )

            net = (
                debit_total
                - credit_total
            )

            debit_balance = (
                Decimal("0.00")
            )

            credit_balance = (
                Decimal("0.00")
            )

            if net > 0:

                debit_balance = (
                    net
                )

            elif net < 0:

                credit_balance = (
                    abs(net)
                )

            if (
                not include_zero_balances
                and
                debit_balance
                == Decimal("0.00")
                and
                credit_balance
                == Decimal("0.00")
            ):
                continue

            total_debit_balance += (
                debit_balance
            )

            total_credit_balance += (
                credit_balance
            )

            rows.append(
                {
                    "account":
                        account,

                    "account_code":
                        account.account_code,

                    "account_name":
                        account.account_name,

                    "account_type":
                        account.account_type,

                    "normal_balance":
                        account.normal_balance,

                    "total_debit":
                        debit_total,

                    "total_credit":
                        credit_total,

                    "debit_balance":
                        debit_balance,

                    "credit_balance":
                        credit_balance,
                }
            )

        difference = (
            total_debit_balance
            - total_credit_balance
        )

        is_balanced = (
            difference
            == Decimal("0.00")
        )

        return {
            "as_of_date":
                as_of_date,

            "rows":
                rows,

            "total_debit_balance":
                total_debit_balance,

            "total_credit_balance":
                total_credit_balance,

            "difference":
                difference,

            "is_balanced":
                is_balanced,
        }