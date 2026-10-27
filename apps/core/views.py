from django.http import JsonResponse

from apps.core.services.health_check_service import (
    HealthCheckService,
)
from apps.core.services.build_info_service import (
    BuildInfoService,
)
from apps.core.services.runtime_info_service import (
    RuntimeInfoService,
)
from apps.core.services.api_response_service import (
    APIResponseService,
)
from django.core.exceptions import (
    PermissionDenied,
)

def health_check(
    request,
):
    # ==================================================
    # METHOD
    # ==================================================

    if request.method != "GET":

        return JsonResponse(
            {
                "error":
                    "Method not allowed."
            },
            status=405,
        )

    # ==================================================
    # HEALTH
    # ==================================================

    result = (
        HealthCheckService
        .check()
    )

    # ==================================================
    # STATUS CODE
    # ==================================================

    status_code = (
        200
        if result.get(
            "healthy"
        )
        is True
        else 503
    )


    build_info = (
        BuildInfoService.get_info()
    )

    runtime_info = (
        RuntimeInfoService
        .get_info()
    )

    # ==================================================
    # SAFE RESPONSE
    # ==================================================

    return JsonResponse(
        {
            "status":
                result.get(
                    "status"
                ),

            "healthy":
                result.get(
                    "healthy"
                ),

            "application": {
                "status":
                    result.get(
                        "application",
                        {},
                    )
                    .get(
                        "status"
                    ),

                "service":
                    result.get(
                        "application",
                        {},
                    )
                    .get(
                        "service"
                    ),
            },
            "build": build_info,
            "runtime":
                runtime_info,
            "mongodb": {
                "status":
                    result.get(
                        "mongodb",
                        {},
                    )
                    .get(
                        "status"
                    ),

                "healthy":
                    result.get(
                        "mongodb",
                        {},
                    )
                    .get(
                        "healthy"
                    ),
            },
        },
        status=status_code,
    )

def liveness_check(
    request,
):
    # ==================================================
    # METHOD
    # ==================================================

    if request.method != "GET":

        return JsonResponse(
            {
                "error":
                    "Method not allowed."
            },
            status=405,
        )

    # ==================================================
    # LIVENESS
    # ==================================================

    result = (
        HealthCheckService
        .check_liveness()
    )

    return JsonResponse(
        result,
        status=200,
    )


def readiness_check(
    request,
):
    # ==================================================
    # METHOD
    # ==================================================

    if request.method != "GET":

        return JsonResponse(
            {
                "error":
                    "Method not allowed."
            },
            status=405,
        )

    # ==================================================
    # READINESS
    # ==================================================

    result = (
        HealthCheckService
        .check_readiness()
    )

    status_code = (
        200
        if result.get(
            "ready"
        )
        is True
        else 503
    )

    return JsonResponse(
        result,
        status=status_code,
    )


def test_api_success(
    request,
):
    return (
        APIResponseService
        .success(
            data={
                "test":
                    True,
            },
            message="Success.",
            request=request,
        )
    )


def test_api_validation_error(
    request,
):
    return (
        APIResponseService
        .validation_error(
            message="Invalid test input.",
            details={
                "email":
                    "Invalid email.",
            },
            request=request,
        )
    )


def test_api_unauthorized(
    request,
):
    return (
        APIResponseService
        .unauthorized(
            request=request,
        )
    )


def test_api_forbidden(
    request,
):
    return (
        APIResponseService
        .forbidden(
            request=request,
        )
    )


def test_api_not_found(
    request,
):
    return (
        APIResponseService
        .not_found(
            request=request,
        )
    )


def test_api_rate_limited(
    request,
):
    return (
        APIResponseService
        .rate_limited(
            request=request,
        )
    )

def test_permission_denied(
    request,
):
    raise PermissionDenied(
        "Controlled Step 19 permission denial."
    )