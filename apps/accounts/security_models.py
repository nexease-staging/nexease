from datetime import datetime

from mongoengine import (
    DateTimeField,
    Document,
    IntField,
    StringField,
)


class LoginAttempt(Document):

    identifier = StringField(
        required=True,
        unique=True,
    )

    failure_count = IntField(
        default=0,
    )

    blocked_until = DateTimeField(
        null=True,
    )

    last_failure_at = DateTimeField(
        null=True,
    )

    created_at = DateTimeField(
        default=datetime.utcnow,
    )

    updated_at = DateTimeField(
        default=datetime.utcnow,
    )

    meta = {
        "collection":
            "login_attempts",

        "indexes": [
            "identifier",
            "blocked_until",
        ],
    }