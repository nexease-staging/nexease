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

    @staticmethod
    def login(
        request,
        user,
    ):
        request.session.cycle_key()
        request.session[
            AuthenticationService.SESSION_USER_ID
        ] = str(
            user.id
        )

        request.session.modified = True
        request.session.save()

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

        request.session.flush()

    @staticmethod
    def get_user(
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

        return user

    @staticmethod
    def logout_all_devices(
        request,
        user,
    ):
        if not user:
            return 0

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

        request.session.flush()

        return deleted_count

    @staticmethod
    def revoke_user_sessions(
        user,
    ):
        if not user:
            return 0

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