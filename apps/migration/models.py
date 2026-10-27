from datetime import datetime

from mongoengine import (
    DateTimeField,
    DictField,
    Document,
    IntField,
    ReferenceField,
    StringField,
)

from apps.accounts.models import User
from apps.organizations.models import Organization


class MigrationBatch(Document):

    organization = ReferenceField(
        Organization,
        required=True,
    )

    created_by = ReferenceField(
        User,
        required=True,
    )

    source_system = StringField(
        required=True,
        max_length=100,
    )

    migration_type = StringField(
        required=True,
        choices=(
            "PRODUCTS",
            "CATEGORIES",
            "CUSTOMERS",
            "SUPPLIERS",
            "WAREHOUSES",
            "INVENTORY",
            "SALES_ORDERS",
            "INVOICES",
            "CUSTOMER_PAYMENTS",
            "PURCHASE_ORDERS",
            "SALES_INVOICES",
            "GOODS_RECEIPTS",
            "EMPLOYEES", "VENDOR_BILLS",
            "SUPPLIER_PAYMENTS",
        ),
        max_length=50,
    )

    status = StringField(
        required=True,
        choices=(
            "CREATED",
            "UPLOADED",
            "VALIDATING",
            "VALIDATED",
            "IMPORTING",
            "COMPLETED",
            "COMPLETED_WITH_ERRORS",
            "FAILED",
            "CANCELLED",
        ),
        default="CREATED",
        max_length=30,
    )

    upload_id = StringField(
        max_length=100,
    )

    job_id = StringField(
        max_length=100,
    )

    mapping = DictField(
        default=dict,
    )

    options = DictField(
        default=dict,
    )

    total_rows = IntField(
        default=0,
        min_value=0,
    )

    valid_rows = IntField(
        default=0,
        min_value=0,
    )

    invalid_rows = IntField(
        default=0,
        min_value=0,
    )

    imported_rows = IntField(
        default=0,
        min_value=0,
    )

    skipped_rows = IntField(
        default=0,
        min_value=0,
    )

    failed_rows = IntField(
        default=0,
        min_value=0,
    )

    validation_result = DictField(
        default=dict,
    )

    import_result = DictField(
        default=dict,
    )

    error_summary = DictField(
        default=dict,
    )

    started_at = DateTimeField(
        required=False,
    )

    completed_at = DateTimeField(
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
            "migration_batches",

        "indexes": [
            "organization",
            "created_by",
            "source_system",
            "migration_type",
            "status",
            "created_at",

            (
                "organization",
                "status",
                "created_at",
            ),

            (
                "organization",
                "migration_type",
                "created_at",
            ),
        ],
    }