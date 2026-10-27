import json

from apps.accounts.user_management_service import (
    UserCreationValidationError,
    UserManagementService,
    UserStateValidationError,
    UserUpdateValidationError,
)

from apps.authorization.services import (
    AuthorizationService,
)
from apps.accounts.api.v1.serializers import (
    UserAPISerializer,
)
from apps.accounts.models import (
    User,
)
from apps.core.api.decorators import (
    api_permission_required,
    api_rate_limit,
    api_login_required,
)
from apps.core.services.api_query_pipeline_service import (
    APIQueryPipelineError,
    APIQueryPipelineService,
)
from apps.core.services.api_response_service import (
    APIResponseService,
)
from apps.core.services.api_serialization_service import (
    APISerializationService,
)
from apps.core.services.api_tenant_query_service import (
    APITenantQueryService,
)


@api_login_required
@api_rate_limit(
    scope="users.collection",
    limit=120,
    window_seconds=60,
)
def user_list_api(
    request,
):
    # ==================================================
    # GET — LIST USERS
    # ==================================================

    if request.method == "GET":

        if not (
            AuthorizationService
            .has_permission(
                request.api_user,
                "users.read",
            )
        ):

            return (
                APIResponseService
                .forbidden(
                    message="Permission denied.",
                    request=request,
                )
            )

        tenant_result = (
            APITenantQueryService
            .scope_queryset(
                User.objects.all(),
                request,
                organization_context=(
                    request
                    .api_organization_context
                ),
            )
        )

        queryset = tenant_result[
            "queryset"
        ]

        try:

            pipeline_result = (
                APIQueryPipelineService
                .execute(
                    queryset,
                    request,
                    allowed_filters={
                        "is_active": {
                            "field":
                                "is_active",

                            "parser":
                                "boolean",
                        },
                    },
                    search_fields=[
                        "email",
                        "first_name",
                        "last_name",
                    ],
                    allowed_sort_fields={
                        "email":
                            "email",

                        "first_name":
                            "first_name",

                        "last_name":
                            "last_name",

                        "created_at":
                            "created_at",

                        "updated_at":
                            "updated_at",
                    },
                    default_sort=[
                        "email",
                    ],
                    default_page_size=25,
                    maximum_page_size=100,
                )
            )

        except APIQueryPipelineError as exc:

            return (
                APIResponseService
                .validation_error(
                    message=exc.message,
                    details={
                        "component":
                            exc.component,

                        "fields":
                            exc.details,
                    },
                    request=request,
                )
            )

        serialized_users = (
            APISerializationService
            .serialize_collection(
                pipeline_result[
                    "items"
                ],
                serializer=(
                    UserAPISerializer
                    .serialize_summary
                ),
            )
        )

        return (
            APIResponseService
            .success(
                data={
                    "users":
                        serialized_users,

                    "pagination":
                        pipeline_result[
                            "pagination"
                        ],

                    "query":
                        pipeline_result[
                            "query"
                        ],
                },
                message=(
                    "Users retrieved successfully."
                ),
                request=request,
            )
        )

    # ==================================================
    # POST — CREATE USER
    # ==================================================

    if request.method == "POST":

        if not (
            AuthorizationService
            .has_permission(
                request.api_user,
                "users.create",
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
                    message="Invalid JSON body.",
                    request=request,
                )
            )

        try:

            created_user = (
                UserManagementService
                .create_user(
                    organization=(
                        request
                        .api_organization
                    ),
                    payload=payload,
                    actor=(
                        request.api_user
                    ),
                    request=request,
                )
            )

        except UserCreationValidationError as exc:

            return (
                APIResponseService
                .validation_error(
                    message=exc.message,
                    details=exc.details,
                    request=request,
                )
            )

        return (
            APIResponseService
            .success(
                data={
                    "user": (
                        UserAPISerializer
                        .serialize_detail(
                            created_user
                        )
                    ),
                },
                message=(
                    "User created successfully."
                ),
                status=201,
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
                "Use GET or POST for users."
            ),
            request=request,
        )
    )

@api_permission_required(
    "users.read"
)
@api_login_required
@api_rate_limit(
    scope="users.detail",
    limit=180,
    window_seconds=60,
)
def user_detail_api(
    request,
    user_id,
):
    # ==================================================
    # SUPPORTED METHODS
    # ==================================================

    if (
        request.method
        not in {
            "GET",
            "PATCH",
        }
    ):

        return (
            APIResponseService
            .method_not_allowed(
                message=(
                    "Use GET or PATCH "
                    "for a user."
                ),
                request=request,
            )
        )

    # ==================================================
    # METHOD-SPECIFIC AUTHORIZATION
    # ==================================================

    required_permission = (
        "users.read"
        if request.method
        ==
        "GET"
        else
        "users.update"
    )

    if not (
        AuthorizationService
        .has_permission(
            request.api_user,
            required_permission,
        )
    ):

        return (
            APIResponseService
            .forbidden(
                message="Permission denied.",
                request=request,
            )
        )

    # ==================================================
    # TENANT-SCOPED USER LOOKUP
    # ==================================================

    result = (
        APITenantQueryService
        .get_document(
            User.objects.all(),
            request,
            user_id,
            organization_context=(
                request
                .api_organization_context
            ),
        )
    )

    target_user = result[
        "document"
    ]

    if not target_user:

        return (
            APIResponseService
            .not_found(
                message="User not found.",
                request=request,
            )
        )

    # ==================================================
    # GET
    # ==================================================

    if request.method == "GET":

        return (
            APIResponseService
            .success(
                data={
                    "user": (
                        UserAPISerializer
                        .serialize_detail(
                            target_user
                        )
                    ),
                },
                message=(
                    "User retrieved successfully."
                ),
                request=request,
            )
        )

    # ==================================================
    # PATCH
    # ==================================================

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
                message="Invalid JSON body.",
                request=request,
            )
        )

    try:

        updated_user = (
            UserManagementService
            .update_user(
                organization=(
                    request
                    .api_organization
                ),
                user=target_user,
                actor=(
                    request.api_user
                ),
                payload=payload,
                request=request,
            )
        )

    except UserUpdateValidationError as exc:

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
                message="User not found.",
                request=request,
            )
        )

    return (
        APIResponseService
        .success(
            data={
                "user": (
                    UserAPISerializer
                    .serialize_detail(
                        updated_user
                    )
                ),
            },
            message=(
                "User updated successfully."
            ),
            request=request,
        )
    )

@api_permission_required(
    "users.activate"
)
@api_rate_limit(
    scope="users.activate",
    limit=30,
    window_seconds=60,
)
def user_activate_api(
    request,
    user_id,
):
    # ==================================================
    # METHOD
    # ==================================================

    if request.method != "POST":

        return (
            APIResponseService
            .method_not_allowed(
                message=(
                    "Use POST to activate "
                    "a user."
                ),
                request=request,
            )
        )

    # ==================================================
    # TENANT-SCOPED TARGET
    # ==================================================

    result = (
        APITenantQueryService
        .get_document(
            User.objects.all(),
            request,
            user_id,
            organization_context=(
                request
                .api_organization_context
            ),
        )
    )

    target_user = result[
        "document"
    ]

    if not target_user:

        return (
            APIResponseService
            .not_found(
                message="User not found.",
                request=request,
            )
        )

    # ==================================================
    # ACTIVATION
    # ==================================================

    try:

        activation_result = (
            UserManagementService
            .activate_user(
                organization=(
                    request
                    .api_organization
                ),
                user=target_user,
                actor=(
                    request.api_user
                ),
                request=request,
            )
        )

    except UserStateValidationError as exc:

        return (
            APIResponseService
            .unprocessable_entity(
                message=exc.message,
                details=exc.details,
                request=request,
            )
        )

    except LookupError:

        return (
            APIResponseService
            .not_found(
                message="User not found.",
                request=request,
            )
        )

    activated_user = (
        activation_result[
            "user"
        ]
    )

    state_changed = (
        activation_result[
            "state_changed"
        ]
    )

    # ==================================================
    # RESPONSE
    # ==================================================

    return (
        APIResponseService
        .success(
            data={
                "user": (
                    UserAPISerializer
                    .serialize_detail(
                        activated_user
                    )
                ),

                "state_changed":
                    state_changed,
            },
            message=(
                "User activated successfully."
                if state_changed
                else
                "User is already active."
            ),
            request=request,
        )
    )

@api_permission_required(
    "users.deactivate"
)
@api_rate_limit(
    scope="users.deactivate",
    limit=30,
    window_seconds=60,
)
def user_deactivate_api(
    request,
    user_id,
):
    # ==================================================
    # METHOD
    # ==================================================

    if request.method != "POST":

        return (
            APIResponseService
            .method_not_allowed(
                message=(
                    "Use POST to deactivate "
                    "a user."
                ),
                request=request,
            )
        )

    # ==================================================
    # TENANT-SCOPED TARGET
    # ==================================================

    result = (
        APITenantQueryService
        .get_document(
            User.objects.all(),
            request,
            user_id,
            organization_context=(
                request
                .api_organization_context
            ),
        )
    )

    target_user = result[
        "document"
    ]

    if not target_user:

        return (
            APIResponseService
            .not_found(
                message="User not found.",
                request=request,
            )
        )

    # ==================================================
    # DEACTIVATION
    # ==================================================

    try:

        deactivation_result = (
            UserManagementService
            .deactivate_user(
                organization=(
                    request
                    .api_organization
                ),
                user=target_user,
                actor=(
                    request.api_user
                ),
                request=request,
            )
        )

    except UserStateValidationError as exc:

        return (
            APIResponseService
            .unprocessable_entity(
                message=exc.message,
                details=exc.details,
                request=request,
            )
        )

    except LookupError:

        return (
            APIResponseService
            .not_found(
                message="User not found.",
                request=request,
            )
        )

    deactivated_user = (
        deactivation_result[
            "user"
        ]
    )

    state_changed = (
        deactivation_result[
            "state_changed"
        ]
    )

    sessions_revoked = (
        deactivation_result[
            "sessions_revoked"
        ]
    )

    # ==================================================
    # RESPONSE
    # ==================================================

    return (
        APIResponseService
        .success(
            data={
                "user": (
                    UserAPISerializer
                    .serialize_detail(
                        deactivated_user
                    )
                ),

                "state_changed":
                    state_changed,

                "sessions_revoked":
                    sessions_revoked,
            },
            message=(
                "User deactivated successfully."
                if state_changed
                else
                "User is already inactive."
            ),
            request=request,
        )
    )