from datetime import datetime
from decimal import Decimal

from apps.authorization.services import (
    AuthorizationService,
)

from apps.finance.models import (
    ChartOfAccount,
    JournalEntry,
)


class ProfitAndLossService:

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
    def _parse_date(
        value,
        field_name,
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
            f"Invalid {field_name}. "
            "Use YYYY-MM-DD or "
            "YYYY-MM-DDTHH:MM:SS."
        )

    @staticmethod
    def generate_profit_and_loss(
        *,
        user,
        organization,
        start_date=None,
        end_date=None,
        include_zero_balances=False,
    ):
        """
        Generate Profit & Loss report from
        posted/reversed journal history.

        Revenue:
            credits - debits

        Expenses:
            debits - credits
        """

        ProfitAndLossService._check_permission(
            user,
            "accounting_reports.read",
        )

        ProfitAndLossService._check_organization(
            user,
            organization,
        )

        start_date = (
            ProfitAndLossService
            ._parse_date(
                start_date,
                "start_date",
            )
        )

        end_date = (
            ProfitAndLossService
            ._parse_date(
                end_date,
                "end_date",
            )
        )

        if (
            start_date
            and
            end_date
            and
            start_date > end_date
        ):
            raise ValueError(
                "Start date cannot be "
                "after end date."
            )

        # ==================================================
        # P&L ACCOUNTS
        # ==================================================

        accounts = list(
            ChartOfAccount.objects(
                organization=organization,
                account_type__in=[
                    "REVENUE",
                    "EXPENSE",
                ],
            ).order_by(
                "account_code"
            )
        )

        account_totals = {
            str(account.id): {
                "account":
                    account,

                "debit":
                    Decimal("0.00"),

                "credit":
                    Decimal("0.00"),
            }
            for account
            in accounts
        }

        # ==================================================
        # JOURNAL QUERY
        # ==================================================

        query = {
            "organization":
                organization,

            "status__in": [
                "POSTED",
                "REVERSED",
            ],
        }

        if start_date:
            query[
                "journal_date__gte"
            ] = start_date

        if end_date:
            query[
                "journal_date__lte"
            ] = end_date

        journals = list(
            JournalEntry.objects(
                **query
            ).order_by(
                "journal_date",
                "created_at",
            )
        )

        # ==================================================
        # AGGREGATE JOURNAL LINES
        # ==================================================

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
                    "debit"
                ] += line.debit

                account_totals[
                    account_id
                ][
                    "credit"
                ] += line.credit

        # ==================================================
        # REPORT SECTIONS
        # ==================================================

        revenue_rows = []

        cogs_rows = []

        operating_expense_rows = []

        total_revenue = (
            Decimal("0.00")
        )

        total_cogs = (
            Decimal("0.00")
        )

        total_operating_expenses = (
            Decimal("0.00")
        )

        # ==================================================
        # CLASSIFY ACCOUNTS
        # ==================================================

        for account in accounts:

            totals = (
                account_totals[
                    str(account.id)
                ]
            )

            debit = totals[
                "debit"
            ]

            credit = totals[
                "credit"
            ]

            if (
                account.account_type
                == "REVENUE"
            ):

                balance = (
                    credit
                    - debit
                )

                row = {
                    "account":
                        account,

                    "account_code":
                        account.account_code,

                    "account_name":
                        account.account_name,

                    "system_key":
                        account.system_key,

                    "debit":
                        debit,

                    "credit":
                        credit,

                    "balance":
                        balance,
                }

                if (
                    include_zero_balances
                    or
                    balance
                    != Decimal("0.00")
                ):
                    revenue_rows.append(
                        row
                    )

                total_revenue += (
                    balance
                )

            elif (
                account.account_type
                == "EXPENSE"
            ):

                balance = (
                    debit
                    - credit
                )

                row = {
                    "account":
                        account,

                    "account_code":
                        account.account_code,

                    "account_name":
                        account.account_name,

                    "system_key":
                        account.system_key,

                    "debit":
                        debit,

                    "credit":
                        credit,

                    "balance":
                        balance,
                }

                if (
                    account.system_key
                    == "COST_OF_GOODS_SOLD"
                ):

                    if (
                        include_zero_balances
                        or
                        balance
                        != Decimal("0.00")
                    ):
                        cogs_rows.append(
                            row
                        )

                    total_cogs += (
                        balance
                    )

                else:

                    if (
                        include_zero_balances
                        or
                        balance
                        != Decimal("0.00")
                    ):
                        operating_expense_rows.append(
                            row
                        )

                    total_operating_expenses += (
                        balance
                    )

        # ==================================================
        # PROFIT CALCULATION
        # ==================================================

        gross_profit = (
            total_revenue
            - total_cogs
        )

        net_profit = (
            gross_profit
            - total_operating_expenses
        )

        return {
            "start_date":
                start_date,

            "end_date":
                end_date,

            "revenue_rows":
                revenue_rows,

            "cogs_rows":
                cogs_rows,

            "operating_expense_rows":
                operating_expense_rows,

            "total_revenue":
                total_revenue,

            "total_cogs":
                total_cogs,

            "gross_profit":
                gross_profit,

            "total_operating_expenses":
                total_operating_expenses,

            "net_profit":
                net_profit,

            "is_profit":
                net_profit >= Decimal("0.00"),
        }