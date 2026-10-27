from datetime import (
    datetime,
    timedelta,
)

from apps.accounts.security_models import (
    LoginAttempt,
)


class LoginRateLimitService:

    MAX_FAILURES = 5
    BLOCK_MINUTES = 15
    STALE_RECORD_DAYS = 30

    @staticmethod
    def normalize_email(
        email,
    ):
        return (
            str(
                email
                or
                ""
            )
            .strip()
            .lower()
        )

    @staticmethod
    def normalize_ip(
        ip_address,
    ):
        return (
            str(
                ip_address
                or
                "unknown"
            )
            .strip()
            .lower()
        )

    @staticmethod
    def build_identifier(
        *,
        email,
        ip_address,
    ):
        normalized_email = (
            LoginRateLimitService
            .normalize_email(
                email
            )
        )

        normalized_ip = (
            LoginRateLimitService
            .normalize_ip(
                ip_address
            )
        )

        return (
            f"{normalized_email}"
            f"|"
            f"{normalized_ip}"
        )

    @staticmethod
    def get_client_ip(
        request,
    ):
        if request is None:
            return "unknown"

        # ==================================================
        # TRUSTED PROXY MODE
        # ==================================================

        from django.conf import settings

        trust_proxy = getattr(
            settings,
            "TRUST_PROXY_SSL_HEADER",
            False,
        )

        if trust_proxy:

            forwarded_for = (
                request.META.get(
                    "HTTP_X_FORWARDED_FOR"
                )
            )

            if forwarded_for:

                first_ip = (
                    forwarded_for
                    .split(
                        ","
                    )[0]
                    .strip()
                )

                if first_ip:
                    return first_ip

        # ==================================================
        # DIRECT CONNECTION
        # ==================================================

        remote_addr = (
            request.META.get(
                "REMOTE_ADDR"
            )
        )

        if remote_addr:

            return (
                str(
                    remote_addr
                )
                .strip()
            )

        return "unknown"

    @staticmethod
    def _get_attempt(
        identifier,
    ):
        return (
            LoginAttempt.objects(
                identifier=identifier
            )
            .first()
        )

    @staticmethod
    def is_blocked(
        identifier,
    ):
        attempt = (
            LoginRateLimitService
            ._get_attempt(
                identifier
            )
        )

        if not attempt:
            return False

        if not attempt.blocked_until:
            return False

        if (
            attempt.blocked_until
            <=
            datetime.utcnow()
        ):
            attempt.failure_count = 0
            attempt.blocked_until = None
            attempt.updated_at = (
                datetime.utcnow()
            )

            attempt.save()

            return False

        return True

    @staticmethod
    def register_failure(
        identifier,
    ):
        if not identifier:
            return

        now = datetime.utcnow()

        attempt = (
            LoginRateLimitService
            ._get_attempt(
                identifier
            )
        )

        if not attempt:

            attempt = LoginAttempt(
                identifier=identifier,
                failure_count=0,
                created_at=now,
                updated_at=now,
            )

        attempt.failure_count += 1
        attempt.last_failure_at = now
        attempt.updated_at = now

        if (
            attempt.failure_count
            >=
            LoginRateLimitService.MAX_FAILURES
        ):
            attempt.blocked_until = (
                now
                +
                timedelta(
                    minutes=(
                        LoginRateLimitService
                        .BLOCK_MINUTES
                    )
                )
            )

        attempt.save()

    @staticmethod
    def register_success(
        identifier,
    ):
        if not identifier:
            return

        LoginAttempt.objects(
            identifier=identifier
        ).delete()

    @staticmethod
    def get_status(
        identifier,
    ):
        attempt = (
            LoginRateLimitService
            ._get_attempt(
                identifier
            )
        )

        if not attempt:

            return {
                "blocked":
                    False,

                "failure_count":
                    0,

                "blocked_until":
                    None,
            }

        blocked = (
            LoginRateLimitService
            .is_blocked(
                identifier
            )
        )

        attempt = (
            LoginRateLimitService
            ._get_attempt(
                identifier
            )
        )

        if not attempt:

            return {
                "blocked":
                    False,

                "failure_count":
                    0,

                "blocked_until":
                    None,
            }

        return {
            "blocked":
                blocked,

            "failure_count":
                attempt.failure_count,

            "blocked_until":
                attempt.blocked_until,
        }

    @staticmethod
    def cleanup_stale_attempts():

        cutoff = (
            datetime.utcnow()
            -
            timedelta(
                days=(
                    LoginRateLimitService
                    .STALE_RECORD_DAYS
                )
            )
        )

        stale_attempts = (
            LoginAttempt.objects(
                updated_at__lt=cutoff
            )
        )

        deleted_count = (
            stale_attempts.count()
        )

        stale_attempts.delete()

        return deleted_count