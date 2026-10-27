from datetime import datetime

from mongoengine import (
    DateTimeField,
    DictField,
    Document,
    IntField,
    ReferenceField,
    StringField,
)

from apps.accounts.models import User
from apps.organizations.models import Organization


class BackgroundJob(Document):

    organization = ReferenceField(
        Organization,
        required=True,
    )

    created_by = ReferenceField(
        User,
        required=True,
    )

    job_type = StringField(
        required=True,
        choices=(
            "BANK_STATEMENT_IMPORT",
            "DOCUMENT_EMAIL",
            "NOTIFICATION",
            "DATA_MIGRATION_VALIDATE",
            "DATA_MIGRATION_IMPORT",
        ),
    )

    status = StringField(
        required=True,
        choices=(
            "PENDING",
            "RUNNING",
            "RETRYING",
            "SUCCEEDED",
            "FAILED",
        ),
        default="PENDING",
        max_length=20,
    )

    payload = DictField(
        default=dict,
    )

    result = DictField(
        default=dict,
    )
    
    idempotency_key = StringField(
        required=True,
        max_length=200,
    )

    attempts = IntField(
        default=0,
        min_value=0,
    )

    max_attempts = IntField(
        default=3,
        min_value=1,
    )

    available_at = DateTimeField(
        default=datetime.utcnow,
    )

    started_at = DateTimeField(
        required=False,
    )

    completed_at = DateTimeField(
        required=False,
    )

    last_error = StringField(
        max_length=1000,
    )

    worker_id = StringField(
        max_length=200,
    )

    locked_at = DateTimeField(
        required=False,
    )

    lock_expires_at = DateTimeField(
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
            "background_jobs",

        "indexes": [
            "organization",
            "created_by",
            "job_type",
            "status",
            "available_at",
            "created_at",
            "lock_expires_at",

            (
                "organization",
                "status",
                "available_at",
            ),

            (
                "organization",
                "job_type",
                "created_at",
            ),

            {
                "fields": [
                    "organization",
                    "idempotency_key",
                ],
                "unique": True,
            },
        ],
    }