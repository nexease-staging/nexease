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
    item_type = StringField(default="goods", choices=("goods", "service"))
    hsn_code = StringField(default="", max_length=8)

    def clean(self):
        import re
        from mongoengine import ValidationError
        if self.item_type not in ("goods","service"):raise ValidationError("Choose goods or service.")
        if self.hsn_code and not re.fullmatch(r"[0-9]{4}|[0-9]{6}|[0-9]{8}", self.hsn_code):
            raise ValidationError("HSN/SAC must contain 4, 6 or 8 digits.")
        if self.item_type == "service" and self.hsn_code and len(self.hsn_code) != 6:
            raise ValidationError("Enter a six-digit SAC for services.")

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