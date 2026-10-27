from datetime import datetime
from apps.finance.models import (
    BankAccount,
)
from apps.inventory.models import Warehouse
from mongoengine import (
    Document,
    EmbeddedDocument,
    EmbeddedDocumentField,
    StringField,
    ReferenceField,
    BooleanField,
    DateTimeField,
    DateField,
    DecimalField,
    IntField,
    EmailField,
    ListField,
)
from apps.products.models import Product
from apps.accounts.models import User
from apps.organizations.models import Organization


class Supplier(Document):
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

    address = StringField(
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
        "collection": "suppliers",
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

class PurchaseOrderItem(EmbeddedDocument):
    product = ReferenceField(
        Product,
        required=True,
    )

    quantity = DecimalField(
        required=True,
        precision=2,
        min_value=0,
    )

    received_quantity = DecimalField(
        precision=2,
        default=0,
        min_value=0,
    )

    unit_price = DecimalField(
        required=True,
        precision=2,
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

    total = DecimalField(
        precision=2,
        default=0,
        min_value=0,
    )


class PurchaseOrder(Document):
    organization = ReferenceField(
        Organization,
        required=True,
    )

    po_number = StringField(
        required=True,
        max_length=50,
    )

    supplier = ReferenceField(
        Supplier,
        required=True,
    )

    status = StringField(
        required=True,
        default="DRAFT",
        choices=[
            "DRAFT",
            "CONFIRMED",
            "PARTIALLY_RECEIVED",
            "RECEIVED",
            "CANCELLED",
        ],
    )

    order_date = DateField(
        required=True,
    )

    expected_delivery_date = DateField()

    items = ListField(
        EmbeddedDocumentField(
            PurchaseOrderItem
        ),
        default=list,
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
        "User",
        required=True,
    )

    created_at = DateTimeField(
        default=datetime.utcnow,
    )

    updated_at = DateTimeField(
        default=datetime.utcnow,
    )

    confirmed_at = DateTimeField()

    cancelled_at = DateTimeField()

    meta = {
        "collection": "purchase_orders",
        "indexes": [
            {
                "fields": [
                    "organization",
                    "po_number",
                ],
                "unique": True,
            },
            {
                "fields": [
                    "organization",
                    "supplier",
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

class GoodsReceiptItem(EmbeddedDocument):
    product = ReferenceField(
        Product,
        required=True,
    )

    quantity_received = DecimalField(
        required=True,
        precision=2,
        min_value=0,
    )

class VendorBillItem(EmbeddedDocument):
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

class VendorBill(Document):
    organization = ReferenceField(
        Organization,
        required=True,
    )

    bill_number = StringField(
        required=True,
        max_length=50,
    )

    supplier_invoice_number = StringField(
        default="",
        max_length=100,
        strip=True,
    )

    purchase_order = ReferenceField(PurchaseOrder, required=False)

    supplier = ReferenceField(
        Supplier,
        required=True,
    )

    status = StringField(
        required=True,
        default="DRAFT",
        choices=(
            "DRAFT",
            "POSTED",
            "PARTIALLY_PAID",
            "PAID",
            "CANCELLED",
        ),
    )

    bill_date = DateTimeField(
        required=True,
    )

    due_date = DateTimeField()

    items = ListField(
        EmbeddedDocumentField(
            VendorBillItem
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

    supplier_name = StringField(
        default="",
        max_length=200,
    )

    supplier_address = StringField(
        default="",
        max_length=500,
    )

    supplier_city = StringField(
        default="",
        max_length=100,
    )

    supplier_state = StringField(
        default="",
        max_length=100,
    )

    supplier_country = StringField(
        default="India",
        max_length=100,
    )

    supplier_pincode = StringField(
        default="",
        max_length=20,
    )

    supplier_gstin = StringField(
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

    posted_at = DateTimeField()

    paid_at = DateTimeField()

    cancelled_at = DateTimeField()

    created_at = DateTimeField(
        default=datetime.utcnow,
    )

    updated_at = DateTimeField(
        default=datetime.utcnow,
    )

    meta = {
        "collection": "vendor_bills",
        "indexes": [
            {
                "fields": [
                    "organization",
                    "bill_number",
                ],
                "unique": True,
            },
            {
                "fields": [
                    "organization",
                    "supplier",
                    "-created_at",
                ],
            },
            {
                "fields": [
                    "organization",
                    "purchase_order",
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
                    "due_date",
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

class SupplierPaymentAllocation(
    EmbeddedDocument
):
    vendor_bill = ReferenceField(
        VendorBill,
        required=True,
    )

    amount = DecimalField(
        precision=2,
        required=True,
        min_value=0.01,
    )

class SupplierPayment(Document):
    organization = ReferenceField(
        Organization,
        required=True,
    )

    payment_number = StringField(
        required=True,
        max_length=50,
    )

    supplier = ReferenceField(
        Supplier,
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
            "CHEQUE",
            "UPI",
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
        strip=True,
    )

    allocations = ListField(
        EmbeddedDocumentField(
            SupplierPaymentAllocation
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
        "collection":
            "supplier_payments",

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
                    "supplier",
                    "-payment_date",
                ],
            },
            {
                "fields": [
                    "organization",
                    "reference_number",
                ],
            },
            {
                "fields": [
                    "organization",
                    "-payment_date",
                ],
            },
        ],
    }
    
class GoodsReceipt(Document):
    organization = ReferenceField(
        Organization,
        required=True,
    )

    grn_number = StringField(
        required=True,
        max_length=50,
    )

    purchase_order = ReferenceField(
        PurchaseOrder,
        required=True,
    )

    supplier = ReferenceField(
        Supplier,
        required=True,
    )

    warehouse = ReferenceField(
        Warehouse,
        required=True,
    )

    items = ListField(
        EmbeddedDocumentField(
            GoodsReceiptItem
        ),
        default=list,
    )

    notes = StringField(
        default="",
        max_length=1000,
    )

    received_by = ReferenceField(
        User,
        required=True,
    )

    received_at = DateTimeField(
        default=datetime.utcnow,
    )

    created_at = DateTimeField(
        default=datetime.utcnow,
    )

    meta = {
        "collection": "goods_receipts",
        "indexes": [
            {
                "fields": [
                    "organization",
                    "grn_number",
                ],
                "unique": True,
            },
            {
                "fields": [
                    "organization",
                    "purchase_order",
                    "-created_at",
                ],
            },
            {
                "fields": [
                    "organization",
                    "supplier",
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
                    "-created_at",
                ],
            },
        ],
    }

class PurchaseReturnItem(
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

class PurchaseReturn(
    Document
):
    organization = ReferenceField(
        Organization,
        required=True,
    )

    return_number = StringField(
        required=True,
        max_length=50,
    )

    purchase_order = ReferenceField(
        PurchaseOrder,
        required=True,
    )

    vendor_bill = ReferenceField(
        VendorBill,
        required=True,
    )

    supplier = ReferenceField(
        Supplier,
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
            PurchaseReturnItem
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
        "collection":
            "purchase_returns",
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
                    "vendor_bill",
                    "-created_at",
                ],
            },
            {
                "fields": [
                    "organization",
                    "purchase_order",
                    "-created_at",
                ],
            },
            {
                "fields": [
                    "organization",
                    "supplier",
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

class VendorDebitNoteItem(
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

class VendorDebitNote(
    Document
):
    organization = ReferenceField(
        Organization,
        required=True,
    )

    debit_note_number = StringField(
        required=True,
        max_length=50,
    )

    purchase_return = ReferenceField(
        PurchaseReturn,
        required=True,
    )

    vendor_bill = ReferenceField(
        VendorBill,
        required=True,
    )

    purchase_order = ReferenceField(
        PurchaseOrder,
        required=True,
    )

    supplier = ReferenceField(
        Supplier,
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

    debit_note_date = DateTimeField(
        required=True,
    )

    items = ListField(
        EmbeddedDocumentField(
            VendorDebitNoteItem
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
        "collection": "vendor_debit_notes",
        "indexes": [
            {
                "fields": [
                    "organization",
                    "debit_note_number",
                ],
                "unique": True,
            },
            {
                "fields": [
                    "organization",
                    "purchase_return",
                ],
                "unique": True,
            },
            {
                "fields": [
                    "organization",
                    "vendor_bill",
                    "-created_at",
                ],
            },
            {
                "fields": [
                    "organization",
                    "purchase_order",
                    "-created_at",
                ],
            },
            {
                "fields": [
                    "organization",
                    "supplier",
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