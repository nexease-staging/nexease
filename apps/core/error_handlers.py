from apps.core.services.api_response_service import (
    APIResponseService,
)


def handler400(
    request,
    exception=None,
):
    return (
        APIResponseService
        .bad_request(
            message="Invalid request.",
            request=request,
        )
    )


def handler403(
    request,
    exception=None,
):
    return (
        APIResponseService
        .forbidden(
            message="Permission denied.",
            request=request,
        )
    )


def handler404(
    request,
    exception=None,
):
    return (
        APIResponseService
        .not_found(
            message="Resource not found.",
            request=request,
        )
    )


def handler500(
    request,
):
    return (
        APIResponseService
        .internal_error(
            message="Internal server error.",
            request=request,
        )
    )