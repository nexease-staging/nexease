from datetime import datetime, timezone

from mongoengine import (
    DateTimeField,
    Document,
    ReferenceField,
    StringField,
    IntField,
)

from apps.accounts.models import User


class PasswordResetToken(Document):
    user = ReferenceField(
        User,
        required=True,
    )

    token_hash = StringField(
        required=True,
        unique=True,
        max_length=64,
    )

    generation = IntField(
        required=True,
        min_value=1,
    )

    created_at = DateTimeField(
        required=True,
        default=lambda: datetime.now(
            timezone.utc
        ),
    )

    expires_at = DateTimeField(
        required=True,
    )

    used_at = DateTimeField(
        null=True,
        default=None,
    )

    meta = {
        "collection": "password_reset_tokens",
        "indexes": [
            "user",
            "used_at",
            {
                "fields": [
                    "expires_at",
                ],
                "expireAfterSeconds": 0,
            },
        ],
    }

    @property
    def is_used(self):
        return self.used_at is not None