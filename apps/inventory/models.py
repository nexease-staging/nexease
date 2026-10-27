from datetime import datetime
from apps.accounts.models import User
from mongoengine import (
    Document,
    StringField,
    ReferenceField,
    BooleanField,
    DateTimeField,
    DecimalField,
)
from apps.organizations.models import Organization
from apps.products.models import Product


class Warehouse(Document):
    organization = ReferenceField(
        Organization,
        required=True,
    )

    name = StringField(
        required=True,
        max_length=150,
        strip=True,
    )

    code = StringField(
        required=True,
        max_length=50,
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
        "collection": "warehouses",
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
                "unique": True,
            },
        ],
    }


class Inventory(Document):
    organization = ReferenceField(
        Organization,
        required=True,
    )

    product = ReferenceField(
        Product,
        required=True,
    )

    warehouse = ReferenceField(
        Warehouse,
        required=True,
    )

    quantity = DecimalField(
        precision=2,
        default=0,
        min_value=0,
    )

    reserved_quantity = DecimalField(
        precision=2,
        default=0,
        min_value=0,
    )

    created_at = DateTimeField(
        default=datetime.utcnow,
    )

    updated_at = DateTimeField(
        default=datetime.utcnow,
    )

    meta = {
        "collection": "inventory",
        "indexes": [
            {
                "fields": [
                    "organization",
                    "product",
                    "warehouse",
                ],
                "unique": True,
            },
            {
                "fields": [
                    "organization",
                    "warehouse",
                ],
            },
            {
                "fields": [
                    "organization",
                    "product",
                ],
            },
        ],
    }

class StockMovement(Document):
    organization = ReferenceField(
        Organization,
        required=True,
    )

    inventory = ReferenceField(
        Inventory,
        required=True,
    )

    product = ReferenceField(
        Product,
        required=True,
    )

    warehouse = ReferenceField(
        Warehouse,
        required=True,
    )

    movement_type = StringField(
        required=True,
        choices=[
            "OPENING_STOCK",
            "STOCK_IN",
            "STOCK_OUT",
            "ADJUSTMENT_IN",
            "ADJUSTMENT_OUT",
            "RESERVATION",
            "RESERVATION_RELEASE",
            "TRANSFER_OUT",
            "TRANSFER_IN",
            "SALES_RETURN",
            "PURCHASE_RETURN",
        ],
        max_length=50,
    )

    quantity = DecimalField(
        precision=2,
        required=True,
    )

    quantity_before = DecimalField(
        precision=2,
        required=True,
        min_value=0,
    )

    quantity_after = DecimalField(
        precision=2,
        required=True,
        min_value=0,
    )

    reserved_before = DecimalField(
        precision=2,
        default=0,
        min_value=0,
    )

    reserved_after = DecimalField(
        precision=2,
        default=0,
        min_value=0,
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

    notes = StringField(
        default="",
        max_length=1000,
        strip=True,
    )

    created_by = ReferenceField(
        User,
        required=True,
    )

    created_at = DateTimeField(
        default=datetime.utcnow,
    )

    meta = {
        "collection": "stock_movements",
        "indexes": [
            {
                "fields": [
                    "organization",
                    "inventory",
                    "-created_at",
                ],
            },
            {
                "fields": [
                    "organization",
                    "product",
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
                    "movement_type",
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

class StockTransfer(Document):
    organization = ReferenceField(
        Organization,
        required=True,
    )

    transfer_number = StringField(
        required=True,
        max_length=50,
        strip=True,
    )

    product = ReferenceField(
        Product,
        required=True,
    )

    source_warehouse = ReferenceField(
        Warehouse,
        required=True,
    )

    destination_warehouse = ReferenceField(
        Warehouse,
        required=True,
    )

    source_inventory = ReferenceField(
        Inventory,
        required=True,
    )

    destination_inventory = ReferenceField(
        Inventory,
        required=True,
    )

    quantity = DecimalField(
        precision=2,
        required=True,
        min_value=0,
    )

    status = StringField(
        required=True,
        choices=[
            "DRAFT",
            "COMPLETED",
            "CANCELLED",
        ],
        default="DRAFT",
        max_length=30,
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

    created_at = DateTimeField(
        default=datetime.utcnow,
    )

    completed_at = DateTimeField(
        null=True,
    )

    meta = {
        "collection": "stock_transfers",
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
                    "product",
                    "-created_at",
                ],
            },
            {
                "fields": [
                    "organization",
                    "source_warehouse",
                    "-created_at",
                ],
            },
            {
                "fields": [
                    "organization",
                    "destination_warehouse",
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
        ],
    }