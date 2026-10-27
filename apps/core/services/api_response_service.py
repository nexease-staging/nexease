from django.http import JsonResponse
from apps.core.services.api_metadata_service import (
    APIMetadataService,
)

class APIResponseService:

    @staticmethod
    def success(
        *,
        data=None,
        message=None,
        status=200,
        request=None,
    ):
        payload = {
            "success":
                True,
        }

        if message is not None:

            payload[
                "message"
            ] = str(
                message
            )

        if data is not None:

            payload[
                "data"
            ] = data

        payload = (
            APIMetadataService
            .attach(
                payload,
                request=request,
            )
        )

        return JsonResponse(
            payload,
            status=status,
        )

    @staticmethod
    def error(
        *,
        code,
        message,
        status,
        details=None,
        request=None,
    ):
        payload = {
            "success":
                False,

            "error": {
                "code":
                    str(
                        code
                    ),

                "message":
                    str(
                        message
                    ),
            },
        }

        if details is not None:

            payload[
                "error"
            ][
                "details"
            ] = details

        payload = (
            APIMetadataService
            .attach(
                payload,
                request=request,
            )
        )

        return JsonResponse(
            payload,
            status=status,
        )

    @staticmethod
    def bad_request(
        *,
        message="Invalid request.",
        details=None,
        request=None,
    ):
        return (
            APIResponseService
            .error(
                code="BAD_REQUEST",
                message=message,
                status=400,
                details=details,
                request=request,
            )
        )

    @staticmethod
    def validation_error(
        *,
        message="Validation failed.",
        details=None,
        request=None,
    ):
        return (
            APIResponseService
            .error(
                code="VALIDATION_ERROR",
                message=message,
                status=400,
                details=details,
                request=request,
            )
        )

    @staticmethod
    def unauthorized(
        *,
        message="Not authenticated.",
        request=None,
    ):
        return (
            APIResponseService
            .error(
                code="UNAUTHORIZED",
                message=message,
                status=401,
                request=request,
            )
        )

    @staticmethod
    def forbidden(
        *,
        message="Permission denied.",
        request=None,
    ):
        return (
            APIResponseService
            .error(
                code="FORBIDDEN",
                message=message,
                status=403,
                request=request,
            )
        )

    @staticmethod
    def not_found(
        *,
        message="Resource not found.",
        request=None,
    ):
        return (
            APIResponseService
            .error(
                code="NOT_FOUND",
                message=message,
                status=404,
                request=request,
            )
        )

    @staticmethod
    def method_not_allowed(
        *,
        message="Method not allowed.",
        request=None,
    ):
        return (
            APIResponseService
            .error(
                code="METHOD_NOT_ALLOWED",
                message=message,
                status=405,
                request=request,
            )
        )

    @staticmethod
    def rate_limited(
        *,
        message="Too many requests.",
        request=None,
    ):
        return (
            APIResponseService
            .error(
                code="RATE_LIMITED",
                message=message,
                status=429,
                request=request,
            )
        )

    @staticmethod
    def internal_error(
        *,
        message="Internal server error.",
        request=None,
    ):
        return (
            APIResponseService
            .error(
                code="INTERNAL_ERROR",
                message=message,
                status=500,
                request=request,
            )
        )

    @staticmethod
    def service_unavailable(
        *,
        message="Service unavailable.",
        request=None,
    ):
        return (
            APIResponseService
            .error(
                code="SERVICE_UNAVAILABLE",
                message=message,
                status=503,
                request=request,
            )
        )

    @staticmethod
    def conflict(
        *,
        message="Resource conflict.",
        details=None,
        request=None,
    ):
        return (
            APIResponseService
            .error(
                code="CONFLICT",
                message=message,
                status=409,
                details=details,
                request=request,
            )
        )

    @staticmethod
    def unprocessable_entity(
        *,
        message="Request could not be processed.",
        details=None,
        request=None,
    ):
        return (
            APIResponseService
            .error(
                code="UNPROCESSABLE_ENTITY",
                message=message,
                status=422,
                details=details,
                request=request,
            )
        )