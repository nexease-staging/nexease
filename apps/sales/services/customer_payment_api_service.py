from datetime import (
    datetime,
)
from decimal import (
    Decimal,
)

from bson import (
    ObjectId,
)

from apps.sales.repositories.invoice_repository import (
    InvoiceRepository,
)
from apps.sales.repositories.payment_repository import (
    PaymentRepository,
)
from apps.sales.services.invoice_service import (
    InvoiceService,
)


class CustomerPaymentAPIValidationError(
    ValueError
):

    def __init__(
        self,
        *,
        message="Validation failed.",
        details=None,
    ):
        super().__init__(
            message
        )

        self.message = message
        self.details = details or {}


class CustomerPaymentAPIService:

    @staticmethod
    def _parse_identifier(
        value,
        *,
        field,
    ):
        if not isinstance(
            value,
            str,
        ):
            raise (
                CustomerPaymentAPIValidationError(
                    details={
                        field: [
                            (
                                "Identifier must "
                                "be a string."
                            ),
                        ],
                    },
                )
            )

        value = value.strip()

        if not ObjectId.is_valid(
            value
        ):
            raise (
                CustomerPaymentAPIValidationError(
                    details={
                        field: [
                            (
                                "Enter a valid "
                                "identifier."
                            ),
                        ],
                    },
                )
            )

        return ObjectId(
            value
        )

    @staticmethod
    def get_payment(
        *,
        organization,
        payment_id,
    ):
        parsed_payment_id = (
            CustomerPaymentAPIService
            ._parse_identifier(
                payment_id,
                field="payment_id",
            )
        )

        payment = (
            PaymentRepository
            .get_by_id(
                organization=organization,
                payment_id=(
                    parsed_payment_id
                ),
            )
        )

        if not payment:
            raise LookupError(
                "Customer payment not found."
            )

        return payment

    @staticmethod
    def _outstanding_invoices(
        *,
        organization,
        as_of,
    ):
        invoices = (
            InvoiceRepository
            .list_outstanding(
                organization=organization,
            )
        )

        outstanding = []

        for invoice in invoices:
            net_receivable = (
                InvoiceService
                .get_invoice_net_receivable(
                    organization=organization,
                    invoice=invoice,
                )
            )

            if (
                net_receivable
                <=
                Decimal("0")
            ):
                continue

            due_date = (
                invoice.due_date
                or
                invoice.invoice_date
            )

            overdue_days = 0

            if (
                due_date
                and
                due_date < as_of
            ):
                overdue_days = max(
                    0,
                    (
                        as_of.date()
                        -
                        due_date.date()
                    ).days,
                )

            outstanding.append({
                "invoice":
                    invoice,
                "net_receivable":
                    net_receivable,
                "due_date":
                    due_date,
                "overdue_days":
                    overdue_days,
                "is_overdue":
                    overdue_days > 0,
            })

        return outstanding

    @staticmethod
    def get_receivable_summary(
        *,
        organization,
        as_of=None,
    ):
        if as_of is None:
            as_of = datetime.utcnow()

        outstanding = (
            CustomerPaymentAPIService
            ._outstanding_invoices(
                organization=organization,
                as_of=as_of,
            )
        )

        total_outstanding = Decimal("0")
        total_current = Decimal("0")
        total_overdue = Decimal("0")

        customer_totals = {}

        for item in outstanding:
            invoice = item[
                "invoice"
            ]

            net_receivable = item[
                "net_receivable"
            ]

            total_outstanding += (
                net_receivable
            )

            if item["is_overdue"]:
                total_overdue += (
                    net_receivable
                )

            else:
                total_current += (
                    net_receivable
                )

            customer_id = str(
                invoice.customer.id
            )

            if (
                customer_id
                not in customer_totals
            ):
                customer_totals[
                    customer_id
                ] = {
                    "customer":
                        invoice.customer,
                    "invoice_count": 0,
                    "overdue_invoice_count":
                        0,
                    "total_outstanding":
                        Decimal("0"),
                    "total_overdue":
                        Decimal("0"),
                }

            customer_item = (
                customer_totals[
                    customer_id
                ]
            )

            customer_item[
                "invoice_count"
            ] += 1

            customer_item[
                "total_outstanding"
            ] += net_receivable

            if item["is_overdue"]:
                customer_item[
                    "overdue_invoice_count"
                ] += 1

                customer_item[
                    "total_overdue"
                ] += net_receivable

        customers = sorted(
            customer_totals.values(),
            key=lambda item: (
                item[
                    "total_outstanding"
                ]
            ),
            reverse=True,
        )

        return {
            "as_of":
                as_of,
            "invoice_count":
                len(
                    outstanding
                ),
            "overdue_invoice_count":
                sum(
                    1
                    for item
                    in outstanding
                    if item["is_overdue"]
                ),
            "customer_count":
                len(
                    customers
                ),
            "total_outstanding":
                total_outstanding,
            "total_current":
                total_current,
            "total_overdue":
                total_overdue,
            "customers":
                customers,
        }

    @staticmethod
    def get_aging_summary(
        *,
        organization,
        as_of=None,
    ):
        if as_of is None:
            as_of = datetime.utcnow()

        outstanding = (
            CustomerPaymentAPIService
            ._outstanding_invoices(
                organization=organization,
                as_of=as_of,
            )
        )

        buckets = {
            "current": {
                "label": "Current",
                "minimum_days": None,
                "maximum_days": 0,
                "invoice_count": 0,
                "amount": Decimal("0"),
            },
            "days_1_30": {
                "label": "1–30 days",
                "minimum_days": 1,
                "maximum_days": 30,
                "invoice_count": 0,
                "amount": Decimal("0"),
            },
            "days_31_60": {
                "label": "31–60 days",
                "minimum_days": 31,
                "maximum_days": 60,
                "invoice_count": 0,
                "amount": Decimal("0"),
            },
            "days_61_90": {
                "label": "61–90 days",
                "minimum_days": 61,
                "maximum_days": 90,
                "invoice_count": 0,
                "amount": Decimal("0"),
            },
            "days_over_90": {
                "label": "Over 90 days",
                "minimum_days": 91,
                "maximum_days": None,
                "invoice_count": 0,
                "amount": Decimal("0"),
            },
        }

        invoice_items = []
        total_outstanding = Decimal("0")

        for item in outstanding:
            overdue_days = item[
                "overdue_days"
            ]

            if overdue_days <= 0:
                bucket_key = "current"

            elif overdue_days <= 30:
                bucket_key = "days_1_30"

            elif overdue_days <= 60:
                bucket_key = "days_31_60"

            elif overdue_days <= 90:
                bucket_key = "days_61_90"

            else:
                bucket_key = (
                    "days_over_90"
                )

            net_receivable = item[
                "net_receivable"
            ]

            buckets[
                bucket_key
            ]["invoice_count"] += 1

            buckets[
                bucket_key
            ]["amount"] += (
                net_receivable
            )

            total_outstanding += (
                net_receivable
            )

            invoice_items.append({
                **item,
                "bucket":
                    bucket_key,
            })

        invoice_items.sort(
            key=lambda item: (
                item["overdue_days"],
                item["invoice"].invoice_date,
            ),
            reverse=True,
        )

        return {
            "as_of":
                as_of,
            "invoice_count":
                len(
                    invoice_items
                ),
            "total_outstanding":
                total_outstanding,
            "buckets":
                buckets,
            "invoices":
                invoice_items,
        }