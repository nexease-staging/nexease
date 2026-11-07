from mongoengine.connection import get_db

from django.conf import settings
from apps.accounts.models import User
from apps.accounts.session_models import (
    MongoSession,
)
from apps.accounts.authentication_audit_service import (
    AuthenticationAuditService,
)

from apps.accounts.login_rate_limit_service import (
    LoginRateLimitService,
)
from apps.core.services.application_logging_service import (
    ApplicationLoggingService,
)
class AuthenticationService:

    SESSION_USER_ID = "ims_user_id"

    SESSION_CHANNEL = "nexease_session_channel"

    @staticmethod
    def _channel(request):
        if (getattr(settings, "NEXEASE_MOBILE_ENABLED", False)
                and request.META.get("HTTP_ORIGIN") == "https://localhost"
                and (request.META.get("HTTP_X_NEXEASE_CLIENT") == "android"
                     or "Android" in request.META.get("HTTP_USER_AGENT", ""))):
            return "android"
        return "web"

    @staticmethod
    def _slots():
        return get_db()["nexease_active_login_slots"]

    @staticmethod
    def login(
        request,
        user,
    ):
        AuthenticationService._clear_request_user(request)
        request.session.cycle_key()
        request.session[
            AuthenticationService.SESSION_USER_ID
        ] = str(
            user.id
        )

        channel = AuthenticationService._channel(request)
        request.session[AuthenticationService.SESSION_CHANNEL] = channel
        if channel == "android":
            request.session.set_expiry(60 * 60 * 24 * 30)
        request.session.modified = True
        request.session.save()
        AuthenticationService._slots().update_one(
            {"_id": f"{user.id}:{channel}"},
            {"$set": {"session_key": request.session.session_key}},
            upsert=True,
        )

    @staticmethod
    def logout(
        request,
    ):
        user = (
            AuthenticationService
            .get_user(
                request
            )
        )

        request_id = getattr(
            request,
            "request_id",
            None,
        )

        if user:

            organization = getattr(
                user,
                "organization",
                None,
            )

            ip_address = (
                LoginRateLimitService
                .get_client_ip(
                    request
                )
            )

            AuthenticationAuditService.record(
                event_type="LOGOUT",
                user=user,
                identifier=user.email,
                ip_address=ip_address,
            )

            ApplicationLoggingService.log(
                level="INFO",
                message="User logged out.",
                module="accounts",
                action="logout",
                status="success",
                user=user,
                organization=organization,
                request_id=request_id,
                ip_address=ip_address,
            )

        AuthenticationService._clear_request_user(request)
        request.session.flush()

    @staticmethod
    def _clear_request_user(request):
        request.__dict__.pop('_nexease_auth_snapshot', None)

    @staticmethod
    def get_user(request):
        from apps.core.services.request_performance import current_scope
        scope = current_scope()
        if scope is None:
            return AuthenticationService._load_user(request)
        key = (request.session.get(AuthenticationService.SESSION_USER_ID),
               request.session.get(AuthenticationService.SESSION_CHANNEL),
               getattr(request.session, "session_key", None))
        cached = getattr(request, '_nexease_auth_snapshot', None)
        if cached is not None and cached[0] is scope and cached[1] == key:
            return cached[2]
        user = AuthenticationService._load_user(request)
        current_key = (request.session.get(AuthenticationService.SESSION_USER_ID),
                       request.session.get(AuthenticationService.SESSION_CHANNEL),
                       getattr(request.session, "session_key", None))
        request._nexease_auth_snapshot = (scope, current_key, user)
        return user

    @staticmethod
    def _load_user(
        request,
    ):

        user_id = request.session.get(
            AuthenticationService.SESSION_USER_ID
        )

        if not user_id:
            return None

        try:

            user = (
                User.objects(
                    id=user_id
                )
                .first()
            )

        except Exception:

            request.session.pop(
                AuthenticationService.SESSION_USER_ID,
                None,
            )

            request.session.modified = True

            return None

        # ==================================================
        # USER NO LONGER EXISTS
        # ==================================================

        if not user:

            request.session.pop(
                AuthenticationService.SESSION_USER_ID,
                None,
            )

            request.session.modified = True

            return None

        # ==================================================
        # USER MUST BE ACTIVE
        # ==================================================

        if not user.is_active:

            request.session.pop(
                AuthenticationService.SESSION_USER_ID,
                None,
            )

            request.session.modified = True

            return None

        # ==================================================
        # ORGANIZATION REQUIRED
        # ==================================================

        organization = getattr(
            user,
            "organization",
            None,
        )

        if not organization:

            request.session.pop(
                AuthenticationService.SESSION_USER_ID,
                None,
            )

            request.session.modified = True

            return None

        # ==================================================
        # ORGANIZATION MUST BE ACTIVE
        # ==================================================

        if not getattr(
            organization,
            "is_active",
            False,
        ):

            request.session.pop(
                AuthenticationService.SESSION_USER_ID,
                None,
            )

            request.session.modified = True

            return None

        channel = request.session.get(AuthenticationService.SESSION_CHANNEL)
        if channel not in {"web", "android"} or not AuthenticationService._slots().find_one({
            "_id": f"{user.id}:{channel}",
            "session_key": request.session.session_key,
        }, {"_id": 1}):
            AuthenticationService._clear_request_user(request)
            request.session.flush()
            return None

        return user

    @staticmethod
    def logout_all_devices(
        request,
        user,
    ):
        if not user:
            return 0

        from apps.core.device_models import NotificationDevice
        NotificationDevice.objects(user=user).delete()

        user_id = str(
            user.id
        )

        deleted_count = 0

        sessions = (
            MongoSession.objects.all()
        )

        from apps.accounts.session_backend import (
            SessionStore,
        )

        for session_record in sessions:

            try:

                store = SessionStore(
                    session_key=(
                        session_record.session_key
                    )
                )

                session_data = (
                    store.load()
                )

            except Exception:

                continue

            if (
                str(
                    session_data.get(
                        AuthenticationService
                        .SESSION_USER_ID
                    )
                )
                ==
                user_id
            ):

                session_record.delete()

                deleted_count += 1

        # ==================================================
        # AUDIT LOG
        # ==================================================

        ip_address = (
            LoginRateLimitService
            .get_client_ip(
                request
            )
        )

        AuthenticationAuditService.record(
            event_type="LOGOUT_ALL",
            user=user,
            identifier=user.email,
            ip_address=ip_address,
        )


        # ==================================================
        # OPERATIONAL LOG
        # ==================================================

        ApplicationLoggingService.log(
            level="INFO",
            message="User logged out from all devices.",
            module="accounts",
            action="logout_all",
            status="success",
            user=user,
            organization=getattr(
                user,
                "organization",
                None,
            ),
            request_id=getattr(
                request,
                "request_id",
                None,
            ),
            ip_address=ip_address,
            sessions_deleted=deleted_count,
        )


        # ==================================================
        # CLEAR CURRENT SESSION
        # ==================================================

        AuthenticationService._clear_request_user(request)
        request.session.flush()

        return deleted_count

    @staticmethod
    def revoke_user_sessions(
        user,
    ):
        if not user:
            return 0

        from apps.core.device_models import NotificationDevice
        NotificationDevice.objects(user=user).delete()

        user_id = str(
            user.id
        )

        deleted_count = 0

        from apps.accounts.session_backend import (
            SessionStore,
        )

        sessions = (
            MongoSession.objects.all()
        )

        for session_record in sessions:

            try:

                store = SessionStore(
                    session_key=(
                        session_record
                        .session_key
                    )
                )

                session_data = (
                    store.load()
                )

            except Exception:

                continue

            if (
                str(
                    session_data.get(
                        AuthenticationService
                        .SESSION_USER_ID
                    )
                )
                ==
                user_id
            ):

                session_record.delete()

                deleted_count += 1

        return deleted_count