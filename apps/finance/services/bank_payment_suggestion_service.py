from datetime import timedelta, datetime
from decimal import Decimal

from apps.finance.repositories.bank_payment_suggestion_repository import (
    BankPaymentSuggestionRepository,
)
from apps.finance.repositories.bank_transaction_repository import (
    BankTransactionRepository,
)
from apps.sales.repositories.invoice_repository import (
    InvoiceRepository,
)
from apps.finance.services.bank_statement_service import (
    BankStatementService,
)
from apps.purchasing.repositories.vendor_bill_repository import (
    VendorBillRepository,
)

from apps.sales.services.invoice_service import (
    InvoiceService,
)
from apps.purchasing.services.supplier_payment_service import (
    SupplierPaymentService,
)
from apps.purchasing.services.vendor_debit_note_service import (
    VendorDebitNoteService,
)
from apps.sales.services.payment_service import (
    PaymentService,
)
class BankPaymentSuggestionService:

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
    def _get_suggestion_type(
        line,
    ):
        if (
            line.credit_amount
            > Decimal("0")
            and
            line.debit_amount
            == Decimal("0")
        ):
            return (
                "CUSTOMER_RECEIPT",
                line.credit_amount,
            )

        if (
            line.debit_amount
            > Decimal("0")
            and
            line.credit_amount
            == Decimal("0")
        ):
            return (
                "SUPPLIER_PAYMENT",
                line.debit_amount,
            )

        raise ValueError(
            "Invalid statement line direction."
        )

    @staticmethod
    def _score_invoice_candidate(
        *,
        invoice,
        line,
        amount,
        organization,
    ):
        score = Decimal("0")
        reasons = []

        net_receivable = (
            InvoiceService
            .get_invoice_net_receivable(
                organization=organization,
                invoice=invoice,
            )
        )

        if (
            net_receivable
            == amount
        ):
            score += Decimal("60")
            reasons.append(
                "Exact outstanding amount match."
            )

        reference_text = (
            (
                line.external_reference
                or ""
            )
            + " "
            + (
                line.description
                or ""
            )
        ).lower()

        if (
            invoice.invoice_number
            and
            invoice.invoice_number
            .lower()
            in reference_text
        ):
            score += Decimal("30")
            reasons.append(
                "Invoice number found "
                "in statement reference."
            )

        date_difference = abs(
            (
                line.transaction_date.date()
                -
                invoice.invoice_date.date()
            ).days
        )

        if date_difference <= 3:
            score += Decimal("10")
            reasons.append(
                "Transaction date is close "
                "to invoice date."
            )

        if score > Decimal("100"):
            score = Decimal("100")

        return {
            "score": score,
            "reason": " ".join(
                reasons
            ),
            "net_receivable":
                net_receivable,
        }

    @staticmethod
    def _score_vendor_bill_candidate(
        *,
        vendor_bill,
        line,
        amount,
        organization,
    ):
        score = Decimal("0")
        reasons = []

        net_payable = (
            VendorDebitNoteService
            .get_vendor_bill_net_payable(
                organization=organization,
                vendor_bill=vendor_bill,
            )
        )

        if (
            net_payable
            == amount
        ):
            score += Decimal("60")
            reasons.append(
                "Exact outstanding amount match."
            )

        reference_text = (
            (
                line.external_reference
                or ""
            )
            + " "
            + (
                line.description
                or ""
            )
        ).lower()

        if (
            vendor_bill.bill_number
            and
            vendor_bill.bill_number
            .lower()
            in reference_text
        ):
            score += Decimal("30")
            reasons.append(
                "Vendor bill number found "
                "in statement reference."
            )

        date_difference = abs(
            (
                line.transaction_date.date()
                -
                vendor_bill.bill_date.date()
            ).days
        )

        if date_difference <= 3:
            score += Decimal("10")
            reasons.append(
                "Transaction date is close "
                "to vendor bill date."
            )

        if score > Decimal("100"):
            score = Decimal("100")

        return {
            "score": score,
            "reason": " ".join(
                reasons
            ),
            "net_payable":
                net_payable,
        }

    @staticmethod
    def _find_best_invoice(
        *,
        organization,
        line,
        amount,
    ):
        invoices = (
            InvoiceRepository
            .list_outstanding(
                organization=organization,
            )
        )

        candidates = []

        for invoice in invoices:
            scoring = (
                BankPaymentSuggestionService
                ._score_invoice_candidate(
                    invoice=invoice,
                    line=line,
                    amount=amount,
                    organization=organization,
                )
            )

            if (
                scoring["net_receivable"]
                <= Decimal("0")
            ):
                continue

            candidates.append(
                {
                    "invoice":
                        invoice,
                    "score":
                        scoring["score"],
                    "reason":
                        scoring["reason"],
                }
            )

        if not candidates:
            return None

        candidates.sort(
            key=lambda item:
                item["score"],
            reverse=True,
        )

        best = candidates[0]

        if best["score"] <= 0:
            return None

        return best

    @staticmethod
    def _find_best_vendor_bill(
        *,
        organization,
        line,
        amount,
    ):
        vendor_bills = (
            VendorBillRepository
            .list_outstanding(
                organization=organization,
            )
        )

        candidates = []

        for vendor_bill in vendor_bills:
            scoring = (
                BankPaymentSuggestionService
                ._score_vendor_bill_candidate(
                    vendor_bill=(
                        vendor_bill
                    ),
                    line=line,
                    amount=amount,
                    organization=organization,
                )
            )

            if (
                scoring["net_payable"]
                <= Decimal("0")
            ):
                continue

            candidates.append(
                {
                    "vendor_bill":
                        vendor_bill,
                    "score":
                        scoring["score"],
                    "reason":
                        scoring["reason"],
                }
            )

        if not candidates:
            return None

        candidates.sort(
            key=lambda item:
                item["score"],
            reverse=True,
        )

        best = candidates[0]

        if best["score"] <= 0:
            return None

        return best

    @staticmethod
    def generate_suggestion(
        *,
        user,
        organization,
        statement,
        line,
    ):
        BankPaymentSuggestionService._check_permission(
            user,
            "bank_statements.reconcile",
        )

        BankPaymentSuggestionService._check_organization(
            user,
            organization,
        )

        if not statement:
            raise ValueError(
                "Bank statement is required."
            )

        if (
            statement.organization.id
            != organization.id
        ):
            raise PermissionError(
                "Bank statement does not belong "
                "to this organization."
            )

        if not line:
            raise ValueError(
                "Statement line is required."
            )

        existing = (
            BankPaymentSuggestionRepository
            .get_by_statement_line(
                organization=organization,
                statement=statement,
                line_number=(
                    line.line_number
                ),
            )
        )

        if existing:
            raise ValueError(
                "Payment suggestion already "
                "exists for this statement line."
            )

        suggestion_type, amount = (
            BankPaymentSuggestionService
            ._get_suggestion_type(
                line
            )
        )

        if (
            suggestion_type
            == "CUSTOMER_RECEIPT"
        ):
            best = (
                BankPaymentSuggestionService
                ._find_best_invoice(
                    organization=organization,
                    line=line,
                    amount=amount,
                )
            )

            if not best:
                return None

            return (
                BankPaymentSuggestionRepository
                .create_suggestion(
                    organization=organization,
                    statement=statement,
                    line_number=(
                        line.line_number
                    ),
                    suggestion_type=(
                        suggestion_type
                    ),
                    invoice=(
                        best["invoice"]
                    ),
                    vendor_bill=None,
                    amount=amount,
                    confidence=(
                        best["score"]
                    ),
                    match_reason=(
                        best["reason"]
                    ),
                    created_by=user,
                )
            )

        best = (
            BankPaymentSuggestionService
            ._find_best_vendor_bill(
                organization=organization,
                line=line,
                amount=amount,
            )
        )

        if not best:
            return None

        return (
            BankPaymentSuggestionRepository
            .create_suggestion(
                organization=organization,
                statement=statement,
                line_number=(
                    line.line_number
                ),
                suggestion_type=(
                    suggestion_type
                ),
                invoice=None,
                vendor_bill=(
                    best["vendor_bill"]
                ),
                amount=amount,
                confidence=(
                    best["score"]
                ),
                match_reason=(
                    best["reason"]
                ),
                created_by=user,
            )
        )

    @staticmethod
    def confirm_suggestion(
        *,
        user,
        organization,
        suggestion,
    ):
        BankPaymentSuggestionService._check_permission(
            user,
            "bank_statements.reconcile",
        )

        BankPaymentSuggestionService._check_organization(
            user,
            organization,
        )

        if not suggestion:
            raise ValueError(
                "Payment suggestion is required."
            )

        if (
            suggestion.organization.id
            != organization.id
        ):
            raise PermissionError(
                "Payment suggestion does not belong "
                "to this organization."
            )

        suggestion.reload()

        if suggestion.status == "CONFIRMED":
            raise ValueError(
                "Payment suggestion is already confirmed."
            )

        if suggestion.status == "REJECTED":
            raise ValueError(
                "Rejected payment suggestions "
                "cannot be confirmed."
            )

        if suggestion.status != "PENDING":
            raise ValueError(
                "Only pending payment suggestions "
                "can be confirmed."
            )

        if (
            suggestion.suggestion_type
            == "CUSTOMER_RECEIPT"
        ):
            if not suggestion.invoice:
                raise ValueError(
                    "Customer receipt suggestion "
                    "has no invoice."
                )

            if suggestion.vendor_bill:
                raise ValueError(
                    "Customer receipt suggestion "
                    "cannot contain a vendor bill."
                )

        elif (
            suggestion.suggestion_type
            == "SUPPLIER_PAYMENT"
        ):
            if not suggestion.vendor_bill:
                raise ValueError(
                    "Supplier payment suggestion "
                    "has no vendor bill."
                )

            if suggestion.invoice:
                raise ValueError(
                    "Supplier payment suggestion "
                    "cannot contain an invoice."
                )

        else:
            raise ValueError(
                "Invalid payment suggestion type."
            )

        return (
            BankPaymentSuggestionRepository
            .update_status(
                suggestion=suggestion,
                status="CONFIRMED",
                confirmed_at=(
                    datetime.utcnow()
                ),
                rejected_at=None,
            )
        )


    @staticmethod
    def reject_suggestion(
        *,
        user,
        organization,
        suggestion,
    ):
        BankPaymentSuggestionService._check_permission(
            user,
            "bank_statements.reconcile",
        )

        BankPaymentSuggestionService._check_organization(
            user,
            organization,
        )

        if not suggestion:
            raise ValueError(
                "Payment suggestion is required."
            )

        if (
            suggestion.organization.id
            != organization.id
        ):
            raise PermissionError(
                "Payment suggestion does not belong "
                "to this organization."
            )

        suggestion.reload()

        if suggestion.status == "REJECTED":
            raise ValueError(
                "Payment suggestion is already rejected."
            )

        if suggestion.status == "CONFIRMED":
            raise ValueError(
                "Confirmed payment suggestions "
                "cannot be rejected."
            )

        if suggestion.status != "PENDING":
            raise ValueError(
                "Only pending payment suggestions "
                "can be rejected."
            )

        return (
            BankPaymentSuggestionRepository
            .update_status(
                suggestion=suggestion,
                status="REJECTED",
                confirmed_at=None,
                rejected_at=(
                    datetime.utcnow()
                ),
            )
        )


    @staticmethod
    def execute_customer_receipt(
        *,
        user,
        organization,
        suggestion,
    ):
        BankPaymentSuggestionService._check_permission(
            user,
            "bank_statements.reconcile",
        )

        BankPaymentSuggestionService._check_organization(
            user,
            organization,
        )

        if not suggestion:
            raise ValueError(
                "Payment suggestion is required."
            )

        if (
            suggestion.organization.id
            != organization.id
        ):
            raise PermissionError(
                "Payment suggestion does not belong "
                "to this organization."
            )

        suggestion.reload()

        if suggestion.status != "CONFIRMED":
            raise ValueError(
                "Only confirmed payment suggestions "
                "can be executed."
            )

        if suggestion.executed_at is not None:
            raise ValueError(
                "Payment suggestion has already "
                "been executed."
            )

        if suggestion.payment_reference:
            raise ValueError(
                "Payment suggestion already has "
                "a payment reference."
            )

        if (
            suggestion.suggestion_type
            != "CUSTOMER_RECEIPT"
        ):
            raise ValueError(
                "Payment suggestion is not "
                "a customer receipt."
            )

        if not suggestion.invoice:
            raise ValueError(
                "Customer receipt suggestion "
                "has no invoice."
            )

        if suggestion.vendor_bill:
            raise ValueError(
                "Customer receipt suggestion "
                "cannot contain a vendor bill."
            )

        statement = (
            suggestion.statement
        )

        if not statement:
            raise ValueError(
                "Payment suggestion has no "
                "bank statement."
            )

        if (
            statement.organization.id
            != organization.id
        ):
            raise PermissionError(
                "Bank statement does not belong "
                "to this organization."
            )

        statement.reload()

        if statement.status == "CANCELLED":
            raise ValueError(
                "Cannot execute a suggestion "
                "from a cancelled statement."
            )

        line = (
            BankStatementService
            .get_statement_line(
                statement=statement,
                line_number=(
                    suggestion.line_number
                ),
            )
        )

        if line.match_status != "UNMATCHED":
            raise ValueError(
                "Statement line must be unmatched "
                "before executing the suggestion."
            )

        if (
            line.matched_transaction
            is not None
        ):
            raise ValueError(
                "Statement line already has "
                "a matched transaction."
            )

        if (
            line.credit_amount <= Decimal("0")
            or
            line.debit_amount != Decimal("0")
        ):
            raise ValueError(
                "Customer receipt suggestion must "
                "come from a statement credit."
            )

        amount = Decimal(
            str(
                suggestion.amount
            )
        )

        if line.credit_amount != amount:
            raise ValueError(
                "Suggestion amount does not match "
                "statement line credit amount."
            )

        invoice = (
            suggestion.invoice
        )

        invoice.reload()

        if (
            invoice.organization.id
            != organization.id
        ):
            raise PermissionError(
                "Invoice does not belong "
                "to this organization."
            )

        net_receivable = (
            InvoiceService
            .get_invoice_net_receivable(
                organization=organization,
                invoice=invoice,
            )
        )

        if amount > net_receivable:
            raise ValueError(
                "Suggestion amount exceeds "
                "invoice net receivable."
            )

        bank_account = (
            statement.bank_account
        )

        if not bank_account:
            raise ValueError(
                "Bank statement has no bank account."
            )

        bank_account.reload()

        #
        # Store original values for compensation.
        #
        original_amount_paid = (
            invoice.amount_paid
        )

        original_balance_due = (
            invoice.balance_due
        )

        original_status = (
            invoice.status
        )

        original_paid_at = (
            invoice.paid_at
        )

        original_bank_balance = (
            bank_account.current_balance
        )

        payment = None
        bank_transaction = None

        #
        # Use a deterministic payment reference.
        #
        execution_reference = (
            "BANK-STMT-"
            + str(suggestion.id)
        )

        try:
            #
            # 1. Create CustomerPayment,
            #    MONEY_IN and update invoice.
            #
            payment = (
                PaymentService
                .record_invoice_payment(
                    user=user,
                    organization=organization,
                    invoice=invoice,
                    amount=amount,
                    payment_method=(
                        "BANK_TRANSFER"
                    ),
                    bank_account=(
                        bank_account
                    ),
                    payment_date=(
                        line.transaction_date
                    ),
                    reference_number=(
                        execution_reference
                    ),
                    notes=(
                        "Created from bank statement "
                        f"{statement.statement_number}, "
                        f"line {line.line_number}."
                    ),
                )
            )

            #
            # 2. Find the MONEY_IN created by
            #    PaymentService.
            #
            bank_transaction = (
                BankTransactionRepository
                .get_by_reference(
                    organization=organization,
                    bank_account=bank_account,
                    reference_type=(
                        "CUSTOMER_PAYMENT"
                    ),
                    reference_id=(
                        payment.payment_number
                    ),
                )
            )

            if not bank_transaction:
                raise ValueError(
                    "Customer payment bank "
                    "transaction was not found."
                )

            if (
                bank_transaction.transaction_type
                != "MONEY_IN"
            ):
                raise ValueError(
                    "Customer payment did not "
                    "create a MONEY_IN transaction."
                )

            if (
                bank_transaction.amount
                != amount
            ):
                raise ValueError(
                    "Bank transaction amount does "
                    "not match suggestion amount."
                )

            #
            # 3. Match and reconcile the imported
            #    statement line.
            #
            statement.reload()

            line = (
                BankStatementService
                .get_statement_line(
                    statement=statement,
                    line_number=(
                        suggestion.line_number
                    ),
                )
            )

            (
                BankStatementService
                .apply_match(
                    user=user,
                    organization=organization,
                    statement=statement,
                    line=line,
                    transaction=(
                        bank_transaction
                    ),
                )
            )

            #
            # 4. Mark suggestion executed only
            #    after every financial action
            #    succeeds.
            #
            suggestion = (
                BankPaymentSuggestionRepository
                .mark_executed(
                    suggestion=suggestion,
                    payment_reference=(
                        payment.payment_number
                    ),
                    executed_at=(
                        datetime.utcnow()
                    ),
                )
            )

            return {
                "suggestion":
                    suggestion,
                "payment":
                    payment,
                "bank_transaction":
                    bank_transaction,
            }

        except Exception:
            #
            # Compensation if failure happens
            # after PaymentService succeeds.
            #

            if bank_transaction:
                try:
                    bank_transaction.reload()

                    if (
                        bank_transaction
                        .reconciliation_status
                        == "RECONCILED"
                    ):
                        bank_transaction.reconciliation_status = (
                            "UNRECONCILED"
                        )

                        bank_transaction.reconciled_at = None

                        bank_transaction.save()

                except Exception:
                    pass

            #
            # Restore statement line if matching
            # was partially persisted.
            #
            try:
                statement.reload()

                current_line = (
                    BankStatementService
                    .get_statement_line(
                        statement=statement,
                        line_number=(
                            suggestion.line_number
                        ),
                    )
                )

                if (
                    current_line.match_status
                    == "MATCHED"
                    and
                    current_line.matched_transaction
                    is not None
                    and
                    bank_transaction
                    is not None
                    and
                    current_line
                    .matched_transaction.id
                    == bank_transaction.id
                ):
                    current_line.match_status = (
                        "UNMATCHED"
                    )

                    current_line.matched_transaction = (
                        None
                    )

                    current_line.matched_at = None

                    statement.save()

                    (
                        BankStatementService
                        .update_statement_reconciliation_status(
                            statement=statement,
                        )
                    )

            except Exception:
                pass

            #
            # Delete bank transaction and restore
            # bank balance.
            #
            if bank_transaction:
                try:
                    bank_transaction.delete()

                    bank_account.reload()

                    bank_account.current_balance = (
                        original_bank_balance
                    )

                    bank_account.save()

                except Exception:
                    pass

            #
            # Delete CustomerPayment.
            #
            if payment:
                try:
                    payment.delete()

                except Exception:
                    pass

            #
            # Restore Invoice.
            #
            try:
                invoice.reload()

                (
                    InvoiceRepository
                    .update_payment_totals(
                        invoice=invoice,
                        amount_paid=(
                            original_amount_paid
                        ),
                        balance_due=(
                            original_balance_due
                        ),
                        status=(
                            original_status
                        ),
                        paid_at=(
                            original_paid_at
                        ),
                    )
                )

            except Exception:
                pass

            raise

    @staticmethod
    def execute_supplier_payment(
        *,
        user,
        organization,
        suggestion,
    ):
        BankPaymentSuggestionService._check_permission(
            user,
            "bank_statements.reconcile",
        )

        BankPaymentSuggestionService._check_organization(
            user,
            organization,
        )

        if not suggestion:
            raise ValueError(
                "Payment suggestion is required."
            )

        if (
            suggestion.organization.id
            != organization.id
        ):
            raise PermissionError(
                "Payment suggestion does not belong "
                "to this organization."
            )

        suggestion.reload()

        if suggestion.status != "CONFIRMED":
            raise ValueError(
                "Only confirmed payment suggestions "
                "can be executed."
            )

        if suggestion.executed_at is not None:
            raise ValueError(
                "Payment suggestion has already "
                "been executed."
            )

        if suggestion.payment_reference:
            raise ValueError(
                "Payment suggestion already has "
                "a payment reference."
            )

        if (
            suggestion.suggestion_type
            != "SUPPLIER_PAYMENT"
        ):
            raise ValueError(
                "Payment suggestion is not "
                "a supplier payment."
            )

        if not suggestion.vendor_bill:
            raise ValueError(
                "Supplier payment suggestion "
                "has no vendor bill."
            )

        if suggestion.invoice:
            raise ValueError(
                "Supplier payment suggestion "
                "cannot contain an invoice."
            )

        statement = (
            suggestion.statement
        )

        if not statement:
            raise ValueError(
                "Payment suggestion has no "
                "bank statement."
            )

        if (
            statement.organization.id
            != organization.id
        ):
            raise PermissionError(
                "Bank statement does not belong "
                "to this organization."
            )

        statement.reload()

        if statement.status == "CANCELLED":
            raise ValueError(
                "Cannot execute a suggestion "
                "from a cancelled statement."
            )

        line = (
            BankStatementService
            .get_statement_line(
                statement=statement,
                line_number=(
                    suggestion.line_number
                ),
            )
        )

        if line.match_status != "UNMATCHED":
            raise ValueError(
                "Statement line must be unmatched "
                "before executing the suggestion."
            )

        if (
            line.matched_transaction
            is not None
        ):
            raise ValueError(
                "Statement line already has "
                "a matched transaction."
            )

        if (
            line.debit_amount <= Decimal("0")
            or
            line.credit_amount != Decimal("0")
        ):
            raise ValueError(
                "Supplier payment suggestion must "
                "come from a statement debit."
            )

        amount = Decimal(
            str(
                suggestion.amount
            )
        )

        if line.debit_amount != amount:
            raise ValueError(
                "Suggestion amount does not match "
                "statement line debit amount."
            )

        vendor_bill = (
            suggestion.vendor_bill
        )

        vendor_bill.reload()

        if (
            vendor_bill.organization.id
            != organization.id
        ):
            raise PermissionError(
                "Vendor bill does not belong "
                "to this organization."
            )

        bank_account = (
            statement.bank_account
        )

        if not bank_account:
            raise ValueError(
                "Bank statement has no bank account."
            )

        bank_account.reload()

        original_amount_paid = (
            vendor_bill.amount_paid
        )

        original_balance_due = (
            vendor_bill.balance_due
        )

        original_status = (
            vendor_bill.status
        )

        original_paid_at = (
            vendor_bill.paid_at
        )

        original_bank_balance = (
            bank_account.current_balance
        )

        payment = None
        bank_transaction = None

        execution_reference = (
            "BANK-STMT-"
            + str(suggestion.id)
        )

        try:
            payment = (
                SupplierPaymentService
                .record_bill_payment(
                    user=user,
                    organization=organization,
                    vendor_bill=vendor_bill,
                    amount=amount,
                    payment_method=(
                        "BANK_TRANSFER"
                    ),
                    bank_account=(
                        bank_account
                    ),
                    payment_date=(
                        line.transaction_date
                    ),
                    reference_number=(
                        execution_reference
                    ),
                    notes=(
                        "Created from bank statement "
                        f"{statement.statement_number}, "
                        f"line {line.line_number}."
                    ),
                )
            )

            bank_transaction = (
                BankTransactionRepository
                .get_by_reference(
                    organization=organization,
                    bank_account=bank_account,
                    reference_type=(
                        "SUPPLIER_PAYMENT"
                    ),
                    reference_id=(
                        payment.payment_number
                    ),
                )
            )

            if not bank_transaction:
                raise ValueError(
                    "Supplier payment bank "
                    "transaction was not found."
                )

            if (
                bank_transaction.transaction_type
                != "MONEY_OUT"
            ):
                raise ValueError(
                    "Supplier payment did not "
                    "create a MONEY_OUT transaction."
                )

            if (
                bank_transaction.amount
                != amount
            ):
                raise ValueError(
                    "Bank transaction amount does "
                    "not match suggestion amount."
                )

            statement.reload()

            line = (
                BankStatementService
                .get_statement_line(
                    statement=statement,
                    line_number=(
                        suggestion.line_number
                    ),
                )
            )

            (
                BankStatementService
                .apply_match(
                    user=user,
                    organization=organization,
                    statement=statement,
                    line=line,
                    transaction=(
                        bank_transaction
                    ),
                )
            )

            suggestion = (
                BankPaymentSuggestionRepository
                .mark_executed(
                    suggestion=suggestion,
                    payment_reference=(
                        payment.payment_number
                    ),
                    executed_at=(
                        datetime.utcnow()
                    ),
                )
            )

            return {
                "suggestion":
                    suggestion,
                "payment":
                    payment,
                "bank_transaction":
                    bank_transaction,
            }

        except Exception:
            if bank_transaction:
                try:
                    bank_transaction.reload()

                    if (
                        bank_transaction
                        .reconciliation_status
                        == "RECONCILED"
                    ):
                        bank_transaction.reconciliation_status = (
                            "UNRECONCILED"
                        )

                        bank_transaction.reconciled_at = None

                        bank_transaction.save()

                except Exception:
                    pass

            try:
                statement.reload()

                current_line = (
                    BankStatementService
                    .get_statement_line(
                        statement=statement,
                        line_number=(
                            suggestion.line_number
                        ),
                    )
                )

                if (
                    current_line.match_status
                    == "MATCHED"
                    and
                    current_line.matched_transaction
                    is not None
                    and
                    bank_transaction
                    is not None
                    and
                    current_line
                    .matched_transaction.id
                    == bank_transaction.id
                ):
                    current_line.match_status = (
                        "UNMATCHED"
                    )

                    current_line.matched_transaction = None
                    current_line.matched_at = None

                    statement.save()

                    (
                        BankStatementService
                        .update_statement_reconciliation_status(
                            statement=statement,
                        )
                    )

            except Exception:
                pass

            if bank_transaction:
                try:
                    bank_transaction.delete()

                    bank_account.reload()

                    bank_account.current_balance = (
                        original_bank_balance
                    )

                    bank_account.save()

                except Exception:
                    pass

            if payment:
                try:
                    payment.delete()

                except Exception:
                    pass

            try:
                vendor_bill.reload()

                (
                    VendorBillRepository
                    .update_payment_totals(
                        bill=vendor_bill,
                        amount_paid=(
                            original_amount_paid
                        ),
                        balance_due=(
                            original_balance_due
                        ),
                        status=(
                            original_status
                        ),
                        paid_at=(
                            original_paid_at
                        ),
                    )
                )

            except Exception:
                pass

            raise