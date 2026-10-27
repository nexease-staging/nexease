from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from uuid import uuid4

from apps.purchasing.models import (
    VendorDebitNoteItem,
)

from apps.purchasing.repositories.vendor_debit_note_repository import (
    VendorDebitNoteRepository,
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

class VendorDebitNoteService:

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
        if not user.has_permission(
            permission_code
        ):
            raise PermissionError(
                "Permission denied."
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

        if (
            not user.organization
            or user.organization.id
            != organization.id
        ):
            raise PermissionError(
                "User does not belong "
                "to this organization."
            )

    @staticmethod
    def _generate_debit_note_number():
        return (
            "DN-"
            + uuid4().hex[
                :12
            ].upper()
        )

    @staticmethod
    def create_from_purchase_return(
        *,
        user,
        organization,
        purchase_return,
        debit_note_date=None,
        reason="",
        notes="",
    ):
        VendorDebitNoteService._check_permission(
            user,
            "vendor_debit_notes.create",
        )

        VendorDebitNoteService._check_organization(
            user,
            organization,
        )

        if not purchase_return:
            raise ValueError(
                "Purchase return is required."
            )

        if (
            purchase_return.organization.id
            != organization.id
        ):
            raise PermissionError(
                "Purchase return does not "
                "belong to this organization."
            )

        if (
            purchase_return.status
            != "CONFIRMED"
        ):
            raise ValueError(
                "Only confirmed purchase "
                "returns can create "
                "vendor debit notes."
            )

        existing = (
            VendorDebitNoteRepository
            .get_by_purchase_return(
                organization=organization,
                purchase_return=(
                    purchase_return
                ),
            )
        )

        if existing:
            raise ValueError(
                "A vendor debit note already "
                "exists for this purchase return."
            )

        vendor_bill = (
            purchase_return.vendor_bill
        )

        purchase_order = (
            purchase_return.purchase_order
        )

        supplier = (
            purchase_return.supplier
        )

        if not vendor_bill:
            raise ValueError(
                "Purchase return has no "
                "vendor bill."
            )

        if not purchase_order:
            raise ValueError(
                "Purchase return has no "
                "purchase order."
            )

        if not supplier:
            raise ValueError(
                "Purchase return has no supplier."
            )

        if (
            vendor_bill.organization.id
            != organization.id
        ):
            raise PermissionError(
                "Vendor bill does not belong "
                "to this organization."
            )

        if (
            purchase_order.organization.id
            != organization.id
        ):
            raise PermissionError(
                "Purchase order does not belong "
                "to this organization."
            )

        if (
            supplier.organization.id
            != organization.id
        ):
            raise PermissionError(
                "Supplier does not belong "
                "to this organization."
            )

        if (
            not vendor_bill.purchase_order
            or vendor_bill.purchase_order.id
            != purchase_order.id
        ):
            raise ValueError(
                "Vendor bill does not match "
                "the purchase order."
            )

        if (
            purchase_order.supplier.id
            != supplier.id
        ):
            raise ValueError(
                "Supplier does not match "
                "the purchase order."
            )

        if not purchase_return.items:
            raise ValueError(
                "Purchase return has no items."
            )
        debit_note_items = []

        subtotal = Decimal("0")
        tax_amount = Decimal("0")
        discount_amount = Decimal("0")
        total_amount = Decimal("0")

        for return_item in purchase_return.items:
            if (
                return_item.product.organization.id
                != organization.id
            ):
                raise PermissionError(
                    "Product does not belong "
                    "to this organization."
                )

            item = VendorDebitNoteItem(
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

            debit_note_items.append(
                item
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

        if total_amount <= Decimal("0"):
            raise ValueError(
                "Vendor debit note total "
                "must be greater than zero."
            )

        if (
            subtotal
            != purchase_return.subtotal
            or tax_amount
            != purchase_return.tax_amount
            or discount_amount
            != purchase_return.discount_amount
            or total_amount
            != purchase_return.total_amount
        ):
            raise ValueError(
                "Purchase return financial "
                "totals are inconsistent."
            )

        if debit_note_date is None:
            debit_note_date = (
                datetime.utcnow()
            )

        debit_note_number = (
            VendorDebitNoteService
            ._generate_debit_note_number()
        )

        return (
            VendorDebitNoteRepository
            .create_debit_note(
                organization=organization,
                debit_note_number=(
                    debit_note_number
                ),
                purchase_return=(
                    purchase_return
                ),
                vendor_bill=vendor_bill,
                purchase_order=(
                    purchase_order
                ),
                supplier=supplier,
                debit_note_date=(
                    debit_note_date
                ),
                items=debit_note_items,
                subtotal=subtotal,
                tax_amount=tax_amount,
                discount_amount=(
                    discount_amount
                ),
                total_amount=total_amount,
                reason=reason.strip(),
                notes=notes.strip(),
                created_by=user,
                status="DRAFT",
            )
        )

    @staticmethod
    def get_vendor_bill_applied_debit(
        *,
        organization,
        vendor_bill,
        exclude_debit_note=None,
    ):
        debit_notes = (
            VendorDebitNoteRepository
            .list_by_vendor_bill(
                organization=organization,
                vendor_bill=vendor_bill,
            )
        )

        total = Decimal("0")

        for debit_note in debit_notes:
            if debit_note.status != "ISSUED":
                continue

            if (
                exclude_debit_note
                and debit_note.id
                == exclude_debit_note.id
            ):
                continue

            total += (
                debit_note.applied_amount
            )

        return total

    @staticmethod
    def get_vendor_bill_net_payable(
        *,
        organization,
        vendor_bill,
    ):
        applied_debit = (
            VendorDebitNoteService
            .get_vendor_bill_applied_debit(
                organization=organization,
                vendor_bill=vendor_bill,
            )
        )

        net_payable = (
            vendor_bill.balance_due
            - applied_debit
        )

        if net_payable < 0:
            return Decimal("0")

        return net_payable

    @staticmethod
    def _post_vendor_debit_note_accounting(
        *,
        user,
        organization,
        debit_note,
    ):
        """
        Create and post accounting for the
        applied portion of an issued vendor
        debit note.

        Dr Accounts Payable
            Cr Purchase Expense
            Cr Input Tax
        """

        if not debit_note:
            raise ValueError(
                "Vendor debit note is required."
            )

        if (
            debit_note.organization.id
            != organization.id
        ):
            raise PermissionError(
                "Vendor debit note does not belong "
                "to this organization."
            )

        if debit_note.status != "ISSUED":
            raise ValueError(
                "Only issued vendor debit notes "
                "can create accounting journals."
            )

        if debit_note.total_amount <= 0:
            raise ValueError(
                "Vendor debit note total must "
                "be greater than zero."
            )

        if debit_note.applied_amount <= 0:
            return None

        if (
            debit_note.applied_amount
            > debit_note.total_amount
        ):
            raise ValueError(
                "Applied debit note amount cannot "
                "exceed debit note total."
            )

        # ==================================================
        # DUPLICATE JOURNAL PROTECTION
        # ==================================================

        existing_journal = (
            JournalEntryRepository
            .get_by_source(
                organization=organization,
                source_type="VENDOR_DEBIT_NOTE",
                source_id=str(
                    debit_note.id
                ),
            )
        )

        if existing_journal:
            return existing_journal

        # ==================================================
        # NET PURCHASE VALUE
        # ==================================================

        net_purchase_amount = (
            debit_note.subtotal
            - debit_note.discount_amount
        )

        if net_purchase_amount < 0:
            raise ValueError(
                "Vendor debit note discount cannot "
                "exceed subtotal."
            )

        expected_total = (
            net_purchase_amount
            + debit_note.tax_amount
        )

        if (
            expected_total
            != debit_note.total_amount
        ):
            raise ValueError(
                "Vendor debit note accounting "
                "totals are inconsistent."
            )

        # ==================================================
        # APPLIED RATIO
        # ==================================================

        applied_ratio = (
            debit_note.applied_amount
            / debit_note.total_amount
        )

        # ==================================================
        # PROPORTIONAL REVERSAL
        # ==================================================

        purchase_credit = (
            net_purchase_amount
            * applied_ratio
        ).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

        tax_credit = (
            debit_note.applied_amount
            - purchase_credit
        )

        tax_credit = (
            tax_credit.quantize(
                Decimal("0.01"),
                rounding=ROUND_HALF_UP,
            )
        )

        if purchase_credit < 0:
            raise ValueError(
                "Purchase reversal cannot "
                "be negative."
            )

        if tax_credit < 0:
            raise ValueError(
                "Input tax reversal cannot "
                "be negative."
            )

        if (
            purchase_credit
            + tax_credit
            != debit_note.applied_amount
        ):
            raise ValueError(
                "Vendor debit note journal "
                "does not balance."
            )

        # ==================================================
        # SYSTEM ACCOUNTS
        # ==================================================

        accounts_payable = (
            ChartOfAccountService
            .get_system_account(
                organization=organization,
                system_key="ACCOUNTS_PAYABLE",
            )
        )

        purchase_expense = None

        if purchase_credit > 0:

            purchase_expense = (
                ChartOfAccountService
                .get_system_account(
                    organization=organization,
                    system_key="PURCHASE_EXPENSE",
                )
            )

        input_tax = None

        if tax_credit > 0:

            input_tax = (
                ChartOfAccountService
                .get_system_account(
                    organization=organization,
                    system_key="INPUT_TAX",
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
                    "Vendor debit note "
                    f"{debit_note.debit_note_number}"
                ),

                "debit":
                    debit_note.applied_amount,

                "credit":
                    "0.00",
            }
        ]

        if purchase_credit > 0:

            raw_lines.append(
                {
                    "account":
                        purchase_expense,

                    "description": (
                        "Purchase reversal for "
                        f"{debit_note.debit_note_number}"
                    ),

                    "debit":
                        "0.00",

                    "credit":
                        purchase_credit,
                }
            )

        if tax_credit > 0:

            raw_lines.append(
                {
                    "account":
                        input_tax,

                    "description": (
                        "Input tax reversal for "
                        f"{debit_note.debit_note_number}"
                    ),

                    "debit":
                        "0.00",

                    "credit":
                        tax_credit,
                }
            )

        # ==================================================
        # CREATE JOURNAL
        # ==================================================

        journal = (
            JournalEntryService
            .create_journal(
                user=user,
                organization=organization,
                journal_date=(
                    debit_note.debit_note_date
                ),
                description=(
                    "Vendor debit note "
                    f"{debit_note.debit_note_number}"
                ),
                source_type=(
                    "VENDOR_DEBIT_NOTE"
                ),
                source_id=str(
                    debit_note.id
                ),
                raw_lines=raw_lines,
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
    def issue_debit_note(
        *,
        user,
        organization,
        debit_note,
    ):
        """
        Issue a draft vendor debit note
        and create its accounting journal.
        """

        VendorDebitNoteService._check_permission(
            user,
            "vendor_debit_notes.issue",
        )

        VendorDebitNoteService._check_organization(
            user,
            organization,
        )

        if not debit_note:
            raise ValueError(
                "Vendor debit note is required."
            )

        if (
            debit_note.organization.id
            != organization.id
        ):
            raise PermissionError(
                "Vendor debit note does not "
                "belong to this organization."
            )

        if debit_note.status != "DRAFT":
            raise ValueError(
                "Only draft vendor debit notes "
                "can be issued."
            )

        # ==================================================
        # PURCHASE RETURN
        # ==================================================

        purchase_return = (
            debit_note.purchase_return
        )

        if (
            not purchase_return
            or
            purchase_return.status
            != "CONFIRMED"
        ):
            raise ValueError(
                "Purchase return must be confirmed "
                "before issuing the debit note."
            )

        # ==================================================
        # VENDOR BILL
        # ==================================================

        vendor_bill = (
            debit_note.vendor_bill
        )

        if not vendor_bill:
            raise ValueError(
                "Debit note has no vendor bill."
            )

        if (
            vendor_bill.organization.id
            != organization.id
        ):
            raise PermissionError(
                "Vendor bill does not belong "
                "to this organization."
            )

        # ==================================================
        # CURRENT APPLIED DEBIT
        # ==================================================

        existing_applied = (
            VendorDebitNoteService
            .get_vendor_bill_applied_debit(
                organization=organization,
                vendor_bill=vendor_bill,
                exclude_debit_note=(
                    debit_note
                ),
            )
        )

        # ==================================================
        # AVAILABLE PAYABLE
        # ==================================================

        available_payable = (
            vendor_bill.balance_due
            - existing_applied
        )

        if available_payable < 0:
            available_payable = (
                Decimal("0")
            )

        # ==================================================
        # APPLICATION
        # ==================================================

        applied_amount = min(
            debit_note.total_amount,
            available_payable,
        )

        remaining_credit = (
            debit_note.total_amount
            - applied_amount
        )

        # ==================================================
        # ORIGINAL STATE
        # ==================================================

        original_applied = (
            debit_note.applied_amount
        )

        original_remaining = (
            debit_note.remaining_credit
        )

        original_status = (
            debit_note.status
        )

        original_issued_at = (
            debit_note.issued_at
        )

        accounting_journal = None

        try:

            # ==============================================
            # UPDATE APPLICATION
            # ==============================================

            debit_note = (
                VendorDebitNoteRepository
                .update_application(
                    debit_note=debit_note,
                    applied_amount=(
                        applied_amount
                    ),
                    remaining_credit=(
                        remaining_credit
                    ),
                )
            )

            # ==============================================
            # ISSUE
            # ==============================================

            debit_note = (
                VendorDebitNoteRepository
                .update_status(
                    debit_note=debit_note,
                    status="ISSUED",
                    issued_at=(
                        datetime.utcnow()
                    ),
                )
            )

            # ==============================================
            # ACCOUNTING
            # ==============================================

            accounting_journal = (
                VendorDebitNoteService
                ._post_vendor_debit_note_accounting(
                    user=user,
                    organization=organization,
                    debit_note=debit_note,
                )
            )

        except Exception:

            # ==============================================
            # ROLLBACK JOURNAL
            # ==============================================

            if accounting_journal:

                try:
                    accounting_journal.delete()

                except Exception:
                    pass

            # ==============================================
            # ROLLBACK STATUS
            # ==============================================

            try:

                debit_note = (
                    VendorDebitNoteRepository
                    .update_status(
                        debit_note=debit_note,
                        status=original_status,
                        issued_at=(
                            original_issued_at
                        ),
                    )
                )

            except Exception:
                pass

            # ==============================================
            # ROLLBACK APPLICATION
            # ==============================================

            try:

                debit_note = (
                    VendorDebitNoteRepository
                    .update_application(
                        debit_note=debit_note,
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

        return debit_note

    @staticmethod
    def cancel_debit_note(
        *,
        user,
        organization,
        debit_note,
    ):
        VendorDebitNoteService._check_permission(
            user,
            "vendor_debit_notes.cancel",
        )

        VendorDebitNoteService._check_organization(
            user,
            organization,
        )

        if not debit_note:
            raise ValueError(
                "Vendor debit note is required."
            )

        if (
            debit_note.organization.id
            != organization.id
        ):
            raise PermissionError(
                "Vendor debit note does not "
                "belong to this organization."
            )

        if debit_note.status == "ISSUED":
            raise ValueError(
                "Issued vendor debit notes "
                "cannot be cancelled directly."
            )

        if debit_note.status == "CANCELLED":
            raise ValueError(
                "Vendor debit note is already "
                "cancelled."
            )

        if debit_note.status != "DRAFT":
            raise ValueError(
                "Only draft vendor debit notes "
                "can be cancelled."
            )

        if (
            debit_note.applied_amount
            != Decimal("0")
        ):
            raise ValueError(
                "Debit note with applied amount "
                "cannot be cancelled."
            )

        return (
            VendorDebitNoteRepository
            .update_status(
                debit_note=debit_note,
                status="CANCELLED",
                cancelled_at=(
                    datetime.utcnow()
                ),
            )
        )