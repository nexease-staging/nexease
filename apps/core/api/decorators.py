from functools import wraps

from apps.authorization.api_context_service import (
    APIPermissionContextService,
)
from apps.authorization.services import (
    AuthorizationService,
)
from apps.core.services.api_response_service import (
    APIResponseService,
)
from apps.organizations.api_context_service import (
    APIOrganizationContextService,
)
from apps.core.services.api_rate_limit_service import (
    APIRateLimitService,
    APIRateLimitUnavailable,
)

def api_login_required(
    view_function,
):
    @wraps(
        view_function
    )
    def wrapped_view(
        request,
        *args,
        **kwargs,
    ):
        try:

            organization_context = (
                APIOrganizationContextService
                .resolve(
                    request
                )
            )

        except PermissionError as exc:

            return (
                APIResponseService
                .unauthorized(
                    message=str(
                        exc
                    ),
                    request=request,
                )
            )

        request.api_organization_context = (
            organization_context
        )

        request.api_user = (
            organization_context[
                "user"
            ]
        )

        request.api_organization = (
            organization_context[
                "organization"
            ]
        )

        return view_function(
            request,
            *args,
            **kwargs,
        )

    return wrapped_view


def api_permission_required(
    permission_code,
):
    permission_code = str(
        permission_code
        or
        ""
    ).strip()

    if not permission_code:

        raise ValueError(
            "permission_code is required."
        )

    def decorator(
        view_function,
    ):
        @wraps(
            view_function
        )
        def wrapped_view(
            request,
            *args,
            **kwargs,
        ):
            # ==========================================
            # AUTHENTICATION AND TENANT CONTEXT
            # ==========================================

            try:

                organization_context = (
                    APIOrganizationContextService
                    .resolve(
                        request
                    )
                )

            except PermissionError as exc:

                return (
                    APIResponseService
                    .unauthorized(
                        message=str(
                            exc
                        ),
                        request=request,
                    )
                )

            # ==========================================
            # PERMISSION CONTEXT
            # ==========================================

            try:

                permission_context = (
                    APIPermissionContextService
                    .resolve(
                        request,
                        organization_context=(
                            organization_context
                        ),
                    )
                )

            except PermissionError as exc:

                return (
                    APIResponseService
                    .forbidden(
                        message=str(
                            exc
                        ),
                        request=request,
                    )
                )

            # ==========================================
            # AUTHORIZATION
            # ==========================================

            allowed = (
                AuthorizationService
                .has_permission(
                    permission_context[
                        "user"
                    ],
                    permission_code,
                )
            )

            if not allowed:

                return (
                    APIResponseService
                    .forbidden(
                        message="Permission denied.",
                        request=request,
                    )
                )

            # ==========================================
            # ATTACH TRUSTED CONTEXT
            # ==========================================

            request.api_organization_context = (
                organization_context
            )

            request.api_permission_context = (
                permission_context
            )

            request.api_user = (
                permission_context[
                    "user"
                ]
            )

            request.api_organization = (
                permission_context[
                    "organization"
                ]
            )

            request.api_role = (
                permission_context[
                    "role"
                ]
            )

            request.api_permission_codes = (
                permission_context[
                    "permission_codes"
                ]
            )

            request.api_required_permission = (
                permission_code
            )

            return view_function(
                request,
                *args,
                **kwargs,
            )

        return wrapped_view

    return decorator

def api_rate_limit(
    *,
    scope,
    limit,
    window_seconds,
):
    # Validate static configuration at import time.

    APIRateLimitService._validate_configuration(
        scope=scope,
        limit=limit,
        window_seconds=window_seconds,
    )

    def decorator(
        view_function,
    ):
        @wraps(
            view_function
        )
        def wrapped_view(
            request,
            *args,
            **kwargs,
        ):
            try:

                rate_limit_result = (
                    APIRateLimitService
                    .check(
                        request,
                        scope=scope,
                        limit=limit,
                        window_seconds=(
                            window_seconds
                        ),
                    )
                )

            except APIRateLimitUnavailable:

                return (
                    APIResponseService
                    .service_unavailable(
                        message=(
                            "API rate-limit service "
                            "is unavailable."
                        ),
                        request=request,
                    )
                )

            if not rate_limit_result[
                "allowed"
            ]:

                response = (
                    APIResponseService
                    .rate_limited(
                        message=(
                            "API request limit "
                            "exceeded. Try again later."
                        ),
                        request=request,
                    )
                )

                return (
                    APIRateLimitService
                    .add_headers(
                        response,
                        rate_limit_result,
                    )
                )

            response = view_function(
                request,
                *args,
                **kwargs,
            )

            return (
                APIRateLimitService
                .add_headers(
                    response,
                    rate_limit_result,
                )
            )

        return wrapped_view

    return decorator