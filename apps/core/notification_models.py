from datetime import datetime

from mongoengine import (
    BooleanField,
    DateTimeField,
    Document,
    ReferenceField,
    StringField,
)

from apps.accounts.models import User
from apps.organizations.models import Organization


class Notification(Document):

    NOTIFICATION_TYPES = (
        "SYSTEM",
        "JOB_SUCCEEDED",
        "JOB_FAILED",
        "IMPORT_COMPLETED",
        "DOCUMENT_SENT",
    )

    SEVERITIES = (
        "INFO",
        "SUCCESS",
        "WARNING",
        "ERROR",
    )

    organization = ReferenceField(
        Organization,
        required=True,
    )

    recipient = ReferenceField(
        User,
        required=True,
    )

    notification_type = StringField(
        required=True,
        choices=NOTIFICATION_TYPES,
        max_length=50,
    )

    title = StringField(
        required=True,
        max_length=200,
    )

    message = StringField(
        required=True,
        max_length=1000,
    )

    severity = StringField(
        required=True,
        choices=SEVERITIES,
        default="INFO",
        max_length=20,
    )

    resource_type = StringField(
        required=False,
        max_length=100,
    )

    resource_id = StringField(
        required=False,
        max_length=100,
    )

    action_url = StringField(
        required=False,
        max_length=500,
    )

    is_read = BooleanField(
        default=False,
    )

    read_at = DateTimeField()

    background_job_key = StringField(
        required=False,
        max_length=200,
    )

    created_at = DateTimeField(
        default=datetime.utcnow,
    )

    meta = {
        "collection": "notifications",
        "indexes": [
            (
                "organization",
                "recipient",
                "-created_at",
            ),
            (
                "organization",
                "recipient",
                "is_read",
                "-created_at",
            ),
            {
                "fields": [
                    "organization",
                    "background_job_key",
                ],
                "unique": True,
                "partialFilterExpression": {
                    "background_job_key": {
                        "$type": "string",
                    },
                },
            },
        ],
    }