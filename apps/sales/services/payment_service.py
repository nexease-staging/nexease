from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from apps.finance.services.bank_transaction_service import (
    BankTransactionService,
)
from apps.sales.services.invoice_service import (
    InvoiceService,
)
from apps.authorization.services import (
    AuthorizationService,
)

from apps.sales.models import (
    PaymentAllocation,
)

from apps.sales.repositories.invoice_repository import (
    InvoiceRepository,
)

from apps.sales.repositories.payment_repository import (
    PaymentRepository,
)
from apps.finance.repositories.journal_entry_repository import (
    JournalEntryRepository,
)

from apps.finance.services.chart_of_account_service import (
    ChartOfAccountService,
)

from apps.finance.services.journal_entry_service import (
    JournalEntryService,
)

class PaymentService:

    VALID_PAYMENT_METHODS = {
        "CASH",
        "BANK_TRANSFER",
        "UPI",
        "CHEQUE",
        "CARD",
        "OTHER",
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

        if not AuthorizationService.has_permission(
            user,
            permission_code,
        ):
            raise PermissionError(
                f"Permission denied: {permission_code}"
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
                "User does not belong to this organization."
            )

    @staticmethod
    def _generate_payment_number():
        return (
            "PAY-"
            + uuid4().hex[:12].upper()
        )

    @staticmethod
    def _to_decimal(
        value,
        field_name,
    ):
        try:
            return Decimal(
                str(value)
            )

        except Exception:
            raise ValueError(
                f"Invalid {field_name}."
            )

    def record_invoice_payment(
        *,
        user,
        organization,
        invoice,
        amount,
        payment_method,
        bank_account,
        payment_date=None,
        reference_number="",
        notes="",
    ):
        """
        Record a customer payment against one invoice.
        """

        PaymentService._check_permission(
            user,
            "invoices.record_payment",
        )

        PaymentService._check_organization(
            user,
            organization,
        )

        if not bank_account:
            raise ValueError(
                "Bank account is required."
            )

        if (
            bank_account.organization.id
            != organization.id
        ):
            raise PermissionError(
                "Bank account does not belong "
                "to this organization."
            )

        if not bank_account.is_active:
            raise ValueError(
                "Bank account is inactive."
            )
        if not invoice:
            raise ValueError(
                "Invoice is required."
            )

        if (
            invoice.organization.id
            != organization.id
        ):
            raise PermissionError(
                "Invoice does not belong to this organization."
            )

        if invoice.status not in {
            "ISSUED",
            "PARTIALLY_PAID",
        }:
            raise ValueError(
                "Payment can only be recorded "
                "against issued or partially paid invoices."
            )

        if not invoice.customer:
            raise ValueError(
                "Invoice has no customer."
            )

        if (
            invoice.customer.organization.id
            != organization.id
        ):
            raise PermissionError(
                "Customer does not belong to this organization."
            )

        amount = (
            PaymentService._to_decimal(
                amount,
                "payment amount",
            )
        )

        if amount <= 0:
            raise ValueError(
                "Payment amount must be greater than zero."
            )

        net_receivable = (
            InvoiceService
            .get_invoice_net_receivable(
                organization=organization,
                invoice=invoice,
            )
        )

        if net_receivable <= Decimal("0"):
            raise ValueError(
                "Invoice has no outstanding "
                "receivable."
            )

        if amount > net_receivable:
            raise ValueError(
                "Payment amount cannot exceed "
                "invoice net receivable."
            )

        payment_method = (
            payment_method
            .strip()
            .upper()
        )

        if payment_method not in (
            PaymentService
            .VALID_PAYMENT_METHODS
        ):
            raise ValueError(
                "Invalid payment method."
            )

        reference_number = (
            reference_number.strip()
        )

        if reference_number:
            existing_payment = (
                PaymentRepository
                .get_by_reference_number(
                    organization=organization,
                    reference_number=(
                        reference_number
                    ),
                )
            )

            if existing_payment:
                raise ValueError(
                    "Payment reference number "
                    "already exists."
                )

        if payment_date is None:
            payment_date = (
                datetime.utcnow()
            )

        payment_number = (
            PaymentService
            ._generate_payment_number()
        )

        allocation = PaymentAllocation(
            invoice=invoice,
            amount=amount,
        )

        new_amount_paid = (
            invoice.amount_paid
            + amount
        )

        new_balance_due = (
            invoice.total_amount
            - new_amount_paid
        )

        applied_credit = (
            invoice.balance_due
            - net_receivable
        )

        new_net_receivable = (
            new_balance_due
            - applied_credit
        )

        if new_net_receivable < 0:
            new_net_receivable = (
                Decimal("0")
            )

        if new_balance_due < 0:
            raise ValueError(
                "Invoice balance cannot become negative."
            )

        if new_net_receivable == 0:
            new_status = "PAID"
            paid_at = datetime.utcnow()

        else:
            new_status = "PARTIALLY_PAID"
            paid_at = None

        payment = None
        bank_transaction = None

        try:
            payment = (
                PaymentRepository
                .create_payment(
                    organization=organization,
                    payment_number=payment_number,
                    customer=invoice.customer,
                    payment_date=payment_date,
                    amount=amount,
                    payment_method=payment_method,
                    bank_account=bank_account,
                    reference_number=(
                        reference_number
                    ),
                    allocations=[
                        allocation
                    ],
                    notes=notes.strip(),
                    created_by=user,
                )
            )

            bank_transaction = (
                BankTransactionService
                .create_transaction(
                    user=user,
                    organization=organization,
                    bank_account=bank_account,
                    transaction_type="MONEY_IN",
                    amount=amount,
                    transaction_date=payment_date,
                    reference_type=(
                        "CUSTOMER_PAYMENT"
                    ),
                    reference_id=(
                        payment.payment_number
                    ),
                    external_reference=(
                        reference_number
                    ),
                    description=(
                        "Customer payment "
                        f"{payment.payment_number} "
                        f"from {invoice.customer.name}"
                    ),
                )
            )

            InvoiceRepository.update_payment_totals(
                invoice=invoice,
                amount_paid=new_amount_paid,
                balance_due=new_balance_due,
                status=new_status,
                paid_at=paid_at,
            )

        except Exception:
            if bank_transaction:
                try:
                    bank_account.reload()

                    bank_account.current_balance = (
                        bank_transaction.balance_before
                    )

                    bank_account.save()

                    bank_transaction.delete()

                except Exception:
                    pass

            if payment:
                try:
                    payment.delete()
                except Exception:
                    pass

            raise

        # ==================================================
        # ACCOUNTING INTEGRATION
        # ==================================================

        PaymentService._post_customer_payment_accounting(
            user=user,
            organization=organization,
            payment=payment,
        )

        return payment

    @staticmethod
    def _post_customer_payment_accounting(
        *,
        user,
        organization,
        payment,
    ):
        """
        Create and post the accounting journal
        for a customer payment.

        CASH:
            Dr Cash
                Cr Accounts Receivable

        Other banking methods:
            Dr Bank
                Cr Accounts Receivable
        """

        if not payment:
            raise ValueError(
                "Customer payment is required."
            )

        if (
            payment.organization.id
            != organization.id
        ):
            raise PermissionError(
                "Customer payment does not belong "
                "to this organization."
            )

        # ==================================================
        # DUPLICATE JOURNAL PROTECTION
        # ==================================================

        existing_journal = (
            JournalEntryRepository
            .get_by_source(
                organization=organization,
                source_type="CUSTOMER_PAYMENT",
                source_id=str(
                    payment.id
                ),
            )
        )

        if existing_journal:
            return existing_journal

        # ==================================================
        # ACCOUNTS RECEIVABLE
        # ==================================================

        accounts_receivable = (
            ChartOfAccountService
            .get_system_account(
                organization=organization,
                system_key=(
                    "ACCOUNTS_RECEIVABLE"
                ),
            )
        )

        # ==================================================
        # CASH / BANK ACCOUNT
        # ==================================================

        payment_method = str(
            payment.payment_method
            or ""
        ).strip().upper()

        if payment_method == "CASH":

            receiving_account = (
                ChartOfAccountService
                .get_system_account(
                    organization=organization,
                    system_key="CASH",
                )
            )

        else:

            receiving_account = (
                ChartOfAccountService
                .get_system_account(
                    organization=organization,
                    system_key="BANK",
                )
            )

        # ==================================================
        # VALIDATE AMOUNT
        # ==================================================

        amount = payment.amount

        if amount <= 0:
            raise ValueError(
                "Customer payment amount must "
                "be greater than zero."
            )

        # ==================================================
        # BUILD DOUBLE-ENTRY JOURNAL
        # ==================================================

        raw_lines = [
            {
                "account":
                    receiving_account,

                "description": (
                    "Customer payment "
                    f"{payment.payment_number}"
                ),

                "debit":
                    amount,

                "credit":
                    "0.00",
            },
            {
                "account":
                    accounts_receivable,

                "description": (
                    "Settlement of customer "
                    "receivable for payment "
                    f"{payment.payment_number}"
                ),

                "debit":
                    "0.00",

                "credit":
                    amount,
            },
        ]

        # ==================================================
        # CREATE JOURNAL
        # ==================================================

        journal = (
            JournalEntryService
            .create_journal(
                user=user,
                organization=organization,
                journal_date=(
                    payment.payment_date
                ),
                description=(
                    "Customer payment "
                    f"{payment.payment_number}"
                ),
                source_type=(
                    "CUSTOMER_PAYMENT"
                ),
                source_id=str(
                    payment.id
                ),
                raw_lines=(
                    raw_lines
                ),
            )
        )

        # ==================================================
        # POST JOURNAL
        # ==================================================

        journal = (
            JournalEntryService
            .post_journal(
                user=user,
                organization=organization,
                journal_id=str(
                    journal.id
                ),
            )
        )

        return journal