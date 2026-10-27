from datetime import datetime
from decimal import Decimal

from mongoengine import (
    BooleanField,
    DateTimeField,
    DecimalField,
    Document,
    ObjectIdField,
    EmbeddedDocument,
    EmbeddedDocumentField,
    ListField,
    ReferenceField,
    StringField,
)

from apps.accounts.models import User
from apps.organizations.models import Organization


class BankAccount(Document):
    organization = ReferenceField(
        Organization,
        required=True,
    )

    account_name = StringField(
        required=True,
        max_length=150,
        strip=True,
    )

    account_type = StringField(
        required=True,
        choices=(
            "BANK",
            "CASH",
        ),
        max_length=20,
    )

    bank_name = StringField(
        default="",
        max_length=150,
        strip=True,
    )

    account_number = StringField(
        default="",
        max_length=100,
        strip=True,
    )

    ifsc_code = StringField(
        default="",
        max_length=20,
        strip=True,
    )

    currency = StringField(
        required=True,
        default="INR",
        max_length=10,
        strip=True,
    )

    opening_balance = DecimalField(
        precision=2,
        default=Decimal("0"),
    )

    current_balance = DecimalField(
        precision=2,
        default=Decimal("0"),
    )

    is_active = BooleanField(
        default=True,
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
        "collection": "bank_accounts",
        "indexes": [
            {
                "fields": [
                    "organization",
                    "account_name",
                ],
                "unique": True,
            },
            {
                "fields": [
                    "organization",
                    "account_type",
                    "is_active",
                ],
            },
            {
                "fields": [
                    "organization",
                    "account_number",
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

class BankTransaction(Document):
    organization = ReferenceField(
        Organization,
        required=True,
    )

    bank_account = ReferenceField(
        BankAccount,
        required=True,
    )

    transaction_number = StringField(
        required=True,
        max_length=50,
    )

    transaction_type = StringField(
        required=True,
        choices=(
            "OPENING_BALANCE",
            "MONEY_IN",
            "MONEY_OUT",
            "TRANSFER_IN",
            "TRANSFER_OUT",
            "BANK_CHARGE",
            "INTEREST",
            "OTHER_IN",
            "OTHER_OUT",
        ),
        max_length=30,
    )

    transaction_date = DateTimeField(
        required=True,
    )

    amount = DecimalField(
        precision=2,
        required=True,
        min_value=0,
    )

    balance_before = DecimalField(
        precision=2,
        required=True,
    )

    balance_after = DecimalField(
        precision=2,
        required=True,
    )

    reference_type = StringField(
        default="",
        max_length=100,
        strip=True,
    )

    reference_id = StringField(
        default="",
        max_length=100,
        strip=True,
    )

    external_reference = StringField(
        default="",
        max_length=150,
        strip=True,
    )

    description = StringField(
        default="",
        max_length=1000,
        strip=True,
    )

    reconciliation_status = StringField(
        required=True,
        default="UNRECONCILED",
        choices=(
            "UNRECONCILED",
            "RECONCILED",
        ),
        max_length=20,
    )

    reconciled_at = DateTimeField()

    created_by = ReferenceField(
        User,
        required=True,
    )

    created_at = DateTimeField(
        default=datetime.utcnow,
    )

    meta = {
        "collection": "bank_transactions",
        "indexes": [
            {
                "fields": [
                    "organization",
                    "transaction_number",
                ],
                "unique": True,
            },
            {
                "fields": [
                    "organization",
                    "bank_account",
                    "transaction_date",
                    "created_at",
                ],
            },
            {
                "fields": [
                    "organization",
                    "bank_account",
                    "transaction_type",
                ],
            },
            {
                "fields": [
                    "organization",
                    "reference_type",
                    "reference_id",
                ],
            },
            {
                "fields": [
                    "organization",
                    "reconciliation_status",
                    "transaction_date",
                ],
            },
            {
                "fields": [
                    "organization",
                    "external_reference",
                ],
            },
                        {
                "fields": [
                    "organization",
                    "bank_account",
                    "reference_type",
                    "reference_id",
                ],
            },
        ],
    }

class BankTransfer(Document):
    organization = ReferenceField(
        Organization,
        required=True,
    )

    transfer_number = StringField(
        required=True,
        max_length=50,
    )

    source_account = ReferenceField(
        BankAccount,
        required=True,
    )

    destination_account = ReferenceField(
        BankAccount,
        required=True,
    )

    transfer_date = DateTimeField(
        required=True,
    )

    amount = DecimalField(
        required=True,
        precision=2,
        min_value=0,
    )

    status = StringField(
        required=True,
        default="DRAFT",
        choices=(
            "DRAFT",
            "POSTED",
            "CANCELLED",
        ),
        max_length=20,
    )

    reference = StringField(
        default="",
        max_length=150,
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

    posted_at = DateTimeField()

    cancelled_at = DateTimeField()

    created_at = DateTimeField(
        default=datetime.utcnow,
    )

    updated_at = DateTimeField(
        default=datetime.utcnow,
    )

    meta = {
        "collection": "bank_transfers",
        "indexes": [
            {
                "fields": [
                    "organization",
                    "transfer_number",
                ],
                "unique": True,
            },
            {
                "fields": [
                    "organization",
                    "source_account",
                    "-transfer_date",
                ],
            },
            {
                "fields": [
                    "organization",
                    "destination_account",
                    "-transfer_date",
                ],
            },
            {
                "fields": [
                    "organization",
                    "status",
                    "-transfer_date",
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

class BankStatementLine(
    EmbeddedDocument
):
    line_number = StringField(
        required=True,
        max_length=50,
    )

    transaction_date = DateTimeField(
        required=True,
    )

    value_date = DateTimeField()

    description = StringField(
        default="",
        max_length=1000,
        strip=True,
    )

    external_reference = StringField(
        default="",
        max_length=150,
        strip=True,
    )

    debit_amount = DecimalField(
        precision=2,
        default=Decimal("0"),
        min_value=0,
    )

    credit_amount = DecimalField(
        precision=2,
        default=Decimal("0"),
        min_value=0,
    )

    running_balance = DecimalField(
        precision=2,
    )

    match_status = StringField(
        required=True,
        default="UNMATCHED",
        choices=(
            "UNMATCHED",
            "MATCHED",
            "IGNORED",
        ),
        max_length=20,
    )

    matched_transaction = ReferenceField(
        BankTransaction,
        required=False,
    )

    matched_at = DateTimeField()

class BankStatement(
    Document
):
    organization = ReferenceField(
        Organization,
        required=True,
    )

    statement_number = StringField(
        required=True,
        max_length=50,
    )

    bank_account = ReferenceField(
        BankAccount,
        required=True,
    )

    statement_start_date = DateTimeField(
        required=True,
    )

    statement_end_date = DateTimeField(
        required=True,
    )

    opening_balance = DecimalField(
        precision=2,
        required=True,
    )

    closing_balance = DecimalField(
        precision=2,
        required=True,
    )

    source_filename = StringField(
        default="",
        max_length=255,
        strip=True,
    )

    source_type = StringField(
        required=True,
        default="MANUAL",
        choices=(
            "MANUAL",
            "CSV",
            "XLSX",
        ),
        max_length=20,
    )

    status = StringField(
        required=True,
        default="IMPORTED",
        choices=(
            "IMPORTED",
            "PARTIALLY_RECONCILED",
            "RECONCILED",
            "CANCELLED",
        ),
        max_length=30,
    )

    lines = ListField(
        EmbeddedDocumentField(
            BankStatementLine
        ),
        default=list,
    )

    created_by = ReferenceField(
        User,
        required=True,
    )

    reconciled_at = DateTimeField()

    cancelled_at = DateTimeField()

    created_at = DateTimeField(
        default=datetime.utcnow,
    )

    updated_at = DateTimeField(
        default=datetime.utcnow,
    )

    meta = {
        "collection":
            "bank_statements",

        "indexes": [
            {
                "fields": [
                    "organization",
                    "statement_number",
                ],
                "unique": True,
            },
            {
                "fields": [
                    "organization",
                    "bank_account",
                    "-statement_start_date",
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

class BankPaymentSuggestion(Document):
    organization = ReferenceField(
        Organization,
        required=True,
    )

    statement = ReferenceField(
        BankStatement,
        required=True,
    )

    line_number = StringField(
        required=True,
        max_length=50,
    )

    suggestion_type = StringField(
        required=True,
        choices=(
            "CUSTOMER_RECEIPT",
            "SUPPLIER_PAYMENT",
        ),
        max_length=30,
    )

    invoice = ReferenceField(
        "Invoice",
        required=False,
    )

    vendor_bill = ReferenceField(
        "VendorBill",
        required=False,
    )

    amount = DecimalField(
        precision=2,
        required=True,
        min_value=0.01,
    )

    confidence = DecimalField(
        precision=2,
        required=True,
        default=Decimal("0"),
        min_value=0,
        max_value=100,
    )

    match_reason = StringField(
        default="",
        max_length=1000,
        strip=True,
    )

    status = StringField(
        required=True,
        default="PENDING",
        choices=(
            "PENDING",
            "CONFIRMED",
            "REJECTED",
        ),
        max_length=20,
    )

    created_by = ReferenceField(
        User,
        required=True,
    )

    confirmed_at = DateTimeField()

    rejected_at = DateTimeField()
    executed_at = DateTimeField()

    payment_reference = StringField(
        default="",
        max_length=100,
        strip=True,
    )
    created_at = DateTimeField(
        default=datetime.utcnow,
    )

    updated_at = DateTimeField(
        default=datetime.utcnow,
    )

    meta = {
        "collection":
            "bank_payment_suggestions",

        "indexes": [
            {
                "fields": [
                    "organization",
                    "statement",
                    "line_number",
                ],
                "unique": True,
            },
            {
                "fields": [
                    "organization",
                    "suggestion_type",
                    "status",
                    "-created_at",
                ],
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
                    "vendor_bill",
                    "-created_at",
                ],
            },
        ],
    }

class ChartOfAccount(Document):
    organization = ReferenceField(
        Organization,
        required=True,
    )

    account_code = StringField(
        required=True,
        max_length=30,
        strip=True,
    )

    account_name = StringField(
        required=True,
        max_length=150,
        strip=True,
    )

    account_type = StringField(
        required=True,
        choices=(
            "ASSET",
            "LIABILITY",
            "EQUITY",
            "REVENUE",
            "EXPENSE",
        ),
        max_length=20,
    )

    account_subtype = StringField(
        default="",
        max_length=50,
        strip=True,
    )

    normal_balance = StringField(
        required=True,
        choices=(
            "DEBIT",
            "CREDIT",
        ),
        max_length=10,
    )

    system_key = StringField(
        default="",
        max_length=100,
        strip=True,
    )

    description = StringField(
        default="",
        max_length=500,
        strip=True,
    )

    is_system_account = BooleanField(
        default=False,
    )

    is_active = BooleanField(
        default=True,
    )

    allow_manual_posting = BooleanField(
        default=True,
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
            "chart_of_accounts",

        "indexes": [
            {
                "fields": [
                    "organization",
                    "account_code",
                ],
                "unique": True,
            },
            {
                "fields": [
                    "organization",
                    "account_name",
                ],
            },
            {
                "fields": [
                    "organization",
                    "account_type",
                    "is_active",
                ],
            },
            {
                "fields": [
                    "organization",
                    "system_key",
                ],
                "sparse": True,
            },
            {
                "fields": [
                    "organization",
                    "-created_at",
                ],
            },
        ],
    }

class JournalLine(EmbeddedDocument):
    account = ReferenceField(
        ChartOfAccount,
        required=True,
    )

    description = StringField(
        default="",
        max_length=500,
        strip=True,
    )

    debit = DecimalField(
        precision=2,
        required=True,
        default=Decimal("0.00"),
        min_value=0,
    )

    credit = DecimalField(
        precision=2,
        required=True,
        default=Decimal("0.00"),
        min_value=0,
    )


class JournalEntry(Document):
    organization = ReferenceField(
        Organization,
        required=True,
    )

    journal_number = StringField(
        required=True,
        max_length=50,
    )

    journal_date = DateTimeField(
        required=True,
    )

    description = StringField(
        default="",
        max_length=1000,
        strip=True,
    )

    source_type = StringField(
        default="MANUAL",
        choices=(
            "MANUAL",
            "PAYROLL", "SALARY_PAYMENT", "EMPLOYEE_ADVANCE", "DAILY_EXPENSE",
            "SALES_INVOICE",
            "CUSTOMER_PAYMENT",
            "SALES_CREDIT_NOTE",
            "VENDOR_BILL",
            "SUPPLIER_PAYMENT",
            "VENDOR_DEBIT_NOTE",
            "BANK_TRANSACTION",
            "OPENING_BALANCE",
            "REVERSAL",
        ),
        max_length=40,
    )

    source_id = StringField(
        default="",
        max_length=100,
        strip=True,
    )

    lines = ListField(
        EmbeddedDocumentField(
            JournalLine
        ),
        required=True,
    )

    total_debit = DecimalField(
        precision=2,
        required=True,
        default=Decimal("0.00"),
        min_value=0,
    )

    total_credit = DecimalField(
        precision=2,
        required=True,
        default=Decimal("0.00"),
        min_value=0,
    )

    status = StringField(
        required=True,
        default="DRAFT",
        choices=(
            "DRAFT",
            "POSTED",
            "REVERSED",
        ),
        max_length=20,
    )

    posted_at = DateTimeField()

    reversed_at = DateTimeField()

    reversal_of = ReferenceField(
        "JournalEntry",
        required=False,
    )

    reversed_by = ReferenceField(
        "JournalEntry",
        required=False,
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
            "journal_entries",

        "indexes": [
            {
                "fields": [
                    "organization",
                    "journal_number",
                ],
                "unique": True,
            },
            {
                "fields": [
                    "organization",
                    "journal_date",
                ],
            },
            {
                "fields": [
                    "organization",
                    "status",
                    "-journal_date",
                ],
            },
            {
                "fields": [
                    "organization",
                    "source_type",
                    "source_id",
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

class DocumentAccessLog(Document):

    organization = ReferenceField(
        Organization,
        required=True,
    )

    user = ReferenceField(
        User,
        required=True,
    )

    document_type = StringField(
        required=True,
        max_length=50,
    )

    document_id = StringField(
        required=True,
        max_length=100,
    )

    document_number = StringField(
        required=True,
        max_length=100,
    )

    action = StringField(
        required=True,
        choices=(
            "PDF_DOWNLOAD",
        ),
        default="PDF_DOWNLOAD",
    )

    created_at = DateTimeField(
        default=datetime.utcnow,
    )

    meta = {
        "collection":
            "document_access_logs",

        "indexes": [
            "organization",
            "user",
            "document_type",
            "document_id",
            "created_at",

            (
                "organization",
                "document_type",
                "created_at",
            ),
        ],
    }

class DocumentDeliveryLog(Document):

    organization = ReferenceField(
        Organization,
        required=True,
    )

    user = ReferenceField(
        User,
        required=True,
    )

    document_type = StringField(
        required=True,
        max_length=50,
    )

    document_id = StringField(
        required=True,
        max_length=100,
    )

    document_number = StringField(
        required=True,
        max_length=100,
    )

    channel = StringField(
        required=True,
        choices=(
            "EMAIL",
            "WHATSAPP",
        ),
    )

    recipient = StringField(
        required=True,
        max_length=255,
    )
    subject = StringField(
        max_length=200,
    )

    recipient_overridden = BooleanField(
        default=False,
    )

    custom_subject = BooleanField(
        default=False,
    )

    custom_message = BooleanField(
        default=False,
    )
    background_job_key = StringField(
        required=False,
        max_length=200,
    )
    status = StringField(
        required=True,
        choices=(
            "PENDING",
            "SENT",
            "FAILED",
        ),
        default="PENDING",
    )

    error_message = StringField(
        max_length=500,
    )

    sent_at = DateTimeField(
        required=False,
    )

    created_at = DateTimeField(
        default=datetime.utcnow,
    )

    updated_at = DateTimeField(
        default=datetime.utcnow,
    )

    meta = {
        "collection":
            "document_delivery_logs",

        "indexes": [
            "organization",
            "background_job_key",
            "user",
            "document_type",
            "document_id",
            "channel",
            "recipient",
            "status",
            "created_at",

            (
                "organization",
                "document_type",
                "created_at",
            ),

            (
                "organization",
                "channel",
                "created_at",
            ),
        ],
    }