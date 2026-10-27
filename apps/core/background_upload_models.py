from datetime import datetime

from mongoengine import (
    BinaryField,
    DateTimeField,
    DictField,
    Document,
    IntField,
    ReferenceField,
    StringField,
)

from apps.accounts.models import User
from apps.organizations.models import Organization


class BackgroundUpload(Document):

    organization = ReferenceField(
        Organization,
        required=True,
    )

    uploaded_by = ReferenceField(
        User,
        required=True,
    )

    purpose = StringField(
        required=True,
        choices=(
            "BANK_STATEMENT_IMPORT",
            "DATA_MIGRATION",
        ),
        max_length=50,
    )

    filename = StringField(
        required=True,
        max_length=255,
    )

    content_type = StringField(
        max_length=100,
    )

    extension = StringField(
        required=True,
        choices=(
            ".csv",
            ".xlsx",
        ),
        max_length=10,
    )

    size = IntField(
        required=True,
        min_value=1,
    )

    content = BinaryField(
        required=True,
    )

    status = StringField(
        required=True,
        choices=(
            "AVAILABLE",
            "CONSUMED",
            "FAILED",
        ),
        default="AVAILABLE",
        max_length=20,
    )

    result = DictField(
        default=dict,
    )

    consumed_at = DateTimeField(
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
            "background_uploads",

        "indexes": [
            "organization",
            "uploaded_by",
            "purpose",
            "status",
            "created_at",

            (
                "organization",
                "purpose",
                "status",
                "created_at",
            ),
        ],
    }