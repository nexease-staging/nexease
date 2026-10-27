from decimal import Decimal

from apps.finance.models import (
    BankAccount,
    BankPaymentSuggestion,
    BankStatement,
    BankTransaction,
)

from apps.sales.models import (
    Invoice,
)

from apps.purchasing.models import (
    VendorBill,
)

from apps.sales.services.invoice_service import (
    InvoiceService,
)

from apps.purchasing.services.vendor_debit_note_service import (
    VendorDebitNoteService,
)

from apps.authorization.services import (
    AuthorizationService,
)

from apps.finance.models import (
    ChartOfAccount,
)

from apps.finance.services.balance_sheet_service import (
    BalanceSheetService,
)

from apps.finance.services.profit_and_loss_service import (
    ProfitAndLossService,
)

from apps.finance.services.trial_balance_service import (
    TrialBalanceService,
)

class FinanceDashboardService:

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
    def get_bank_account_summary(
        *,
        organization,
    ):
        accounts = list(
            BankAccount.objects(
                organization=organization,
                is_active=True,
            )
        )

        total_balance = sum(
            (
                account.current_balance
                for account in accounts
            ),
            Decimal("0"),
        )

        return {
            "account_count":
                len(accounts),

            "total_balance":
                total_balance,

            "accounts": [
                {
                    "id":
                        str(account.id),

                    "account_name":
                        account.account_name,

                    "account_type":
                        account.account_type,

                    "current_balance":
                        account.current_balance,

                    "currency":
                        account.currency,
                }
                for account
                in accounts
            ],
        }

    @staticmethod
    def get_transaction_summary(
        *,
        organization,
    ):
        transactions = list(
            BankTransaction.objects(
                organization=organization
            )
        )

        inflow_types = {
            "MONEY_IN",
            "TRANSFER_IN",
            "INTEREST",
            "OTHER_IN",
        }

        outflow_types = {
            "MONEY_OUT",
            "TRANSFER_OUT",
            "BANK_CHARGE",
            "OTHER_OUT",
        }

        total_in = sum(
            (
                transaction.amount
                for transaction
                in transactions
                if (
                    transaction.transaction_type
                    in inflow_types
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
                    in outflow_types
                )
            ),
            Decimal("0"),
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

        return {
            "transaction_count":
                len(transactions),

            "total_in":
                total_in,

            "total_out":
                total_out,

            "net_cash_flow":
                total_in
                - total_out,

            "reconciled_count":
                reconciled_count,

            "unreconciled_count":
                unreconciled_count,
        }

    @staticmethod
    def get_statement_summary(
        *,
        organization,
    ):
        statements = list(
            BankStatement.objects(
                organization=organization
            )
        )

        return {
            "statement_count":
                len(statements),

            "imported":
                sum(
                    1
                    for statement
                    in statements
                    if (
                        statement.status
                        == "IMPORTED"
                    )
                ),

            "partially_reconciled":
                sum(
                    1
                    for statement
                    in statements
                    if (
                        statement.status
                        == "PARTIALLY_RECONCILED"
                    )
                ),

            "reconciled":
                sum(
                    1
                    for statement
                    in statements
                    if (
                        statement.status
                        == "RECONCILED"
                    )
                ),

            "cancelled":
                sum(
                    1
                    for statement
                    in statements
                    if (
                        statement.status
                        == "CANCELLED"
                    )
                ),
        }

    @staticmethod
    def get_suggestion_summary(
        *,
        organization,
    ):
        suggestions = list(
            BankPaymentSuggestion.objects(
                organization=organization
            )
        )

        return {
            "suggestion_count":
                len(suggestions),

            "pending":
                sum(
                    1
                    for suggestion
                    in suggestions
                    if (
                        suggestion.status
                        == "PENDING"
                    )
                ),

            "confirmed":
                sum(
                    1
                    for suggestion
                    in suggestions
                    if (
                        suggestion.status
                        == "CONFIRMED"
                    )
                ),

            "rejected":
                sum(
                    1
                    for suggestion
                    in suggestions
                    if (
                        suggestion.status
                        == "REJECTED"
                    )
                ),

            "executed":
                sum(
                    1
                    for suggestion
                    in suggestions
                    if (
                        suggestion.executed_at
                        is not None
                    )
                ),

            "customer_receipts":
                sum(
                    1
                    for suggestion
                    in suggestions
                    if (
                        suggestion.suggestion_type
                        == "CUSTOMER_RECEIPT"
                    )
                ),

            "supplier_payments":
                sum(
                    1
                    for suggestion
                    in suggestions
                    if (
                        suggestion.suggestion_type
                        == "SUPPLIER_PAYMENT"
                    )
                ),
        }

    @staticmethod
    def get_receivables_summary(
        *,
        organization,
    ):
        invoices = list(
            Invoice.objects(
                organization=organization,
                status__in=[
                    "ISSUED",
                    "PARTIALLY_PAID",
                ],
            )
        )

        total_receivable = sum(
            (
                InvoiceService
                .get_invoice_net_receivable(
                    organization=organization,
                    invoice=invoice,
                )
                for invoice
                in invoices
            ),
            Decimal("0"),
        )

        positive_invoices = [
            invoice
            for invoice in invoices
            if (
                InvoiceService
                .get_invoice_net_receivable(
                    organization=organization,
                    invoice=invoice,
                )
                > Decimal("0")
            )
        ]

        return {
            "invoice_count":
                len(positive_invoices),

            "total_receivable":
                total_receivable,
        }

    @staticmethod
    def get_payables_summary(
        *,
        organization,
    ):
        bills = list(
            VendorBill.objects(
                organization=organization,
                status__in=[
                    "POSTED",
                    "PARTIALLY_PAID",
                ],
            )
        )

        payable_values = [
            (
                bill,
                VendorDebitNoteService
                .get_vendor_bill_net_payable(
                    organization=organization,
                    vendor_bill=bill,
                ),
            )
            for bill
            in bills
        ]

        positive_bills = [
            bill
            for bill, amount
            in payable_values
            if amount > Decimal("0")
        ]

        total_payable = sum(
            (
                amount
                for bill, amount
                in payable_values
                if amount > Decimal("0")
            ),
            Decimal("0"),
        )

        return {
            "bill_count":
                len(positive_bills),

            "total_payable":
                total_payable,
        }

    @staticmethod
    def get_dashboard(
        *,
        user,
        organization,
    ):
        FinanceDashboardService._check_permission(
            user,
            "bank_accounts.read",
        )

        FinanceDashboardService._check_organization(
            user,
            organization,
        )

        bank_accounts = (
            FinanceDashboardService
            .get_bank_account_summary(
                organization=organization
            )
        )

        transactions = (
            FinanceDashboardService
            .get_transaction_summary(
                organization=organization
            )
        )

        statements = (
            FinanceDashboardService
            .get_statement_summary(
                organization=organization
            )
        )

        suggestions = (
            FinanceDashboardService
            .get_suggestion_summary(
                organization=organization
            )
        )

        receivables = (
            FinanceDashboardService
            .get_receivables_summary(
                organization=organization
            )
        )

        payables = (
            FinanceDashboardService
            .get_payables_summary(
                organization=organization
            )
        )

        return {
            "bank_accounts":
                bank_accounts,

            "transactions":
                transactions,

            "statements":
                statements,

            "payment_suggestions":
                suggestions,

            "receivables":
                receivables,

            "payables":
                payables,
        }

    @staticmethod
    def get_accounting_dashboard(
        *,
        user,
        organization,
        as_of_date=None,
    ):
        """
        Return a management accounting dashboard
        using the existing accounting reports.

        Includes:
        - Cash
        - Bank
        - Accounts Receivable
        - Accounts Payable
        - Revenue
        - COGS
        - Operating Expenses
        - Gross Profit
        - Net Profit
        - Assets
        - Liabilities
        - Equity
        - Trial Balance status
        - Balance Sheet status
        """

        if not user:
            raise ValueError(
                "User is required."
            )

        if not user.is_active:
            raise ValueError(
                "User is inactive."
            )

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

        if not AuthorizationService.has_permission(
            user,
            "accounting_reports.read",
        ):
            raise PermissionError(
                "Permission denied: "
                "accounting_reports.read"
            )

        # ==================================================
        # BALANCE SHEET
        # ==================================================

        balance_sheet = (
            BalanceSheetService
            .generate_balance_sheet(
                user=user,
                organization=organization,
                as_of_date=as_of_date,
                include_zero_balances=True,
            )
        )

        # ==================================================
        # PROFIT & LOSS
        # ==================================================

        profit_and_loss = (
            ProfitAndLossService
            .generate_profit_and_loss(
                user=user,
                organization=organization,
                start_date=None,
                end_date=as_of_date,
                include_zero_balances=True,
            )
        )

        # ==================================================
        # TRIAL BALANCE
        # ==================================================

        trial_balance = (
            TrialBalanceService
            .generate_trial_balance(
                user=user,
                organization=organization,
                as_of_date=as_of_date,
                include_zero_balances=True,
            )
        )

        # ==================================================
        # HELPER: BALANCE FROM BALANCE SHEET
        # ==================================================

        def find_balance(
            rows,
            system_key,
        ):
            row = next(
                (
                    item
                    for item in rows
                    if (
                        item[
                            "system_key"
                        ]
                        == system_key
                    )
                ),
                None,
            )

            if not row:
                return Decimal("0.00")

            return row[
                "balance"
            ]

        # ==================================================
        # KEY ASSET / LIABILITY BALANCES
        # ==================================================

        cash_balance = (
            find_balance(
                balance_sheet[
                    "asset_rows"
                ],
                "CASH",
            )
        )

        bank_balance = (
            find_balance(
                balance_sheet[
                    "asset_rows"
                ],
                "BANK",
            )
        )

        receivables = (
            find_balance(
                balance_sheet[
                    "asset_rows"
                ],
                "ACCOUNTS_RECEIVABLE",
            )
        )

        payables = (
            find_balance(
                balance_sheet[
                    "liability_rows"
                ],
                "ACCOUNTS_PAYABLE",
            )
        )

        # ==================================================
        # LIQUID FUNDS
        # ==================================================

        cash_and_bank = (
            cash_balance
            + bank_balance
        )

        # ==================================================
        # DASHBOARD
        # ==================================================

        return {
            "as_of_date":
                balance_sheet[
                    "as_of_date"
                ],

            "liquidity": {
                "cash":
                    cash_balance,

                "bank":
                    bank_balance,

                "cash_and_bank":
                    cash_and_bank,
            },

            "working_capital": {
                "accounts_receivable":
                    receivables,

                "accounts_payable":
                    payables,

                "net_receivable_position": (
                    receivables
                    - payables
                ),
            },

            "profitability": {
                "revenue":
                    profit_and_loss[
                        "total_revenue"
                    ],

                "cost_of_goods_sold":
                    profit_and_loss[
                        "total_cogs"
                    ],

                "gross_profit":
                    profit_and_loss[
                        "gross_profit"
                    ],

                "operating_expenses":
                    profit_and_loss[
                        "total_operating_expenses"
                    ],

                "net_profit":
                    profit_and_loss[
                        "net_profit"
                    ],

                "is_profit":
                    profit_and_loss[
                        "is_profit"
                    ],
            },

            "balance_sheet": {
                "assets":
                    balance_sheet[
                        "total_assets"
                    ],

                "liabilities":
                    balance_sheet[
                        "total_liabilities"
                    ],

                "equity":
                    balance_sheet[
                        "total_equity"
                    ],

                "current_earnings":
                    balance_sheet[
                        "current_earnings"
                    ],

                "difference":
                    balance_sheet[
                        "difference"
                    ],

                "is_balanced":
                    balance_sheet[
                        "is_balanced"
                    ],
            },

            "trial_balance": {
                "debit":
                    trial_balance[
                        "total_debit_balance"
                    ],

                "credit":
                    trial_balance[
                        "total_credit_balance"
                    ],

                "difference":
                    trial_balance[
                        "difference"
                    ],

                "is_balanced":
                    trial_balance[
                        "is_balanced"
                    ],
            },

            "accounting_health": {
                "trial_balance_ok":
                    trial_balance[
                        "is_balanced"
                    ],

                "balance_sheet_ok":
                    balance_sheet[
                        "is_balanced"
                    ],

                "profit_matches_equity": (
                    profit_and_loss[
                        "net_profit"
                    ]
                    ==
                    balance_sheet[
                        "current_earnings"
                    ]
                ),
            },
        }