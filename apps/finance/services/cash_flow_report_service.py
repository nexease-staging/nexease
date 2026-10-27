from datetime import datetime, time, timedelta
from decimal import Decimal

from apps.finance.models import (
    BankAccount,
    BankTransaction,
)


class CashFlowReportService:

    INFLOW_TYPES = {
        "MONEY_IN",
        "TRANSFER_IN",
        "INTEREST",
        "OTHER_IN",
    }

    OUTFLOW_TYPES = {
        "MONEY_OUT",
        "TRANSFER_OUT",
        "BANK_CHARGE",
        "OTHER_OUT",
    }

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

        if not user.has_permission(
            permission_code
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
        if not value:
            raise ValueError(
                f"{field_name} is required."
            )

        if isinstance(
            value,
            datetime,
        ):
            return value

        try:
            return datetime.strptime(
                str(value).strip(),
                "%Y-%m-%d",
            )

        except ValueError:
            raise ValueError(
                f"Invalid {field_name}. "
                "Use YYYY-MM-DD."
            )

    @staticmethod
    def _get_period_bounds(
        *,
        start_date,
        end_date,
    ):
        start_date = (
            CashFlowReportService
            ._parse_date(
                start_date,
                "start_date",
            )
        )

        end_date = (
            CashFlowReportService
            ._parse_date(
                end_date,
                "end_date",
            )
        )

        start_at = datetime.combine(
            start_date.date(),
            time.min,
        )

        end_at = datetime.combine(
            end_date.date(),
            time.max,
        )

        if end_at < start_at:
            raise ValueError(
                "end_date cannot be before "
                "start_date."
            )

        return (
            start_at,
            end_at,
        )

    @staticmethod
    def _signed_amount(
        transaction,
    ):
        if (
            transaction.transaction_type
            in CashFlowReportService
            .INFLOW_TYPES
        ):
            return transaction.amount

        if (
            transaction.transaction_type
            in CashFlowReportService
            .OUTFLOW_TYPES
        ):
            return -transaction.amount

        return Decimal("0")

    @staticmethod
    def get_opening_balance(
        *,
        organization,
        start_at,
        bank_account=None,
    ):
        accounts = list(
            BankAccount.objects(
                organization=organization,
                is_active=True,
            )
        )

        if bank_account is not None:
            accounts = [
                account
                for account in accounts
                if account.id
                == bank_account.id
            ]

        total_opening = Decimal("0")

        for account in accounts:
            latest_before = (
                BankTransaction.objects(
                    organization=organization,
                    bank_account=account,
                    transaction_date__lt=(
                        start_at
                    ),
                )
                .order_by(
                    "-transaction_date",
                    "-created_at",
                )
                .first()
            )

            if latest_before:
                total_opening += (
                    latest_before.balance_after
                )

            else:
                total_opening += Decimal(
                    str(
                        account.opening_balance
                    )
                )

        return total_opening

    @staticmethod
    def get_period_transactions(
        *,
        organization,
        start_at,
        end_at,
        bank_account=None,
    ):
        query = {
            "organization":
                organization,
            "transaction_date__gte":
                start_at,
            "transaction_date__lte":
                end_at,
        }

        if bank_account is not None:
            query[
                "bank_account"
            ] = bank_account

        return list(
            BankTransaction.objects(
                **query
            ).order_by(
                "transaction_date",
                "created_at",
            )
        )

    @staticmethod
    def _build_daily_summary(
        *,
        transactions,
    ):
        daily = {}

        for transaction in transactions:
            date_key = (
                transaction
                .transaction_date
                .date()
                .isoformat()
            )

            if date_key not in daily:
                daily[
                    date_key
                ] = {
                    "date":
                        date_key,
                    "money_in":
                        Decimal("0"),
                    "money_out":
                        Decimal("0"),
                    "net_cash_flow":
                        Decimal("0"),
                    "transaction_count":
                        0,
                }

            row = daily[
                date_key
            ]

            if (
                transaction.transaction_type
                in CashFlowReportService
                .INFLOW_TYPES
            ):
                row[
                    "money_in"
                ] += transaction.amount

            elif (
                transaction.transaction_type
                in CashFlowReportService
                .OUTFLOW_TYPES
            ):
                row[
                    "money_out"
                ] += transaction.amount

            row[
                "net_cash_flow"
            ] += (
                CashFlowReportService
                ._signed_amount(
                    transaction
                )
            )

            row[
                "transaction_count"
            ] += 1

        return [
            daily[key]
            for key
            in sorted(
                daily.keys()
            )
        ]

    @staticmethod
    def get_cash_flow_report(
        *,
        user,
        organization,
        start_date,
        end_date,
        bank_account=None,
    ):
        CashFlowReportService._check_permission(
            user,
            "bank_transactions.read",
        )

        CashFlowReportService._check_organization(
            user,
            organization,
        )

        if (
            bank_account is not None
            and
            bank_account.organization.id
            != organization.id
        ):
            raise PermissionError(
                "Bank account does not belong "
                "to this organization."
            )

        start_at, end_at = (
            CashFlowReportService
            ._get_period_bounds(
                start_date=start_date,
                end_date=end_date,
            )
        )

        opening_balance = (
            CashFlowReportService
            .get_opening_balance(
                organization=organization,
                start_at=start_at,
                bank_account=bank_account,
            )
        )

        transactions = (
            CashFlowReportService
            .get_period_transactions(
                organization=organization,
                start_at=start_at,
                end_at=end_at,
                bank_account=bank_account,
            )
        )

        total_in = sum(
            (
                transaction.amount
                for transaction
                in transactions
                if (
                    transaction.transaction_type
                    in CashFlowReportService
                    .INFLOW_TYPES
                )
            ),
            Decimal("0"),
        )

        total_out = sum(
            (
                transaction.amount
                for transaction
                in transactions
                if (
                    transaction.transaction_type
                    in CashFlowReportService
                    .OUTFLOW_TYPES
                )
            ),
            Decimal("0"),
        )

        net_cash_flow = (
            total_in
            - total_out
        )

        closing_balance = (
            opening_balance
            + net_cash_flow
        )

        reconciled_count = sum(
            1
            for transaction
            in transactions
            if (
                transaction.reconciliation_status
                == "RECONCILED"
            )
        )

        unreconciled_count = sum(
            1
            for transaction
            in transactions
            if (
                transaction.reconciliation_status
                == "UNRECONCILED"
            )
        )

        transaction_rows = [
            {
                "id":
                    str(transaction.id),

                "transaction_number":
                    transaction.transaction_number,

                "bank_account": {
                    "id":
                        str(
                            transaction
                            .bank_account
                            .id
                        ),

                    "account_name":
                        transaction
                        .bank_account
                        .account_name,
                },

                "transaction_type":
                    transaction.transaction_type,

                "transaction_date":
                    transaction.transaction_date,

                "amount":
                    transaction.amount,

                "signed_amount":
                    CashFlowReportService
                    ._signed_amount(
                        transaction
                    ),

                "reference_type":
                    transaction.reference_type,

                "reference_id":
                    transaction.reference_id,

                "reconciliation_status":
                    transaction
                    .reconciliation_status,
            }
            for transaction
            in transactions
        ]

        daily_summary = (
            CashFlowReportService
            ._build_daily_summary(
                transactions=transactions
            )
        )

        return {
            "start_date":
                start_at.date(),

            "end_date":
                end_at.date(),

            "bank_account": (
                {
                    "id":
                        str(bank_account.id),

                    "account_name":
                        bank_account.account_name,
                }
                if bank_account
                else None
            ),

            "opening_balance":
                opening_balance,

            "total_in":
                total_in,

            "total_out":
                total_out,

            "net_cash_flow":
                net_cash_flow,

            "closing_balance":
                closing_balance,

            "transaction_count":
                len(transactions),

            "reconciled_count":
                reconciled_count,

            "unreconciled_count":
                unreconciled_count,

            "daily_summary":
                daily_summary,

            "transactions":
                transaction_rows,
        }