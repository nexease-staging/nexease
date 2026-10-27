from django.contrib.auth.backends import BaseBackend

from apps.accounts.models import User

from apps.accounts.login_rate_limit_service import (
    LoginRateLimitService,
)

from apps.accounts.authentication_audit_service import (
    AuthenticationAuditService,
)

from apps.core.services.application_logging_service import (
    ApplicationLoggingService,
)


class MongoEngineBackend(BaseBackend):

    def authenticate(
        self,
        request,
        username=None,
        password=None,
        **kwargs,
    ):
        # ==================================================
        # IDENTIFIER
        # ==================================================

        email = (
            kwargs.get(
                "email"
            )
            or
            username
        )

        if not email or not password:
            return None

        email = (
            str(
                email
            )
            .strip()
            .lower()
        )

        if not email:
            return None

        # ==================================================
        # CLIENT IP
        # ==================================================

        ip_address = (
            LoginRateLimitService
            .get_client_ip(
                request
            )
        )

        request_id = getattr(
            request,
            "request_id",
            None,
        )

        # ==================================================
        # RATE LIMIT IDENTIFIER
        # ==================================================

        rate_limit_identifier = (
            LoginRateLimitService
            .build_identifier(
                email=email,
                ip_address=ip_address,
            )
        )

        # ==================================================
        # RATE LIMIT CHECK
        # ==================================================

        if (
            LoginRateLimitService
            .is_blocked(
                rate_limit_identifier
            )
        ):

            AuthenticationAuditService.record(
                event_type="LOGIN_BLOCKED",
                identifier=email,
                ip_address=ip_address,
            )

            ApplicationLoggingService.log(
                level="WARNING",
                message=(
                    "Authentication blocked "
                    "by rate limit."
                ),
                module="accounts",
                action="login",
                status="blocked",
                request_id=request_id,
                identifier=email,
                ip_address=ip_address,
            )

            return None

        # ==================================================
        # USER LOOKUP
        # ==================================================

        try:

            user = (
                User.objects(
                    email=email
                )
                .first()
            )

        except Exception:

            return None

        # ==================================================
        # UNKNOWN USER
        # ==================================================

        if not user:

            LoginRateLimitService.register_failure(
                rate_limit_identifier
            )

            AuthenticationAuditService.record(
                event_type="LOGIN_FAILED",
                identifier=email,
                ip_address=ip_address,
            )

            ApplicationLoggingService.log(
                level="WARNING",
                message="Authentication failed.",
                module="accounts",
                action="login",
                status="failed",
                request_id=request_id,
                identifier=email,
                ip_address=ip_address,
                reason="invalid_credentials",
            )

            return None

        # ==================================================
        # USER STATUS
        # ==================================================

        if not user.is_active:

            ApplicationLoggingService.log(
                level="WARNING",
                message="Authentication rejected.",
                module="accounts",
                action="login",
                status="blocked",
                user=user,
                organization=getattr(
                    user,
                    "organization",
                    None,
                ),
                request_id=request_id,
                identifier=email,
                ip_address=ip_address,
                reason="inactive_account",
            )

            return None

        # ==================================================
        # ORGANIZATION
        # ==================================================

        organization = getattr(
            user,
            "organization",
            None,
        )

        if not organization:

            ApplicationLoggingService.log(
                level="WARNING",
                message="Authentication rejected.",
                module="accounts",
                action="login",
                status="blocked",
                user=user,
                request_id=request_id,
                identifier=email,
                ip_address=ip_address,
                reason="organization_missing",
            )

            return None

        if not getattr(
            organization,
            "is_active",
            False,
        ):

            ApplicationLoggingService.log(
                level="WARNING",
                message="Authentication rejected.",
                module="accounts",
                action="login",
                status="blocked",
                user=user,
                organization=organization,
                request_id=request_id,
                identifier=email,
                ip_address=ip_address,
                reason="organization_inactive",
            )

            return None

        # ==================================================
        # PASSWORD
        # ==================================================

        if not user.check_password(
            password
        ):

            LoginRateLimitService.register_failure(
                rate_limit_identifier
            )

            AuthenticationAuditService.record(
                event_type="LOGIN_FAILED",
                user=user,
                identifier=email,
                ip_address=ip_address,
            )

            ApplicationLoggingService.log(
                level="WARNING",
                message="Authentication failed.",
                module="accounts",
                action="login",
                status="failed",
                user=user,
                organization=organization,
                request_id=request_id,
                identifier=email,
                ip_address=ip_address,
                reason="invalid_credentials",
            )

            return None

        # ==================================================
        # SUCCESS
        # ==================================================

        LoginRateLimitService.register_success(
            rate_limit_identifier
        )

        AuthenticationAuditService.record(
            event_type="LOGIN_SUCCESS",
            user=user,
            identifier=email,
            ip_address=ip_address,
        )

        ApplicationLoggingService.log(
            level="INFO",
            message="Authentication succeeded.",
            module="accounts",
            action="login",
            status="success",
            user=user,
            organization=organization,
            request_id=request_id,
            identifier=email,
            ip_address=ip_address,
        )

        return user

    def get_user(
        self,
        user_id,
    ):
        try:

            user = (
                User.objects(
                    id=user_id
                )
                .first()
            )

        except Exception:

            return None

        # ==================================================
        # USER
        # ==================================================

        if not user:
            return None

        if not user.is_active:
            return None

        # ==================================================
        # ORGANIZATION
        # ==================================================

        organization = getattr(
            user,
            "organization",
            None,
        )

        if not organization:
            return None

        if not getattr(
            organization,
            "is_active",
            False,
        ):
            return None

        return user