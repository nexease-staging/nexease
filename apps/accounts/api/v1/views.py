import json
from mongoengine.errors import DoesNotExist
from django.contrib.auth import authenticate
from apps.accounts.password_reset_timing_service import (
    PasswordResetTimingService,
)
from apps.accounts.login_rate_limit_service import (
    LoginRateLimitService,
)
from apps.accounts.services import (
    AuthenticationService,
)
from apps.accounts.password_reset_email_service import (
    PasswordResetEmailError,
    PasswordResetEmailService,
)
from apps.core.services.api_response_service import (
    APIResponseService,
)
from django.http import (
    HttpResponse,
    JsonResponse,
)
from django.views.decorators.http import (
    require_http_methods,
)
from apps.organizations.api_context_service import (
    APIOrganizationContextService,
)
from apps.authorization.api_context_service import (
    APIPermissionContextService,
)
from apps.core.api.decorators import (
    api_login_required,
    api_rate_limit,
)
from apps.accounts.password_reset_service import (
    PasswordResetError,
    PasswordResetService,
)
from apps.accounts.api.v1.serializers import (
    AccountAPISerializer,
)
from apps.accounts.organization_signup_service import (
    OrganizationSignupError,
    OrganizationSignupService,
)
from django.core.validators import (
    validate_email,
)
from django.core.exceptions import (
    ValidationError as DjangoValidationError,
)
from django.contrib.auth.password_validation import (
    validate_password,
)
from apps.accounts.authentication_audit_log_service import (
    AuthenticationAuditLogService,
)

from apps.core.services.api_discovery_service import (
    APIDiscoveryService,
)
from django.middleware.csrf import (
    get_token,
)
from django.views.decorators.csrf import (
    ensure_csrf_cookie,
)

def auth_root(
    request,
):
    # ==================================================
    # METHOD
    # ==================================================

    if request.method != "GET":

        return (
            APIResponseService
            .method_not_allowed(
                message=(
                    "Use GET to retrieve "
                    "authentication metadata."
                ),
                request=request,
            )
        )

    # ==================================================
    # RESPONSE
    # ==================================================

    return (
        APIResponseService
        .success(
            data={
                "namespace":
                    "auth",

                "version":
                    "v1",

                "authentication":
                    "session",

                "endpoints": (
                    APIDiscoveryService
                    .get_authentication_endpoints()
                ),

                "capabilities": {
                    "csrf_required_for_unsafe_methods":
                        True,

                    "session_cookie_name":
                        (
                            APIDiscoveryService
                            .get_capabilities()
                            [
                                "authentication"
                            ]
                            [
                                "cookie_name"
                            ]
                        ),

                    "server_request_header":
                        "X-Request-ID",

                    "client_correlation_header":
                        "X-Correlation-ID",
                },
            },
            message=(
                "Authentication API metadata "
                "retrieved successfully."
            ),
            request=request,
        )
    )


@ensure_csrf_cookie
def csrf_api(
    request,
):
    # ==================================================
    # METHOD
    # ==================================================

    if request.method != "GET":

        return (
            APIResponseService
            .method_not_allowed(
                message=(
                    "Use GET to retrieve "
                    "a CSRF token."
                ),
                request=request,
            )
        )

    # ==================================================
    # TOKEN
    # ==================================================

    csrf_token = get_token(
        request
    )

    # ==================================================
    # RESPONSE
    # ==================================================

    return (
        APIResponseService
        .success(
            data={
                "csrf": {
                    "token":
                        csrf_token,

                    "header_name":
                        "X-CSRFToken",

                    "cookie_name":
                        "csrftoken",
                },
            },
            message=(
                "CSRF token issued "
                "successfully."
            ),
            request=request,
        )
    )


def login_api(
    request,
):
    # ==================================================
    # METHOD
    # ==================================================

    if request.method != "POST":

        return (
            APIResponseService
            .method_not_allowed(
                message=(
                    "Use POST to authenticate."
                ),
                request=request,
            )
        )

    # ==================================================
    # CONTENT TYPE
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

    # ==================================================
    # JSON BODY
    # ==================================================

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

    if not isinstance(
        payload,
        dict,
    ):

        return (
            APIResponseService
            .validation_error(
                message="Validation failed.",
                details={
                    "body": [
                        (
                            "JSON body must "
                            "be an object."
                        )
                    ],
                },
                request=request,
            )
        )

    # ==================================================
    # INPUT
    # ==================================================

    email = (
        LoginRateLimitService
        .normalize_email(
            payload.get(
                "email"
            )
        )
    )

    password = payload.get(
        "password"
    )

    validation_errors = {}

    if not email:

        validation_errors[
            "email"
        ] = [
            "Email is required."
        ]

    if (
        not isinstance(
            password,
            str,
        )
        or
        not password
    ):

        validation_errors[
            "password"
        ] = [
            "Password is required."
        ]

    if validation_errors:

        return (
            APIResponseService
            .validation_error(
                message="Validation failed.",
                details=validation_errors,
                request=request,
            )
        )

    # ==================================================
    # AUTHENTICATE
    #
    # MongoEngineBackend performs:
    # - login rate-limit checking
    # - user lookup
    # - user active validation
    # - organization validation
    # - password verification
    # - authentication audit logging
    # - operational logging
    # ==================================================

    user = authenticate(
        request=request,
        email=email,
        password=password,
    )

    # ==================================================
    # AUTHENTICATION FAILED
    # ==================================================

    if user is None:

        ip_address = (
            LoginRateLimitService
            .get_client_ip(
                request
            )
        )

        rate_limit_identifier = (
            LoginRateLimitService
            .build_identifier(
                email=email,
                ip_address=ip_address,
            )
        )

        rate_limit_status = (
            LoginRateLimitService
            .get_status(
                rate_limit_identifier
            )
        )

        if rate_limit_status[
            "blocked"
        ]:

            return (
                APIResponseService
                .rate_limited(
                    message=(
                        "Too many failed login "
                        "attempts. Try again later."
                    ),
                    request=request,
                )
            )

        return (
            APIResponseService
            .unauthorized(
                message=(
                    "Invalid email or password."
                ),
                request=request,
            )
        )

    # ==================================================
    # ORGANIZATION
    # ==================================================

    organization = getattr(
        user,
        "organization",
        None,
    )

    if not organization:

        return (
            APIResponseService
            .forbidden(
                message=(
                    "Organization context "
                    "is unavailable."
                ),
                request=request,
            )
        )

    # ==================================================
    # ORGANIZATION CONTEXT
    #
    # This context is derived from the authenticated
    # backend user, never from request JSON.
    # ==================================================

    organization_context = {
        "user":
            user,

        "organization":
            organization,

        "organization_id":
            str(
                organization.id
            ),
    }

    # ==================================================
    # PERMISSION CONTEXT
    #
    # Resolve this before creating the session. If the
    # role belongs to another tenant, no authenticated
    # session should be issued.
    # ==================================================

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

    except PermissionError:

        return (
            APIResponseService
            .forbidden(
                message=(
                    "Invalid authorization "
                    "context."
                ),
                request=request,
            )
        )

    role = permission_context[
        "role"
    ]

    permissions = permission_context[
        "permission_codes"
    ]

    permissions_by_module = (
        permission_context[
            "permissions_by_module"
        ]
    )

    # ==================================================
    # CREATE SESSION
    # ==================================================

    try:

        AuthenticationService.login(
            request,
            user,
        )

    except Exception:

        return (
            APIResponseService
            .internal_error(
                message=(
                    "Unable to create "
                    "authentication session."
                ),
                request=request,
            )
        )

    # ==================================================
    # SERIALIZED RESPONSE
    # ==================================================

    response_data = (
        AccountAPISerializer
        .serialize_authentication_context(
            user=user,
            organization=organization,
            role=role,
            permission_codes=(
                permissions
            ),
            permissions_by_module=(
                permissions_by_module
            ),
            authenticated=True,
        )
    )

    return (
        APIResponseService
        .success(
            data=response_data,
            message="Login successful.",
            status=200,
            request=request,
        )
    )
def logout_api(
    request,
):
    # ==================================================
    # METHOD
    # ==================================================

    if request.method != "POST":

        return (
            APIResponseService
            .method_not_allowed(
                message=(
                    "Use POST to log out."
                ),
                request=request,
            )
        )

    # ==================================================
    # AUTHENTICATION
    # ==================================================

    user = (
        AuthenticationService
        .get_user(
            request
        )
    )

    if not user:

        return (
            APIResponseService
            .unauthorized(
                message="Not authenticated.",
                request=request,
            )
        )

    user_id = str(
        user.id
    )

    email = user.email

    # ==================================================
    # LOGOUT
    #
    # AuthenticationService.logout():
    # - records LOGOUT audit
    # - records operational log
    # - flushes the current session
    # ==================================================

    try:

        AuthenticationService.logout(
            request
        )

    except Exception:

        return (
            APIResponseService
            .internal_error(
                message=(
                    "Unable to terminate "
                    "authentication session."
                ),
                request=request,
            )
        )

    # ==================================================
    # RESPONSE
    # ==================================================

    return (
        APIResponseService
        .success(
            data={
                "authentication": {
                    "type":
                        "session",

                    "authenticated":
                        False,
                },

                "logged_out_user": {
                    "id":
                        user_id,

                    "email":
                        email,
                },
            },
            message="Logout successful.",
            status=200,
            request=request,
        )
    )

@api_login_required
def logout_all_api(
    request,
):
    # ==================================================
    # METHOD
    # ==================================================

    if request.method != "POST":

        return (
            APIResponseService
            .method_not_allowed(
                message=(
                    "Use POST to log out "
                    "from all devices."
                ),
                request=request,
            )
        )

    # ==================================================
    # TRUSTED AUTHENTICATION CONTEXT
    # ==================================================

    user = request.api_user

    user_id = str(
        user.id
    )

    email = user.email

    # ==================================================
    # LOGOUT ALL DEVICES
    #
    # The service:
    # - finds every MongoDB session for the user
    # - deletes those sessions
    # - records LOGOUT_ALL audit
    # - records the operational log
    # - flushes the current session
    # ==================================================

    try:

        deleted_count = (
            AuthenticationService
            .logout_all_devices(
                request,
                user,
            )
        )

    except Exception:

        return (
            APIResponseService
            .internal_error(
                message=(
                    "Unable to terminate "
                    "authentication sessions."
                ),
                request=request,
            )
        )

    # ==================================================
    # RESPONSE
    # ==================================================

    return (
        APIResponseService
        .success(
            data={
                "authentication": {
                    "type":
                        "session",

                    "authenticated":
                        False,
                },

                "logged_out_user": {
                    "id":
                        user_id,

                    "email":
                        email,
                },

                "sessions_deleted":
                    deleted_count,
            },
            message=(
                "Logged out from all "
                "devices successfully."
            ),
            status=200,
            request=request,
        )
    )


@api_login_required
def me_api(
    request,
):
    # ==================================================
    # METHOD
    # ==================================================

    if request.method != "GET":

        return (
            APIResponseService
            .method_not_allowed(
                message=(
                    "Use GET to retrieve "
                    "the current user."
                ),
                request=request,
            )
        )

    # ==================================================
    # ORGANIZATION CONTEXT
    # ==================================================

    organization_context = (
        request.api_organization_context
    )

    user = request.api_user

    organization = (
        request.api_organization
    )

    # ==================================================
    # PERMISSION CONTEXT
    # ==================================================

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

    role = permission_context[
        "role"
    ]

    permissions = permission_context[
        "permission_codes"
    ]

    permissions_by_module = (
        permission_context[
            "permissions_by_module"
        ]
    )

    # ==================================================
    # RESPONSE
    # ==================================================

    return (
        APIResponseService
        .success(
            data=(
                AccountAPISerializer
                .serialize_authentication_context(
                    user=user,
                    organization=organization,
                    role=role,
                    permission_codes=(
                        permissions
                    ),
                    permissions_by_module=(
                        permissions_by_module
                    ),
                    authenticated=True,
                )
            ),
            message=(
                "Current user retrieved "
                "successfully."
            ),
            status=200,
            request=request,
        )
    )

@api_login_required
def authentication_audit_logs_api(
    request,
):
    # ==================================================
    # METHOD
    # ==================================================

    if request.method != "GET":

        return (
            APIResponseService
            .method_not_allowed(
                message=(
                    "Use GET to retrieve "
                    "authentication audit logs."
                ),
                request=request,
            )
        )

    # ==================================================
    # TRUSTED CONTEXT
    #
    # Organization is derived from the authenticated
    # session. Never accept a tenant ID from the client.
    # ==================================================

    user = request.api_user

    organization = (
        request.api_organization
    )

    # ==================================================
    # QUERY PARAMETERS
    # ==================================================

    event_type = (
        request.GET.get(
            "event_type"
        )
    )

    identifier = (
        request.GET.get(
            "identifier"
        )
    )

    ip_address = (
        request.GET.get(
            "ip_address"
        )
    )

    limit = (
        request.GET.get(
            "limit",
            "100",
        )
    )

    # ==================================================
    # SERVICE
    # ==================================================

    try:

        logs = (
            AuthenticationAuditLogService
            .list_logs(
                user=user,
                organization=organization,
                event_type=event_type,
                identifier=identifier,
                ip_address=ip_address,
                limit=limit,
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

    except ValueError as exc:

        return (
            APIResponseService
            .validation_error(
                message="Validation failed.",
                details={
                    "query": [
                        str(
                            exc
                        )
                    ],
                },
                request=request,
            )
        )

    # ==================================================
    # SERIALIZE
    # ==================================================

    serialized_logs = []

    for log in logs:
        try:
            log_user = log.user
        except DoesNotExist:
            log_user = None

        serialized_logs.append(
            {
                "id":
                    str(
                        log.id
                    ),

                "event_type":
                    log.event_type,

                "user": (
                    {
                        "id":
                            str(
                                log_user.id
                            ),

                        "email":
                            log_user.email,
                    }

                    if log_user
                    else None
                ),

                "identifier":
                    log.identifier,

                "ip_address":
                    log.ip_address,

                "created_at": (
                    log.created_at.isoformat()
                    if log.created_at
                    else None
                ),

                "integrity": {
                    "hashed":
                        bool(
                            log.integrity_hash
                        ),

                    "verified":
                        log.verify_integrity(),
                },
            }
        )

    # ==================================================
    # RESPONSE
    # ==================================================

    return (
        APIResponseService
        .success(
            data={
                "authentication_audit_logs":
                    serialized_logs,

                "count":
                    len(
                        serialized_logs
                    ),

                "query": {
                    "event_type":
                        event_type,

                    "identifier":
                        identifier,

                    "ip_address":
                        ip_address,

                    "limit":
                        int(
                            limit
                        ),
                },
            },
            message=(
                "Authentication audit logs "
                "retrieved successfully."
            ),
            status=200,
            request=request,
        )
    )

@api_rate_limit(
    scope="auth.signup",
    limit=5,
    window_seconds=3600,
)
def signup_api(
    request,
):
    # ==================================================
    # METHOD
    # ==================================================

    if request.method != "POST":

        return (
            APIResponseService
            .method_not_allowed(
                message=(
                    "Use POST to create "
                    "an organization account."
                ),
                request=request,
            )
        )

    # ==================================================
    # CONTENT TYPE
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

    # ==================================================
    # JSON BODY
    # ==================================================

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

    if not isinstance(
        payload,
        dict,
    ):

        return (
            APIResponseService
            .validation_error(
                message="Validation failed.",
                details={
                    "body": [
                        (
                            "JSON body must "
                            "be an object."
                        )
                    ],
                },
                request=request,
            )
        )

    # ==================================================
    # INPUT
    # ==================================================

    def clean_string(
        field_name,
    ):
        value = payload.get(
            field_name
        )

        if not isinstance(
            value,
            str,
        ):
            return ""

        return value.strip()

    organization_name = clean_string(
        "organization_name"
    )

    organization_email = (
        OrganizationSignupService
        .normalize_email(
            payload.get(
                "organization_email"
            )
        )
    )

    first_name = clean_string(
        "first_name"
    )

    last_name = clean_string(
        "last_name"
    )

    user_email = (
        OrganizationSignupService
        .normalize_email(
            payload.get(
                "email"
            )
        )
    )

    password = payload.get(
        "password"
    )

    phone = clean_string(
        "phone"
    )

    # ==================================================
    # REQUIRED FIELDS
    # ==================================================

    validation_errors = {}

    if not organization_name:
        validation_errors[
            "organization_name"
        ] = [
            "Organization name is required."
        ]

    if not organization_email:
        validation_errors[
            "organization_email"
        ] = [
            "Organization email is required."
        ]

    if not first_name:
        validation_errors[
            "first_name"
        ] = [
            "First name is required."
        ]

    if not last_name:
        validation_errors[
            "last_name"
        ] = [
            "Last name is required."
        ]

    if not user_email:
        validation_errors[
            "email"
        ] = [
            "Email is required."
        ]

    if (
        not isinstance(
            password,
            str,
        )
        or
        not password
    ):
        validation_errors[
            "password"
        ] = [
            "Password is required."
        ]

    # ==================================================
    # EMAIL VALIDATION
    # ==================================================

    if organization_email:

        try:
            validate_email(
                organization_email
            )

        except DjangoValidationError:
            validation_errors[
                "organization_email"
            ] = [
                (
                    "Enter a valid organization "
                    "email address."
                )
            ]

    if user_email:

        try:
            validate_email(
                user_email
            )

        except DjangoValidationError:
            validation_errors[
                "email"
            ] = [
                "Enter a valid email address."
            ]

    # ==================================================
    # PASSWORD VALIDATION
    # ==================================================

    if (
        isinstance(
            password,
            str,
        )
        and
        password
    ):

        try:

            validate_password(
                password
            )

        except DjangoValidationError as exc:

            validation_errors[
                "password"
            ] = list(
                exc.messages
            )

    # ==================================================
    # VALIDATION RESPONSE
    # ==================================================

    if validation_errors:

        return (
            APIResponseService
            .validation_error(
                message="Validation failed.",
                details=validation_errors,
                request=request,
            )
        )

    # ==================================================
    # CREATE ORGANIZATION ACCOUNT
    # ==================================================

    try:

        result = (
            OrganizationSignupService
            .create_organization_account(
                business_scope=payload.get("business_scope", "mixed"),
                organization_name=(
                    organization_name
                ),
                organization_email=(
                    organization_email
                ),
                first_name=first_name,
                last_name=last_name,
                user_email=user_email,
                password=password,
                phone=phone,
            )
        )

    except OrganizationSignupError as exc:

        return (
            APIResponseService
            .validation_error(
                message=str(
                    exc
                ),
                request=request,
            )
        )

    except Exception:

        return (
            APIResponseService
            .internal_error(
                message=(
                    "Unable to create "
                    "organization account."
                ),
                request=request,
            )
        )

    # ==================================================
    # RESPONSE
    # ==================================================

    organization = result[
        "organization"
    ]

    user = result[
        "user"
    ]

    role = result[
        "role"
    ]

    return (
        APIResponseService
        .success(
            data={
                "organization": {
                    "id":
                        str(
                            organization.id
                        ),

                    "name":
                        organization.name,

                    "email":
                        organization.email,
                },

                "user": {
                    "id":
                        str(
                            user.id
                        ),

                    "email":
                        user.email,

                    "first_name":
                        user.first_name,

                    "last_name":
                        user.last_name,
                },

                "role": {
                    "id":
                        str(
                            role.id
                        ),

                    "name":
                        role.name,
                },
            },
            message=(
                "Organization account "
                "created successfully."
            ),
            status=201,
            request=request,
        )
    )

@api_rate_limit(
    scope="auth.forgot_password",
    limit=5,
    window_seconds=900,
)
@require_http_methods(["POST"])
def forgot_password_api(request):
    try:
        payload = json.loads(
            request.body or "{}"
        )
    except json.JSONDecodeError:
        return (
            APIResponseService
            .bad_request(
                message="Invalid JSON body.",
                request=request,
            )
        )

    email = str(
        payload.get(
            "email",
            "",
        )
    ).strip()

    if not email:
        return (
            APIResponseService
            .validation_error(
                message="Validation failed.",
                details={
                    "email": [
                        "Email is required."
                    ],
                },
                request=request,
            )
        )

    timing_started_at = (
        PasswordResetTimingService.start()
    )

    # Deliberately ignore whether a matching
    # account exists. The public response must
    # be identical in both cases.
    reset_result = (
        PasswordResetService
        .create_reset_token(
            email=email,
        )
    )

    if reset_result is not None:
        try:
            PasswordResetEmailService.send_reset_email(
                user=reset_result["user"],
                token=reset_result["token"],
                expires_at=reset_result[
                    "expires_at"
                ],
            )

        except PasswordResetEmailError:
            # Keep the public response generic so
            # email delivery failures do not reveal
            # whether an account exists.
            pass

    # Ensure valid forgot-password requests have
    # a minimum response duration so account
    # existence is harder to infer from timing.
    PasswordResetTimingService.wait_for_minimum_duration(
        started_at=timing_started_at,
    )

    return (
        APIResponseService
        .success(
            data={
                "message": (
                    "If an account exists for that "
                    "email address, password reset "
                    "instructions will be sent."
                ),
            },
            message=(
                "Password reset request "
                "processed successfully."
            ),
            request=request,
        )
    )

@api_rate_limit(
    scope="auth.reset_password",
    limit=10,
    window_seconds=900,
)
@require_http_methods(["POST"])
def reset_password_api(request):
    try:
        payload = json.loads(
            request.body or "{}"
        )
    except json.JSONDecodeError:
        return (
            APIResponseService
            .bad_request(
                message="Invalid JSON body.",
                request=request,
            )
        )

    token = str(
        payload.get(
            "token",
            "",
        )
    ).strip()

    new_password = str(
        payload.get(
            "new_password",
            "",
        )
    )

    errors = {}

    if not token:
        errors["token"] = [
            "Reset token is required."
        ]

    if not new_password:
        errors["new_password"] = [
            "New password is required."
        ]

    if errors:
        return (
            APIResponseService
            .validation_error(
                message="Validation failed.",
                details=errors,
                request=request,
            )
        )

    try:
        result = (
            PasswordResetService
            .reset_password(
                token=token,
                new_password=new_password,
            )
        )

    except PasswordResetError as error:
        return (
            APIResponseService
            .bad_request(
                message=str(error),
                request=request,
            )
        )
    return (
        APIResponseService
        .success(
            data={
                "message": (
                    "Your password has been reset "
                    "successfully. Please sign in "
                    "with your new password."
                ),
                "sessions_revoked": (
                    result[
                        "sessions_revoked"
                    ]
                ),
            },
            message=(
                "Password reset completed "
                "successfully."
            ),
            request=request,
        )
    )