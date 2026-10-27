from datetime import datetime, timedelta

from mongoengine.errors import NotUniqueError

from apps.core.background_job_models import BackgroundJob
from pymongo import ReturnDocument


class BackgroundJobRepository:

    @staticmethod
    def create(
        *,
        organization,
        created_by,
        job_type,
        payload,
        idempotency_key,
        max_attempts=3,
        available_at=None,
    ):
        available_at = (
            available_at
            or datetime.utcnow()
        )

        job = BackgroundJob(
            organization=organization,
            created_by=created_by,
            job_type=job_type,
            payload=payload or {},
            idempotency_key=idempotency_key,
            max_attempts=max_attempts,
            available_at=available_at,
            status="PENDING",
            attempts=0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        try:
            job.save()
        except NotUniqueError:
            return (
                BackgroundJob.objects(
                    organization=organization,
                    idempotency_key=idempotency_key,
                )
                .first()
            )

        return job

    @staticmethod
    def get_by_id(
        *,
        organization,
        job_id,
    ):
        return (
            BackgroundJob.objects(
                organization=organization,
                id=job_id,
            )
            .first()
        )

    @staticmethod
    def get_for_user(
        *,
        organization,
        created_by,
        job_id,
    ):
        return (
            BackgroundJob.objects(
                organization=organization,
                created_by=created_by,
                id=job_id,
            )
            .first()
        )

    @staticmethod
    def list_for_user(
        *,
        organization,
        created_by,
        status=None,
        job_type=None,
        limit=50,
    ):
        queryset = BackgroundJob.objects(
            organization=organization,
            created_by=created_by,
        )

        if status:
            queryset = queryset.filter(
                status=status,
            )

        if job_type:
            queryset = queryset.filter(
                job_type=job_type,
            )

        return (
            queryset
            .order_by(
                "-created_at"
            )
            .limit(
                limit
            )
        )

    @staticmethod
    def get_by_idempotency_key(
        *,
        organization,
        idempotency_key,
    ):
        return (
            BackgroundJob.objects(
                organization=organization,
                idempotency_key=idempotency_key,
            )
            .first()
        )

    @staticmethod
    def claim_next(
        *,
        worker_id,
        lease_seconds=300,
    ):
        now = datetime.utcnow()

        lock_expires_at = (
            now
            + timedelta(
                seconds=lease_seconds,
            )
        )

        collection = (
            BackgroundJob
            ._get_collection()
        )

        claimed = (
            collection
            .find_one_and_update(
                {
                    "status": "PENDING",

                    "available_at": {
                        "$lte": now,
                    },

                    "$or": [
                        {
                            "lock_expires_at": None,
                        },
                        {
                            "lock_expires_at": {
                                "$exists": False,
                            },
                        },
                        {
                            "lock_expires_at": {
                                "$lte": now,
                            },
                        },
                    ],
                },
                {
                    "$set": {
                        "status":
                            "RUNNING",

                        "worker_id":
                            worker_id,

                        "locked_at":
                            now,

                        "lock_expires_at":
                            lock_expires_at,

                        "started_at":
                            now,

                        "updated_at":
                            now,
                    },

                    "$inc": {
                        "attempts": 1,
                    },
                },
                sort=[
                    (
                        "available_at",
                        1,
                    ),
                    (
                        "created_at",
                        1,
                    ),
                ],
                return_document=ReturnDocument.AFTER,
            )
        )

        if not claimed:
            return None

        return (
            BackgroundJob
            ._from_son(
                claimed
            )
        )

    @staticmethod
    def mark_succeeded(
        *,
        job,
        result=None,
    ):
        now = datetime.utcnow()

        job.status = "SUCCEEDED"
        job.result = result or {}
        job.completed_at = now
        job.updated_at = now

        job.worker_id = None
        job.locked_at = None
        job.lock_expires_at = None
        job.last_error = None

        job.save()

        return job

    @staticmethod
    def mark_retrying(
        *,
        job,
        error_message,
        available_at,
    ):
        now = datetime.utcnow()

        job.status = "RETRYING"
        job.last_error = (
            error_message[:1000]
            if error_message
            else None
        )

        job.available_at = available_at
        job.updated_at = now

        job.worker_id = None
        job.locked_at = None
        job.lock_expires_at = None

        job.save()

        return job

    @staticmethod
    def requeue(
        *,
        job,
    ):
        job.status = "PENDING"
        job.updated_at = datetime.utcnow()

        job.save()

        return job

    @staticmethod
    def retry_failed(
        *,
        job,
    ):
        now = datetime.utcnow()

        job.status = "PENDING"

        # Manual retry starts a fresh execution cycle.
        job.attempts = 0

        job.available_at = now

        job.started_at = None
        job.completed_at = None

        job.result = {}
        job.last_error = None

        job.worker_id = None
        job.locked_at = None
        job.lock_expires_at = None

        job.updated_at = now

        job.save()

        return job
    
    @staticmethod
    def mark_failed(
        *,
        job,
        error_message,
    ):
        now = datetime.utcnow()

        job.status = "FAILED"
        job.last_error = (
            error_message[:1000]
            if error_message
            else None
        )

        job.completed_at = now
        job.updated_at = now

        job.worker_id = None
        job.locked_at = None
        job.lock_expires_at = None

        job.save()

        return job

    @staticmethod
    def recover_expired_jobs():
        now = datetime.utcnow()

        return (
            BackgroundJob.objects(
                status="RUNNING",
                lock_expires_at__lte=now,
            )
            .update(
                multi=True,

                set__status=
                    "PENDING",

                set__worker_id=
                    None,

                set__locked_at=
                    None,

                set__lock_expires_at=
                    None,

                set__updated_at=
                    now,
            )
        )