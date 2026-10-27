from apps.core.services.api_serialization_service import (
    APISerializationService,
)


class CustomerAPISerializer:

    @staticmethod
    def serialize_summary(
        customer,
    ):
        if not customer:
            return None

        return {
            "id": (
                APISerializationService
                .serialize_identifier(
                    customer.id
                )
            ),
            "code":
                customer.code,
            "name":
                customer.name,
            "email":
                (
                    customer.email
                    or
                    None
                ),
            "phone":
                (
                    customer.phone
                    or
                    None
                ),
            "gstin":
                (
                    customer.gstin
                    or
                    None
                ),
            "city":
                (
                    customer.city
                    or
                    None
                ),
            "state":
                (
                    customer.state
                    or
                    None
                ),
            "country":
                (
                    customer.country
                    or
                    None
                ),
            "is_active":
                bool(
                    customer.is_active
                ),
        }

    @staticmethod
    def serialize_detail(
        customer,
    ):
        if not customer:
            return None

        summary = (
            CustomerAPISerializer
            .serialize_summary(
                customer
            )
        )

        return {
            **summary,
            "billing_address":
                (
                    customer.billing_address
                    or
                    None
                ),
            "shipping_address":
                (
                    customer.shipping_address
                    or
                    None
                ),
            "pincode":
                (
                    customer.pincode
                    or
                    None
                ),
            "created_at": (
                APISerializationService
                .serialize_datetime(
                    customer.created_at
                )
            ),
            "updated_at": (
                APISerializationService
                .serialize_datetime(
                    customer.updated_at
                )
            ),
        }

    @staticmethod
    def serialize_many(
        customers,
    ):
        return [
            (
                CustomerAPISerializer
                .serialize_summary(
                    customer
                )
            )
            for customer
            in customers
        ]

class SalesOrderAPISerializer:

    @staticmethod
    def _serialize_warehouse(
        warehouse,
    ):
        if not warehouse:
            return None

        return {
            "id": (
                APISerializationService
                .serialize_identifier(
                    warehouse.id
                )
            ),
            "code":
                warehouse.code,
            "name":
                warehouse.name,
            "city":
                (
                    warehouse.city
                    or
                    None
                ),
            "is_active":
                bool(
                    warehouse.is_active
                ),
        }

    @staticmethod
    def _serialize_product(
        product,
    ):
        if not product:
            return None

        return {
            "id": (
                APISerializationService
                .serialize_identifier(
                    product.id
                )
            ),
            "sku":
                product.sku,
            "name":
                product.name,
            "unit":
                product.unit,
            "is_active":
                bool(
                    product.is_active
                ),
        }

    @staticmethod
    def _serialize_created_by(
        user,
    ):
        if not user:
            return None

        return {
            "id": (
                APISerializationService
                .serialize_identifier(
                    user.id
                )
            ),
            "email":
                user.email,
            "first_name":
                user.first_name,
            "last_name":
                user.last_name,
        }

    @staticmethod
    def serialize_item(
        item,
    ):
        if not item:
            return None

        remaining_quantity = (
            item.quantity
            -
            item.fulfilled_quantity
        )

        return {
            "product": (
                SalesOrderAPISerializer
                ._serialize_product(
                    item.product
                )
            ),
            "quantity":
                str(
                    item.quantity
                ),
            "fulfilled_quantity":
                str(
                    item.fulfilled_quantity
                ),
            "remaining_quantity":
                str(
                    remaining_quantity
                ),
            "unit_price":
                str(
                    item.unit_price
                ),
            "tax_rate":
                str(
                    item.tax_rate
                ),
            "discount":
                str(
                    item.discount
                ),
            "line_subtotal":
                str(
                    item.line_subtotal
                ),
            "line_tax":
                str(
                    item.line_tax
                ),
            "line_total":
                str(
                    item.line_total
                ),
        }

    @staticmethod
    def serialize_summary(
        sales_order,
    ):
        if not sales_order:
            return None

        return {
            "id": (
                APISerializationService
                .serialize_identifier(
                    sales_order.id
                )
            ),
            "so_number":
                sales_order.so_number,
            "customer": (
                CustomerAPISerializer
                .serialize_summary(
                    sales_order.customer
                )
            ),
            "warehouse": (
                SalesOrderAPISerializer
                ._serialize_warehouse(
                    sales_order.warehouse
                )
            ),
            "status":
                sales_order.status,
            "order_date": (
                APISerializationService
                .serialize_datetime(
                    sales_order.order_date
                )
            ),
            "expected_delivery_date": (
                APISerializationService
                .serialize_datetime(
                    sales_order
                    .expected_delivery_date
                )
            ),
            "subtotal":
                str(
                    sales_order.subtotal
                ),
            "tax_amount":
                str(
                    sales_order.tax_amount
                ),
            "discount_amount":
                str(
                    sales_order
                    .discount_amount
                ),
            "total_amount":
                str(
                    sales_order.total_amount
                ),
            "item_count":
                len(
                    sales_order.items
                    or
                    []
                ),
            "created_at": (
                APISerializationService
                .serialize_datetime(
                    sales_order.created_at
                )
            ),
            "updated_at": (
                APISerializationService
                .serialize_datetime(
                    sales_order.updated_at
                )
            ),
        }

    @staticmethod
    def serialize_detail(
        sales_order,
    ):
        if not sales_order:
            return None

        summary = (
            SalesOrderAPISerializer
            .serialize_summary(
                sales_order
            )
        )

        return {
            **summary,
            "items": [
                (
                    SalesOrderAPISerializer
                    .serialize_item(
                        item
                    )
                )
                for item
                in (
                    sales_order.items
                    or
                    []
                )
            ],
            "notes":
                (
                    sales_order.notes
                    or
                    None
                ),
            "created_by": (
                SalesOrderAPISerializer
                ._serialize_created_by(
                    sales_order.created_by
                )
            ),
            "confirmed_at": (
                APISerializationService
                .serialize_datetime(
                    sales_order.confirmed_at
                )
            ),
            "fulfilled_at": (
                APISerializationService
                .serialize_datetime(
                    sales_order.fulfilled_at
                )
            ),
            "cancelled_at": (
                APISerializationService
                .serialize_datetime(
                    sales_order.cancelled_at
                )
            ),
        }

    @staticmethod
    def serialize_many(
        sales_orders,
    ):
        return [
            (
                SalesOrderAPISerializer
                .serialize_summary(
                    sales_order
                )
            )
            for sales_order
            in sales_orders
        ]

class BankAccountLookupAPISerializer:

    @staticmethod
    def serialize_summary(
        bank_account,
    ):
        if not bank_account:
            return None

        account_number = (
            bank_account.account_number
            or
            ""
        )

        masked_account_number = (
            (
                "••••"
                +
                account_number[-4:]
            )
            if account_number
            else
            None
        )

        return {
            "id": (
                APISerializationService
                .serialize_identifier(
                    bank_account.id
                )
            ),
            "account_name":
                bank_account.account_name,
            "account_type":
                bank_account.account_type,
            "bank_name":
                (
                    bank_account.bank_name
                    or
                    None
                ),
            "masked_account_number": (
                masked_account_number
            ),
            "currency":
                bank_account.currency,
            "is_active":
                bool(
                    bank_account.is_active
                ),
        }

    @staticmethod
    def serialize_many(
        bank_accounts,
    ):
        return [
            (
                BankAccountLookupAPISerializer
                .serialize_summary(
                    bank_account
                )
            )
            for bank_account
            in bank_accounts
        ]


class InvoiceAPISerializer:

    @staticmethod
    def _serialize_sales_order(
        sales_order,
    ):
        if not sales_order:
            return None

        return {
            "id": (
                APISerializationService
                .serialize_identifier(
                    sales_order.id
                )
            ),
            "so_number":
                sales_order.so_number,
            "status":
                sales_order.status,
        }

    @staticmethod
    def _serialize_product(
        product,
    ):
        if not product:
            return None

        return {
            "id": (
                APISerializationService
                .serialize_identifier(
                    product.id
                )
            ),
            "sku":
                product.sku,
            "name":
                product.name,
            "unit":
                product.unit,
        }

    @staticmethod
    def _serialize_created_by(
        user,
    ):
        if not user:
            return None

        return {
            "id": (
                APISerializationService
                .serialize_identifier(
                    user.id
                )
            ),
            "email":
                user.email,
            "first_name":
                user.first_name,
            "last_name":
                user.last_name,
        }

    @staticmethod
    def serialize_item(
        item,
    ):
        if not item:
            return None

        return {
            "product": (
                InvoiceAPISerializer
                ._serialize_product(
                    item.product
                )
            ),
            "description": getattr(item,"description",""),
            "show_description": getattr(item,"show_description",False),
            "quantity":
                str(
                    item.quantity
                ),
            "unit_price":
                str(
                    item.unit_price
                ),
            "tax_rate":
                str(
                    item.tax_rate
                ),
            "discount":
                str(
                    item.discount
                ),
            "line_subtotal":
                str(
                    item.line_subtotal
                ),
            "line_tax":
                str(
                    item.line_tax
                ),
            "line_total":
                str(
                    item.line_total
                ),
        }

    @staticmethod
    def serialize_summary(
        invoice,
    ):
        if not invoice:
            return None

        return {
            "id": (
                APISerializationService
                .serialize_identifier(
                    invoice.id
                )
            ),
            "invoice_number":
                invoice.invoice_number,
            "sales_order": (
                InvoiceAPISerializer
                ._serialize_sales_order(
                    invoice.sales_order
                )
            ),
            "customer": (
                CustomerAPISerializer
                .serialize_summary(
                    invoice.customer
                )
            ),
            "status":
                invoice.status,
            "invoice_date": (
                APISerializationService
                .serialize_datetime(
                    invoice.invoice_date
                )
            ),
            "due_date": (
                APISerializationService
                .serialize_datetime(
                    invoice.due_date
                )
            ),
            "subtotal":
                str(
                    invoice.subtotal
                ),
            "tax_amount":
                str(
                    invoice.tax_amount
                ),
            "discount_amount":
                str(
                    invoice.discount_amount
                ),
            "total_amount":
                str(
                    invoice.total_amount
                ),
            "amount_paid":
                str(
                    invoice.amount_paid
                ),
            "balance_due":
                str(
                    invoice.balance_due
                ),
            "item_count":
                len(
                    invoice.items
                    or
                    []
                ),
            "created_at": (
                APISerializationService
                .serialize_datetime(
                    invoice.created_at
                )
            ),
            "updated_at": (
                APISerializationService
                .serialize_datetime(
                    invoice.updated_at
                )
            ),
        }

    @staticmethod
    def serialize_detail(
        invoice,
    ):
        if not invoice:
            return None

        summary = (
            InvoiceAPISerializer
            .serialize_summary(
                invoice
            )
        )

        return {
            **summary,
            "items": [
                (
                    InvoiceAPISerializer
                    .serialize_item(
                        item
                    )
                )
                for item
                in (
                    invoice.items
                    or
                    []
                )
            ],
            "billing": {
                "name":
                    invoice.billing_name,
                "address":
                    (
                        invoice.billing_address
                        or
                        None
                    ),
                "city":
                    (
                        invoice.billing_city
                        or
                        None
                    ),
                "state":
                    (
                        invoice.billing_state
                        or
                        None
                    ),
                "country":
                    (
                        invoice.billing_country
                        or
                        None
                    ),
                "pincode":
                    (
                        invoice.billing_pincode
                        or
                        None
                    ),
                "gstin":
                    (
                        invoice.customer_gstin
                        or
                        None
                    ),
            },
            "notes":
                (
                    invoice.notes
                    or
                    None
                ),
            "created_by": (
                InvoiceAPISerializer
                ._serialize_created_by(
                    invoice.created_by
                )
            ),
            "issued_at": (
                APISerializationService
                .serialize_datetime(
                    invoice.issued_at
                )
            ),
            "paid_at": (
                APISerializationService
                .serialize_datetime(
                    invoice.paid_at
                )
            ),
            "cancelled_at": (
                APISerializationService
                .serialize_datetime(
                    invoice.cancelled_at
                )
            ),
        }

    @staticmethod
    def serialize_many(
        invoices,
    ):
        return [
            (
                InvoiceAPISerializer
                .serialize_summary(
                    invoice
                )
            )
            for invoice
            in invoices
        ]


class CustomerPaymentAPISerializer:

    @staticmethod
    def serialize_summary(
        payment,
    ):
        if not payment:
            return None

        return {
            "id": (
                APISerializationService
                .serialize_identifier(
                    payment.id
                )
            ),
            "payment_number":
                payment.payment_number,
            "customer": (
                CustomerAPISerializer
                .serialize_summary(
                    payment.customer
                )
            ),
            "payment_date": (
                APISerializationService
                .serialize_datetime(
                    payment.payment_date
                )
            ),
            "amount":
                str(
                    payment.amount
                ),
            "payment_method":
                payment.payment_method,
            "bank_account": (
                BankAccountLookupAPISerializer
                .serialize_summary(
                    payment.bank_account
                )
            ),
            "reference_number":
                (
                    payment.reference_number
                    or
                    None
                ),
            "allocation_count":
                len(
                    payment.allocations
                    or
                    []
                ),
            "created_at": (
                APISerializationService
                .serialize_datetime(
                    payment.created_at
                )
            ),
            "updated_at": (
                APISerializationService
                .serialize_datetime(
                    payment.updated_at
                )
            ),
        }

    @staticmethod
    def serialize_detail(
        payment,
    ):
        if not payment:
            return None

        summary = (
            CustomerPaymentAPISerializer
            .serialize_summary(
                payment
            )
        )

        return {
            **summary,
            "allocations": [
                {
                    "invoice": {
                        "id": (
                            APISerializationService
                            .serialize_identifier(
                                allocation
                                .invoice
                                .id
                            )
                        ),
                        "invoice_number": (
                            allocation
                            .invoice
                            .invoice_number
                        ),
                        "status": (
                            allocation
                            .invoice
                            .status
                        ),
                        "invoice_date": (
                            APISerializationService
                            .serialize_datetime(
                                allocation
                                .invoice
                                .invoice_date
                            )
                        ),
                        "total_amount":
                            str(
                                allocation
                                .invoice
                                .total_amount
                            ),
                        "balance_due":
                            str(
                                allocation
                                .invoice
                                .balance_due
                            ),
                    },
                    "amount":
                        str(
                            allocation.amount
                        ),
                }
                for allocation
                in (
                    payment.allocations
                    or
                    []
                )
            ],
            "notes":
                (
                    payment.notes
                    or
                    None
                ),
            "created_by": (
                InvoiceAPISerializer
                ._serialize_created_by(
                    payment.created_by
                )
            ),
        }

    @staticmethod
    def serialize_many(
        payments,
    ):
        return [
            (
                CustomerPaymentAPISerializer
                .serialize_summary(
                    payment
                )
            )
            for payment
            in payments
        ]

class AccountsReceivableAPISerializer:

    @staticmethod
    def serialize_summary(
        result,
    ):
        return {
            "as_of": (
                APISerializationService
                .serialize_datetime(
                    result["as_of"]
                )
            ),
            "invoice_count":
                result[
                    "invoice_count"
                ],
            "overdue_invoice_count": (
                result[
                    "overdue_invoice_count"
                ]
            ),
            "customer_count":
                result[
                    "customer_count"
                ],
            "total_outstanding":
                str(
                    result[
                        "total_outstanding"
                    ]
                ),
            "total_current":
                str(
                    result[
                        "total_current"
                    ]
                ),
            "total_overdue":
                str(
                    result[
                        "total_overdue"
                    ]
                ),
            "customers": [
                {
                    "customer": (
                        CustomerAPISerializer
                        .serialize_summary(
                            item[
                                "customer"
                            ]
                        )
                    ),
                    "invoice_count":
                        item[
                            "invoice_count"
                        ],
                    "overdue_invoice_count": (
                        item[
                            "overdue_invoice_count"
                        ]
                    ),
                    "total_outstanding":
                        str(
                            item[
                                "total_outstanding"
                            ]
                        ),
                    "total_overdue":
                        str(
                            item[
                                "total_overdue"
                            ]
                        ),
                }
                for item
                in result[
                    "customers"
                ]
            ],
        }

    @staticmethod
    def serialize_aging(
        result,
    ):
        serialized_buckets = {}

        for (
            key,
            bucket,
        ) in result[
            "buckets"
        ].items():
            serialized_buckets[
                key
            ] = {
                "label":
                    bucket[
                        "label"
                    ],
                "minimum_days":
                    bucket[
                        "minimum_days"
                    ],
                "maximum_days":
                    bucket[
                        "maximum_days"
                    ],
                "invoice_count":
                    bucket[
                        "invoice_count"
                    ],
                "amount":
                    str(
                        bucket[
                            "amount"
                        ]
                    ),
            }

        serialized_invoices = []

        for item in result[
            "invoices"
        ]:
            invoice = item[
                "invoice"
            ]

            serialized_invoices.append({
                "invoice": {
                    "id": (
                        APISerializationService
                        .serialize_identifier(
                            invoice.id
                        )
                    ),
                    "invoice_number":
                        invoice.invoice_number,
                    "status":
                        invoice.status,
                    "invoice_date": (
                        APISerializationService
                        .serialize_datetime(
                            invoice.invoice_date
                        )
                    ),
                    "due_date": (
                        APISerializationService
                        .serialize_datetime(
                            invoice.due_date
                        )
                    ),
                    "total_amount":
                        str(
                            invoice.total_amount
                        ),
                    "amount_paid":
                        str(
                            invoice.amount_paid
                        ),
                    "balance_due":
                        str(
                            invoice.balance_due
                        ),
                },
                "customer": (
                    CustomerAPISerializer
                    .serialize_summary(
                        invoice.customer
                    )
                ),
                "net_receivable":
                    str(
                        item[
                            "net_receivable"
                        ]
                    ),
                "overdue_days":
                    item[
                        "overdue_days"
                    ],
                "is_overdue":
                    bool(
                        item[
                            "is_overdue"
                        ]
                    ),
                "bucket":
                    item[
                        "bucket"
                    ],
            })

        return {
            "as_of": (
                APISerializationService
                .serialize_datetime(
                    result["as_of"]
                )
            ),
            "invoice_count":
                result[
                    "invoice_count"
                ],
            "total_outstanding":
                str(
                    result[
                        "total_outstanding"
                    ]
                ),
            "buckets":
                serialized_buckets,
            "invoices":
                serialized_invoices,
        }

class SalesReturnAPISerializer:

    @staticmethod
    def _serialize_reference(
        document,
        *,
        number_field,
    ):
        if not document:
            return None

        return {
            "id": (
                APISerializationService
                .serialize_identifier(
                    document.id
                )
            ),
            number_field:
                getattr(
                    document,
                    number_field,
                    None,
                ),
            "status":
                getattr(
                    document,
                    "status",
                    None,
                ),
        }

    @staticmethod
    def _serialize_product(
        product,
    ):
        if not product:
            return None

        return {
            "id": (
                APISerializationService
                .serialize_identifier(
                    product.id
                )
            ),
            "sku":
                product.sku,
            "name":
                product.name,
            "unit":
                product.unit,
        }

    @staticmethod
    def _serialize_warehouse(
        warehouse,
    ):
        if not warehouse:
            return None

        return {
            "id": (
                APISerializationService
                .serialize_identifier(
                    warehouse.id
                )
            ),
            "code":
                warehouse.code,
            "name":
                warehouse.name,
            "city":
                (
                    warehouse.city
                    or
                    None
                ),
        }

    @staticmethod
    def _serialize_created_by(
        user,
    ):
        if not user:
            return None

        return {
            "id": (
                APISerializationService
                .serialize_identifier(
                    user.id
                )
            ),
            "email":
                user.email,
            "first_name":
                user.first_name,
            "last_name":
                user.last_name,
        }

    @staticmethod
    def serialize_item(
        item,
    ):
        if not item:
            return None

        return {
            "product": (
                SalesReturnAPISerializer
                ._serialize_product(
                    item.product
                )
            ),
            "quantity":
                str(
                    item.quantity
                ),
            "unit_price":
                str(
                    item.unit_price
                ),
            "tax_rate":
                str(
                    item.tax_rate
                ),
            "discount":
                str(
                    item.discount
                ),
            "line_subtotal":
                str(
                    item.line_subtotal
                ),
            "line_tax":
                str(
                    item.line_tax
                ),
            "line_total":
                str(
                    item.line_total
                ),
            "reason":
                (
                    item.reason
                    or
                    None
                ),
        }

    @staticmethod
    def serialize_summary(
        sales_return,
    ):
        if not sales_return:
            return None

        return {
            "id": (
                APISerializationService
                .serialize_identifier(
                    sales_return.id
                )
            ),
            "return_number":
                sales_return.return_number,
            "sales_order": (
                SalesReturnAPISerializer
                ._serialize_reference(
                    sales_return.sales_order,
                    number_field="so_number",
                )
            ),
            "invoice": (
                SalesReturnAPISerializer
                ._serialize_reference(
                    sales_return.invoice,
                    number_field=(
                        "invoice_number"
                    ),
                )
            ),
            "customer": (
                CustomerAPISerializer
                .serialize_summary(
                    sales_return.customer
                )
            ),
            "warehouse": (
                SalesReturnAPISerializer
                ._serialize_warehouse(
                    sales_return.warehouse
                )
            ),
            "status":
                sales_return.status,
            "return_date": (
                APISerializationService
                .serialize_datetime(
                    sales_return.return_date
                )
            ),
            "subtotal":
                str(
                    sales_return.subtotal
                ),
            "tax_amount":
                str(
                    sales_return.tax_amount
                ),
            "discount_amount":
                str(
                    sales_return.discount_amount
                ),
            "total_amount":
                str(
                    sales_return.total_amount
                ),
            "item_count":
                len(
                    sales_return.items
                    or
                    []
                ),
            "created_at": (
                APISerializationService
                .serialize_datetime(
                    sales_return.created_at
                )
            ),
            "updated_at": (
                APISerializationService
                .serialize_datetime(
                    sales_return.updated_at
                )
            ),
        }

    @staticmethod
    def serialize_detail(
        sales_return,
    ):
        if not sales_return:
            return None

        summary = (
            SalesReturnAPISerializer
            .serialize_summary(
                sales_return
            )
        )

        return {
            **summary,
            "items": [
                (
                    SalesReturnAPISerializer
                    .serialize_item(
                        item
                    )
                )
                for item
                in (
                    sales_return.items
                    or
                    []
                )
            ],
            "reason":
                (
                    sales_return.reason
                    or
                    None
                ),
            "notes":
                (
                    sales_return.notes
                    or
                    None
                ),
            "created_by": (
                SalesReturnAPISerializer
                ._serialize_created_by(
                    sales_return.created_by
                )
            ),
            "confirmed_at": (
                APISerializationService
                .serialize_datetime(
                    sales_return.confirmed_at
                )
            ),
            "cancelled_at": (
                APISerializationService
                .serialize_datetime(
                    sales_return.cancelled_at
                )
            ),
        }

    @staticmethod
    def serialize_many(
        sales_returns,
    ):
        return [
            (
                SalesReturnAPISerializer
                .serialize_summary(
                    sales_return
                )
            )
            for sales_return
            in sales_returns
        ]

class CreditNoteAPISerializer:

    @staticmethod
    def _serialize_reference(
        document,
        *,
        number_field,
    ):
        if not document:
            return None

        return {
            "id": (
                APISerializationService
                .serialize_identifier(
                    document.id
                )
            ),
            number_field:
                getattr(
                    document,
                    number_field,
                    None,
                ),
            "status":
                getattr(
                    document,
                    "status",
                    None,
                ),
        }

    @staticmethod
    def _serialize_product(
        product,
    ):
        if not product:
            return None

        return {
            "id": (
                APISerializationService
                .serialize_identifier(
                    product.id
                )
            ),
            "sku":
                product.sku,
            "name":
                product.name,
            "unit":
                product.unit,
        }

    @staticmethod
    def _serialize_created_by(
        user,
    ):
        if not user:
            return None

        return {
            "id": (
                APISerializationService
                .serialize_identifier(
                    user.id
                )
            ),
            "email":
                user.email,
            "first_name":
                user.first_name,
            "last_name":
                user.last_name,
        }

    @staticmethod
    def serialize_item(
        item,
    ):
        if not item:
            return None

        return {
            "product": (
                CreditNoteAPISerializer
                ._serialize_product(
                    item.product
                )
            ),
            "quantity":
                str(
                    item.quantity
                ),
            "unit_price":
                str(
                    item.unit_price
                ),
            "tax_rate":
                str(
                    item.tax_rate
                ),
            "discount":
                str(
                    item.discount
                ),
            "line_subtotal":
                str(
                    item.line_subtotal
                ),
            "line_tax":
                str(
                    item.line_tax
                ),
            "line_total":
                str(
                    item.line_total
                ),
        }

    @staticmethod
    def serialize_summary(
        credit_note,
    ):
        if not credit_note:
            return None

        return {
            "id": (
                APISerializationService
                .serialize_identifier(
                    credit_note.id
                )
            ),
            "credit_note_number":
                credit_note.credit_note_number,
            "invoice": (
                CreditNoteAPISerializer
                ._serialize_reference(
                    credit_note.invoice,
                    number_field=(
                        "invoice_number"
                    ),
                )
            ),
            "sales_return": (
                CreditNoteAPISerializer
                ._serialize_reference(
                    credit_note.sales_return,
                    number_field=(
                        "return_number"
                    ),
                )
            ),
            "customer": (
                CustomerAPISerializer
                .serialize_summary(
                    credit_note.customer
                )
            ),
            "status":
                credit_note.status,
            "credit_note_date": (
                APISerializationService
                .serialize_datetime(
                    credit_note.credit_note_date
                )
            ),
            "subtotal":
                str(
                    credit_note.subtotal
                ),
            "tax_amount":
                str(
                    credit_note.tax_amount
                ),
            "discount_amount":
                str(
                    credit_note.discount_amount
                ),
            "total_amount":
                str(
                    credit_note.total_amount
                ),
            "applied_amount":
                str(
                    credit_note.applied_amount
                ),
            "remaining_credit":
                str(
                    credit_note.remaining_credit
                ),
            "item_count":
                len(
                    credit_note.items
                    or
                    []
                ),
            "created_at": (
                APISerializationService
                .serialize_datetime(
                    credit_note.created_at
                )
            ),
            "updated_at": (
                APISerializationService
                .serialize_datetime(
                    credit_note.updated_at
                )
            ),
        }

    @staticmethod
    def serialize_detail(
        credit_note,
    ):
        if not credit_note:
            return None

        summary = (
            CreditNoteAPISerializer
            .serialize_summary(
                credit_note
            )
        )

        return {
            **summary,
            "items": [
                (
                    CreditNoteAPISerializer
                    .serialize_item(
                        item
                    )
                )
                for item
                in (
                    credit_note.items
                    or
                    []
                )
            ],
            "reason":
                (
                    credit_note.reason
                    or
                    None
                ),
            "notes":
                (
                    credit_note.notes
                    or
                    None
                ),
            "created_by": (
                CreditNoteAPISerializer
                ._serialize_created_by(
                    credit_note.created_by
                )
            ),
            "issued_at": (
                APISerializationService
                .serialize_datetime(
                    credit_note.issued_at
                )
            ),
            "cancelled_at": (
                APISerializationService
                .serialize_datetime(
                    credit_note.cancelled_at
                )
            ),
        }

    @staticmethod
    def serialize_many(
        credit_notes,
    ):
        return [
            (
                CreditNoteAPISerializer
                .serialize_summary(
                    credit_note
                )
            )
            for credit_note
            in credit_notes
        ]