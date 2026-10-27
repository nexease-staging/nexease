from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from apps.authorization.services import (
    AuthorizationService,
)

from apps.purchasing.models import (
    VendorBillItem,
)

from apps.purchasing.repositories.vendor_bill_repository import (
    VendorBillRepository,
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

class VendorBillService:

    VALID_STATUSES = {
        "DRAFT",
        "POSTED",
        "PARTIALLY_PAID",
        "PAID",
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
    def _generate_bill_number():
        return (
            "BILL-"
            + uuid4().hex[:12].upper()
        )

    @staticmethod
    def generate_from_purchase_order(
        *,
        user,
        organization,
        purchase_order,
        supplier_invoice_number="",
        bill_date=None,
        due_date=None,
        notes="",
    ):
        VendorBillService._check_permission(
            user,
            "bills.create",
        )

        VendorBillService._check_organization(
            user,
            organization,
        )

        if not purchase_order:
            raise ValueError(
                "Purchase order is required."
            )

        if (
            purchase_order.organization.id
            != organization.id
        ):
            raise PermissionError(
                "Purchase order does not belong "
                "to this organization."
            )

        if purchase_order.status != "RECEIVED":
            raise ValueError(
                "Vendor bill can only be generated "
                "from a fully received purchase order."
            )

        supplier = purchase_order.supplier

        if not supplier:
            raise ValueError(
                "Purchase order has no supplier."
            )

        if (
            supplier.organization.id
            != organization.id
        ):
            raise PermissionError(
                "Supplier does not belong "
                "to this organization."
            )

        supplier_invoice_number = (
            supplier_invoice_number.strip()
        )

        if supplier_invoice_number:
            existing = (
                VendorBillRepository
                .get_by_supplier_invoice_number(
                    organization=organization,
                    supplier=supplier,
                    supplier_invoice_number=(
                        supplier_invoice_number
                    ),
                )
            )

            if existing:
                raise ValueError(
                    "Supplier invoice number "
                    "already exists for this supplier."
                )

        existing_po_bills = (
            VendorBillRepository
            .list_by_purchase_order(
                organization=organization,
                purchase_order=purchase_order,
            )
        )

        active_po_bill = (
            existing_po_bills.filter(
                status__ne="CANCELLED"
            ).first()
        )

        if active_po_bill:
            raise ValueError(
                "An active vendor bill already "
                "exists for this purchase order."
            )

        if not purchase_order.items:
            raise ValueError(
                "Purchase order has no items."
            )

        bill_items = []

        subtotal = Decimal("0")
        tax_amount = Decimal("0")
        discount_amount = Decimal("0")
        total_amount = Decimal("0")

        for po_item in purchase_order.items:
            quantity = Decimal(
                str(po_item.received_quantity)
            )

            if quantity <= 0:
                continue

            unit_price = Decimal(
                str(po_item.unit_price)
            )

            tax_rate = Decimal(
                str(po_item.tax_rate)
            )

            discount = Decimal(
                str(po_item.discount)
            )

            line_subtotal = (
                quantity
                * unit_price
            )

            if discount > line_subtotal:
                raise ValueError(
                    "Item discount cannot exceed "
                    "line subtotal."
                )

            taxable_amount = (
                line_subtotal
                - discount
            )

            line_tax = (
                taxable_amount
                * tax_rate
                / Decimal("100")
            )

            line_total = (
                taxable_amount
                + line_tax
            )

            bill_item = VendorBillItem(
                product=po_item.product,
                quantity=quantity,
                unit_price=unit_price,
                tax_rate=tax_rate,
                discount=discount,
                line_subtotal=line_subtotal,
                line_tax=line_tax,
                line_total=line_total,
            )

            bill_items.append(
                bill_item
            )

            subtotal += line_subtotal
            discount_amount += discount
            tax_amount += line_tax
            total_amount += line_total

        if not bill_items:
            raise ValueError(
                "Purchase order has no received "
                "items to bill."
            )

        if bill_date is None:
            bill_date = datetime.utcnow()

        bill_number = (
            VendorBillService
            ._generate_bill_number()
        )

        bill = (
            VendorBillRepository
            .create_vendor_bill(
                organization=organization,
                bill_number=bill_number,
                supplier_invoice_number=(
                    supplier_invoice_number
                ),
                purchase_order=purchase_order,
                supplier=supplier,
                bill_date=bill_date,
                due_date=due_date,
                items=bill_items,
                subtotal=subtotal,
                tax_amount=tax_amount,
                discount_amount=(
                    discount_amount
                ),
                total_amount=total_amount,
                supplier_name=(
                    supplier.name
                ),
                supplier_address=(
                    supplier.address
                ),
                supplier_city=(
                    supplier.city
                ),
                supplier_state=(
                    supplier.state
                ),
                supplier_country=(
                    supplier.country
                ),
                supplier_pincode=(
                    supplier.pincode
                ),
                supplier_gstin=(
                    supplier.gstin
                ),
                notes=notes.strip(),
                created_by=user,
                status="DRAFT",
            )
        )

        return bill
    
    @staticmethod
    def _post_vendor_bill_accounting(
        *,
        user,
        organization,
        bill,
    ):
        """
        Create and post accounting for a
        posted vendor bill.

        Dr Purchase Expense
        Dr Input Tax Credit
            Cr Accounts Payable
        """

        if not bill:
            raise ValueError(
                "Vendor bill is required."
            )

        if (
            bill.organization.id
            != organization.id
        ):
            raise PermissionError(
                "Vendor bill does not belong "
                "to this organization."
            )

        if bill.total_amount <= 0:
            raise ValueError(
                "Vendor bill total must be "
                "greater than zero."
            )

        # ==================================================
        # DUPLICATE JOURNAL PROTECTION
        # ==================================================

        existing_journal = (
            JournalEntryRepository
            .get_by_source(
                organization=organization,
                source_type="VENDOR_BILL",
                source_id=str(
                    bill.id
                ),
            )
        )

        if existing_journal:
            return existing_journal

        # ==================================================
        # GET SYSTEM ACCOUNTS
        # ==================================================

        purchase_expense = (
            ChartOfAccountService
            .get_system_account(
                organization=organization,
                system_key="PURCHASE_EXPENSE",
            )
        )

        accounts_payable = (
            ChartOfAccountService
            .get_system_account(
                organization=organization,
                system_key="ACCOUNTS_PAYABLE",
            )
        )

        input_tax = None

        if bill.tax_amount > 0:
            input_tax = (
                ChartOfAccountService
                .get_system_account(
                    organization=organization,
                    system_key="INPUT_TAX",
                )
            )

        # ==================================================
        # CALCULATE NET PURCHASE
        # ==================================================

        net_purchase_amount = (
            bill.subtotal
            - bill.discount_amount
        )

        if net_purchase_amount < 0:
            raise ValueError(
                "Vendor bill discount cannot "
                "exceed subtotal."
            )

        # ==================================================
        # ACCOUNTING INTEGRITY
        # ==================================================

        expected_total = (
            net_purchase_amount
            + bill.tax_amount
        )

        if expected_total != bill.total_amount:
            raise ValueError(
                "Vendor bill accounting totals "
                "do not match bill total."
            )

        # ==================================================
        # BUILD JOURNAL LINES
        # ==================================================

        raw_lines = []

        if net_purchase_amount > 0:

            raw_lines.append(
                {
                    "account":
                        purchase_expense,

                    "description": (
                        "Purchase expense for "
                        f"{bill.bill_number}"
                    ),

                    "debit":
                        net_purchase_amount,

                    "credit":
                        "0.00",
                }
            )

        if bill.tax_amount > 0:

            raw_lines.append(
                {
                    "account":
                        input_tax,

                    "description": (
                        "Input tax credit for "
                        f"{bill.bill_number}"
                    ),

                    "debit":
                        bill.tax_amount,

                    "credit":
                        "0.00",
                }
            )

        raw_lines.append(
            {
                "account":
                    accounts_payable,

                "description": (
                    "Supplier payable for "
                    f"{bill.bill_number}"
                ),

                "debit":
                    "0.00",

                "credit":
                    bill.total_amount,
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
                journal_date=bill.bill_date,
                description=(
                    "Vendor bill "
                    f"{bill.bill_number}"
                ),
                source_type="VENDOR_BILL",
                source_id=str(
                    bill.id
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
    def post_bill(
        *,
        user,
        organization,
        bill,
    ):
        """
        Post a draft vendor bill and create
        the corresponding accounting journal.
        """

        VendorBillService._check_permission(
            user,
            "bills.post",
        )

        VendorBillService._check_organization(
            user,
            organization,
        )

        if not bill:
            raise ValueError(
                "Vendor bill is required."
            )

        if (
            bill.organization.id
            != organization.id
        ):
            raise PermissionError(
                "Vendor bill does not belong "
                "to this organization."
            )

        if bill.status != "DRAFT":
            raise ValueError(
                "Only DRAFT vendor bills "
                "can be posted."
            )

        if bill.total_amount <= 0:
            raise ValueError(
                "Vendor bill total must "
                "be greater than zero."
            )

        # ==================================================
        # VALIDATE ACCOUNTING TOTALS BEFORE POSTING
        # ==================================================

        net_purchase_amount = (
            bill.subtotal
            - bill.discount_amount
        )

        expected_total = (
            net_purchase_amount
            + bill.tax_amount
        )

        if net_purchase_amount < 0:
            raise ValueError(
                "Vendor bill discount cannot "
                "exceed subtotal."
            )

        if expected_total != bill.total_amount:
            raise ValueError(
                "Vendor bill accounting totals "
                "do not match bill total."
            )

        # ==================================================
        # ORIGINAL STATE FOR COMPENSATION
        # ==================================================

        original_amount_paid = (
            bill.amount_paid
        )

        original_balance_due = (
            bill.balance_due
        )

        original_status = (
            bill.status
        )

        original_posted_at = (
            bill.posted_at
        )

        # ==================================================
        # POST BILL
        # ==================================================

        try:

            bill.amount_paid = Decimal("0")

            bill.balance_due = (
                bill.total_amount
            )

            bill = (
                VendorBillRepository
                .update_status(
                    bill=bill,
                    status="POSTED",
                    posted_at=datetime.utcnow(),
                )
            )

            # ==============================================
            # ACCOUNTING
            # ==============================================

            (
                VendorBillService
                ._post_vendor_bill_accounting(
                    user=user,
                    organization=organization,
                    bill=bill,
                )
            )

        except Exception:

            # ==============================================
            # COMPENSATION
            # ==============================================

            try:

                bill.amount_paid = (
                    original_amount_paid
                )

                bill.balance_due = (
                    original_balance_due
                )

                bill.save()

            except Exception:
                pass

            try:

                bill = (
                    VendorBillRepository
                    .update_status(
                        bill=bill,
                        status=original_status,
                        posted_at=(
                            original_posted_at
                        ),
                    )
                )

            except Exception:
                pass

            raise

        return bill

    @staticmethod
    def cancel_bill(
        *,
        user,
        organization,
        bill,
    ):
        VendorBillService._check_permission(
            user,
            "bills.cancel",
        )

        VendorBillService._check_organization(
            user,
            organization,
        )

        if not bill:
            raise ValueError(
                "Vendor bill is required."
            )

        if (
            bill.organization.id
            != organization.id
        ):
            raise PermissionError(
                "Vendor bill does not belong "
                "to this organization."
            )

        if bill.status == "CANCELLED":
            raise ValueError(
                "Vendor bill is already cancelled."
            )

        if bill.status == "PAID":
            raise ValueError(
                "Paid vendor bills cannot "
                "be cancelled."
            )

        if bill.status == "PARTIALLY_PAID":
            raise ValueError(
                "Partially paid vendor bills "
                "cannot be cancelled."
            )

        if bill.amount_paid > Decimal("0"):
            raise ValueError(
                "Vendor bill with payment "
                "history cannot be cancelled."
            )

        if bill.status not in {
            "DRAFT",
            "POSTED",
        }:
            raise ValueError(
                "Vendor bill cannot be cancelled "
                "from its current status."
            )

        bill = (
            VendorBillRepository.update_status(
                bill=bill,
                status="CANCELLED",
                cancelled_at=datetime.utcnow(),
            )
        )

        return bill