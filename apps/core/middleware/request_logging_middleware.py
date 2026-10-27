import time

from django.conf import settings

from apps.core.services.application_logging_service import (
    ApplicationLoggingService,
)


class RequestLoggingMiddleware:

    def __init__(
        self,
        get_response,
    ):
        self.get_response = (
            get_response
        )

    @staticmethod
    def _get_user(
        request,
    ):
        # API decorators attach api_user after
        # successful authentication/authorization.

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

        if user is None:
            return None

        if not getattr(
            user,
            "is_authenticated",
            False,
        ):

            return None

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

    def __call__(
        self,
        request,
    ):
        # ==================================================
        # START TIMER
        # ==================================================

        start_time = time.perf_counter()

        # ==================================================
        # CORRELATION CONTEXT
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

        # ==================================================
        # INITIAL USER CONTEXT
        # ==================================================

        user = self._get_user(
            request
        )

        organization = (
            self._get_organization(
                request,
                user,
            )
        )

        # ==================================================
        # REQUEST LOG
        # ==================================================

        ApplicationLoggingService.log(
            level="INFO",
            message="HTTP request started.",
            module="http",
            action="request",
            status="started",
            user=user,
            organization=organization,
            request_id=request_id,
            client_correlation_id=(
                client_correlation_id
            ),
            method=request.method,
            path=request.path,
        )

        # ==================================================
        # RESPONSE
        # ==================================================

        response = self.get_response(
            request
        )

        # ==================================================
        # DURATION
        # ==================================================

        duration_ms = round(
            (
                time.perf_counter()
                -
                start_time
            )
            *
            1000,
            2,
        )

        # ==================================================
        # SLOW REQUEST
        # ==================================================

        slow_threshold_ms = (
            settings
            .SLOW_REQUEST_THRESHOLD_SECONDS
            *
            1000
        )

        is_slow_request = (
            duration_ms
            >=
            slow_threshold_ms
        )

        # ==================================================
        # REFRESH USER CONTEXT
        #
        # Authentication and API decorators may have
        # attached user/organization context while the
        # request was being processed.
        # ==================================================

        user = self._get_user(
            request
        )

        organization = (
            self._get_organization(
                request,
                user,
            )
        )

        # ==================================================
        # RESPONSE LEVEL
        # ==================================================

        status_code = (
            response.status_code
        )

        if status_code >= 500:

            log_level = "ERROR"

        elif (
            status_code >= 400
            or
            is_slow_request
        ):

            log_level = "WARNING"

        else:

            log_level = "INFO"

        # ==================================================
        # RESPONSE LOG
        # ==================================================

        ApplicationLoggingService.log(
            level=log_level,
            message="HTTP request completed.",
            module="http",
            action="response",
            status="completed",
            user=user,
            organization=organization,
            request_id=request_id,
            client_correlation_id=(
                client_correlation_id
            ),
            method=request.method,
            path=request.path,
            status_code=status_code,
            duration_ms=duration_ms,
            slow_request=is_slow_request,
        )

        return response