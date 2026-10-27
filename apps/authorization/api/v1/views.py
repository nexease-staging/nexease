import json

from apps.authorization.api.v1.serializers import (
    PermissionAPISerializer,
    RoleAPISerializer,
)
from apps.authorization.models import (
    Permission,
    Role,
)
from apps.authorization.role_management_service import (
    RoleManagementService,
    RoleStateValidationError,
    RoleValidationError,
)
from apps.authorization.services import (
    AuthorizationService,
)
from apps.core.api.decorators import (
    api_login_required,
    api_permission_required,
    api_rate_limit,
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


@api_permission_required(
    "permissions.read"
)
@api_rate_limit(
    scope="permissions.collection",
    limit=180,
    window_seconds=60,
)
def permission_list_api(
    request,
):
    if request.method != "GET":
        return (
            APIResponseService
            .method_not_allowed(
                message=(
                    "Use GET to retrieve "
                    "permissions."
                ),
                request=request,
            )
        )

    # Legacy/inactive permissions are hidden unless
    # the caller explicitly supplies is_active.

    queryset = (
        Permission.objects.all()
    )

    if (
        "is_active"
        not in request.GET
    ):
        queryset = queryset.filter(
            is_active=True
        )

    try:
        pipeline_result = (
            APIQueryPipelineService
            .execute(
                queryset,
                request,
                allowed_filters={
                    "module": {
                        "field":
                            "module",

                        "parser":
                            "string",
                    },

                    "is_active": {
                        "field":
                            "is_active",

                        "parser":
                            "boolean",
                    },
                },
                search_fields=[
                    "code",
                    "name",
                    "description",
                    "module",
                ],
                allowed_sort_fields={
                    "code":
                        "code",

                    "name":
                        "name",

                    "module":
                        "module",

                    "created_at":
                        "created_at",

                    "updated_at":
                        "updated_at",
                },
                default_sort=[
                    "module",
                    "code",
                ],
                default_page_size=50,
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

    serialized_permissions = (
        APISerializationService
        .serialize_collection(
            pipeline_result[
                "items"
            ],
            serializer=(
                PermissionAPISerializer
                .serialize_detail
            ),
        )
    )

    modules = sorted({
        permission[
            "module"
        ]

        for permission
        in serialized_permissions

        if permission
    })

    return (
        APIResponseService
        .success(
            data={
                "permissions":
                    serialized_permissions,

                "modules":
                    modules,

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
                "Permissions retrieved "
                "successfully."
            ),
            request=request,
        )
    )

@api_login_required
@api_rate_limit(
    scope="roles.collection",
    limit=120,
    window_seconds=60,
)
def role_list_api(
    request,
):
    # ==================================================
    # GET — LIST ROLES
    # ==================================================

    if request.method == "GET":
        if not (
            AuthorizationService
            .has_permission(
                request.api_user,
                "roles.read",
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
                Role.objects.all(),
                request,
                organization_context=(
                    request
                    .api_organization_context
                ),
            )
        )

        try:
            pipeline_result = (
                APIQueryPipelineService
                .execute(
                    tenant_result[
                        "queryset"
                    ],
                    request,
                    allowed_filters={
                        "is_active": {
                            "field":
                                "is_active",

                            "parser":
                                "boolean",
                        },

                        "is_system": {
                            "field":
                                "is_system",

                            "parser":
                                "boolean",
                        },
                    },
                    search_fields=[
                        "name",
                        "description",
                    ],
                    allowed_sort_fields={
                        "name":
                            "name",

                        "created_at":
                            "created_at",

                        "updated_at":
                            "updated_at",
                    },
                    default_sort=[
                        "name",
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

        serialized_roles = (
            APISerializationService
            .serialize_collection(
                pipeline_result[
                    "items"
                ],
                serializer=(
                    RoleAPISerializer
                    .serialize_summary
                ),
            )
        )

        return (
            APIResponseService
            .success(
                data={
                    "roles":
                        serialized_roles,

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
                    "Roles retrieved successfully."
                ),
                request=request,
            )
        )

    # ==================================================
    # POST — CREATE ROLE
    # ==================================================

    if request.method == "POST":
        if not (
            AuthorizationService
            .has_permission(
                request.api_user,
                "roles.create",
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
            created_role = (
                RoleManagementService
                .create_role(
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

        except RoleValidationError as exc:
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
                    "role":
                        (
                            RoleAPISerializer
                            .serialize_detail(
                                created_role
                            )
                        ),
                },
                message=(
                    "Role created successfully."
                ),
                status=201,
                request=request,
            )
        )

    return (
        APIResponseService
        .method_not_allowed(
            message=(
                "Use GET or POST for roles."
            ),
            request=request,
        )
    )


@api_permission_required(
    "roles.read"
)
@api_rate_limit(
    scope="roles.detail",
    limit=180,
    window_seconds=60,
)
def role_detail_api(
    request,
    role_id,
):
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
                    "for a role."
                ),
                request=request,
            )
        )

    required_permission = (
        "roles.read"
        if request.method == "GET"
        else
        "roles.update"
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

    result = (
        APITenantQueryService
        .get_document(
            Role.objects.all(),
            request,
            role_id,
            organization_context=(
                request
                .api_organization_context
            ),
        )
    )

    role = result[
        "document"
    ]

    if not role:
        return (
            APIResponseService
            .not_found(
                message="Role not found.",
                request=request,
            )
        )

    if request.method == "GET":
        return (
            APIResponseService
            .success(
                data={
                    "role":
                        (
                            RoleAPISerializer
                            .serialize_detail(
                                role
                            )
                        ),
                },
                message=(
                    "Role retrieved successfully."
                ),
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
        updated_role = (
            RoleManagementService
            .update_role(
                organization=(
                    request
                    .api_organization
                ),
                role=role,
                payload=payload,
                actor=(
                    request.api_user
                ),
                request=request,
            )
        )

    except RoleValidationError as exc:
        return (
            APIResponseService
            .validation_error(
                message=exc.message,
                details=exc.details,
                request=request,
            )
        )

    except RoleStateValidationError as exc:
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
                message="Role not found.",
                request=request,
            )
        )

    return (
        APIResponseService
        .success(
            data={
                "role":
                    (
                        RoleAPISerializer
                        .serialize_detail(
                            updated_role
                        )
                    ),
            },
            message=(
                "Role updated successfully."
            ),
            request=request,
        )
    )

@api_permission_required(
    "roles.assign_permissions"
)
@api_rate_limit(
    scope="roles.permissions",
    limit=60,
    window_seconds=60,
)
def role_permissions_api(
    request,
    role_id,
):
    if request.method != "PATCH":
        return (
            APIResponseService
            .method_not_allowed(
                message=(
                    "Use PATCH to replace "
                    "role permissions."
                ),
                request=request,
            )
        )

    result = (
        APITenantQueryService
        .get_document(
            Role.objects.all(),
            request,
            role_id,
            organization_context=(
                request
                .api_organization_context
            ),
        )
    )

    role = result[
        "document"
    ]

    if not role:
        return (
            APIResponseService
            .not_found(
                message="Role not found.",
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
        updated_role = (
            RoleManagementService
            .assign_permissions(
                organization=(
                    request
                    .api_organization
                ),
                role=role,
                payload=payload,
                actor=(
                    request.api_user
                ),
                request=request,
            )
        )

    except RoleValidationError as exc:
        return (
            APIResponseService
            .validation_error(
                message=exc.message,
                details=exc.details,
                request=request,
            )
        )

    except RoleStateValidationError as exc:
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
                message="Role not found.",
                request=request,
            )
        )

    return (
        APIResponseService
        .success(
            data={
                "role":
                    (
                        RoleAPISerializer
                        .serialize_detail(
                            updated_role
                        )
                    ),
            },
            message=(
                "Role permissions updated "
                "successfully."
            ),
            request=request,
        )
    )


@api_permission_required(
    "roles.activate"
)
@api_rate_limit(
    scope="roles.activate",
    limit=30,
    window_seconds=60,
)
def role_activate_api(
    request,
    role_id,
):
    if request.method != "POST":
        return (
            APIResponseService
            .method_not_allowed(
                message=(
                    "Use POST to activate "
                    "a role."
                ),
                request=request,
            )
        )

    result = (
        APITenantQueryService
        .get_document(
            Role.objects.all(),
            request,
            role_id,
            organization_context=(
                request
                .api_organization_context
            ),
        )
    )

    role = result[
        "document"
    ]

    if not role:
        return (
            APIResponseService
            .not_found(
                message="Role not found.",
                request=request,
            )
        )

    try:
        activation_result = (
            RoleManagementService
            .activate_role(
                organization=(
                    request
                    .api_organization
                ),
                role=role,
                actor=(
                    request.api_user
                ),
                request=request,
            )
        )

    except RoleStateValidationError as exc:
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
                message="Role not found.",
                request=request,
            )
        )

    activated_role = (
        activation_result[
            "role"
        ]
    )

    state_changed = (
        activation_result[
            "state_changed"
        ]
    )

    return (
        APIResponseService
        .success(
            data={
                "role":
                    (
                        RoleAPISerializer
                        .serialize_detail(
                            activated_role
                        )
                    ),

                "state_changed":
                    state_changed,
            },
            message=(
                "Role activated successfully."
                if state_changed
                else
                "Role is already active."
            ),
            request=request,
        )
    )


@api_permission_required(
    "roles.deactivate"
)
@api_rate_limit(
    scope="roles.deactivate",
    limit=30,
    window_seconds=60,
)
def role_deactivate_api(
    request,
    role_id,
):
    if request.method != "POST":
        return (
            APIResponseService
            .method_not_allowed(
                message=(
                    "Use POST to deactivate "
                    "a role."
                ),
                request=request,
            )
        )

    result = (
        APITenantQueryService
        .get_document(
            Role.objects.all(),
            request,
            role_id,
            organization_context=(
                request
                .api_organization_context
            ),
        )
    )

    role = result[
        "document"
    ]

    if not role:
        return (
            APIResponseService
            .not_found(
                message="Role not found.",
                request=request,
            )
        )

    try:
        deactivation_result = (
            RoleManagementService
            .deactivate_role(
                organization=(
                    request
                    .api_organization
                ),
                role=role,
                actor=(
                    request.api_user
                ),
                request=request,
            )
        )

    except RoleStateValidationError as exc:
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
                message="Role not found.",
                request=request,
            )
        )

    deactivated_role = (
        deactivation_result[
            "role"
        ]
    )

    state_changed = (
        deactivation_result[
            "state_changed"
        ]
    )

    assigned_active_users = (
        deactivation_result[
            "assigned_active_users"
        ]
    )

    return (
        APIResponseService
        .success(
            data={
                "role":
                    (
                        RoleAPISerializer
                        .serialize_detail(
                            deactivated_role
                        )
                    ),

                "state_changed":
                    state_changed,

                "assigned_active_users":
                    assigned_active_users,
            },
            message=(
                "Role deactivated successfully."
                if state_changed
                else
                "Role is already inactive."
            ),
            request=request,
        )
    )