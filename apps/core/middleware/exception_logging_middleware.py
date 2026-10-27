import traceback

from django.utils.deprecation import (
    MiddlewareMixin,
)

from apps.core.services.api_exception_mapping_service import (
    APIExceptionMappingService,
)
from apps.core.services.api_response_service import (
    APIResponseService,
)
from apps.core.services.application_logging_service import (
    ApplicationLoggingService,
)
from apps.core.services.mongodb_error_logging_service import (
    MongoDBErrorLoggingService,
)


class ExceptionLoggingMiddleware(
    MiddlewareMixin
):

    @staticmethod
    def _get_user(
        request,
    ):
        user = getattr(
            request,
            "api_user",
            None,
        )

        if user is None:

            user = getattr(
                request,
                "user",
                None,
            )

        if (
            user is not None
            and
            not getattr(
                user,
                "is_authenticated",
                False,
            )
        ):

            user = None

        return user

    @staticmethod
    def _get_organization(
        request,
        user,
    ):
        organization = getattr(
            request,
            "api_organization",
            None,
        )

        if organization is not None:
            return organization

        if user is None:
            return None

        return getattr(
            user,
            "organization",
            None,
        )

    def process_exception(
        self,
        request,
        exception,
    ):
        # ==================================================
        # CONTEXT
        # ==================================================

        request_id = getattr(
            request,
            "request_id",
            None,
        )

        client_correlation_id = getattr(
            request,
            "client_correlation_id",
            None,
        )

        user = self._get_user(
            request
        )

        organization = (
            self._get_organization(
                request,
                user,
            )
        )

        is_api_request = (
            request.path.startswith(
                "/api/"
            )
        )

        is_mongodb_error = (
            MongoDBErrorLoggingService
            .is_mongodb_error(
                exception
            )
        )

        # ==================================================
        # TRACEBACK FOR INTERNAL LOGS ONLY
        # ==================================================

        traceback_text = "".join(
            traceback.format_exception(
                type(
                    exception
                ),
                exception,
                exception.__traceback__,
            )
        )

        # ==================================================
        # MONGODB LOG
        # ==================================================

        if is_mongodb_error:

            MongoDBErrorLoggingService.log_exception(
                exception=exception,
                request=request,
                module="http",
                action="mongodb_exception",
                user=user,
                organization=organization,
                extra_context={
                    "client_correlation_id":
                        client_correlation_id,

                    "method":
                        request.method,

                    "path":
                        request.path,
                },
            )

        # ==================================================
        # OPERATIONAL LOG
        # ==================================================

        else:

            ApplicationLoggingService.log(
                level="ERROR",
                message=(
                    "Application exception."
                ),
                module="http",
                action="exception",
                status="failed",
                user=user,
                organization=organization,
                request_id=request_id,
                client_correlation_id=(
                    client_correlation_id
                ),
                method=request.method,
                path=request.path,
                exception_type=(
                    type(
                        exception
                    )
                    .__name__
                ),
                exception_message=str(
                    exception
                ),
                traceback=traceback_text,
            )

        # ==================================================
        # NON-API REQUEST
        # ==================================================

        if not is_api_request:

            return None

        # ==================================================
        # KNOWN API EXCEPTION
        # ==================================================

        mapped_response = (
            APIExceptionMappingService
            .map(
                exception,
                request=request,
            )
        )

        if mapped_response is not None:

            return mapped_response

        # ==================================================
        # SAFE UNEXPECTED API ERROR
        # ==================================================

        return (
            APIResponseService
            .internal_error(
                message=(
                    "Internal server error."
                ),
                request=request,
            )
        )