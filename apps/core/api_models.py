from datetime import datetime

from mongoengine import (
    DateTimeField,
    Document,
    IntField,
    StringField,
)


class APIRateLimitBucket(
    Document
):

    bucket_key = StringField(
        required=True,
        unique=True,
    )

    scope = StringField(
        required=True,
        max_length=150,
    )

    identity_hash = StringField(
        required=True,
        max_length=64,
    )

    request_method = StringField(
        required=True,
        max_length=10,
    )

    request_count = IntField(
        required=True,
        default=0,
        min_value=0,
    )

    window_started_at = (
        DateTimeField(
            required=True,
        )
    )

    expires_at = DateTimeField(
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
            "api_rate_limit_buckets",

        "indexes": [
            {
                "fields": [
                    "bucket_key",
                ],
                "unique":
                    True,
            },

            {
                "fields": [
                    "expires_at",
                ],
                "expireAfterSeconds":
                    0,
            },

            "scope",
            "identity_hash",
        ],
    }