from datetime import datetime
from decimal import Decimal

from apps.authorization.services import (
    AuthorizationService,
)

from apps.finance.models import (
    ChartOfAccount,
    JournalEntry,
)


class BalanceSheetService:

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
    def generate_balance_sheet(
        *,
        user,
        organization,
        as_of_date=None,
        include_zero_balances=False,
    ):
        """
        Generate Balance Sheet from
        posted journal history.

        Assets:
            debit - credit

        Liabilities:
            credit - debit

        Equity:
            credit - debit

        Current earnings:
            revenue - expenses
        """

        BalanceSheetService._check_permission(
            user,
            "accounting_reports.read",
        )

        BalanceSheetService._check_organization(
            user,
            organization,
        )

        as_of_date = (
            BalanceSheetService
            ._parse_as_of_date(
                as_of_date
            )
        )

        # ==================================================
        # ALL ACCOUNTS
        # ==================================================

        accounts = list(
            ChartOfAccount.objects(
                organization=organization,
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
        # JOURNALS
        # ==================================================

        query = {
            "organization":
                organization,

            "status__in": [
                "POSTED",
                "REVERSED",
            ],
        }

        if as_of_date:
            query[
                "journal_date__lte"
            ] = as_of_date

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

        asset_rows = []

        liability_rows = []

        equity_rows = []

        total_assets = (
            Decimal("0.00")
        )

        total_liabilities = (
            Decimal("0.00")
        )

        total_equity_accounts = (
            Decimal("0.00")
        )

        total_revenue = (
            Decimal("0.00")
        )

        total_expenses = (
            Decimal("0.00")
        )

        # ==================================================
        # CLASSIFY BALANCES
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

            # ----------------------------------------------
            # ASSETS
            # ----------------------------------------------

            if (
                account.account_type
                == "ASSET"
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
                    include_zero_balances
                    or
                    balance
                    != Decimal("0.00")
                ):
                    asset_rows.append(
                        row
                    )

                total_assets += (
                    balance
                )

            # ----------------------------------------------
            # LIABILITIES
            # ----------------------------------------------

            elif (
                account.account_type
                == "LIABILITY"
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
                    liability_rows.append(
                        row
                    )

                total_liabilities += (
                    balance
                )

            # ----------------------------------------------
            # EQUITY
            # ----------------------------------------------

            elif (
                account.account_type
                == "EQUITY"
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
                    equity_rows.append(
                        row
                    )

                total_equity_accounts += (
                    balance
                )

            # ----------------------------------------------
            # REVENUE
            # ----------------------------------------------

            elif (
                account.account_type
                == "REVENUE"
            ):

                total_revenue += (
                    credit
                    - debit
                )

            # ----------------------------------------------
            # EXPENSE
            # ----------------------------------------------

            elif (
                account.account_type
                == "EXPENSE"
            ):

                total_expenses += (
                    debit
                    - credit
                )

        # ==================================================
        # CURRENT EARNINGS
        # ==================================================

        current_earnings = (
            total_revenue
            - total_expenses
        )

        # ==================================================
        # TOTAL EQUITY
        # ==================================================

        total_equity = (
            total_equity_accounts
            + current_earnings
        )

        # ==================================================
        # LIABILITIES + EQUITY
        # ==================================================

        total_liabilities_and_equity = (
            total_liabilities
            + total_equity
        )

        difference = (
            total_assets
            - total_liabilities_and_equity
        )

        is_balanced = (
            difference
            == Decimal("0.00")
        )

        return {
            "as_of_date":
                as_of_date,

            "asset_rows":
                asset_rows,

            "liability_rows":
                liability_rows,

            "equity_rows":
                equity_rows,

            "total_assets":
                total_assets,

            "total_liabilities":
                total_liabilities,

            "equity_account_balance":
                total_equity_accounts,

            "total_revenue":
                total_revenue,

            "total_expenses":
                total_expenses,

            "current_earnings":
                current_earnings,

            "total_equity":
                total_equity,

            "total_liabilities_and_equity":
                total_liabilities_and_equity,

            "difference":
                difference,

            "is_balanced":
                is_balanced,
        }