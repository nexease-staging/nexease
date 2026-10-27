from datetime import datetime

from mongoengine import (
    Document,
    StringField,
    BooleanField,
    DateTimeField,
    ReferenceField,
    ListField,
)

from apps.organizations.models import Organization


class Permission(Document):
    code = StringField(
        required=True,
        unique=True,
        max_length=100,
    )

    name = StringField(
        required=True,
        max_length=150,
    )

    description = StringField(
        max_length=500,
    )

    module = StringField(
        required=True,
        max_length=100,
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
        "collection": "permissions",
    }


class Role(Document):
    organization = ReferenceField(
        Organization,
        required=True,
    )

    name = StringField(
        required=True,
        max_length=100,
    )

    description = StringField(
        max_length=500,
    )
    
    is_system = BooleanField(
        default=False,
    )

    permissions = ListField(
        ReferenceField(Permission),
        default=list,
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
        "collection": "roles",
        "indexes": [
            {
                "fields": [
                    "organization",
                    "name",
                ],
                "unique": True,
            }
        ],
    }