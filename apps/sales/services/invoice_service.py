from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4
from apps.sales.repositories.credit_note_repository import (
    CreditNoteRepository,
)
from apps.authorization.services import (
    AuthorizationService,
)

from apps.sales.models import (
    InvoiceItem,
)

from apps.sales.repositories.invoice_repository import (
    InvoiceRepository,
)
from apps.finance.services.chart_of_account_service import (
    ChartOfAccountService,
)

from apps.finance.services.journal_entry_service import (
    JournalEntryService,
)

class InvoiceService:

    VALID_STATUSES = {
        "DRAFT",
        "ISSUED",
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

        if user.organization.id != organization.id:
            raise PermissionError(
                "User does not belong to this organization."
            )

    @staticmethod
    def _generate_invoice_number():
        return (
            "INV-"
            + uuid4().hex[:12].upper()
        )

    @staticmethod
    def generate_from_sales_order(
        *,
        user,
        organization,
        sales_order,
        invoice_date=None,
        due_date=None,
        notes="",
        invoice_number=None,
        billing_details=None,
    ):
        """
        Generate a draft invoice from a fulfilled sales order.
        """

        InvoiceService._check_permission(
            user,
            "invoices.create",
        )

        InvoiceService._check_organization(
            user,
            organization,
        )

        if not sales_order:
            raise ValueError(
                "Sales order is required."
            )

        if (
            sales_order.organization.id
            != organization.id
        ):
            raise PermissionError(
                "Sales order does not belong to this organization."
            )

        if sales_order.status != "FULFILLED":
            raise ValueError(
                "Invoice can only be generated "
                "from a fulfilled sales order."
            )

        existing_invoice = (
            InvoiceRepository
            .get_by_sales_order(
                organization=organization,
                sales_order=sales_order,
            )
        )

        if existing_invoice:
            raise ValueError(
                "Invoice already exists for this sales order."
            )

        customer = (
            sales_order.customer
        )

        if not customer:
            raise ValueError(
                "Sales order has no customer."
            )

        if (
            customer.organization.id
            != organization.id
        ):
            raise PermissionError(
                "Customer does not belong to this organization."
            )

        if invoice_date is None:
            invoice_date = (
                datetime.utcnow()
            )

        if due_date is None:
            due_date = (
                invoice_date
                + timedelta(days=30)
            )

        if due_date < invoice_date:
            raise ValueError(
                "Due date cannot be before invoice date."
            )

        invoice_items = []

        subtotal = Decimal("0")
        tax_amount = Decimal("0")
        discount_amount = Decimal("0")
        total_amount = Decimal("0")

        for sales_item in sales_order.items:

            if (
                sales_item.fulfilled_quantity
                <= 0
            ):
                continue

            # Because we currently allow one invoice
            # only after full SO fulfilment, this should
            # normally equal the ordered quantity.
            invoice_quantity = (
                sales_item.fulfilled_quantity
            )

            line_subtotal = (
                invoice_quantity
                * sales_item.unit_price
            )

            # Current SO discount is stored as
            # an absolute line discount.
            discount = (
                sales_item.discount
            )

            if discount > line_subtotal:
                raise ValueError(
                    f"Invalid discount for product "
                    f"{sales_item.product.sku}."
                )

            taxable_amount = (
                line_subtotal
                - discount
            )

            line_tax = (
                taxable_amount
                * sales_item.tax_rate
                / Decimal("100")
            )

            line_total = (
                taxable_amount
                + line_tax
            )

            invoice_items.append(
                InvoiceItem(
                    item_type=sales_item.product.item_type, hsn_code=sales_item.product.hsn_code, item_name=sales_item.product.name, unit=sales_item.product.unit,
                    product=sales_item.product,
                    quantity=invoice_quantity,
                    unit_price=sales_item.unit_price,
                    tax_rate=sales_item.tax_rate,
                    discount=discount,
                    line_subtotal=line_subtotal,
                    line_tax=line_tax,
                    line_total=line_total,
                )
            )

            subtotal += line_subtotal
            tax_amount += line_tax
            discount_amount += discount
            total_amount += line_total

        if not invoice_items:
            raise ValueError(
                "Sales order has no fulfilled items to invoice."
            )

        if invoice_number is None:
            invoice_number = (
                InvoiceService
                ._generate_invoice_number()
            )
        else:
            invoice_number = (
                str(invoice_number)
                .strip()
                .upper()
            )

            if not invoice_number:
                raise ValueError(
                    "Invoice number is required."
                )

            existing_number = (
                InvoiceRepository
                .get_by_invoice_number(
                    organization=organization,
                    invoice_number=invoice_number,
                )
            )

            if existing_number is not None:
                raise ValueError(
                    "Invoice number already exists."
                )

        details={}
        if billing_details is not None:
            from apps.business.billing import clean_details,settings
            details={**settings(organization),**clean_details(billing_details,organization,invoice_items)}
        return (
            InvoiceRepository
            .create_invoice(
                **({"billing_details":details} if billing_details is not None else {}),
                organization=organization,
                invoice_number=invoice_number,
                sales_order=sales_order,
                customer=customer,
                invoice_date=invoice_date,
                due_date=due_date,
                items=invoice_items,
                subtotal=subtotal,
                tax_amount=tax_amount,
                discount_amount=discount_amount,
                total_amount=total_amount,
                billing_name=customer.name,
                billing_address=(
                    customer.billing_address
                ),
                billing_city=(
                    customer.city
                ),
                billing_state=(
                    customer.state
                ),
                billing_country=(
                    customer.country
                ),
                billing_pincode=(
                    customer.pincode
                ),
                customer_gstin=(
                    customer.gstin
                ),
                notes=notes.strip(),
                created_by=user,
                status="DRAFT",
            )
        )

    @staticmethod
    def issue_invoice(
        *,
        user,
        organization,
        invoice_id,
    ):
        """
        Issue a draft invoice
        and create the accounting journal.
        """

        InvoiceService._check_permission(
            user,
            "invoices.issue",
        )

        InvoiceService._check_organization(
            user,
            organization,
        )

        invoice = (
            InvoiceRepository.get_by_id(
                organization=organization,
                invoice_id=invoice_id,
            )
        )

        if not invoice:
            raise ValueError(
                "Invoice not found."
            )

        if invoice.status != "DRAFT":
            raise ValueError(
                "Only draft invoices can be issued."
            )

        if invoice.total_amount <= 0:
            raise ValueError(
                "Invoice total must be greater than zero."
            )

        if (
            invoice.balance_due
            != invoice.total_amount
        ):
            raise ValueError(
                "Draft invoice balance is invalid."
            )

        issued_at = datetime.utcnow()

        invoice = (
            InvoiceRepository.update_status(
                invoice=invoice,
                status="ISSUED",
                issued_at=issued_at,
            )
        )

        # ==============================================
        # ACCOUNTING INTEGRATION
        # ==============================================

        try:
            (
                InvoiceService
                ._post_invoice_accounting(
                    user=user,
                    organization=organization,
                    invoice=invoice,
                )
            )

        except Exception:
            # Restore invoice to DRAFT if
            # accounting posting fails.
            (
                InvoiceRepository.update_status(
                    invoice=invoice,
                    status="DRAFT",
                    issued_at=None,
                )
            )

            raise

        return invoice

    @staticmethod
    def cancel_invoice(
        *,
        user,
        organization,
        invoice_id,
    ):
        """
        Cancel an eligible invoice.
        """

        InvoiceService._check_permission(
            user,
            "invoices.cancel",
        )

        InvoiceService._check_organization(
            user,
            organization,
        )

        invoice = (
            InvoiceRepository.get_by_id(
                organization=organization,
                invoice_id=invoice_id,
            )
        )

        if not invoice:
            raise ValueError(
                "Invoice not found."
            )

        if invoice.status == "CANCELLED":
            raise ValueError(
                "Invoice is already cancelled."
            )

        if invoice.status == "PAID":
            raise ValueError(
                "Paid invoice cannot be cancelled."
            )

        if invoice.status == "PARTIALLY_PAID":
            raise ValueError(
                "Partially paid invoice cannot be cancelled."
            )

        if invoice.amount_paid > 0:
            raise ValueError(
                "Invoice with recorded payments "
                "cannot be cancelled."
            )

        if invoice.status not in {
            "DRAFT",
            "ISSUED",
        }:
            raise ValueError(
                "Invoice cannot be cancelled "
                "from its current status."
            )

        return (
            InvoiceRepository.update_status(
                invoice=invoice,
                status="CANCELLED",
                cancelled_at=datetime.utcnow(),
            )
        )

    @staticmethod
    def get_customer_outstanding(
        *,
        user,
        organization,
        customer,
    ):
        """
        Calculate outstanding receivables
        for one customer.
        """

        InvoiceService._check_permission(
            user,
            "invoices.read",
        )

        InvoiceService._check_organization(
            user,
            organization,
        )

        if not customer:
            raise ValueError(
                "Customer is required."
            )

        if (
            customer.organization.id
            != organization.id
        ):
            raise PermissionError(
                "Customer does not belong "
                "to this organization."
            )

        invoices = (
            InvoiceRepository.list_outstanding(
                organization=organization,
                customer=customer,
            )
        )

        total_outstanding = Decimal("0")

        invoice_data = []

        for invoice in invoices:
            net_receivable = (
                InvoiceService
                .get_invoice_net_receivable(
                    organization=organization,
                    invoice=invoice,
                )
            )

            if net_receivable <= Decimal("0"):
                continue

            total_outstanding += (
                net_receivable
            )

            invoice_data.append(
                {
                    "id": str(invoice.id),
                    "invoice_number":
                        invoice.invoice_number,
                    "status":
                        invoice.status,
                    "invoice_date":
                        invoice.invoice_date,
                    "due_date":
                        invoice.due_date,
                    "total_amount":
                        invoice.total_amount,
                    "amount_paid":
                        invoice.amount_paid,
                    "balance_due":
                        invoice.balance_due,
                    "net_receivable":
                        net_receivable,
                }
            )
            
        return {
            "customer": customer,
            "invoice_count":
                len(invoice_data),
            "total_outstanding":
                total_outstanding,
            "invoices":
                invoice_data,
        }

    @staticmethod
    def get_organization_receivables(
        *,
        user,
        organization,
    ):
        """
        Calculate total outstanding
        receivables for the organization.
        """

        InvoiceService._check_permission(
            user,
            "invoices.read",
        )

        InvoiceService._check_organization(
            user,
            organization,
        )

        invoices = (
            InvoiceRepository.list_outstanding(
                organization=organization,
            )
        )

        total_outstanding = Decimal("0")

        customer_totals = {}

        invoice_count = 0

        for invoice in invoices:
            net_receivable = (
                InvoiceService
                .get_invoice_net_receivable(
                    organization=organization,
                    invoice=invoice,
                )
            )

            if net_receivable <= Decimal("0"):
                continue

            invoice_count += 1

            total_outstanding += (
                net_receivable
            )

            customer_id = str(
                invoice.customer.id
            )

            if customer_id not in customer_totals:
                customer_totals[
                    customer_id
                ] = {
                    "customer":
                        invoice.customer,
                    "invoice_count": 0,
                    "total_outstanding":
                        Decimal("0"),
                }

            customer_totals[
                customer_id
            ]["invoice_count"] += 1

            customer_totals[
                customer_id
            ]["total_outstanding"] += (
                net_receivable
            )

        return {
            "invoice_count":
                invoice_count,
            "customer_count":
                len(customer_totals),
            "total_outstanding":
                total_outstanding,
            "customers":
                list(
                    customer_totals.values()
                ),
        }

    @staticmethod
    def get_invoice_net_receivable(
        *,
        organization,
        invoice,
    ):
        if not invoice:
            raise ValueError(
                "Invoice is required."
            )

        if (
            invoice.organization.id
            != organization.id
        ):
            raise PermissionError(
                "Invoice does not belong "
                "to this organization."
            )

        issued_credit_notes = (
            CreditNoteRepository
            .list_by_invoice(
                organization=organization,
                invoice=invoice,
            )
        )

        applied_credit = sum(
            (
                credit_note.applied_amount
                for credit_note
                in issued_credit_notes
                if credit_note.status
                == "ISSUED"
            ),
            Decimal("0"),
        )

        net_receivable = (
            invoice.balance_due
            - applied_credit
        )

        if net_receivable < 0:
            return Decimal("0")

        return net_receivable

    @staticmethod
    def _post_invoice_accounting(
        *,
        user,
        organization,
        invoice,
    ):
        if not invoice:
            raise ValueError(
                "Invoice is required."
            )

        if (
            invoice.organization.id
            != organization.id
        ):
            raise PermissionError(
                "Invoice does not belong "
                "to this organization."
            )

        existing_journal = (
            JournalEntryService
            .list_journals(
                user=user,
                organization=organization,
                source_type="SALES_INVOICE",
            )
        )

        existing_journal = next(
            (
                journal
                for journal
                in existing_journal
                if (
                    journal.source_id
                    == str(invoice.id)
                )
            ),
            None,
        )

        if existing_journal:
            return existing_journal

        accounts_receivable = (
            ChartOfAccountService
            .get_system_account(
                organization=organization,
                system_key=(
                    "ACCOUNTS_RECEIVABLE"
                ),
            )
        )

        sales_revenue = (
            ChartOfAccountService
            .get_system_account(
                organization=organization,
                system_key="SALES_REVENUE",
            )
        )

        output_tax = (
            ChartOfAccountService
            .get_system_account(
                organization=organization,
                system_key="OUTPUT_TAX",
            )
        )

        total_amount = (
            invoice.total_amount
        )

        tax_amount = (
            invoice.tax_amount
        )

        revenue_amount = (
            total_amount
            - tax_amount
        )

        raw_lines = [
            {
                "account":
                    accounts_receivable,

                "description": (
                    "Accounts receivable for "
                    f"{invoice.invoice_number}"
                ),

                "debit":
                    total_amount,

                "credit":
                    "0.00",
            },
            {
                "account":
                    sales_revenue,

                "description": (
                    "Sales revenue for "
                    f"{invoice.invoice_number}"
                ),

                "debit":
                    "0.00",

                "credit":
                    revenue_amount,
            },
        ]

        if tax_amount > 0:
            raw_lines.append(
                {
                    "account":
                        output_tax,

                    "description": (
                        "Output tax for "
                        f"{invoice.invoice_number}"
                    ),

                    "debit":
                        "0.00",

                    "credit":
                        tax_amount,
                }
            )

        from apps.business.billing import invoice_account, tax_heads
        service_value=sum((i.line_subtotal-i.discount for i in invoice.items if i.item_type=='service'),Decimal(0))
        if service_value:
            raw_lines[1]['credit']=revenue_amount-service_value
            if not raw_lines[1]['credit']:raw_lines.pop(1)
            raw_lines.append({'account':invoice_account(organization,user,'SERVICE_REVENUE'),'description':'Service revenue '+invoice.invoice_number,'debit':'0.00','credit':service_value})
        if tax_amount>0 and invoice.billing_details.get('tax_reviewed'):
            raw_lines=[line for line in raw_lines if line['account'].id!=output_tax.id]
            for key,value in zip(('OUTPUT_CGST','OUTPUT_SGST','OUTPUT_IGST'),tax_heads(invoice)):
                if value:raw_lines.append({'account':invoice_account(organization,user,key),'description':key+' '+invoice.invoice_number,'debit':'0.00','credit':value})

        journal = (
            JournalEntryService
            .create_journal(
                user=user,
                organization=organization,
                journal_date=(
                    invoice.invoice_date
                ),
                description=(
                    "Sales invoice "
                    f"{invoice.invoice_number}"
                ),
                source_type=(
                    "SALES_INVOICE"
                ),
                source_id=str(
                    invoice.id
                ),
                raw_lines=(
                    raw_lines
                ),
            )
        )

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