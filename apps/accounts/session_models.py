from datetime import datetime

from mongoengine import (
    DateTimeField,
    Document,
    StringField,
)


class MongoSession(Document):

    session_key = StringField(
        required=True,
        unique=True,
    )

    session_data = StringField(
        required=True,
    )

    expire_date = DateTimeField(
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
            "ims_sessions",

        "indexes": [
            "session_key",
            "expire_date",
        ],
    }