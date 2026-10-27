from datetime import datetime

from mongoengine import (
    Document,
    StringField,
    ReferenceField,
    DecimalField,
    BooleanField,
    DateTimeField,
)

from apps.organizations.models import Organization


class Category(Document):
    organization = ReferenceField(
        Organization,
        required=True,
    )

    name = StringField(
        required=True,
        max_length=100,
        strip=True,
    )

    description = StringField(
        default="",
        max_length=500,
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
        "collection": "categories",
        "indexes": [
            {
                "fields": ["organization", "name"],
                "unique": True,
            },
        ],
    }


class Product(Document):
    organization = ReferenceField(
        Organization,
        required=True,
    )

    sku = StringField(
        required=True,
        max_length=50,
        strip=True,
    )

    name = StringField(
        required=True,
        max_length=200,
        strip=True,
    )

    description = StringField(
        default="",
        max_length=1000,
        strip=True,
    )

    category = ReferenceField(
        Category,
        required=True,
    )

    brand = StringField(
        default="",
        max_length=100,
        strip=True,
    )

    unit = StringField(
        required=True,
        max_length=30,
        strip=True,
    )

    cost_price = DecimalField(
        precision=2,
        default=0,
    )

    selling_price = DecimalField(
        precision=2,
        default=0,
    )

    barcode = StringField(
        default="",
        max_length=100,
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
        "collection": "products",
        "indexes": [
            {
                "fields": ["organization", "sku"],
                "unique": True,
            },
            {
                "fields": ["organization", "name"],
            },
            {
                "fields": ["organization", "barcode"],
            },
        ],
    }