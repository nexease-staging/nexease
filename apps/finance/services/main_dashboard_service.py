from datetime import date, datetime, time
from decimal import Decimal
from apps.finance.services.cash_flow_report_service import (
    CashFlowReportService,
)
from apps.finance.models import BankTransaction
from apps.inventory.repositories.stock_movement_repository import (
    StockMovementRepository,
)
from apps.finance.repositories.bank_account_repository import (
    BankAccountRepository,
)
from apps.inventory.repositories.inventory_repository import (
    InventoryRepository,
)
from apps.purchasing.repositories.vendor_bill_repository import (
    VendorBillRepository,
)
from apps.sales.repositories.invoice_repository import (
    InvoiceRepository,
)
from apps.purchasing.services.vendor_bill_api_service import (
    VendorBillAPIService,
)
from apps.sales.services.customer_payment_api_service import (
    CustomerPaymentAPIService,
)

class MainDashboardService:
    """
    Organization-scoped aggregation service for the main IMS dashboard.

    This service provides operational and financial dashboard data without
    replacing the existing dedicated finance/accounting report services.
    """

    ZERO = Decimal("0")

    @staticmethod
    def _to_decimal(value):
        if value is None:
            return MainDashboardService.ZERO

        if isinstance(value, Decimal):
            return value

        return Decimal(str(value))

    @staticmethod
    def _start_of_day(value):
        return datetime.combine(
            value,
            time.min,
        )

    @staticmethod
    def _as_datetime(value):
        if value is None:
            return datetime.min

        if isinstance(
            value,
            datetime,
        ):
            return value

        if isinstance(
            value,
            date,
        ):
            return datetime.combine(
                value,
                time.min,
            )

        raise ValueError(
            "Expected date or datetime value."
        )

    @staticmethod
    def _as_date(value):
        if value is None:
            return None

        if isinstance(
            value,
            datetime,
        ):
            return value.date()

        if isinstance(
            value,
            date,
        ):
            return value

        raise ValueError(
            "Expected date or datetime value."
        )

    @staticmethod
    def _end_of_day(value):
        return datetime.combine(
            value,
            time.max,
        )

    @staticmethod
    def _normalize_period(
        *,
        start_date=None,
        end_date=None,
    ):
        today = date.today()

        normalized_end = end_date or today

        normalized_start = (
            start_date
            or date(
                normalized_end.year,
                1,
                1,
            )
        )

        if normalized_start > normalized_end:
            raise ValueError(
                "Start date cannot be after end date."
            )

        return {
            "start_date": normalized_start,
            "end_date": normalized_end,
            "start_datetime": (
                MainDashboardService
                ._start_of_day(
                    normalized_start
                )
            ),
            "end_datetime": (
                MainDashboardService
                ._end_of_day(
                    normalized_end
                )
            ),
        }

    @staticmethod
    def _get_invoices(
        *,
        organization,
    ):
        return (
            InvoiceRepository
            .queryset_for_organization(
                organization=organization,
            )
        )

    @staticmethod
    def _get_vendor_bills(
        *,
        organization,
    ):
        return (
            VendorBillRepository
            .queryset_for_organization(
                organization=organization,
            )
        )

    @staticmethod
    def _get_inventory(
        *,
        organization,
    ):
        return (
            InventoryRepository
            .queryset_for_organization(
                organization=organization,
            )
        )

    @staticmethod
    def _get_bank_accounts(
        *,
        organization,
    ):
        return (
            BankAccountRepository
            .queryset_for_organization(
                organization=organization,
            )
        )

    @staticmethod
    def _get_total_sales(
        *,
        organization,
        period,
    ):
        invoices = (
            MainDashboardService
            ._get_invoices(
                organization=organization,
            )
            .filter(
                invoice_date__gte=(
                    period["start_datetime"]
                ),
                invoice_date__lte=(
                    period["end_datetime"]
                ),
                status__nin=[
                    "DRAFT",
                    "CANCELLED",
                ],
            )
        )

        total = sum(
            (
                MainDashboardService
                ._to_decimal(
                    invoice.total_amount
                )
                for invoice in invoices
            ),
            MainDashboardService.ZERO,
        )

        return total

    @staticmethod
    def _get_total_purchases(
        *,
        organization,
        period,
    ):
        bills = (
            MainDashboardService
            ._get_vendor_bills(
                organization=organization,
            )
            .filter(
                bill_date__gte=(
                    period["start_datetime"]
                ),
                bill_date__lte=(
                    period["end_datetime"]
                ),
                status__nin=[
                    "DRAFT",
                    "CANCELLED",
                ],
            )
        )

        total = sum(
            (
                MainDashboardService
                ._to_decimal(
                    bill.total_amount
                )
                for bill in bills
            ),
            MainDashboardService.ZERO,
        )

        return total

    @staticmethod
    def _get_bank_balance(
        *,
        organization,
    ):
        accounts = (
            MainDashboardService
            ._get_bank_accounts(
                organization=organization,
            )
            .filter(
                is_active=True,
            )
        )

        total = sum(
            (
                MainDashboardService
                ._to_decimal(
                    account.current_balance
                )
                for account in accounts
            ),
            MainDashboardService.ZERO,
        )

        return total

    @staticmethod
    def _get_inventory_summary(
        *,
        organization,
    ):
        inventory_records = (
            MainDashboardService
            ._get_inventory(
                organization=organization,
            )
        )

        inventory_value = (
            MainDashboardService.ZERO
        )

        product_totals = {}

        for inventory in inventory_records:
            quantity = (
                MainDashboardService
                ._to_decimal(
                    inventory.quantity
                )
            )

            reserved_quantity = (
                MainDashboardService
                ._to_decimal(
                    inventory.reserved_quantity
                )
            )

            available_quantity = (
                quantity
                - reserved_quantity
            )

            product = inventory.product

            product_id = str(
                product.id
            )

            if product_id not in product_totals:
                product_totals[product_id] = {
                    "product": product,
                    "quantity": (
                        MainDashboardService.ZERO
                    ),
                    "reserved_quantity": (
                        MainDashboardService.ZERO
                    ),
                    "available_quantity": (
                        MainDashboardService.ZERO
                    ),
                }

            product_totals[
                product_id
            ]["quantity"] += quantity

            product_totals[
                product_id
            ][
                "reserved_quantity"
            ] += reserved_quantity

            product_totals[
                product_id
            ][
                "available_quantity"
            ] += available_quantity

            inventory_value += (
                quantity
                * MainDashboardService
                ._to_decimal(
                    product.cost_price
                )
            )

        out_of_stock_items = 0
        in_stock_items = 0

        for values in (
            product_totals.values()
        ):
            if (
                values[
                    "available_quantity"
                ]
                <= MainDashboardService.ZERO
            ):
                out_of_stock_items += 1
            else:
                in_stock_items += 1

        return {
            "inventory_value":
                inventory_value,
            "in_stock_items":
                in_stock_items,
            "out_of_stock_items":
                out_of_stock_items,
        }

    @staticmethod
    def _get_receivables_summary(
        *,
        organization,
    ):
        result = (
            CustomerPaymentAPIService
            .get_receivable_summary(
                organization=organization,
            )
        )

        return {
            "total_outstanding": (
                MainDashboardService
                ._to_decimal(
                    result[
                        "total_outstanding"
                    ]
                )
            ),
            "total_current": (
                MainDashboardService
                ._to_decimal(
                    result[
                        "total_current"
                    ]
                )
            ),
            "total_overdue": (
                MainDashboardService
                ._to_decimal(
                    result[
                        "total_overdue"
                    ]
                )
            ),
            "invoice_count": result[
                "invoice_count"
            ],
            "overdue_invoice_count": (
                result[
                    "overdue_invoice_count"
                ]
            ),
            "customer_count": result[
                "customer_count"
            ],
        }

    @staticmethod
    def _get_receivable_aging(
        *,
        organization,
    ):
        result = (
            CustomerPaymentAPIService
            .get_aging_summary(
                organization=organization,
            )
        )

        buckets = result["buckets"]

        def amount(bucket_key):
            return (
                MainDashboardService
                ._to_decimal(
                    buckets[
                        bucket_key
                    ]["amount"]
                )
            )

        return {
            "current": (
                amount("current")
            ),
            "1_30": (
                amount("days_1_30")
            ),
            "31_60": (
                amount("days_31_60")
            ),
            "61_90": (
                amount("days_61_90")
            ),
            "90_plus": (
                amount("days_over_90")
            ),
        }

    @staticmethod
    def _get_payables_summary(
        *,
        organization,
    ):
        bills = list(
            VendorBillAPIService
            .list_outstanding(
                organization=organization,
            )
        )

        total_outstanding = sum(
            (
                MainDashboardService
                ._to_decimal(
                    bill.balance_due
                )
                for bill in bills
            ),
            MainDashboardService.ZERO,
        )

        supplier_ids = {
            str(
                bill.supplier.id
            )
            for bill in bills
            if bill.supplier
        }

        return {
            "total_outstanding":
                total_outstanding,
            "bill_count":
                len(bills),
            "supplier_count":
                len(supplier_ids),
        }

    @staticmethod
    def _get_invoice_status_summary(
        *,
        organization,
    ):
        invoices = (
            MainDashboardService
            ._get_invoices(
                organization=organization,
            )
        )

        today = date.today()

        issued = 0
        partially_paid = 0
        paid = 0
        overdue = 0

        for invoice in invoices:
            status = invoice.status

            if status in (
                "DRAFT",
                "CANCELLED",
            ):
                continue

            if status == "ISSUED":
                issued += 1

            elif status == "PARTIALLY_PAID":
                partially_paid += 1

            elif status == "PAID":
                paid += 1

            balance_due = (
                MainDashboardService
                ._to_decimal(
                    invoice.balance_due
                )
            )

            due_date = (
                MainDashboardService
                ._as_date(
                    invoice.due_date
                )
            )

            if (
                balance_due
                > MainDashboardService.ZERO
                and due_date
                and due_date < today
                and status
                not in (
                    "PAID",
                    "CANCELLED",
                )
            ):
                overdue += 1

        return {
            "issued": issued,
            "partially_paid":
                partially_paid,
            "paid": paid,
            "overdue": overdue,
        }

    @staticmethod
    def _get_bill_status_summary(
        *,
        organization,
    ):
        bills = (
            MainDashboardService
            ._get_vendor_bills(
                organization=organization,
            )
        )

        today = date.today()

        posted = 0
        partially_paid = 0
        paid = 0
        overdue = 0

        for bill in bills:
            status = bill.status

            if status in (
                "DRAFT",
                "CANCELLED",
            ):
                continue

            if status == "POSTED":
                posted += 1

            elif status == "PARTIALLY_PAID":
                partially_paid += 1

            elif status == "PAID":
                paid += 1

            balance_due = (
                MainDashboardService
                ._to_decimal(
                    bill.balance_due
                )
            )

            due_date = (
                MainDashboardService
                ._as_date(
                    bill.due_date
                )
            )

            if (
                balance_due
                > MainDashboardService.ZERO
                and due_date
                and due_date < today
                and status
                not in (
                    "PAID",
                    "CANCELLED",
                )
            ):
                overdue += 1

        return {
            "posted": posted,
            "partially_paid":
                partially_paid,
            "paid": paid,
            "overdue": overdue,
        }

    @staticmethod
    def _month_key(value):
        value_date = (
            MainDashboardService
            ._as_date(value)
        )

        return value_date.strftime(
            "%Y-%m"
        )

    @staticmethod
    def _month_range(
        *,
        start_date,
        end_date,
    ):
        current_year = (
            start_date.year
        )
        current_month = (
            start_date.month
        )

        months = []

        while (
            current_year
            < end_date.year
            or (
                current_year
                == end_date.year
                and current_month
                <= end_date.month
            )
        ):
            months.append(
                f"{current_year:04d}-"
                f"{current_month:02d}"
            )

            if current_month == 12:
                current_month = 1
                current_year += 1
            else:
                current_month += 1

        return months

    @staticmethod
    def _get_sales_trend(
        *,
        organization,
        period,
    ):
        months = (
            MainDashboardService
            ._month_range(
                start_date=(
                    period["start_date"]
                ),
                end_date=(
                    period["end_date"]
                ),
            )
        )

        totals = {
            month: (
                MainDashboardService.ZERO
            )
            for month in months
        }

        invoices = (
            MainDashboardService
            ._get_invoices(
                organization=organization,
            )
            .filter(
                invoice_date__gte=(
                    period["start_datetime"]
                ),
                invoice_date__lte=(
                    period["end_datetime"]
                ),
                status__nin=[
                    "DRAFT",
                    "CANCELLED",
                ],
            )
        )

        for invoice in invoices:
            month = (
                MainDashboardService
                ._month_key(
                    invoice.invoice_date
                )
            )

            if month not in totals:
                continue

            totals[month] += (
                MainDashboardService
                ._to_decimal(
                    invoice.total_amount
                )
            )

        return [
            {
                "period": month,
                "amount": (
                    f"{totals[month]:.2f}"
                ),
            }
            for month in months
        ]

    @staticmethod
    def _get_purchase_trend(
        *,
        organization,
        period,
    ):
        months = (
            MainDashboardService
            ._month_range(
                start_date=(
                    period["start_date"]
                ),
                end_date=(
                    period["end_date"]
                ),
            )
        )

        totals = {
            month: (
                MainDashboardService.ZERO
            )
            for month in months
        }

        bills = (
            MainDashboardService
            ._get_vendor_bills(
                organization=organization,
            )
            .filter(
                bill_date__gte=(
                    period["start_datetime"]
                ),
                bill_date__lte=(
                    period["end_datetime"]
                ),
                status__nin=[
                    "DRAFT",
                    "CANCELLED",
                ],
            )
        )

        for bill in bills:
            month = (
                MainDashboardService
                ._month_key(
                    bill.bill_date
                )
            )

            if month not in totals:
                continue

            totals[month] += (
                MainDashboardService
                ._to_decimal(
                    bill.total_amount
                )
            )

        return [
            {
                "period": month,
                "amount": (
                    f"{totals[month]:.2f}"
                ),
            }
            for month in months
        ]

    @staticmethod
    def _get_cash_flow(
        *,
        user,
        organization,
        period,
    ):
        months = (
            MainDashboardService
            ._month_range(
                start_date=(
                    period["start_date"]
                ),
                end_date=(
                    period["end_date"]
                ),
            )
        )

        totals = {
            month: {
                "inflow":
                    MainDashboardService.ZERO,
                "outflow":
                    MainDashboardService.ZERO,
            }
            for month in months
        }

        report = (
            CashFlowReportService
            .get_cash_flow_report(
                user=user,
                organization=organization,
                start_date=(
                    period[
                        "start_date"
                    ].isoformat()
                ),
                end_date=(
                    period[
                        "end_date"
                    ].isoformat()
                ),
            )
        )

        for transaction in report[
            "transactions"
        ]:
            month = (
                MainDashboardService
                ._month_key(
                    transaction[
                        "transaction_date"
                    ]
                )
            )

            if month not in totals:
                continue

            transaction_type = (
                transaction[
                    "transaction_type"
                ]
            )

            amount = (
                MainDashboardService
                ._to_decimal(
                    transaction["amount"]
                )
            )

            if (
                transaction_type
                in CashFlowReportService
                .INFLOW_TYPES
            ):
                totals[
                    month
                ]["inflow"] += amount

            elif (
                transaction_type
                in CashFlowReportService
                .OUTFLOW_TYPES
            ):
                totals[
                    month
                ]["outflow"] += amount

        return [
            {
                "period":
                    month,

                "inflow": (
                    f"{totals[month]['inflow']:.2f}"
                ),

                "outflow": (
                    f"{totals[month]['outflow']:.2f}"
                ),

                "net": (
                    f"{(
                        totals[month]['inflow']
                        -
                        totals[month]['outflow']
                    ):.2f}"
                ),
            }
            for month in months
        ]

    @staticmethod
    def _get_top_customers(
        *,
        organization,
        period,
        limit=5,
    ):
        invoices = (
            MainDashboardService
            ._get_invoices(
                organization=organization,
            )
            .filter(
                invoice_date__gte=(
                    period["start_datetime"]
                ),
                invoice_date__lte=(
                    period["end_datetime"]
                ),
                status__nin=[
                    "DRAFT",
                    "CANCELLED",
                ],
            )
        )

        totals = {}

        for invoice in invoices:
            customer = invoice.customer

            if not customer:
                continue

            customer_id = str(
                customer.id
            )

            if customer_id not in totals:
                totals[
                    customer_id
                ] = {
                    "customer_id":
                        customer_id,
                    "customer_name":
                        customer.name,
                    "amount":
                        MainDashboardService.ZERO,
                }

            totals[
                customer_id
            ]["amount"] += (
                MainDashboardService
                ._to_decimal(
                    invoice.total_amount
                )
            )

        ranked = sorted(
            totals.values(),
            key=lambda item: (
                item["amount"]
            ),
            reverse=True,
        )

        return [
            {
                "customer_id":
                    item["customer_id"],
                "customer_name":
                    item["customer_name"],
                "amount": (
                    f"{item['amount']:.2f}"
                ),
            }
            for item in ranked[:limit]
        ]

    @staticmethod
    def _get_top_suppliers(
        *,
        organization,
        period,
        limit=5,
    ):
        bills = (
            MainDashboardService
            ._get_vendor_bills(
                organization=organization,
            )
            .filter(
                bill_date__gte=(
                    period["start_datetime"]
                ),
                bill_date__lte=(
                    period["end_datetime"]
                ),
                status__nin=[
                    "DRAFT",
                    "CANCELLED",
                ],
            )
        )

        totals = {}

        for bill in bills:
            supplier = bill.supplier

            if not supplier:
                continue

            supplier_id = str(
                supplier.id
            )

            if supplier_id not in totals:
                totals[
                    supplier_id
                ] = {
                    "supplier_id":
                        supplier_id,
                    "supplier_name":
                        supplier.name,
                    "amount":
                        MainDashboardService.ZERO,
                }

            totals[
                supplier_id
            ]["amount"] += (
                MainDashboardService
                ._to_decimal(
                    bill.total_amount
                )
            )

        ranked = sorted(
            totals.values(),
            key=lambda item: (
                item["amount"]
            ),
            reverse=True,
        )

        return [
            {
                "supplier_id":
                    item["supplier_id"],
                "supplier_name":
                    item["supplier_name"],
                "amount": (
                    f"{item['amount']:.2f}"
                ),
            }
            for item in ranked[:limit]
        ]

    @staticmethod
    def _get_recent_activity(
        *,
        organization,
        limit=10,
    ):
        activities = []

        invoices = (
            MainDashboardService
            ._get_invoices(
                organization=organization,
            )
            .filter(
                status__nin=[
                    "DRAFT",
                    "CANCELLED",
                ]
            )
            .order_by(
                "-invoice_date",
                "-created_at",
            )[:limit]
        )

        for invoice in invoices:
            customer_name = (
                invoice.customer.name
                if invoice.customer
                else "Customer"
            )

            activities.append({
                "activity_type":
                    "INVOICE",
                "reference_id":
                    str(invoice.id),
                "reference_number":
                    invoice.invoice_number,
                "description": (
                    f"Invoice "
                    f"{invoice.invoice_number} "
                    f"for {customer_name}"
                ),
                "activity_date":
                    invoice.invoice_date,
                "amount": (
                    f"{MainDashboardService._to_decimal(invoice.total_amount):.2f}"
                ),
            })

        bills = (
            MainDashboardService
            ._get_vendor_bills(
                organization=organization,
            )
            .filter(
                status__nin=[
                    "DRAFT",
                    "CANCELLED",
                ]
            )
            .order_by(
                "-bill_date",
                "-created_at",
            )[:limit]
        )

        for bill in bills:
            supplier_name = (
                bill.supplier.name
                if bill.supplier
                else "Supplier"
            )

            activities.append({
                "activity_type":
                    "VENDOR_BILL",
                "reference_id":
                    str(bill.id),
                "reference_number":
                    bill.bill_number,
                "description": (
                    f"Vendor bill "
                    f"{bill.bill_number} "
                    f"from {supplier_name}"
                ),
                "activity_date":
                    bill.bill_date,
                "amount": (
                    f"{MainDashboardService._to_decimal(bill.total_amount):.2f}"
                ),
            })

        bank_transactions = (
            BankTransaction.objects(
                organization=organization,
            )
            .order_by(
                "-transaction_date",
                "-created_at",
            )[:limit]
        )

        for transaction in bank_transactions:
            activities.append({
                "activity_type":
                    "BANK_TRANSACTION",
                "reference_id":
                    str(transaction.id),
                "reference_number":
                    transaction.transaction_number,
                "description": (
                    transaction.description
                    or (
                        transaction
                        .transaction_type
                        .replace("_", " ")
                        .title()
                    )
                ),
                "activity_date":
                    transaction.transaction_date,
                "amount": (
                    f"{MainDashboardService._to_decimal(transaction.amount):.2f}"
                ),
            })

        stock_movements = (
            StockMovementRepository
            .list_by_organization(
                organization=organization,
            )[:limit]
        )

        for movement in stock_movements:
            product_name = (
                movement.product.name
                if movement.product
                else "Product"
            )

            reference_number = (
                movement.reference_id
                or str(movement.id)
            )

            activities.append({
                "activity_type":
                    "STOCK_MOVEMENT",
                "reference_id":
                    str(movement.id),
                "reference_number":
                    reference_number,
                "description": (
                    f"{movement.movement_type.replace('_', ' ').title()} "
                    f"— {product_name}"
                ),
                "activity_date":
                    movement.created_at,
                "amount":
                    None,
                "quantity": (
                    f"{MainDashboardService._to_decimal(movement.quantity):.2f}"
                ),
            })

        activities.sort(
            key=lambda item: (
                MainDashboardService
                ._as_datetime(
                    item[
                        "activity_date"
                    ]
                )
            ),
            reverse=True,
        )

        return activities[:limit]

    @staticmethod
    def get_dashboard(
        *,
        user,
        organization,
        start_date=None,
        end_date=None,
    ):
        period = (
            MainDashboardService
            ._normalize_period(
                start_date=start_date,
                end_date=end_date,
            )
        )

        total_sales = (
            MainDashboardService
            ._get_total_sales(
                organization=organization,
                period=period,
            )
        )

        total_purchases = (
            MainDashboardService
            ._get_total_purchases(
                organization=organization,
                period=period,
            )
        )

        bank_balance = (
            MainDashboardService
            ._get_bank_balance(
                organization=organization,
            )
        )

        inventory_summary = (
            MainDashboardService
            ._get_inventory_summary(
                organization=organization,
            )
        )

        receivables_summary = (
            MainDashboardService
            ._get_receivables_summary(
                organization=organization,
            )
        )

        payables_summary = (
            MainDashboardService
            ._get_payables_summary(
                organization=organization,
            )
        )

        receivable_aging = (
            MainDashboardService
            ._get_receivable_aging(
                organization=organization,
            )
        )

        invoice_status = (
            MainDashboardService
            ._get_invoice_status_summary(
                organization=organization,
            )
        )

        bill_status = (
            MainDashboardService
            ._get_bill_status_summary(
                organization=organization,
            )
        )

        sales_trend = (
            MainDashboardService
            ._get_sales_trend(
                organization=organization,
                period=period,
            )
        )

        purchase_trend = (
            MainDashboardService
            ._get_purchase_trend(
                organization=organization,
                period=period,
            )
        )

        cash_flow = (
            MainDashboardService
            ._get_cash_flow(
                user=user,
                organization=organization,
                period=period,
            )
        )

        top_customers = (
            MainDashboardService
            ._get_top_customers(
                organization=organization,
                period=period,
            )
        )

        top_suppliers = (
            MainDashboardService
            ._get_top_suppliers(
                organization=organization,
                period=period,
            )
        )
        recent_activity = (
            MainDashboardService
            ._get_recent_activity(
                organization=organization,
            )
        )

        return {
            "period": {
                "start_date": (
                    period["start_date"]
                    .isoformat()
                ),
                "end_date": (
                    period["end_date"]
                    .isoformat()
                ),
            },
            "kpis": {
                "total_sales": (
                    f"{total_sales:.2f}"
                ),
                "total_purchases": (
                    f"{total_purchases:.2f}"
                ),
                "bank_balance": (
                    f"{bank_balance:.2f}"
                ),
                "inventory_value": (
                    f"{inventory_summary['inventory_value']:.2f}"
                ),
                "out_of_stock_items": (
                    inventory_summary[
                        "out_of_stock_items"
                    ]
                ),
                "receivables": (
                    f"{receivables_summary['total_outstanding']:.2f}"
                ),
                "payables": (
                    f"{payables_summary['total_outstanding']:.2f}"
                ),
            },
            "sales_trend":
                sales_trend,

            "purchase_trend":
                purchase_trend,
            "cash_flow":
                cash_flow,
            "receivable_aging": {
                "current": (
                    f"{receivable_aging['current']:.2f}"
                ),
                "1_30": (
                    f"{receivable_aging['1_30']:.2f}"
                ),
                "31_60": (
                    f"{receivable_aging['31_60']:.2f}"
                ),
                "61_90": (
                    f"{receivable_aging['61_90']:.2f}"
                ),
                "90_plus": (
                    f"{receivable_aging['90_plus']:.2f}"
                ),
            },
            "invoice_status": {
                "issued": (
                    invoice_status["issued"]
                ),
                "partially_paid": (
                    invoice_status[
                        "partially_paid"
                    ]
                ),
                "paid": (
                    invoice_status["paid"]
                ),
                "overdue": (
                    invoice_status["overdue"]
                ),
            },
            "bill_status": {
                "posted": (
                    bill_status["posted"]
                ),
                "partially_paid": (
                    bill_status[
                        "partially_paid"
                    ]
                ),
                "paid": (
                    bill_status["paid"]
                ),
                "overdue": (
                    bill_status["overdue"]
                ),
            },
            "inventory_status": {
                "in_stock": (
                    inventory_summary[
                        "in_stock_items"
                    ]
                ),
                "out_of_stock": (
                    inventory_summary[
                        "out_of_stock_items"
                    ]
                ),
            },
            "top_customers":
                top_customers,

            "top_suppliers":
                top_suppliers,
            "alerts": {
                "overdue_invoices": (
                    receivables_summary[
                        "overdue_invoice_count"
                    ]
                ),
                "overdue_bills": (
                    bill_status["overdue"]
                ),
                "out_of_stock_items": (
                    inventory_summary[
                        "out_of_stock_items"
                    ]
                ),
            },
            "recent_activity":
                recent_activity,
        }