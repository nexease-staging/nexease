from decimal import Decimal

from apps.finance.models import (
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


class FinanceAuditService:

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

    # ==================================================
    # STATEMENT LINE EXCEPTIONS
    # ==================================================

    @staticmethod
    def get_statement_exceptions(
        *,
        organization,
    ):
        unmatched_lines = []

        invalid_matched_lines = []

        stale_unresolved_links = []

        statements = (
            BankStatement.objects(
                organization=organization,
                status__ne="CANCELLED",
            )
        )

        for statement in statements:

            for line in statement.lines:

                if (
                    line.match_status
                    == "UNMATCHED"
                ):
                    unmatched_lines.append(
                        {
                            "statement_id":
                                str(
                                    statement.id
                                ),
                            "statement_number":
                                statement.statement_number,
                            "line_number":
                                line.line_number,
                            "transaction_date":
                                line.transaction_date,
                            "description":
                                line.description,
                            "external_reference":
                                line.external_reference,
                            "debit_amount":
                                line.debit_amount,
                            "credit_amount":
                                line.credit_amount,
                        }
                    )

                if (
                    line.match_status
                    in {
                        "UNMATCHED",
                        "IGNORED",
                    }
                    and
                    (
                        line.matched_transaction
                        is not None
                        or
                        line.matched_at
                        is not None
                    )
                ):
                    stale_unresolved_links.append(
                        {
                            "statement_number":
                                statement.statement_number,
                            "line_number":
                                line.line_number,
                            "match_status":
                                line.match_status,
                        }
                    )

                if (
                    line.match_status
                    == "MATCHED"
                ):
                    valid = True
                    reason = ""

                    transaction = (
                        line.matched_transaction
                    )

                    if not transaction:
                        valid = False
                        reason = (
                            "Matched line has no "
                            "bank transaction."
                        )

                    elif (
                        transaction
                        .reconciliation_status
                        != "RECONCILED"
                    ):
                        valid = False
                        reason = (
                            "Matched transaction is "
                            "not reconciled."
                        )

                    elif (
                        transaction.bank_account.id
                        != statement.bank_account.id
                    ):
                        valid = False
                        reason = (
                            "Matched transaction belongs "
                            "to another bank account."
                        )

                    elif (
                        line.credit_amount
                        > Decimal("0")
                    ):
                        if (
                            transaction
                            .transaction_type
                            not in FinanceAuditService
                            .INFLOW_TYPES
                        ):
                            valid = False
                            reason = (
                                "Statement credit matched "
                                "to non-inflow transaction."
                            )

                        elif (
                            transaction.amount
                            != line.credit_amount
                        ):
                            valid = False
                            reason = (
                                "Statement credit amount "
                                "does not match transaction."
                            )

                    elif (
                        line.debit_amount
                        > Decimal("0")
                    ):
                        if (
                            transaction
                            .transaction_type
                            not in FinanceAuditService
                            .OUTFLOW_TYPES
                        ):
                            valid = False
                            reason = (
                                "Statement debit matched "
                                "to non-outflow transaction."
                            )

                        elif (
                            transaction.amount
                            != line.debit_amount
                        ):
                            valid = False
                            reason = (
                                "Statement debit amount "
                                "does not match transaction."
                            )

                    else:
                        valid = False
                        reason = (
                            "Matched statement line has "
                            "no debit or credit amount."
                        )

                    if not valid:
                        invalid_matched_lines.append(
                            {
                                "statement_number":
                                    statement.statement_number,
                                "line_number":
                                    line.line_number,
                                "reason":
                                    reason,
                            }
                        )

        return {
            "unmatched_lines":
                unmatched_lines,

            "invalid_matched_lines":
                invalid_matched_lines,

            "stale_unresolved_links":
                stale_unresolved_links,
        }

    # ==================================================
    # BANK TRANSACTION EXCEPTIONS
    # ==================================================

    @staticmethod
    def get_transaction_exceptions(
        *,
        organization,
    ):
        unreconciled = list(
            BankTransaction.objects(
                organization=organization,
                reconciliation_status=(
                    "UNRECONCILED"
                ),
            ).order_by(
                "transaction_date",
                "created_at",
            )
        )

        duplicate_matches = []

        matched_map = {}

        statements = (
            BankStatement.objects(
                organization=organization,
                status__ne="CANCELLED",
            )
        )

        for statement in statements:
            for line in statement.lines:

                if (
                    line.match_status
                    != "MATCHED"
                    or
                    line.matched_transaction
                    is None
                ):
                    continue

                transaction_id = str(
                    line.matched_transaction.id
                )

                matched_map.setdefault(
                    transaction_id,
                    [],
                ).append(
                    {
                        "statement_number":
                            statement.statement_number,
                        "line_number":
                            line.line_number,
                    }
                )

        for (
            transaction_id,
            matches,
        ) in matched_map.items():

            if len(matches) > 1:
                duplicate_matches.append(
                    {
                        "transaction_id":
                            transaction_id,
                        "matches":
                            matches,
                    }
                )

        return {
            "unreconciled_transactions": [
                {
                    "id":
                        str(
                            transaction.id
                        ),
                    "transaction_number":
                        transaction.transaction_number,
                    "bank_account":
                        transaction
                        .bank_account
                        .account_name,
                    "transaction_type":
                        transaction.transaction_type,
                    "transaction_date":
                        transaction.transaction_date,
                    "amount":
                        transaction.amount,
                    "reference_type":
                        transaction.reference_type,
                    "reference_id":
                        transaction.reference_id,
                }
                for transaction
                in unreconciled
            ],

            "duplicate_matches":
                duplicate_matches,
        }

    # ==================================================
    # PAYMENT SUGGESTION EXCEPTIONS
    # ==================================================

    @staticmethod
    def get_suggestion_exceptions(
        *,
        organization,
    ):
        suggestions = list(
            BankPaymentSuggestion.objects(
                organization=organization
            )
        )

        pending = [
            suggestion
            for suggestion in suggestions
            if (
                suggestion.status
                == "PENDING"
            )
        ]

        confirmed_unexecuted = [
            suggestion
            for suggestion in suggestions
            if (
                suggestion.status
                == "CONFIRMED"
                and
                suggestion.executed_at
                is None
            )
        ]

        rejected = [
            suggestion
            for suggestion in suggestions
            if (
                suggestion.status
                == "REJECTED"
            )
        ]

        invalid_execution_state = [
            suggestion
            for suggestion in suggestions
            if (
                suggestion.executed_at
                is not None
                and
                not suggestion
                .payment_reference
            )
        ]

        def serialize(
            suggestion,
        ):
            return {
                "id":
                    str(
                        suggestion.id
                    ),
                "type":
                    suggestion.suggestion_type,
                "statement_number":
                    suggestion
                    .statement
                    .statement_number,
                "line_number":
                    suggestion.line_number,
                "amount":
                    suggestion.amount,
                "confidence":
                    suggestion.confidence,
                "status":
                    suggestion.status,
                "executed_at":
                    suggestion.executed_at,
                "payment_reference":
                    suggestion.payment_reference,
            }

        return {
            "pending": [
                serialize(
                    suggestion
                )
                for suggestion
                in pending
            ],

            "confirmed_unexecuted": [
                serialize(
                    suggestion
                )
                for suggestion
                in confirmed_unexecuted
            ],

            "rejected": [
                serialize(
                    suggestion
                )
                for suggestion
                in rejected
            ],

            "invalid_execution_state": [
                serialize(
                    suggestion
                )
                for suggestion
                in invalid_execution_state
            ],
        }

    # ==================================================
    # INVOICE EXCEPTIONS
    # ==================================================

    @staticmethod
    def get_invoice_exceptions(
        *,
        organization,
    ):
        exceptions = []

        invoices = Invoice.objects(
            organization=organization
        )

        for invoice in invoices:

            expected_balance = (
                invoice.total_amount
                - invoice.amount_paid
            )

            if expected_balance < 0:
                exceptions.append(
                    {
                        "invoice_number":
                            invoice.invoice_number,
                        "reason":
                            "Invoice amount paid exceeds "
                            "total amount.",
                    }
                )

                continue

            if (
                invoice.balance_due
                != expected_balance
            ):
                exceptions.append(
                    {
                        "invoice_number":
                            invoice.invoice_number,
                        "reason":
                            "Invoice balance_due does not "
                            "match total minus amount_paid.",
                    }
                )

            net_receivable = (
                InvoiceService
                .get_invoice_net_receivable(
                    organization=organization,
                    invoice=invoice,
                )
            )

            if net_receivable < 0:
                exceptions.append(
                    {
                        "invoice_number":
                            invoice.invoice_number,
                        "reason":
                            "Invoice net receivable "
                            "is negative.",
                    }
                )

            if (
                invoice.status == "PAID"
                and
                net_receivable
                != Decimal("0")
            ):
                exceptions.append(
                    {
                        "invoice_number":
                            invoice.invoice_number,
                        "reason":
                            "Paid invoice still has "
                            "net receivable.",
                    }
                )

        return exceptions

    # ==================================================
    # VENDOR BILL EXCEPTIONS
    # ==================================================

    @staticmethod
    def get_vendor_bill_exceptions(
        *,
        organization,
    ):
        exceptions = []

        bills = VendorBill.objects(
            organization=organization
        )

        for bill in bills:

            expected_balance = (
                bill.total_amount
                - bill.amount_paid
            )

            if expected_balance < 0:
                exceptions.append(
                    {
                        "bill_number":
                            bill.bill_number,
                        "reason":
                            "Vendor bill amount paid "
                            "exceeds total amount.",
                    }
                )

                continue

            if (
                bill.balance_due
                != expected_balance
            ):
                exceptions.append(
                    {
                        "bill_number":
                            bill.bill_number,
                        "reason":
                            "Vendor bill balance_due "
                            "does not match total minus "
                            "amount_paid.",
                    }
                )

            net_payable = (
                VendorDebitNoteService
                .get_vendor_bill_net_payable(
                    organization=organization,
                    vendor_bill=bill,
                )
            )

            if net_payable < 0:
                exceptions.append(
                    {
                        "bill_number":
                            bill.bill_number,
                        "reason":
                            "Vendor bill net payable "
                            "is negative.",
                    }
                )

            if (
                bill.status == "PAID"
                and
                net_payable
                != Decimal("0")
            ):
                exceptions.append(
                    {
                        "bill_number":
                            bill.bill_number,
                        "reason":
                            "Paid vendor bill still "
                            "has net payable.",
                    }
                )

        return exceptions

    # ==================================================
    # COMPLETE AUDIT
    # ==================================================

    @staticmethod
    def get_audit_report(
        *,
        user,
        organization,
    ):
        FinanceAuditService._check_permission(
            user,
            "bank_transactions.read",
        )

        FinanceAuditService._check_organization(
            user,
            organization,
        )

        statement_exceptions = (
            FinanceAuditService
            .get_statement_exceptions(
                organization=organization
            )
        )

        transaction_exceptions = (
            FinanceAuditService
            .get_transaction_exceptions(
                organization=organization
            )
        )

        suggestion_exceptions = (
            FinanceAuditService
            .get_suggestion_exceptions(
                organization=organization
            )
        )

        invoice_exceptions = (
            FinanceAuditService
            .get_invoice_exceptions(
                organization=organization
            )
        )

        bill_exceptions = (
            FinanceAuditService
            .get_vendor_bill_exceptions(
                organization=organization
            )
        )

        critical_exception_count = (
            len(
                statement_exceptions[
                    "invalid_matched_lines"
                ]
            )
            +
            len(
                statement_exceptions[
                    "stale_unresolved_links"
                ]
            )
            +
            len(
                transaction_exceptions[
                    "duplicate_matches"
                ]
            )
            +
            len(
                suggestion_exceptions[
                    "invalid_execution_state"
                ]
            )
            +
            len(
                invoice_exceptions
            )
            +
            len(
                bill_exceptions
            )
        )

        attention_count = (
            len(
                statement_exceptions[
                    "unmatched_lines"
                ]
            )
            +
            len(
                transaction_exceptions[
                    "unreconciled_transactions"
                ]
            )
            +
            len(
                suggestion_exceptions[
                    "pending"
                ]
            )
            +
            len(
                suggestion_exceptions[
                    "confirmed_unexecuted"
                ]
            )
        )

        return {
            "healthy":
                critical_exception_count
                == 0,

            "critical_exception_count":
                critical_exception_count,

            "attention_count":
                attention_count,

            "statement_exceptions":
                statement_exceptions,

            "transaction_exceptions":
                transaction_exceptions,

            "suggestion_exceptions":
                suggestion_exceptions,

            "invoice_exceptions":
                invoice_exceptions,

            "vendor_bill_exceptions":
                bill_exceptions,
        }