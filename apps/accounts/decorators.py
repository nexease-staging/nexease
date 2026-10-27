from functools import wraps

from django.http import HttpResponse

from apps.accounts.services import AuthenticationService


def mongo_login_required(view_func):

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):

        user = AuthenticationService.get_user(request)

        if user is None:
            return HttpResponse(
                "Authentication required",
                status=401,
            )

        request.user = user

        return view_func(
            request,
            *args,
            **kwargs,
        )

    return wrapper

from functools import wraps

from django.http import HttpResponse


def permission_required(permission_code):

    def decorator(view_func):

        @wraps(view_func)
        def wrapper(request, *args, **kwargs):

            if not request.user.is_authenticated:
                return HttpResponse(
                    "Not authenticated",
                    status=401,
                )

            if not request.user.has_permission(
                permission_code
            ):
                return HttpResponse(
                    "Permission denied",
                    status=403,
                )

            return view_func(
                request,
                *args,
                **kwargs,
            )

        return wrapper

    return decorator

from functools import wraps

from django.http import HttpResponse

from apps.authorization.tenant_service import TenantService


def tenant_required(view_func):

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):

        if not request.user.is_authenticated:
            return HttpResponse(
                "Not authenticated",
                status=401,
            )

        organization = getattr(
            request.user,
            "organization",
            None,
        )

        if not organization:
            return HttpResponse(
                "User has no organization",
                status=403,
            )

        return view_func(
            request,
            *args,
            **kwargs,
        )

    return wrapper