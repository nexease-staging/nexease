from django.contrib.auth import authenticate
from django.http import HttpResponse, JsonResponse
from apps.accounts.decorators import (
    mongo_login_required,
    permission_required,
    tenant_required,
)
import time
from apps.accounts.services import AuthenticationService
from apps.accounts.decorators import mongo_login_required
from apps.accounts.decorators import (
    mongo_login_required,
    permission_required,
)
from apps.accounts.services import (
    AuthenticationService,
)
from apps.accounts.authentication_audit_log_service import (
    AuthenticationAuditLogService,
)
from pymongo.errors import (
    NetworkTimeout,
)
def test_login(request):

    user = authenticate(
        request,
        email="admin@example.com",
        password="Admin@12345",
    )

    if user is None:
        return HttpResponse(
            "Authentication failed"
        )

    AuthenticationService.login(
        request,
        user,
    )

    return HttpResponse(
        f"Logged in as: {user.email}"
    )


def test_current_user(request):

    if not request.user.is_authenticated:
        return HttpResponse(
            "Not authenticated",
            status=401,
        )

    return HttpResponse(
        f"Authenticated as: {request.user.email}"
    )

def test_logout(request):

    AuthenticationService.logout(request)

    return HttpResponse(
        "Logged out successfully"
    )

@mongo_login_required
def test_protected(request):

    return HttpResponse(
        f"Protected page. Logged in as: {request.user.email}"
    )

def test_product_create_permission(request):

    if not request.user.is_authenticated:
        return HttpResponse(
            "Not authenticated",
            status=401,
        )

    if not request.user.has_permission(
        "products.create"
    ):
        return HttpResponse(
            "Permission denied",
            status=403,
        )

    return HttpResponse(
        "Product creation allowed"
    )

@permission_required("products.create")
def test_product_create_permission(request):

    return HttpResponse(
        "Product creation allowed"
    )

@tenant_required
def test_tenant_access(request):

    organization = request.user.organization

    return HttpResponse(
        f"Tenant access allowed: {organization.name}"
    )

def test_logout_all_devices(
    request,
):

    user = (
        AuthenticationService
        .get_user(
            request
        )
    )

    if not user:

        return HttpResponse(
            "Not authenticated",
            status=401,
        )

    deleted_count = (
        AuthenticationService
        .logout_all_devices(
            request,
            user,
        )
    )

    return HttpResponse(
        (
            "Logged out from all devices. "
            f"Sessions deleted: "
            f"{deleted_count}"
        )
    )

def authentication_audit_logs(
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
    # AUTHENTICATION
    # MUST COME BEFORE ORGANIZATION / PERMISSION
    # ==================================================

    user = request.user

    if (
        not user
        or
        not getattr(
            user,
            "is_authenticated",
            False,
        )
    ):

        return JsonResponse(
            {
                "error":
                    "Not authenticated."
            },
            status=401,
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

        return JsonResponse(
            {
                "error":
                    "Organization not found."
            },
            status=403,
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

        message = str(
            exc
        )

        if (
            message
            ==
            "Not authenticated."
        ):

            status_code = 401

        else:

            status_code = 403

        return JsonResponse(
            {
                "error":
                    message
            },
            status=status_code,
        )

    except ValueError as exc:

        return JsonResponse(
            {
                "error":
                    str(
                        exc
                    )
            },
            status=400,
        )

    # ==================================================
    # SERIALIZE
    # ==================================================

    data = []

    for log in logs:

        log_user = (
            log.user
        )

        data.append(
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

    return JsonResponse(
        {
            "count":
                len(
                    data
                ),

            "authentication_audit_logs":
                data,
        },
        status=200,
    )

def test_unhandled_exception(
    request,
):
    raise RuntimeError(
        "Controlled Step 6 test exception."
    )

def test_mongodb_exception(
    request,
):
    raise NetworkTimeout(
        "Controlled MongoDB timeout for Step 7."
    )

def test_slow_request(
    request,
):
    time.sleep(
        0.15
    )

    return HttpResponse(
        "Slow request test."
    )