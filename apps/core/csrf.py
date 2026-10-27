from apps.core.services.api_response_service import (
    APIResponseService,
)


def csrf_failure(
    request,
    reason="",
):
    # Never expose Django's internal CSRF
    # failure reason to the frontend.

    if request.path.startswith(
        "/api/"
    ):

        return (
            APIResponseService
            .error(
                code="CSRF_FAILED",
                message=(
                    "CSRF verification failed."
                ),
                status=403,
                request=request,
            )
        )

    # Non-API requests receive the same safe
    # response without exposing internal details.

    return (
        APIResponseService
        .forbidden(
            message=(
                "CSRF verification failed."
            ),
            request=request,
        )
    )