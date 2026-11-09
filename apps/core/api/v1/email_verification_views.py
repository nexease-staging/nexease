from django.views.decorators.http import require_http_methods
from mongoengine.errors import ValidationError
from apps.core.api.decorators import api_login_required
from apps.core.services.api_response_service import APIResponseService as R
from apps.core.services import email_verification as service
from apps.business.views import payload
from apps.saas.security import rate


@api_login_required
@require_http_methods(["POST"])
def request_link(request):
    try:
        rate("sender-verify:" + str(request.api_user.id), 3, 900)
        service.request_link(request.api_user, request.headers.get("Origin", ""))
        return R.success(
            data={"sent": True},
            message="Check your inbox for the verification link.",
            request=request,
        )
    except Exception:
        return R.validation_error(
            message="Could not send verification email. Check system email configuration or retry later.",
            request=request,
        )


@require_http_methods(["POST"])
def confirm(request):
    try:
        rate(
            "sender-verify-confirm:" + request.META.get("REMOTE_ADDR", "unknown"),
            30,
            300,
        )
        token = payload(request).get("token", "")
        if not isinstance(token, str) or len(token) > 4096:
            raise ValueError("Invalid verification link.")
        service.confirm(token)
        return R.success(
            data={"verified": True}, message="Email verified.", request=request
        )
    except (ValueError, TypeError, ValidationError) as e:
        return R.validation_error(message=str(e), request=request)
