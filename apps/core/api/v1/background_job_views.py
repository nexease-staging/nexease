from apps.core.api.decorators import (
    api_login_required,
)
from apps.core.services.api_response_service import (
    APIResponseService,
)
from apps.core.services.background_job_service import (
    BackgroundJobService,
)


def _iso(value):
    if value is None:
        return None

    return value.isoformat()


def _serialize_job(
    job,
):
    return {
        "id": str(job.id),
        "job_type": job.job_type,
        "status": job.status,
        "attempts": job.attempts,
        "max_attempts": job.max_attempts,
        "available_at": _iso(
            job.available_at
        ),
        "started_at": _iso(
            job.started_at
        ),
        "completed_at": _iso(
            job.completed_at
        ),
        "last_error": job.last_error,
        "result": job.result or {},
        "created_at": _iso(
            job.created_at
        ),
        "updated_at": _iso(
            job.updated_at
        ),
    }


@api_login_required
def background_job_list_api(
    request,
):
    if request.method != "GET":
        return (
            APIResponseService
            .method_not_allowed(
                message=(
                    "Use GET to retrieve "
                    "background jobs."
                ),
                request=request,
            )
        )

    try:
        jobs = (
            BackgroundJobService
            .list_jobs_for_user(
                user=request.api_user,
                status=(
                    request.GET.get(
                        "status"
                    )
                ),
                job_type=(
                    request.GET.get(
                        "job_type"
                    )
                ),
                limit=(
                    request.GET.get(
                        "limit",
                        50,
                    )
                ),
            )
        )

        data = [
            _serialize_job(job)
            for job in jobs
        ]

        return (
            APIResponseService
            .success(
                data={
                    "results": data,
                    "count": len(data),
                },
                message=(
                    "Background jobs retrieved "
                    "successfully."
                ),
                request=request,
            )
        )

    except ValueError as exc:
        return (
            APIResponseService
            .validation_error(
                message=str(exc),
                request=request,
            )
        )


@api_login_required
def background_job_detail_api(
    request,
    job_id,
):
    if request.method != "GET":
        return (
            APIResponseService
            .method_not_allowed(
                message=(
                    "Use GET to retrieve "
                    "a background job."
                ),
                request=request,
            )
        )

    try:
        job = (
            BackgroundJobService
            .get_job_for_user(
                user=request.api_user,
                job_id=job_id,
            )
        )

        if job is None:
            return (
                APIResponseService
                .not_found(
                    message=(
                        "Background job "
                        "not found."
                    ),
                    request=request,
                )
            )

        return (
            APIResponseService
            .success(
                data=_serialize_job(job),
                message=(
                    "Background job retrieved "
                    "successfully."
                ),
                request=request,
            )
        )

    except ValueError as exc:
        return (
            APIResponseService
            .validation_error(
                message=str(exc),
                request=request,
            )
        )


@api_login_required
def background_job_retry_api(
    request,
    job_id,
):
    if request.method != "POST":
        return (
            APIResponseService
            .method_not_allowed(
                message=(
                    "Use POST to retry "
                    "a failed background job."
                ),
                request=request,
            )
        )

    try:
        job = (
            BackgroundJobService
            .get_job_for_user(
                user=request.api_user,
                job_id=job_id,
            )
        )

        if job is None:
            return (
                APIResponseService
                .not_found(
                    message=(
                        "Background job "
                        "not found."
                    ),
                    request=request,
                )
            )

        job = (
            BackgroundJobService
            .retry_failed_job(
                user=request.api_user,
                job=job,
            )
        )

        return (
            APIResponseService
            .success(
                data=_serialize_job(job),
                message=(
                    "Background job queued "
                    "for retry."
                ),
                request=request,
            )
        )

    except PermissionError as exc:
        return (
            APIResponseService
            .forbidden(
                message=str(exc),
                request=request,
            )
        )

    except ValueError as exc:
        return (
            APIResponseService
            .validation_error(
                message=str(exc),
                request=request,
            )
        )
