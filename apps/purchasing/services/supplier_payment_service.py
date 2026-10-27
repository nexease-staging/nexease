from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from apps.authorization.services import (
    AuthorizationService,
)

from apps.finance.services.bank_transaction_service import (
    BankTransactionService,
)

from apps.purchasing.models import (
    SupplierPaymentAllocation,
)

from apps.purchasing.repositories.supplier_payment_repository import (
    SupplierPaymentRepository,
)

from apps.purchasing.repositories.vendor_bill_repository import (
    VendorBillRepository,
)

from apps.purchasing.services.vendor_debit_note_service import (
    VendorDebitNoteService,
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
class SupplierPaymentService:

    VALID_PAYMENT_METHODS = {
        "CASH",
        "BANK_TRANSFER",
        "CHEQUE",
        "UPI",
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
    def _generate_payment_number():
        return (
            "SPAY-"
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

    @staticmethod
    def _post_supplier_payment_accounting(
        *,
        user,
        organization,
        payment,
    ):
        """
        Create and post accounting for a
        supplier payment.

        Dr Accounts Payable
            Cr Cash / Bank
        """

        if not payment:
            raise ValueError(
                "Supplier payment is required."
            )

        if (
            payment.organization.id
            != organization.id
        ):
            raise PermissionError(
                "Supplier payment does not belong "
                "to this organization."
            )

        if payment.amount <= 0:
            raise ValueError(
                "Supplier payment amount must be "
                "greater than zero."
            )

        # ==================================================
        # DUPLICATE JOURNAL PROTECTION
        # ==================================================

        existing_journal = (
            JournalEntryRepository
            .get_by_source(
                organization=organization,
                source_type="SUPPLIER_PAYMENT",
                source_id=str(
                    payment.id
                ),
            )
        )

        if existing_journal:
            return existing_journal

        # ==================================================
        # ACCOUNTS PAYABLE
        # ==================================================

        accounts_payable = (
            ChartOfAccountService
            .get_system_account(
                organization=organization,
                system_key="ACCOUNTS_PAYABLE",
            )
        )

        # ==================================================
        # PAYMENT ACCOUNT
        # ==================================================
        #
        # CASH payments use the CASH GL account.
        #
        # Other methods currently use the BANK GL account
        # because the operational payment itself is linked
        # to a BankAccount.
        # ==================================================

        if payment.payment_method == "CASH":

            payment_account = (
                ChartOfAccountService
                .get_system_account(
                    organization=organization,
                    system_key="CASH",
                )
            )

        else:

            payment_account = (
                ChartOfAccountService
                .get_system_account(
                    organization=organization,
                    system_key="BANK",
                )
            )

        # ==================================================
        # JOURNAL LINES
        # ==================================================

        raw_lines = [
            {
                "account":
                    accounts_payable,

                "description": (
                    "Supplier payment "
                    f"{payment.payment_number}"
                ),

                "debit":
                    payment.amount,

                "credit":
                    "0.00",
            },
            {
                "account":
                    payment_account,

                "description": (
                    "Payment to supplier "
                    f"{payment.payment_number}"
                ),

                "debit":
                    "0.00",

                "credit":
                    payment.amount,
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
                raw_lines=raw_lines,
                description=(
                    "Supplier payment "
                    f"{payment.payment_number}"
                ),
                source_type=(
                    "SUPPLIER_PAYMENT"
                ),
                source_id=str(
                    payment.id
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

    @staticmethod
    def record_bill_payment(
        *,
        user,
        organization,
        vendor_bill,
        amount,
        payment_method,
        bank_account,
        payment_date=None,
        reference_number="",
        notes="",
    ):
        """
        Record a supplier payment against one vendor bill,
        create a MONEY_OUT bank transaction,
        update the vendor bill,
        and create the accounting journal.

        Accounting:
            Dr Accounts Payable
                Cr Cash / Bank
        """

        SupplierPaymentService._check_permission(
            user,
            "bills.record_payment",
        )

        SupplierPaymentService._check_organization(
            user,
            organization,
        )

        # ==================================================
        # BANK ACCOUNT VALIDATION
        # ==================================================

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

        # ==================================================
        # VENDOR BILL VALIDATION
        # ==================================================

        if not vendor_bill:
            raise ValueError(
                "Vendor bill is required."
            )

        if (
            vendor_bill.organization.id
            != organization.id
        ):
            raise PermissionError(
                "Vendor bill does not belong "
                "to this organization."
            )

        if vendor_bill.status not in {
            "POSTED",
            "PARTIALLY_PAID",
        }:
            raise ValueError(
                "Payment can only be recorded "
                "against posted or partially "
                "paid bills."
            )

        if not vendor_bill.supplier:
            raise ValueError(
                "Vendor bill has no supplier."
            )

        if (
            vendor_bill.supplier
            .organization.id
            != organization.id
        ):
            raise PermissionError(
                "Supplier does not belong "
                "to this organization."
            )

        # ==================================================
        # AMOUNT VALIDATION
        # ==================================================

        amount = (
            SupplierPaymentService
            ._to_decimal(
                amount,
                "payment amount",
            )
        )

        if amount <= 0:
            raise ValueError(
                "Payment amount must be "
                "greater than zero."
            )

        # ==================================================
        # DEBIT-NOTE-AWARE PAYABLE
        # ==================================================

        net_payable = (
            VendorDebitNoteService
            .get_vendor_bill_net_payable(
                organization=organization,
                vendor_bill=vendor_bill,
            )
        )

        if net_payable <= Decimal("0"):
            raise ValueError(
                "Vendor bill has no "
                "outstanding payable."
            )

        if amount > net_payable:
            raise ValueError(
                "Payment amount cannot exceed "
                "vendor bill net payable."
            )

        # ==================================================
        # PAYMENT METHOD
        # ==================================================

        payment_method = (
            payment_method
            .strip()
            .upper()
        )

        if payment_method not in (
            SupplierPaymentService
            .VALID_PAYMENT_METHODS
        ):
            raise ValueError(
                "Invalid payment method."
            )

        # ==================================================
        # PAYMENT REFERENCE
        # ==================================================

        reference_number = (
            reference_number.strip()
        )

        if reference_number:

            existing_payment = (
                SupplierPaymentRepository
                .get_by_reference_number(
                    organization=organization,
                    reference_number=(
                        reference_number
                    ),
                )
            )

            if existing_payment:
                raise ValueError(
                    "Supplier payment reference "
                    "number already exists."
                )

        # ==================================================
        # PAYMENT DATE
        # ==================================================

        if payment_date is None:
            payment_date = (
                datetime.utcnow()
            )

        # ==================================================
        # PAYMENT NUMBER
        # ==================================================

        payment_number = (
            SupplierPaymentService
            ._generate_payment_number()
        )

        # ==================================================
        # ALLOCATION
        # ==================================================

        allocation = (
            SupplierPaymentAllocation(
                vendor_bill=vendor_bill,
                amount=amount,
            )
        )

        # ==================================================
        # BILL PAYMENT TOTALS
        # ==================================================

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

        new_amount_paid = (
            vendor_bill.amount_paid
            + amount
        )

        new_balance_due = (
            vendor_bill.total_amount
            - new_amount_paid
        )

        if new_balance_due < 0:
            raise ValueError(
                "Vendor bill balance "
                "cannot become negative."
            )

        # ==================================================
        # DEBIT NOTE IMPACT
        # ==================================================

        applied_debit = (
            vendor_bill.balance_due
            - net_payable
        )

        new_net_payable = (
            new_balance_due
            - applied_debit
        )

        if new_net_payable < 0:
            new_net_payable = (
                Decimal("0")
            )

        # ==================================================
        # NEW BILL STATUS
        # ==================================================

        if new_net_payable == 0:

            new_status = "PAID"

            paid_at = (
                datetime.utcnow()
            )

        else:

            new_status = (
                "PARTIALLY_PAID"
            )

            paid_at = None

        # ==================================================
        # EXECUTION STATE
        # ==================================================

        payment = None

        bank_transaction = None

        accounting_journal = None

        try:

            # ==============================================
            # 1. CREATE SUPPLIER PAYMENT
            # ==============================================

            payment = (
                SupplierPaymentRepository
                .create_payment(
                    organization=organization,
                    payment_number=(
                        payment_number
                    ),
                    supplier=(
                        vendor_bill.supplier
                    ),
                    payment_date=(
                        payment_date
                    ),
                    amount=amount,
                    payment_method=(
                        payment_method
                    ),
                    bank_account=(
                        bank_account
                    ),
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

            # ==============================================
            # 2. CREATE MONEY_OUT BANK TRANSACTION
            # ==============================================

            bank_transaction = (
                BankTransactionService
                .create_transaction(
                    user=user,
                    organization=organization,
                    bank_account=(
                        bank_account
                    ),
                    transaction_type=(
                        "MONEY_OUT"
                    ),
                    amount=amount,
                    transaction_date=(
                        payment_date
                    ),
                    reference_type=(
                        "SUPPLIER_PAYMENT"
                    ),
                    reference_id=(
                        payment.payment_number
                    ),
                    external_reference=(
                        reference_number
                    ),
                    description=(
                        "Supplier payment "
                        f"{payment.payment_number} "
                        f"to "
                        f"{vendor_bill.supplier.name}"
                    ),
                )
            )

            # ==============================================
            # 3. UPDATE VENDOR BILL
            # ==============================================

            VendorBillRepository.update_payment_totals(
                bill=vendor_bill,
                amount_paid=(
                    new_amount_paid
                ),
                balance_due=(
                    new_balance_due
                ),
                status=new_status,
                paid_at=paid_at,
            )

            # ==============================================
            # 4. ACCOUNTING JOURNAL
            # ==============================================

            accounting_journal = (
                SupplierPaymentService
                ._post_supplier_payment_accounting(
                    user=user,
                    organization=organization,
                    payment=payment,
                )
            )

        except Exception:

            # ==============================================
            # ROLLBACK ACCOUNTING JOURNAL
            # ==============================================

            if accounting_journal:

                try:

                    accounting_journal.delete()

                except Exception:
                    pass

            # ==============================================
            # RESTORE VENDOR BILL
            # ==============================================

            try:

                VendorBillRepository.update_payment_totals(
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

            except Exception:
                pass

            # ==============================================
            # ROLLBACK BANK LEDGER
            # ==============================================

            if bank_transaction:

                try:

                    bank_account.reload()

                    bank_account.current_balance = (
                        bank_transaction
                        .balance_before
                    )

                    bank_account.save()

                    bank_transaction.delete()

                except Exception:
                    pass

            # ==============================================
            # ROLLBACK SUPPLIER PAYMENT
            # ==============================================

            if payment:

                try:

                    payment.delete()

                except Exception:
                    pass

            raise

        return payment