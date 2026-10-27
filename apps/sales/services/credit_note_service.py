from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from apps.authorization.services import (
    AuthorizationService,
)

from apps.sales.models import (
    CreditNoteItem,
)

from apps.sales.repositories.credit_note_repository import (
    CreditNoteRepository,
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

class CreditNoteService:

    VALID_STATUSES = {
        "DRAFT",
        "ISSUED",
        "CANCELLED",
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
    def _generate_credit_note_number():
        return (
            "CN-"
            + uuid4().hex[:12].upper()
        )

    @staticmethod
    def create_from_sales_return(
        *,
        user,
        organization,
        sales_return,
        credit_note_date=None,
        reason="",
        notes="",
    ):
        CreditNoteService._check_permission(
            user,
            "credit_notes.create",
        )

        CreditNoteService._check_organization(
            user,
            organization,
        )

        if not sales_return:
            raise ValueError(
                "Sales return is required."
            )

        if (
            sales_return.organization.id
            != organization.id
        ):
            raise PermissionError(
                "Sales return does not belong "
                "to this organization."
            )

        if sales_return.status != "CONFIRMED":
            raise ValueError(
                "Credit note can only be created "
                "from a confirmed sales return."
            )

        invoice = sales_return.invoice

        if not invoice:
            raise ValueError(
                "Sales return has no invoice."
            )

        if (
            invoice.organization.id
            != organization.id
        ):
            raise PermissionError(
                "Invoice does not belong "
                "to this organization."
            )

        customer = sales_return.customer

        if not customer:
            raise ValueError(
                "Sales return has no customer."
            )

        if (
            customer.organization.id
            != organization.id
        ):
            raise PermissionError(
                "Customer does not belong "
                "to this organization."
            )

        if (
            invoice.customer.id
            != customer.id
        ):
            raise ValueError(
                "Sales return customer does not "
                "match invoice customer."
            )

        existing_credit_note = (
            CreditNoteRepository
            .get_by_sales_return(
                organization=organization,
                sales_return=sales_return,
            )
        )

        if existing_credit_note:
            raise ValueError(
                "Credit note already exists "
                "for this sales return."
            )

        if not sales_return.items:
            raise ValueError(
                "Sales return has no items."
            )

        credit_note_items = []

        subtotal = Decimal("0")
        tax_amount = Decimal("0")
        discount_amount = Decimal("0")
        total_amount = Decimal("0")

        for return_item in sales_return.items:
            credit_item = CreditNoteItem(
                product=return_item.product,
                quantity=return_item.quantity,
                unit_price=return_item.unit_price,
                tax_rate=return_item.tax_rate,
                discount=return_item.discount,
                line_subtotal=(
                    return_item.line_subtotal
                ),
                line_tax=(
                    return_item.line_tax
                ),
                line_total=(
                    return_item.line_total
                ),
            )

            credit_note_items.append(
                credit_item
            )

            subtotal += (
                return_item.line_subtotal
            )

            tax_amount += (
                return_item.line_tax
            )

            discount_amount += (
                return_item.discount
            )

            total_amount += (
                return_item.line_total
            )

        if total_amount <= 0:
            raise ValueError(
                "Credit note total must be "
                "greater than zero."
            )

        if credit_note_date is None:
            credit_note_date = (
                datetime.utcnow()
            )

        return (
            CreditNoteRepository
            .create_credit_note(
                organization=organization,
                credit_note_number=(
                    CreditNoteService
                    ._generate_credit_note_number()
                ),
                invoice=invoice,
                sales_return=sales_return,
                customer=customer,
                credit_note_date=(
                    credit_note_date
                ),
                items=credit_note_items,
                subtotal=subtotal,
                tax_amount=tax_amount,
                discount_amount=(
                    discount_amount
                ),
                total_amount=total_amount,
                reason=(
                    reason.strip()
                    or sales_return.reason
                ),
                notes=notes.strip(),
                created_by=user,
                status="DRAFT",
            )
        )

    @staticmethod
    def get_invoice_applied_credit(
        *,
        organization,
        invoice,
        exclude_credit_note=None,
    ):
        credit_notes = (
            CreditNoteRepository
            .list_by_invoice(
                organization=organization,
                invoice=invoice,
            )
        )

        total = Decimal("0")

        for credit_note in credit_notes:
            if credit_note.status != "ISSUED":
                continue

            if (
                exclude_credit_note
                and credit_note.id
                == exclude_credit_note.id
            ):
                continue

            total += credit_note.applied_amount

        return total

    @staticmethod
    def get_invoice_net_receivable(
        *,
        organization,
        invoice,
    ):
        applied_credit = (
            CreditNoteService
            .get_invoice_applied_credit(
                organization=organization,
                invoice=invoice,
            )
        )

        net_receivable = (
            invoice.balance_due
            - applied_credit
        )

        if net_receivable < 0:
            return Decimal("0")

        return net_receivable

    @staticmethod
    def _post_credit_note_accounting(
        *,
        user,
        organization,
        credit_note,
    ):
        """
        Create and post accounting for an
        issued sales credit note.

        Dr Sales Revenue
        Dr Output Tax Payable
            Cr Accounts Receivable
        """

        if not credit_note:
            raise ValueError(
                "Credit note is required."
            )

        if (
            credit_note.organization.id
            != organization.id
        ):
            raise PermissionError(
                "Credit note does not belong "
                "to this organization."
            )

        if credit_note.total_amount <= 0:
            raise ValueError(
                "Credit note total must be "
                "greater than zero."
            )

        # ==============================================
        # DUPLICATE JOURNAL PROTECTION
        # ==============================================

        existing_journal = (
            JournalEntryRepository
            .get_by_source(
                organization=organization,
                source_type="SALES_CREDIT_NOTE",
                source_id=str(
                    credit_note.id
                ),
            )
        )

        if existing_journal:
            return existing_journal

        # ==============================================
        # GET SYSTEM ACCOUNTS
        # ==============================================

        sales_revenue = (
            ChartOfAccountService
            .get_system_account(
                organization=organization,
                system_key="SALES_REVENUE",
            )
        )

        accounts_receivable = (
            ChartOfAccountService
            .get_system_account(
                organization=organization,
                system_key=(
                    "ACCOUNTS_RECEIVABLE"
                ),
            )
        )

        output_tax_payable = None

        if credit_note.tax_amount > 0:
            output_tax_payable = (
                ChartOfAccountService
                .get_system_account(
                    organization=organization,
                    system_key=(
                        "OUTPUT_TAX"
                    ),
                )
            )

        # ==============================================
        # BUILD JOURNAL LINES
        # ==============================================

        raw_lines = []

        # ----------------------------------------------
        # DR SALES REVENUE
        # ----------------------------------------------

        if credit_note.subtotal > 0:
            raw_lines.append(
                {
                    "account":
                        sales_revenue,

                    "description": (
                        "Sales reversal for "
                        f"{credit_note.credit_note_number}"
                    ),

                    "debit":
                        credit_note.subtotal,

                    "credit":
                        "0.00",
                }
            )

        # ----------------------------------------------
        # DR OUTPUT TAX PAYABLE
        # ----------------------------------------------

        if credit_note.tax_amount > 0:
            raw_lines.append(
                {
                    "account":
                        output_tax_payable,

                    "description": (
                        "Output tax reversal for "
                        f"{credit_note.credit_note_number}"
                    ),

                    "debit":
                        credit_note.tax_amount,

                    "credit":
                        "0.00",
                }
            )

        # ----------------------------------------------
        # CR ACCOUNTS RECEIVABLE
        # ----------------------------------------------

        raw_lines.append(
            {
                "account":
                    accounts_receivable,

                "description": (
                    "Customer receivable reduction "
                    f"for {credit_note.credit_note_number}"
                ),

                "debit":
                    "0.00",

                "credit":
                    credit_note.total_amount,
            }
        )

        # ==============================================
        # CREATE JOURNAL
        # ==============================================

        journal = (
            JournalEntryService
            .create_journal(
                user=user,
                organization=organization,
                journal_date=(
                    credit_note.credit_note_date
                ),
                description=(
                    "Sales credit note "
                    f"{credit_note.credit_note_number}"
                ),
                source_type="SALES_CREDIT_NOTE",
                source_id=str(
                    credit_note.id
                ),
                raw_lines=raw_lines,
            )
        )

        # ==============================================
        # POST JOURNAL
        # ==============================================

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
    def issue_credit_note(
        *,
        user,
        organization,
        credit_note,
    ):
        """
        Issue a draft credit note and post
        the corresponding accounting journal.
        """

        CreditNoteService._check_permission(
            user,
            "credit_notes.issue",
        )

        CreditNoteService._check_organization(
            user,
            organization,
        )

        if not credit_note:
            raise ValueError(
                "Credit note is required."
            )

        if (
            credit_note.organization.id
            != organization.id
        ):
            raise PermissionError(
                "Credit note does not belong "
                "to this organization."
            )

        if credit_note.status != "DRAFT":
            raise ValueError(
                "Only draft credit notes "
                "can be issued."
            )

        # ==============================================
        # SALES RETURN VALIDATION
        # ==============================================

        sales_return = (
            credit_note.sales_return
        )

        if not sales_return:
            raise ValueError(
                "Credit note has no "
                "sales return."
            )

        if (
            sales_return.status
            != "CONFIRMED"
        ):
            raise ValueError(
                "Sales return must be "
                "confirmed before issuing "
                "the credit note."
            )

        # ==============================================
        # INVOICE VALIDATION
        # ==============================================

        invoice = credit_note.invoice

        if not invoice:
            raise ValueError(
                "Credit note has no invoice."
            )

        if (
            invoice.organization.id
            != organization.id
        ):
            raise PermissionError(
                "Invoice does not belong "
                "to this organization."
            )

        if (
            credit_note.customer.id
            != invoice.customer.id
        ):
            raise ValueError(
                "Credit note customer does "
                "not match invoice customer."
            )

        if (
            sales_return.invoice.id
            != invoice.id
        ):
            raise ValueError(
                "Sales return invoice does "
                "not match credit note invoice."
            )

        if (
            sales_return.id
            != credit_note.sales_return.id
        ):
            raise ValueError(
                "Invalid credit note "
                "sales return."
            )

        if credit_note.total_amount <= 0:
            raise ValueError(
                "Credit note total must be "
                "greater than zero."
            )

        # ==============================================
        # DETERMINE CREDIT APPLICATION
        # ==============================================

        existing_applied_credit = (
            CreditNoteService
            .get_invoice_applied_credit(
                organization=organization,
                invoice=invoice,
                exclude_credit_note=(
                    credit_note
                ),
            )
        )

        available_receivable = (
            invoice.balance_due
            - existing_applied_credit
        )

        if available_receivable < 0:
            available_receivable = (
                Decimal("0")
            )

        applied_amount = min(
            credit_note.total_amount,
            available_receivable,
        )

        remaining_credit = (
            credit_note.total_amount
            - applied_amount
        )

        # ==============================================
        # SAVE ORIGINAL STATE
        # ==============================================

        original_applied = (
            credit_note.applied_amount
        )

        original_remaining = (
            credit_note.remaining_credit
        )

        # ==============================================
        # ISSUE + ACCOUNTING
        # ==============================================

        try:

            credit_note = (
                CreditNoteRepository
                .update_application(
                    credit_note=credit_note,
                    applied_amount=(
                        applied_amount
                    ),
                    remaining_credit=(
                        remaining_credit
                    ),
                )
            )

            credit_note = (
                CreditNoteRepository
                .update_status(
                    credit_note=credit_note,
                    status="ISSUED",
                    issued_at=(
                        datetime.utcnow()
                    ),
                )
            )

            # ==========================================
            # ACCOUNTING INTEGRATION
            # ==========================================

            (
                CreditNoteService
                ._post_credit_note_accounting(
                    user=user,
                    organization=organization,
                    credit_note=credit_note,
                )
            )

        except Exception:

            # ==========================================
            # COMPENSATION
            # ==========================================

            try:
                (
                    CreditNoteRepository
                    .update_status(
                        credit_note=credit_note,
                        status="DRAFT",
                        issued_at=None,
                    )
                )

            except Exception:
                pass

            try:
                (
                    CreditNoteRepository
                    .update_application(
                        credit_note=credit_note,
                        applied_amount=(
                            original_applied
                        ),
                        remaining_credit=(
                            original_remaining
                        ),
                    )
                )

            except Exception:
                pass

            raise

        return credit_note

    @staticmethod
    def cancel_credit_note(
        *,
        user,
        organization,
        credit_note,
    ):
        CreditNoteService._check_permission(
            user,
            "credit_notes.cancel",
        )

        CreditNoteService._check_organization(
            user,
            organization,
        )

        if not credit_note:
            raise ValueError(
                "Credit note is required."
            )

        if (
            credit_note.organization.id
            != organization.id
        ):
            raise PermissionError(
                "Credit note does not belong "
                "to this organization."
            )

        if credit_note.status == "CANCELLED":
            raise ValueError(
                "Credit note is already cancelled."
            )

        if credit_note.status == "ISSUED":
            raise ValueError(
                "Issued credit notes cannot be "
                "cancelled directly."
            )

        if credit_note.status != "DRAFT":
            raise ValueError(
                "Only draft credit notes "
                "can be cancelled."
            )

        if (
            credit_note.applied_amount
            != Decimal("0")
        ):
            raise ValueError(
                "Credit note with an applied "
                "amount cannot be cancelled."
            )

        return (
            CreditNoteRepository
            .update_status(
                credit_note=credit_note,
                status="CANCELLED",
                cancelled_at=(
                    datetime.utcnow()
                ),
            )
        )