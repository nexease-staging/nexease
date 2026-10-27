from datetime import datetime, timedelta

from apps.core.repositories.background_job_repository import (
    BackgroundJobRepository,
)


class BackgroundJobService:

    ALLOWED_JOB_TYPES = {
        "BANK_STATEMENT_IMPORT",
        "DOCUMENT_EMAIL",
        "NOTIFICATION",
        "DATA_MIGRATION_VALIDATE",
        "DATA_MIGRATION_IMPORT",
    }

    DEFAULT_MAX_ATTEMPTS = 3

    RETRY_DELAYS_SECONDS = {
        1: 30,
        2: 120,
        3: 300,
    }

    @staticmethod
    def create_job(
        *,
        organization,
        created_by,
        job_type,
        payload,
        idempotency_key,
        max_attempts=None,
    ):
        if organization is None:
            raise ValueError(
                "Organization is required."
            )

        if created_by is None:
            raise ValueError(
                "Created by user is required."
            )

        job_type = (
            str(job_type or "")
            .strip()
            .upper()
        )

        if job_type not in (
            BackgroundJobService
            .ALLOWED_JOB_TYPES
        ):
            raise ValueError(
                "Invalid background job type."
            )

        if not isinstance(
            payload,
            dict,
        ):
            raise ValueError(
                "Background job payload "
                "must be a dictionary."
            )

        idempotency_key = (
            str(
                idempotency_key
                or ""
            )
            .strip()
        )

        if not idempotency_key:
            raise ValueError(
                "Idempotency key is required."
            )

        if len(idempotency_key) > 200:
            raise ValueError(
                "Idempotency key cannot "
                "exceed 200 characters."
            )

        if max_attempts is None:
            max_attempts = (
                BackgroundJobService
                .DEFAULT_MAX_ATTEMPTS
            )

        try:
            max_attempts = int(
                max_attempts
            )
        except (
            TypeError,
            ValueError,
        ) as exc:
            raise ValueError(
                "Max attempts must "
                "be an integer."
            ) from exc

        if max_attempts < 1:
            raise ValueError(
                "Max attempts must be "
                "at least 1."
            )

        return (
            BackgroundJobRepository
            .create(
                organization=
                    organization,

                created_by=
                    created_by,

                job_type=
                    job_type,

                payload=
                    payload,

                idempotency_key=
                    idempotency_key,

                max_attempts=
                    max_attempts,
            )
        )

    @staticmethod
    def get_job(
        *,
        organization,
        job_id,
    ):
        if organization is None:
            raise ValueError(
                "Organization is required."
            )

        if not job_id:
            raise ValueError(
                "Job ID is required."
            )

        return (
            BackgroundJobRepository
            .get_by_id(
                organization=
                    organization,

                job_id=
                    job_id,
            )
        )

    @staticmethod
    def list_jobs_for_user(
        *,
        user,
        status=None,
        job_type=None,
        limit=50,
    ):
        if user is None:
            raise ValueError(
                "User is required."
            )

        if not user.is_active:
            raise ValueError(
                "User is inactive."
            )

        normalized_status = (
            str(status or "")
            .strip()
            .upper()
        )

        if normalized_status:
            valid_statuses = {
                "PENDING",
                "RUNNING",
                "RETRYING",
                "SUCCEEDED",
                "FAILED",
            }

            if normalized_status not in valid_statuses:
                raise ValueError(
                    "Invalid background job status."
                )
        else:
            normalized_status = None

        normalized_job_type = (
            str(job_type or "")
            .strip()
            .upper()
        )

        if normalized_job_type:
            if normalized_job_type not in (
                BackgroundJobService
                .ALLOWED_JOB_TYPES
            ):
                raise ValueError(
                    "Invalid background job type."
                )
        else:
            normalized_job_type = None

        try:
            limit = int(limit)
        except (
            TypeError,
            ValueError,
        ) as exc:
            raise ValueError(
                "Limit must be an integer."
            ) from exc

        if limit < 1 or limit > 100:
            raise ValueError(
                "Limit must be between 1 and 100."
            )

        return (
            BackgroundJobRepository
            .list_for_user(
                organization=user.organization,
                created_by=user,
                status=normalized_status,
                job_type=normalized_job_type,
                limit=limit,
            )
        )

    @staticmethod
    def get_job_for_user(
        *,
        user,
        job_id,
    ):
        if user is None:
            raise ValueError(
                "User is required."
            )

        if not user.is_active:
            raise ValueError(
                "User is inactive."
            )

        if not job_id:
            raise ValueError(
                "Job ID is required."
            )

        return (
            BackgroundJobRepository
            .get_for_user(
                organization=user.organization,
                created_by=user,
                job_id=job_id,
            )
        )

    @staticmethod
    def claim_next_job(
        *,
        worker_id,
        lease_seconds=300,
    ):
        worker_id = (
            str(worker_id or "")
            .strip()
        )

        if not worker_id:
            raise ValueError(
                "Worker ID is required."
            )

        try:
            lease_seconds = int(
                lease_seconds
            )
        except (
            TypeError,
            ValueError,
        ) as exc:
            raise ValueError(
                "Lease seconds must "
                "be an integer."
            ) from exc

        if lease_seconds < 30:
            raise ValueError(
                "Lease seconds must be "
                "at least 30."
            )

        return (
            BackgroundJobRepository
            .claim_next(
                worker_id=
                    worker_id,

                lease_seconds=
                    lease_seconds,
            )
        )

    @staticmethod
    def mark_succeeded(
        *,
        job,
        result=None,
    ):
        if job is None:
            raise ValueError(
                "Background job is required."
            )

        if job.status != "RUNNING":
            raise ValueError(
                "Only a running job can "
                "be marked succeeded."
            )

        return (
            BackgroundJobRepository
            .mark_succeeded(
                job=job,
                result=result
            )
        )

    @staticmethod
    def handle_failure(
        *,
        job,
        error,
    ):
        if job is None:
            raise ValueError(
                "Background job is required."
            )

        if job.status != "RUNNING":
            raise ValueError(
                "Only a running job can "
                "handle execution failure."
            )

        error_message = (
            str(error or "")
            .strip()
        )

        if not error_message:
            error_message = (
                "Background job execution failed."
            )

        if (
            job.attempts
            >= job.max_attempts
        ):
            return (
                BackgroundJobRepository
                .mark_failed(
                    job=job,
                    error_message=
                        error_message,
                )
            )

        delay_seconds = (
            BackgroundJobService
            ._retry_delay_seconds(
                attempt=job.attempts,
            )
        )

        available_at = (
            datetime.utcnow()
            + timedelta(
                seconds=
                    delay_seconds,
            )
        )

        return (
            BackgroundJobRepository
            .mark_retrying(
                job=job,
                error_message=
                    error_message,

                available_at=
                    available_at,
            )
        )

    @staticmethod
    def requeue_retrying_job(
        *,
        job,
    ):
        if job is None:
            raise ValueError(
                "Background job is required."
            )

        if job.status != "RETRYING":
            raise ValueError(
                "Only a retrying job can "
                "be requeued."
            )

        if job.available_at > datetime.utcnow():
            return job

        return (
            BackgroundJobRepository
            .requeue(
                job=job,
            )
        )

    @staticmethod
    def retry_failed_job(
        *,
        user,
        job,
    ):
        if user is None:
            raise ValueError(
                "User is required."
            )

        if not user.is_active:
            raise ValueError(
                "User is inactive."
            )

        if job is None:
            raise ValueError(
                "Background job is required."
            )

        if (
            str(job.organization.id)
            !=
            str(user.organization.id)
        ):
            raise PermissionError(
                "Background job does not belong "
                "to this organization."
            )

        if (
            str(job.created_by.id)
            !=
            str(user.id)
        ):
            raise PermissionError(
                "Background job does not belong "
                "to this user."
            )

        if job.status != "FAILED":
            raise ValueError(
                "Only a failed background job "
                "can be manually retried."
            )

        return (
            BackgroundJobRepository
            .retry_failed(
                job=job,
            )
        )

    @staticmethod
    def recover_expired_jobs():
        return (
            BackgroundJobRepository
            .recover_expired_jobs()
        )

    @staticmethod
    def _retry_delay_seconds(
        *,
        attempt,
    ):
        if attempt in (
            BackgroundJobService
            .RETRY_DELAYS_SECONDS
        ):
            return (
                BackgroundJobService
                .RETRY_DELAYS_SECONDS[
                    attempt
                ]
            )

        return 300