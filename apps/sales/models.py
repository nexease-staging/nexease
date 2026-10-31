from datetime import datetime
from apps.finance.models import (
    BankAccount,
)
from mongoengine import (
    DictField,
    Document,
    EmbeddedDocument,
    EmbeddedDocumentField,
    StringField,
    ReferenceField,
    BooleanField,
    DateTimeField,
    DecimalField,
    ListField,
    EmailField,
)
from apps.accounts.models import User
from apps.products.models import Product
from apps.inventory.models import Warehouse
from apps.organizations.models import Organization


class Customer(Document):
    organization = ReferenceField(
        Organization,
        required=True,
    )

    name = StringField(
        required=True,
        max_length=200,
        strip=True,
    )

    code = StringField(
        required=True,
        max_length=50,
        strip=True,
    )

    email = EmailField()

    phone = StringField(
        default="",
        max_length=30,
        strip=True,
    )

    gstin = StringField(
        default="",
        max_length=20,
        strip=True,
    )

    billing_address = StringField(
        default="",
        max_length=500,
        strip=True,
    )

    shipping_address = StringField(
        default="",
        max_length=500,
        strip=True,
    )

    city = StringField(
        default="",
        max_length=100,
        strip=True,
    )

    state = StringField(
        default="",
        max_length=100,
        strip=True,
    )

    country = StringField(
        default="India",
        max_length=100,
        strip=True,
    )

    pincode = StringField(
        default="",
        max_length=20,
        strip=True,
    )

    is_active = BooleanField(
        default=True,
    )

    created_at = DateTimeField(
        default=datetime.utcnow,
    )

    updated_at = DateTimeField(
        default=datetime.utcnow,
    )

    meta = {
        "collection": "customers",
        "indexes": [
            {
                "fields": [
                    "organization",
                    "code",
                ],
                "unique": True,
            },
            {
                "fields": [
                    "organization",
                    "name",
                ],
            },
            {
                "fields": [
                    "organization",
                    "gstin",
                ],
            },
        ],
    }

class SalesOrderItem(EmbeddedDocument):
    product = ReferenceField(
        Product,
        required=True,
    )

    quantity = DecimalField(
        precision=2,
        required=True,
        min_value=0.01,
    )

    fulfilled_quantity = DecimalField(
        precision=2,
        default=0,
        min_value=0,
    )

    unit_price = DecimalField(
        precision=2,
        required=True,
        min_value=0,
    )

    tax_rate = DecimalField(
        precision=2,
        default=0,
        min_value=0,
    )

    discount = DecimalField(
        precision=2,
        default=0,
        min_value=0,
    )

    line_subtotal = DecimalField(
        precision=2,
        default=0,
        min_value=0,
    )

    line_tax = DecimalField(
        precision=2,
        default=0,
        min_value=0,
    )

    line_total = DecimalField(
        precision=2,
        default=0,
        min_value=0,
    )

class SalesOrder(Document):
    organization = ReferenceField(
        Organization,
        required=True,
    )

    so_number = StringField(
        required=True,
        max_length=50,
    )

    customer = ReferenceField(
        Customer,
        required=True,
    )

    warehouse = ReferenceField(
        Warehouse,
        required=True,
    )

    status = StringField(
        required=True,
        default="DRAFT",
        choices=(
            "DRAFT",
            "CONFIRMED",
            "PARTIALLY_FULFILLED",
            "FULFILLED",
            "CANCELLED",
        ),
    )

    order_date = DateTimeField(
        required=True,
    )

    expected_delivery_date = DateTimeField()

    items = ListField(
        EmbeddedDocumentField(
            SalesOrderItem
        ),
        required=True,
    )

    subtotal = DecimalField(
        precision=2,
        default=0,
        min_value=0,
    )

    tax_amount = DecimalField(
        precision=2,
        default=0,
        min_value=0,
    )

    discount_amount = DecimalField(
        precision=2,
        default=0,
        min_value=0,
    )

    total_amount = DecimalField(
        precision=2,
        default=0,
        min_value=0,
    )

    notes = StringField(
        default="",
        max_length=1000,
    )

    created_by = ReferenceField(
        User,
        required=True,
    )

    confirmed_at = DateTimeField()

    fulfilled_at = DateTimeField()

    cancelled_at = DateTimeField()

    created_at = DateTimeField(
        default=datetime.utcnow,
    )

    updated_at = DateTimeField(
        default=datetime.utcnow,
    )

    meta = {
        "collection": "sales_orders",
        "indexes": [
            {
                "fields": [
                    "organization",
                    "so_number",
                ],
                "unique": True,
            },
            {
                "fields": [
                    "organization",
                    "customer",
                    "-created_at",
                ],
            },
            {
                "fields": [
                    "organization",
                    "warehouse",
                    "-created_at",
                ],
            },
            {
                "fields": [
                    "organization",
                    "status",
                    "-created_at",
                ],
            },
            {
                "fields": [
                    "organization",
                    "-created_at",
                ],
            },
        ],
    }

class InvoiceItem(EmbeddedDocument):
    item_type = StringField(default="goods", choices=("goods", "service"))
    hsn_code = StringField(default="", max_length=8)
    item_name = StringField(default="", max_length=200)
    unit = StringField(default="", max_length=30)
    description = StringField(default="", max_length=2000)
    show_description = BooleanField(default=False)
    product = ReferenceField(
        Product,
        required=True,
    )

    quantity = DecimalField(
        precision=2,
        required=True,
        min_value=0.01,
    )

    unit_price = DecimalField(
        precision=2,
        required=True,
        min_value=0,
    )

    tax_rate = DecimalField(
        precision=2,
        default=0,
        min_value=0,
    )

    discount = DecimalField(
        precision=2,
        default=0,
        min_value=0,
    )

    line_subtotal = DecimalField(
        precision=2,
        default=0,
        min_value=0,
    )

    line_tax = DecimalField(
        precision=2,
        default=0,
        min_value=0,
    )

    line_total = DecimalField(
        precision=2,
        default=0,
        min_value=0,
    )


class Invoice(Document):
    billing_details = DictField(default=dict)
    workforce_billing_key = StringField()
    workforce_timesheet_ids = ListField(StringField(), default=list)
    direct_entry = BooleanField(default=False)
    stock_review_required = BooleanField(default=False)

    organization = ReferenceField(
        Organization,
        required=True,
    )

    invoice_number = StringField(
        required=True,
        max_length=50,
    )

    sales_order = ReferenceField(SalesOrder, required=False)

    customer = ReferenceField(
        Customer,
        required=True,
    )

    status = StringField(
        required=True,
        default="DRAFT",
        choices=(
            "DRAFT",
            "ISSUED",
            "PARTIALLY_PAID",
            "PAID",
            "CANCELLED",
        ),
    )

    invoice_date = DateTimeField(
        required=True,
    )

    due_date = DateTimeField()

    items = ListField(
        EmbeddedDocumentField(
            InvoiceItem
        ),
        required=True,
    )

    subtotal = DecimalField(
        precision=2,
        default=0,
        min_value=0,
    )

    tax_amount = DecimalField(
        precision=2,
        default=0,
        min_value=0,
    )

    discount_amount = DecimalField(
        precision=2,
        default=0,
        min_value=0,
    )

    total_amount = DecimalField(
        precision=2,
        default=0,
        min_value=0,
    )

    amount_paid = DecimalField(
        precision=2,
        default=0,
        min_value=0,
    )

    balance_due = DecimalField(
        precision=2,
        default=0,
        min_value=0,
    )

    billing_name = StringField(
        required=True,
        max_length=200,
    )

    billing_address = StringField(
        default="",
        max_length=500,
    )

    billing_city = StringField(
        default="",
        max_length=100,
    )

    billing_state = StringField(
        default="",
        max_length=100,
    )

    billing_country = StringField(
        default="India",
        max_length=100,
    )

    billing_pincode = StringField(
        default="",
        max_length=20,
    )

    customer_gstin = StringField(
        default="",
        max_length=20,
    )

    notes = StringField(
        default="",
        max_length=1000,
    )

    created_by = ReferenceField(
        User,
        required=True,
    )

    issued_at = DateTimeField()

    paid_at = DateTimeField()

    cancelled_at = DateTimeField()

    created_at = DateTimeField(
        default=datetime.utcnow,
    )

    updated_at = DateTimeField(
        default=datetime.utcnow,
    )

    meta = {'collection': 'invoices', 'indexes': [{"fields":["organization","workforce_billing_key"],"unique":True,"name":"workforce_site_month_unique","partialFilterExpression":{"workforce_billing_key":{"$type":"string"}}},{'fields': ['organization', 'invoice_number'], 'unique': True}, {'fields': ['organization', 'sales_order'], 'unique': True, 'name': 'invoice_sales_order_unique_present', 'partialFilterExpression': {'sales_order': {'$type': 'objectId'}}}, {'fields': ['organization', 'customer', '-created_at']}, {'fields': ['organization', 'status', '-created_at']}, {'fields': ['organization', 'due_date']}, {'fields': ['organization', '-created_at']}]}

class PaymentAllocation(EmbeddedDocument):
    invoice = ReferenceField(
        Invoice,
        required=True,
    )

    amount = DecimalField(
        precision=2,
        required=True,
        min_value=0.01,
    )

class CustomerPayment(Document):
    organization = ReferenceField(
        Organization,
        required=True,
    )

    payment_number = StringField(
        required=True,
        max_length=50,
    )

    customer = ReferenceField(
        Customer,
        required=True,
    )

    payment_date = DateTimeField(
        required=True,
    )

    amount = DecimalField(
        precision=2,
        required=True,
        min_value=0.01,
    )

    payment_method = StringField(
        required=True,
        choices=(
            "CASH",
            "BANK_TRANSFER",
            "UPI",
            "CHEQUE",
            "CARD",
            "OTHER",
        ),
    )

    bank_account = ReferenceField(
        BankAccount,
        required=False,
    )
    
    reference_number = StringField(
        default="",
        max_length=100,
    )

    allocations = ListField(
        EmbeddedDocumentField(
            PaymentAllocation
        ),
        required=True,
    )

    notes = StringField(
        default="",
        max_length=1000,
    )

    created_by = ReferenceField(
        User,
        required=True,
    )

    created_at = DateTimeField(
        default=datetime.utcnow,
    )

    updated_at = DateTimeField(
        default=datetime.utcnow,
    )

    meta = {
        "collection": "customer_payments",
        "indexes": [
            {
                "fields": [
                    "organization",
                    "payment_number",
                ],
                "unique": True,
            },
            {
                "fields": [
                    "organization",
                    "customer",
                    "-payment_date",
                ],
            },
            {
                "fields": [
                    "organization",
                    "-payment_date",
                ],
            },
            {
                "fields": [
                    "organization",
                    "reference_number",
                ],
            },
        ],
    }

class SalesReturnItem(
    EmbeddedDocument
):
    product = ReferenceField(
        Product,
        required=True,
    )

    quantity = DecimalField(
        precision=2,
        required=True,
        min_value=0.01,
    )

    unit_price = DecimalField(
        precision=2,
        required=True,
        min_value=0,
    )

    tax_rate = DecimalField(
        precision=2,
        default=0,
        min_value=0,
    )

    discount = DecimalField(
        precision=2,
        default=0,
        min_value=0,
    )

    line_subtotal = DecimalField(
        precision=2,
        default=0,
        min_value=0,
    )

    line_tax = DecimalField(
        precision=2,
        default=0,
        min_value=0,
    )

    line_total = DecimalField(
        precision=2,
        default=0,
        min_value=0,
    )

    reason = StringField(
        default="",
        max_length=500,
        strip=True,
    )

class SalesReturn(Document):
    organization = ReferenceField(
        Organization,
        required=True,
    )

    return_number = StringField(
        required=True,
        max_length=50,
    )

    sales_order = ReferenceField(
        SalesOrder,
        required=True,
    )

    invoice = ReferenceField(
        Invoice,
        required=True,
    )

    customer = ReferenceField(
        Customer,
        required=True,
    )

    warehouse = ReferenceField(
        Warehouse,
        required=True,
    )

    status = StringField(
        required=True,
        default="DRAFT",
        choices=(
            "DRAFT",
            "CONFIRMED",
            "CANCELLED",
        ),
    )

    return_date = DateTimeField(
        required=True,
    )

    items = ListField(
        EmbeddedDocumentField(
            SalesReturnItem
        ),
        required=True,
    )

    subtotal = DecimalField(
        precision=2,
        default=0,
        min_value=0,
    )

    tax_amount = DecimalField(
        precision=2,
        default=0,
        min_value=0,
    )

    discount_amount = DecimalField(
        precision=2,
        default=0,
        min_value=0,
    )

    total_amount = DecimalField(
        precision=2,
        default=0,
        min_value=0,
    )

    reason = StringField(
        default="",
        max_length=500,
        strip=True,
    )

    notes = StringField(
        default="",
        max_length=1000,
        strip=True,
    )

    created_by = ReferenceField(
        User,
        required=True,
    )

    confirmed_at = DateTimeField()

    cancelled_at = DateTimeField()

    created_at = DateTimeField(
        default=datetime.utcnow,
    )

    updated_at = DateTimeField(
        default=datetime.utcnow,
    )

    meta = {
        "collection": "sales_returns",
        "indexes": [
            {
                "fields": [
                    "organization",
                    "return_number",
                ],
                "unique": True,
            },
            {
                "fields": [
                    "organization",
                    "invoice",
                    "-created_at",
                ],
            },
            {
                "fields": [
                    "organization",
                    "sales_order",
                    "-created_at",
                ],
            },
            {
                "fields": [
                    "organization",
                    "customer",
                    "-created_at",
                ],
            },
            {
                "fields": [
                    "organization",
                    "status",
                    "-created_at",
                ],
            },
            {
                "fields": [
                    "organization",
                    "-created_at",
                ],
            },
        ],
    }

class CreditNoteItem(
    EmbeddedDocument
):
    product = ReferenceField(
        Product,
        required=True,
    )

    quantity = DecimalField(
        precision=2,
        required=True,
        min_value=0.01,
    )

    unit_price = DecimalField(
        precision=2,
        required=True,
        min_value=0,
    )

    tax_rate = DecimalField(
        precision=2,
        default=0,
        min_value=0,
    )

    discount = DecimalField(
        precision=2,
        default=0,
        min_value=0,
    )

    line_subtotal = DecimalField(
        precision=2,
        default=0,
        min_value=0,
    )

    line_tax = DecimalField(
        precision=2,
        default=0,
        min_value=0,
    )

    line_total = DecimalField(
        precision=2,
        default=0,
        min_value=0,
    )

class CreditNote(Document):
    organization = ReferenceField(
        Organization,
        required=True,
    )

    credit_note_number = StringField(
        required=True,
        max_length=50,
    )

    invoice = ReferenceField(
        Invoice,
        required=True,
    )

    sales_return = ReferenceField(
        SalesReturn,
        required=True,
    )

    customer = ReferenceField(
        Customer,
        required=True,
    )

    status = StringField(
        required=True,
        default="DRAFT",
        choices=(
            "DRAFT",
            "ISSUED",
            "CANCELLED",
        ),
    )

    credit_note_date = DateTimeField(
        required=True,
    )

    items = ListField(
        EmbeddedDocumentField(
            CreditNoteItem
        ),
        required=True,
    )

    subtotal = DecimalField(
        precision=2,
        default=0,
        min_value=0,
    )

    tax_amount = DecimalField(
        precision=2,
        default=0,
        min_value=0,
    )

    discount_amount = DecimalField(
        precision=2,
        default=0,
        min_value=0,
    )

    total_amount = DecimalField(
        precision=2,
        default=0,
        min_value=0,
    )

    applied_amount = DecimalField(
        precision=2,
        default=0,
        min_value=0,
    )

    remaining_credit = DecimalField(
        precision=2,
        default=0,
        min_value=0,
    )

    reason = StringField(
        default="",
        max_length=500,
        strip=True,
    )

    notes = StringField(
        default="",
        max_length=1000,
        strip=True,
    )

    created_by = ReferenceField(
        User,
        required=True,
    )

    issued_at = DateTimeField()

    cancelled_at = DateTimeField()

    created_at = DateTimeField(
        default=datetime.utcnow,
    )

    updated_at = DateTimeField(
        default=datetime.utcnow,
    )

    meta = {
        "collection": "credit_notes",
        "indexes": [
            {
                "fields": [
                    "organization",
                    "credit_note_number",
                ],
                "unique": True,
            },
            {
                "fields": [
                    "organization",
                    "sales_return",
                ],
                "unique": True,
            },
            {
                "fields": [
                    "organization",
                    "invoice",
                    "-created_at",
                ],
            },
            {
                "fields": [
                    "organization",
                    "customer",
                    "-created_at",
                ],
            },
            {
                "fields": [
                    "organization",
                    "status",
                    "-created_at",
                ],
            },
            {
                "fields": [
                    "organization",
                    "-created_at",
                ],
            },
        ],
    }