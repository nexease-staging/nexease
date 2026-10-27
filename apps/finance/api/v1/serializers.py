from apps.core.services.api_serialization_service import (
    APISerializationService,
)
from apps.purchasing.api.v1.serializers import (
    SupplierPaymentAPISerializer,
    VendorBillAPISerializer,
)
from apps.sales.api.v1.serializers import (
    CustomerPaymentAPISerializer,
    InvoiceAPISerializer,
)

class ChartOfAccountAPISerializer:

    @staticmethod
    def _serialize_created_by(
        user,
    ):
        if not user:
            return None

        return {
            "id": (
                APISerializationService
                .serialize_identifier(
                    user.id
                )
            ),
            "email":
                user.email,
            "first_name":
                user.first_name,
            "last_name":
                user.last_name,
        }

    @staticmethod
    def serialize_summary(
        account,
    ):
        if not account:
            return None

        return {
            "id": (
                APISerializationService
                .serialize_identifier(
                    account.id
                )
            ),
            "account_code":
                account.account_code,
            "account_name":
                account.account_name,
            "account_type":
                account.account_type,
            "account_subtype":
                (
                    account.account_subtype
                    or
                    None
                ),
            "normal_balance":
                account.normal_balance,
            "system_key":
                (
                    account.system_key
                    or
                    None
                ),
            "is_system_account":
                bool(
                    account.is_system_account
                ),
            "is_active":
                bool(
                    account.is_active
                ),
            "allow_manual_posting":
                bool(
                    account.allow_manual_posting
                ),
        }

    @staticmethod
    def serialize_detail(
        account,
    ):
        if not account:
            return None

        summary = (
            ChartOfAccountAPISerializer
            .serialize_summary(
                account
            )
        )

        return {
            **summary,
            "description":
                (
                    account.description
                    or
                    None
                ),
            "created_by": (
                ChartOfAccountAPISerializer
                ._serialize_created_by(
                    account.created_by
                )
            ),
            "created_at": (
                APISerializationService
                .serialize_datetime(
                    account.created_at
                )
            ),
            "updated_at": (
                APISerializationService
                .serialize_datetime(
                    account.updated_at
                )
            ),
        }

    @staticmethod
    def serialize_many(
        accounts,
    ):
        return [
            (
                ChartOfAccountAPISerializer
                .serialize_summary(
                    account
                )
            )
            for account
            in accounts
        ]


class JournalEntryAPISerializer:

    @staticmethod
    def _serialize_created_by(
        user,
    ):
        if not user:
            return None

        return {
            "id": (
                APISerializationService
                .serialize_identifier(
                    user.id
                )
            ),
            "email":
                user.email,
            "first_name":
                user.first_name,
            "last_name":
                user.last_name,
        }

    @staticmethod
    def serialize_line(
        line,
    ):
        if not line:
            return None

        return {
            "account": (
                ChartOfAccountAPISerializer
                .serialize_summary(
                    line.account
                )
            ),
            "description":
                (
                    line.description
                    or
                    None
                ),
            "debit":
                str(
                    line.debit
                ),
            "credit":
                str(
                    line.credit
                ),
        }

    @staticmethod
    def serialize_summary(
        journal,
    ):
        if not journal:
            return None

        return {
            "id": (
                APISerializationService
                .serialize_identifier(
                    journal.id
                )
            ),
            "journal_number":
                journal.journal_number,
            "journal_date": (
                APISerializationService
                .serialize_datetime(
                    journal.journal_date
                )
            ),
            "description":
                (
                    journal.description
                    or
                    None
                ),
            "source_type":
                journal.source_type,
            "source_id":
                (
                    journal.source_id
                    or
                    None
                ),
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
            "line_count":
                len(
                    journal.lines
                    or
                    []
                ),
            "created_at": (
                APISerializationService
                .serialize_datetime(
                    journal.created_at
                )
            ),
            "updated_at": (
                APISerializationService
                .serialize_datetime(
                    journal.updated_at
                )
            ),
        }

    @staticmethod
    def serialize_detail(
        journal,
    ):
        if not journal:
            return None

        summary = (
            JournalEntryAPISerializer
            .serialize_summary(
                journal
            )
        )

        return {
            **summary,
            "lines": [
                (
                    JournalEntryAPISerializer
                    .serialize_line(
                        line
                    )
                )
                for line
                in (
                    journal.lines
                    or
                    []
                )
            ],
            "posted_at": (
                APISerializationService
                .serialize_datetime(
                    journal.posted_at
                )
            ),
            "reversed_at": (
                APISerializationService
                .serialize_datetime(
                    journal.reversed_at
                )
            ),
            "reversal_of_id": (
                APISerializationService
                .serialize_identifier(
                    journal.reversal_of.id
                )
                if journal.reversal_of
                else None
            ),
            "reversed_by_id": (
                APISerializationService
                .serialize_identifier(
                    journal.reversed_by.id
                )
                if journal.reversed_by
                else None
            ),
            "created_by": (
                JournalEntryAPISerializer
                ._serialize_created_by(
                    journal.created_by
                )
            ),
        }

    @staticmethod
    def serialize_many(
        journals,
    ):
        return [
            (
                JournalEntryAPISerializer
                .serialize_summary(
                    journal
                )
            )
            for journal
            in journals
        ]


class GeneralLedgerAPISerializer:

    @staticmethod
    def serialize(
        result,
    ):
        return {
            "account": (
                ChartOfAccountAPISerializer
                .serialize_detail(
                    result["account"]
                )
            ),
            "start_date": (
                APISerializationService
                .serialize_datetime(
                    result["start_date"]
                )
            ),
            "end_date": (
                APISerializationService
                .serialize_datetime(
                    result["end_date"]
                )
            ),
            "opening_balance":
                str(
                    result[
                        "opening_balance"
                    ]
                ),
            "entries": [
                {
                    "journal_number":
                        entry[
                            "journal_number"
                        ],
                    "journal_date": (
                        APISerializationService
                        .serialize_datetime(
                            entry[
                                "journal_date"
                            ]
                        )
                    ),
                    "description":
                        (
                            entry[
                                "description"
                            ]
                            or
                            None
                        ),
                    "source_type":
                        entry[
                            "source_type"
                        ],
                    "source_id":
                        (
                            entry[
                                "source_id"
                            ]
                            or
                            None
                        ),
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
                in result[
                    "entries"
                ]
            ],
            "total_debit":
                str(
                    result[
                        "total_debit"
                    ]
                ),
            "total_credit":
                str(
                    result[
                        "total_credit"
                    ]
                ),
            "closing_balance":
                str(
                    result[
                        "closing_balance"
                    ]
                ),
        }


class TrialBalanceAPISerializer:

    @staticmethod
    def serialize(
        result,
    ):
        return {
            "as_of_date": (
                APISerializationService
                .serialize_datetime(
                    result["as_of_date"]
                )
            ),
            "rows": [
                {
                    "account": (
                        ChartOfAccountAPISerializer
                        .serialize_summary(
                            row["account"]
                        )
                    ),
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
                in result[
                    "rows"
                ]
            ],
            "total_debit_balance":
                str(
                    result[
                        "total_debit_balance"
                    ]
                ),
            "total_credit_balance":
                str(
                    result[
                        "total_credit_balance"
                    ]
                ),
            "difference":
                str(
                    result[
                        "difference"
                    ]
                ),
            "is_balanced":
                bool(
                    result[
                        "is_balanced"
                    ]
                ),
        }

class BankAccountAPISerializer:

    @staticmethod
    def _serialize_created_by(
        user,
    ):
        if not user:
            return None

        return {
            "id": (
                APISerializationService
                .serialize_identifier(
                    user.id
                )
            ),
            "email":
                user.email,
            "first_name":
                user.first_name,
            "last_name":
                user.last_name,
        }

    @staticmethod
    def serialize_summary(
        bank_account,
    ):
        if not bank_account:
            return None

        return {
            "id": (
                APISerializationService
                .serialize_identifier(
                    bank_account.id
                )
            ),
            "account_name":
                bank_account.account_name,
            "account_type":
                bank_account.account_type,
            "bank_name":
                (
                    bank_account.bank_name
                    or
                    None
                ),
            "account_number":
                (
                    bank_account.account_number
                    or
                    None
                ),
            "ifsc_code":
                (
                    bank_account.ifsc_code
                    or
                    None
                ),
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
                bool(
                    bank_account.is_active
                ),
        }

    @staticmethod
    def serialize_detail(
        bank_account,
    ):
        if not bank_account:
            return None

        summary = (
            BankAccountAPISerializer
            .serialize_summary(
                bank_account
            )
        )

        return {
            **summary,
            "created_by": (
                BankAccountAPISerializer
                ._serialize_created_by(
                    bank_account.created_by
                )
            ),
            "created_at": (
                APISerializationService
                .serialize_datetime(
                    bank_account.created_at
                )
            ),
            "updated_at": (
                APISerializationService
                .serialize_datetime(
                    bank_account.updated_at
                )
            ),
        }

    @staticmethod
    def serialize_many(
        bank_accounts,
    ):
        return [
            (
                BankAccountAPISerializer
                .serialize_summary(
                    bank_account
                )
            )
            for bank_account
            in bank_accounts
        ]

class BankTransactionAPISerializer:

    @staticmethod
    def _serialize_created_by(
        user,
    ):
        if not user:
            return None

        return {
            "id": (
                APISerializationService
                .serialize_identifier(
                    user.id
                )
            ),
            "email":
                user.email,
            "first_name":
                user.first_name,
            "last_name":
                user.last_name,
        }

    @staticmethod
    def serialize_summary(
        transaction,
    ):
        if not transaction:
            return None

        return {
            "id": (
                APISerializationService
                .serialize_identifier(
                    transaction.id
                )
            ),
            "bank_account": (
                BankAccountAPISerializer
                .serialize_summary(
                    transaction.bank_account
                )
            ),
            "transaction_number":
                transaction.transaction_number,
            "transaction_type":
                transaction.transaction_type,
            "transaction_date": (
                APISerializationService
                .serialize_datetime(
                    transaction.transaction_date
                )
            ),
            "amount":
                str(
                    transaction.amount
                ),
            "balance_before":
                str(
                    transaction.balance_before
                ),
            "balance_after":
                str(
                    transaction.balance_after
                ),
            "external_reference":
                (
                    transaction.external_reference
                    or
                    None
                ),
            "description":
                (
                    transaction.description
                    or
                    None
                ),
            "reconciliation_status":
                transaction.reconciliation_status,
            "reconciled_at": (
                APISerializationService
                .serialize_datetime(
                    transaction.reconciled_at
                )
            ),
        }

    @staticmethod
    def serialize_detail(
        transaction,
    ):
        if not transaction:
            return None

        summary = (
            BankTransactionAPISerializer
            .serialize_summary(
                transaction
            )
        )

        return {
            **summary,
            "reference_type":
                (
                    transaction.reference_type
                    or
                    None
                ),
            "reference_id":
                (
                    transaction.reference_id
                    or
                    None
                ),
            "created_by": (
                BankTransactionAPISerializer
                ._serialize_created_by(
                    transaction.created_by
                )
            ),
            "created_at": (
                APISerializationService
                .serialize_datetime(
                    transaction.created_at
                )
            ),
        }

    @staticmethod
    def serialize_many(
        transactions,
    ):
        return [
            (
                BankTransactionAPISerializer
                .serialize_summary(
                    transaction
                )
            )
            for transaction
            in transactions
        ]

class BankTransferAPISerializer:

    @staticmethod
    def _serialize_created_by(
        user,
    ):
        if not user:
            return None

        return {
            "id": (
                APISerializationService
                .serialize_identifier(
                    user.id
                )
            ),
            "email":
                user.email,
            "first_name":
                user.first_name,
            "last_name":
                user.last_name,
        }

    @staticmethod
    def serialize_summary(
        transfer,
    ):
        if not transfer:
            return None

        return {
            "id": (
                APISerializationService
                .serialize_identifier(
                    transfer.id
                )
            ),
            "transfer_number":
                transfer.transfer_number,
            "source_account": (
                BankAccountAPISerializer
                .serialize_summary(
                    transfer.source_account
                )
            ),
            "destination_account": (
                BankAccountAPISerializer
                .serialize_summary(
                    transfer.destination_account
                )
            ),
            "transfer_date": (
                APISerializationService
                .serialize_datetime(
                    transfer.transfer_date
                )
            ),
            "amount":
                str(
                    transfer.amount
                ),
            "status":
                transfer.status,
            "reference":
                (
                    transfer.reference
                    or
                    None
                ),
            "created_at": (
                APISerializationService
                .serialize_datetime(
                    transfer.created_at
                )
            ),
            "updated_at": (
                APISerializationService
                .serialize_datetime(
                    transfer.updated_at
                )
            ),
        }

    @staticmethod
    def serialize_detail(
        transfer,
    ):
        if not transfer:
            return None

        summary = (
            BankTransferAPISerializer
            .serialize_summary(
                transfer
            )
        )

        return {
            **summary,
            "notes":
                (
                    transfer.notes
                    or
                    None
                ),
            "posted_at": (
                APISerializationService
                .serialize_datetime(
                    transfer.posted_at
                )
            ),
            "cancelled_at": (
                APISerializationService
                .serialize_datetime(
                    transfer.cancelled_at
                )
            ),
            "created_by": (
                BankTransferAPISerializer
                ._serialize_created_by(
                    transfer.created_by
                )
            ),
        }

    @staticmethod
    def serialize_many(
        transfers,
    ):
        return [
            (
                BankTransferAPISerializer
                .serialize_summary(
                    transfer
                )
            )
            for transfer
            in transfers
        ]

class BankStatementAPISerializer:

    @staticmethod
    def serialize_line(
        line,
    ):
        if not line:
            return None

        return {
            "line_number":
                line.line_number,
            "transaction_date": (
                APISerializationService
                .serialize_datetime(
                    line.transaction_date
                )
            ),
            "value_date": (
                APISerializationService
                .serialize_datetime(
                    line.value_date
                )
            ),
            "description":
                (
                    line.description
                    or
                    None
                ),
            "external_reference":
                (
                    line.external_reference
                    or
                    None
                ),
            "debit_amount":
                str(
                    line.debit_amount
                ),
            "credit_amount":
                str(
                    line.credit_amount
                ),
            "running_balance": (
                str(
                    line.running_balance
                )
                if (
                    line.running_balance
                    is not None
                )
                else None
            ),
            "match_status":
                line.match_status,
            "matched_transaction": (
                BankTransactionAPISerializer
                .serialize_summary(
                    line.matched_transaction
                )
                if line.matched_transaction
                else None
            ),
            "matched_at": (
                APISerializationService
                .serialize_datetime(
                    line.matched_at
                )
            ),
        }

    @staticmethod
    def serialize_summary(
        statement,
    ):
        if not statement:
            return None

        lines = (
            statement.lines
            or
            []
        )

        matched_count = sum(
            1
            for line in lines
            if line.match_status == "MATCHED"
        )

        ignored_count = sum(
            1
            for line in lines
            if line.match_status == "IGNORED"
        )

        return {
            "id": (
                APISerializationService
                .serialize_identifier(
                    statement.id
                )
            ),
            "statement_number":
                statement.statement_number,
            "bank_account": (
                BankAccountAPISerializer
                .serialize_summary(
                    statement.bank_account
                )
            ),
            "statement_start_date": (
                APISerializationService
                .serialize_datetime(
                    statement
                    .statement_start_date
                )
            ),
            "statement_end_date": (
                APISerializationService
                .serialize_datetime(
                    statement
                    .statement_end_date
                )
            ),
            "opening_balance":
                str(
                    statement.opening_balance
                ),
            "closing_balance":
                str(
                    statement.closing_balance
                ),
            "source_filename":
                (
                    statement.source_filename
                    or
                    None
                ),
            "source_type":
                statement.source_type,
            "status":
                statement.status,
            "line_count":
                len(
                    lines
                ),
            "matched_count":
                matched_count,
            "ignored_count":
                ignored_count,
            "unmatched_count": (
                len(
                    lines
                )
                -
                matched_count
                -
                ignored_count
            ),
            "created_at": (
                APISerializationService
                .serialize_datetime(
                    statement.created_at
                )
            ),
            "updated_at": (
                APISerializationService
                .serialize_datetime(
                    statement.updated_at
                )
            ),
        }

    @staticmethod
    def serialize_detail(
        statement,
    ):
        if not statement:
            return None

        summary = (
            BankStatementAPISerializer
            .serialize_summary(
                statement
            )
        )

        return {
            **summary,
            "lines": [
                (
                    BankStatementAPISerializer
                    .serialize_line(
                        line
                    )
                )
                for line
                in (
                    statement.lines
                    or
                    []
                )
            ],
            "reconciled_at": (
                APISerializationService
                .serialize_datetime(
                    statement.reconciled_at
                )
            ),
            "cancelled_at": (
                APISerializationService
                .serialize_datetime(
                    statement.cancelled_at
                )
            ),
            "created_by": (
                BankAccountAPISerializer
                ._serialize_created_by(
                    statement.created_by
                )
            ),
        }

    @staticmethod
    def serialize_many(
        statements,
    ):
        return [
            (
                BankStatementAPISerializer
                .serialize_summary(
                    statement
                )
            )
            for statement
            in statements
        ]

class BankPaymentSuggestionAPISerializer:

    @staticmethod
    def serialize_summary(
        suggestion,
    ):
        if not suggestion:
            return None

        return {
            "id": (
                APISerializationService
                .serialize_identifier(
                    suggestion.id
                )
            ),
            "statement": (
                BankStatementAPISerializer
                .serialize_summary(
                    suggestion.statement
                )
            ),
            "line_number":
                suggestion.line_number,
            "suggestion_type":
                suggestion.suggestion_type,
            "invoice": (
                InvoiceAPISerializer
                .serialize_summary(
                    suggestion.invoice
                )
                if suggestion.invoice
                else None
            ),
            "vendor_bill": (
                VendorBillAPISerializer
                .serialize_summary(
                    suggestion.vendor_bill
                )
                if suggestion.vendor_bill
                else None
            ),
            "amount":
                str(
                    suggestion.amount
                ),
            "confidence":
                str(
                    suggestion.confidence
                ),
            "match_reason":
                (
                    suggestion.match_reason
                    or
                    None
                ),
            "status":
                suggestion.status,
            "is_executed":
                bool(
                    suggestion.executed_at
                    is not None
                ),
            "payment_reference":
                (
                    suggestion.payment_reference
                    or
                    None
                ),
            "created_at": (
                APISerializationService
                .serialize_datetime(
                    suggestion.created_at
                )
            ),
            "updated_at": (
                APISerializationService
                .serialize_datetime(
                    suggestion.updated_at
                )
            ),
        }

    @staticmethod
    def serialize_detail(
        suggestion,
    ):
        if not suggestion:
            return None

        summary = (
            BankPaymentSuggestionAPISerializer
            .serialize_summary(
                suggestion
            )
        )

        return {
            **summary,
            "confirmed_at": (
                APISerializationService
                .serialize_datetime(
                    suggestion.confirmed_at
                )
            ),
            "rejected_at": (
                APISerializationService
                .serialize_datetime(
                    suggestion.rejected_at
                )
            ),
            "executed_at": (
                APISerializationService
                .serialize_datetime(
                    suggestion.executed_at
                )
            ),
            "created_by": (
                BankAccountAPISerializer
                ._serialize_created_by(
                    suggestion.created_by
                )
            ),
        }

    @staticmethod
    def serialize_execution(
        result,
    ):
        if not result:
            return None

        suggestion = (
            result["suggestion"]
        )

        payment = (
            result["payment"]
        )

        if (
            suggestion.suggestion_type
            ==
            "CUSTOMER_RECEIPT"
        ):
            serialized_payment = (
                CustomerPaymentAPISerializer
                .serialize_detail(
                    payment
                )
            )

        else:
            serialized_payment = (
                SupplierPaymentAPISerializer
                .serialize_detail(
                    payment
                )
            )

        return {
            "suggestion": (
                BankPaymentSuggestionAPISerializer
                .serialize_detail(
                    suggestion
                )
            ),
            "payment":
                serialized_payment,
            "bank_transaction": (
                BankTransactionAPISerializer
                .serialize_detail(
                    result[
                        "bank_transaction"
                    ]
                )
            ),
        }

    @staticmethod
    def serialize_many(
        suggestions,
    ):
        return [
            (
                BankPaymentSuggestionAPISerializer
                .serialize_summary(
                    suggestion
                )
            )
            for suggestion
            in suggestions
        ]

class MainDashboardAPISerializer:

    @staticmethod
    def _serialize_date(
        value,
    ):
        if value is None:
            return None

        if hasattr(
            value,
            "isoformat",
        ):
            return value.isoformat()

        return value

    @staticmethod
    def serialize(
        data,
    ):
        return {
            "period": {
                "start_date": (
                    MainDashboardAPISerializer
                    ._serialize_date(
                        data[
                            "period"
                        ][
                            "start_date"
                        ]
                    )
                ),
                "end_date": (
                    MainDashboardAPISerializer
                    ._serialize_date(
                        data[
                            "period"
                        ][
                            "end_date"
                        ]
                    )
                ),
            },

            "kpis":
                data["kpis"],

            "sales_trend":
                data[
                    "sales_trend"
                ],

            "purchase_trend":
                data[
                    "purchase_trend"
                ],

            "cash_flow":
                data[
                    "cash_flow"
                ],

            "receivable_aging":
                data[
                    "receivable_aging"
                ],

            "invoice_status":
                data[
                    "invoice_status"
                ],

            "bill_status":
                data[
                    "bill_status"
                ],

            "inventory_status":
                data[
                    "inventory_status"
                ],

            "top_customers":
                data[
                    "top_customers"
                ],

            "top_suppliers":
                data[
                    "top_suppliers"
                ],

            "alerts":
                data[
                    "alerts"
                ],

            "recent_activity": [
                {
                    **activity,

                    "activity_date": (
                        MainDashboardAPISerializer
                        ._serialize_date(
                            activity.get(
                                "activity_date"
                            )
                        )
                    ),
                }
                for activity
                in data[
                    "recent_activity"
                ]
            ],
        }

class FinanceDashboardAPISerializer:

    @staticmethod
    def _serialize_decimal(
        value,
    ):
        if value is None:
            return None

        return str(value)

    @staticmethod
    def serialize(
        data,
    ):
        return {
            "bank_accounts": {
                "account_count":
                    data[
                        "bank_accounts"
                    ][
                        "account_count"
                    ],

                "total_balance":
                    (
                        FinanceDashboardAPISerializer
                        ._serialize_decimal(
                            data[
                                "bank_accounts"
                            ][
                                "total_balance"
                            ]
                        )
                    ),

                "accounts": [
                    {
                        **account,

                        "current_balance":
                            (
                                FinanceDashboardAPISerializer
                                ._serialize_decimal(
                                    account[
                                        "current_balance"
                                    ]
                                )
                            ),
                    }
                    for account
                    in data[
                        "bank_accounts"
                    ][
                        "accounts"
                    ]
                ],
            },

            "transactions": {
                **data[
                    "transactions"
                ],

                "total_in":
                    (
                        FinanceDashboardAPISerializer
                        ._serialize_decimal(
                            data[
                                "transactions"
                            ][
                                "total_in"
                            ]
                        )
                    ),

                "total_out":
                    (
                        FinanceDashboardAPISerializer
                        ._serialize_decimal(
                            data[
                                "transactions"
                            ][
                                "total_out"
                            ]
                        )
                    ),

                "net_cash_flow":
                    (
                        FinanceDashboardAPISerializer
                        ._serialize_decimal(
                            data[
                                "transactions"
                            ][
                                "net_cash_flow"
                            ]
                        )
                    ),
            },

            "statements":
                data[
                    "statements"
                ],

            "payment_suggestions":
                data[
                    "payment_suggestions"
                ],

            "receivables": {
                **data[
                    "receivables"
                ],

                "total_receivable":
                    (
                        FinanceDashboardAPISerializer
                        ._serialize_decimal(
                            data[
                                "receivables"
                            ][
                                "total_receivable"
                            ]
                        )
                    ),
            },

            "payables": {
                **data[
                    "payables"
                ],

                "total_payable":
                    (
                        FinanceDashboardAPISerializer
                        ._serialize_decimal(
                            data[
                                "payables"
                            ][
                                "total_payable"
                            ]
                        )
                    ),
            },
        }


class AccountingDashboardAPISerializer:

    @staticmethod
    def _serialize_decimal(
        value,
    ):
        if value is None:
            return None

        return str(value)

    @staticmethod
    def serialize(
        data,
    ):
        return {
            "as_of_date":
                (
                    data[
                        "as_of_date"
                    ].isoformat()
                    if hasattr(
                        data[
                            "as_of_date"
                        ],
                        "isoformat",
                    )
                    else data[
                        "as_of_date"
                    ]
                ),

            "liquidity": {
                key:
                    (
                        AccountingDashboardAPISerializer
                        ._serialize_decimal(
                            value
                        )
                    )
                for key, value
                in data[
                    "liquidity"
                ].items()
            },

            "working_capital": {
                key:
                    (
                        AccountingDashboardAPISerializer
                        ._serialize_decimal(
                            value
                        )
                    )
                for key, value
                in data[
                    "working_capital"
                ].items()
            },

            "profitability": {
                key: (
                    value
                    if isinstance(
                        value,
                        bool,
                    )
                    else (
                        AccountingDashboardAPISerializer
                        ._serialize_decimal(
                            value
                        )
                    )
                )
                for key, value
                in data[
                    "profitability"
                ].items()
            },

            "balance_sheet": {
                key: (
                    value
                    if isinstance(
                        value,
                        bool,
                    )
                    else (
                        AccountingDashboardAPISerializer
                        ._serialize_decimal(
                            value
                        )
                    )
                )
                for key, value
                in data[
                    "balance_sheet"
                ].items()
            },

            "trial_balance": {
                key: (
                    value
                    if isinstance(
                        value,
                        bool,
                    )
                    else (
                        AccountingDashboardAPISerializer
                        ._serialize_decimal(
                            value
                        )
                    )
                )
                for key, value
                in data[
                    "trial_balance"
                ].items()
            },

            "accounting_health":
                data[
                    "accounting_health"
                ],
        }


class CashFlowReportAPISerializer:

    @staticmethod
    def _serialize_decimal(
        value,
    ):
        if value is None:
            return None

        return str(value)

    @staticmethod
    def _serialize_date(
        value,
    ):
        if value is None:
            return None

        if hasattr(
            value,
            "isoformat",
        ):
            return value.isoformat()

        return value

    @staticmethod
    def serialize(
        data,
    ):
        return {
            "start_date":
                (
                    CashFlowReportAPISerializer
                    ._serialize_date(
                        data[
                            "start_date"
                        ]
                    )
                ),

            "end_date":
                (
                    CashFlowReportAPISerializer
                    ._serialize_date(
                        data[
                            "end_date"
                        ]
                    )
                ),

            "bank_account":
                data[
                    "bank_account"
                ],

            "opening_balance":
                (
                    CashFlowReportAPISerializer
                    ._serialize_decimal(
                        data[
                            "opening_balance"
                        ]
                    )
                ),

            "total_in":
                (
                    CashFlowReportAPISerializer
                    ._serialize_decimal(
                        data[
                            "total_in"
                        ]
                    )
                ),

            "total_out":
                (
                    CashFlowReportAPISerializer
                    ._serialize_decimal(
                        data[
                            "total_out"
                        ]
                    )
                ),

            "net_cash_flow":
                (
                    CashFlowReportAPISerializer
                    ._serialize_decimal(
                        data[
                            "net_cash_flow"
                        ]
                    )
                ),

            "closing_balance":
                (
                    CashFlowReportAPISerializer
                    ._serialize_decimal(
                        data[
                            "closing_balance"
                        ]
                    )
                ),

            "transaction_count":
                data[
                    "transaction_count"
                ],

            "reconciled_count":
                data[
                    "reconciled_count"
                ],

            "unreconciled_count":
                data[
                    "unreconciled_count"
                ],

            "daily_summary": [
                {
                    **row,

                    "money_in":
                        (
                            CashFlowReportAPISerializer
                            ._serialize_decimal(
                                row[
                                    "money_in"
                                ]
                            )
                        ),

                    "money_out":
                        (
                            CashFlowReportAPISerializer
                            ._serialize_decimal(
                                row[
                                    "money_out"
                                ]
                            )
                        ),

                    "net_cash_flow":
                        (
                            CashFlowReportAPISerializer
                            ._serialize_decimal(
                                row[
                                    "net_cash_flow"
                                ]
                            )
                        ),
                }
                for row
                in data[
                    "daily_summary"
                ]
            ],

            "transactions": [
                {
                    **row,

                    "transaction_date":
                        (
                            CashFlowReportAPISerializer
                            ._serialize_date(
                                row[
                                    "transaction_date"
                                ]
                            )
                        ),

                    "amount":
                        (
                            CashFlowReportAPISerializer
                            ._serialize_decimal(
                                row[
                                    "amount"
                                ]
                            )
                        ),

                    "signed_amount":
                        (
                            CashFlowReportAPISerializer
                            ._serialize_decimal(
                                row[
                                    "signed_amount"
                                ]
                            )
                        ),
                }
                for row
                in data[
                    "transactions"
                ]
            ],
        }


class FinanceAuditAPISerializer:

    @staticmethod
    def _serialize_value(
        value,
    ):
        if hasattr(
            value,
            "isoformat",
        ):
            return value.isoformat()

        if value.__class__.__name__ == "Decimal":
            return str(value)

        return value

    @staticmethod
    def _serialize_dict(
        value,
    ):
        if isinstance(
            value,
            dict,
        ):
            return {
                key:
                    (
                        FinanceAuditAPISerializer
                        ._serialize_dict(
                            item
                        )
                    )
                for key, item
                in value.items()
            }

        if isinstance(
            value,
            list,
        ):
            return [
                (
                    FinanceAuditAPISerializer
                    ._serialize_dict(
                        item
                    )
                )
                for item
                in value
            ]

        return (
            FinanceAuditAPISerializer
            ._serialize_value(
                value
            )
        )

    @staticmethod
    def serialize(
        data,
    ):
        return (
            FinanceAuditAPISerializer
            ._serialize_dict(
                data
            )
        )

class DocumentEmailRequestAPISerializer:

    MAX_RECIPIENT_LENGTH = 320
    MAX_SUBJECT_LENGTH = 500
    MAX_MESSAGE_LENGTH = 10000

    @staticmethod
    def _normalize_optional_text(
        value,
        *,
        field_name,
        max_length,
    ):
        if value is None:
            return None

        if not isinstance(
            value,
            str,
        ):
            raise ValueError(
                f"{field_name} must be a string."
            )

        normalized = value.strip()

        if not normalized:
            return None

        if len(normalized) > max_length:
            raise ValueError(
                f"{field_name} exceeds maximum length "
                f"of {max_length} characters."
            )

        return normalized

    @staticmethod
    def deserialize(
        payload,
    ):
        if payload is None:
            payload = {}

        if not isinstance(
            payload,
            dict,
        ):
            raise ValueError(
                "Request body must be a JSON object."
            )

        allowed_fields = {
            "recipient_email",
            "subject",
            "message",
        }

        unknown_fields = (
            set(payload.keys())
            -
            allowed_fields
        )

        if unknown_fields:
            raise ValueError(
                "Unsupported field(s): "
                +
                ", ".join(
                    sorted(
                        str(field)
                        for field
                        in unknown_fields
                    )
                )
            )

        recipient_email = (
            DocumentEmailRequestAPISerializer
            ._normalize_optional_text(
                payload.get(
                    "recipient_email"
                ),
                field_name="recipient_email",
                max_length=(
                    DocumentEmailRequestAPISerializer
                    .MAX_RECIPIENT_LENGTH
                ),
            )
        )

        subject = (
            DocumentEmailRequestAPISerializer
            ._normalize_optional_text(
                payload.get(
                    "subject"
                ),
                field_name="subject",
                max_length=(
                    DocumentEmailRequestAPISerializer
                    .MAX_SUBJECT_LENGTH
                ),
            )
        )

        message = (
            DocumentEmailRequestAPISerializer
            ._normalize_optional_text(
                payload.get(
                    "message"
                ),
                field_name="message",
                max_length=(
                    DocumentEmailRequestAPISerializer
                    .MAX_MESSAGE_LENGTH
                ),
            )
        )

        if (
            recipient_email
            and
            (
                "@" not in recipient_email
                or
                recipient_email.startswith("@")
                or
                recipient_email.endswith("@")
            )
        ):
            raise ValueError(
                "Invalid recipient_email."
            )

        return {
            "recipient_email":
                recipient_email,

            "subject":
                subject,

            "message":
                message,
        }


class DocumentAccessLogAPISerializer:

    @staticmethod
    def serialize(
        log,
    ):
        if not log:
            return None

        user = getattr(
            log,
            "user",
            None,
        )

        return {
            "id": (
                APISerializationService
                .serialize_identifier(
                    log.id
                )
            ),

            "user": (
                {
                    "id": (
                        APISerializationService
                        .serialize_identifier(
                            user.id
                        )
                    ),
                    "email":
                        user.email,
                }
                if user
                else None
            ),

            "document_type":
                log.document_type,

            "document_id":
                log.document_id,

            "document_number":
                log.document_number,

            "action":
                log.action,

            "created_at": (
                APISerializationService
                .serialize_datetime(
                    log.created_at
                )
            ),
        }

    @staticmethod
    def serialize_many(
        logs,
    ):
        return [
            (
                DocumentAccessLogAPISerializer
                .serialize(
                    log
                )
            )
            for log
            in (
                logs
                or
                []
            )
        ]


class DocumentDeliveryLogAPISerializer:

    @staticmethod
    def serialize(
        log,
    ):
        if not log:
            return None

        return {
            "id": (
                APISerializationService
                .serialize_identifier(
                    log.id
                )
            ),

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

            "status":
                log.status,

            "recipient_overridden":
                bool(
                    log.recipient_overridden
                ),

            "custom_subject":
                bool(
                    log.custom_subject
                ),

            "custom_message":
                bool(
                    log.custom_message
                ),

            "error_message":
                (
                    log.error_message
                    or
                    None
                ),

            "sent_at": (
                APISerializationService
                .serialize_datetime(
                    log.sent_at
                )
            ),

            "created_at": (
                APISerializationService
                .serialize_datetime(
                    log.created_at
                )
            ),

            "updated_at": (
                APISerializationService
                .serialize_datetime(
                    log.updated_at
                )
            ),
        }

    @staticmethod
    def serialize_many(
        logs,
    ):
        return [
            (
                DocumentDeliveryLogAPISerializer
                .serialize(
                    log
                )
            )
            for log
            in (
                logs
                or
                []
            )
        ]