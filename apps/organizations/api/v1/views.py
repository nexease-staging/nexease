from apps.core.api.decorators import (
    api_login_required,
    api_rate_limit,
)
from apps.core.services.api_response_service import (
    APIResponseService,
)
from apps.organizations.api.v1.serializers import (
    OrganizationAPISerializer,
)
import json

from apps.authorization.services import (
    AuthorizationService,
)
from apps.organizations.services import (
    OrganizationService,
    OrganizationUpdateValidationError,
)


@api_login_required
@api_rate_limit(
    scope="organization.current",
    limit=120,
    window_seconds=60,
)
def current_organization_api(
    request,
):
    organization = (
        request.api_organization
    )

    # ==================================================
    # GET
    # ==================================================

    if request.method == "GET":

        return (
            APIResponseService
            .success(
                data={
                    "organization": (
                        OrganizationAPISerializer
                        .serialize_detail(
                            organization
                        )
                    ),
                },
                message=(
                    "Current organization retrieved "
                    "successfully."
                ),
                request=request,
            )
        )

    # ==================================================
    # PATCH
    # ==================================================

    if request.method == "PATCH":

        user = request.api_user

        if not (
            AuthorizationService
            .has_permission(
                user,
                "organizations.update",
            )
        ):

            return (
                APIResponseService
                .forbidden(
                    message="Permission denied.",
                    request=request,
                )
            )

        content_type = (
            request.content_type
            or
            ""
        ).lower()

        if (
            "application/json"
            not in content_type
        ):

            return (
                APIResponseService
                .bad_request(
                    message=(
                        "Content-Type must be "
                        "application/json."
                    ),
                    request=request,
                )
            )

        try:

            payload = json.loads(
                request.body.decode(
                    "utf-8"
                )
            )

        except (
            json.JSONDecodeError,
            UnicodeDecodeError,
        ):

            return (
                APIResponseService
                .bad_request(
                    message=(
                        "Invalid JSON body."
                    ),
                    request=request,
                )
            )

        try:

            updated_organization = (
                OrganizationService
                .update_organization(
                    organization=(
                        organization
                    ),
                    payload=payload,
                )
            )

        except (
            OrganizationUpdateValidationError
        ) as exc:

            return (
                APIResponseService
                .validation_error(
                    message=exc.message,
                    details=exc.details,
                    request=request,
                )
            )

        except LookupError:

            return (
                APIResponseService
                .not_found(
                    message=(
                        "Organization not found."
                    ),
                    request=request,
                )
            )

        return (
            APIResponseService
            .success(
                data={
                    "organization": (
                        OrganizationAPISerializer
                        .serialize_detail(
                            updated_organization
                        )
                    ),
                },
                message=(
                    "Organization updated "
                    "successfully."
                ),
                request=request,
            )
        )

    # ==================================================
    # UNSUPPORTED METHOD
    # ==================================================

    return (
        APIResponseService
        .method_not_allowed(
            message=(
                "Use GET or PATCH for "
                "the current organization."
            ),
            request=request,
        )
    )