import os

from django.conf import settings


class EnvironmentValidationService:

    @staticmethod
    def validate():
        errors = []

        # ==================================================
        # APP ENV
        # ==================================================

        app_env = getattr(
            settings,
            "APP_ENV",
            None,
        )

        if app_env not in {
            "development",
            "production",
        }:
            errors.append(
                "Invalid APP_ENV."
            )

        is_production = (
            app_env
            ==
            "production"
        )

        # ==================================================
        # SECRET KEY
        # ==================================================

        secret_key = os.getenv(
            "DJANGO_SECRET_KEY"
        )

        if not secret_key:
            errors.append(
                "DJANGO_SECRET_KEY is required."
            )

        # ==================================================
        # DEBUG
        # ==================================================

        if (
            is_production
            and
            settings.DEBUG
        ):
            errors.append(
                "DEBUG must be False in production."
            )

        # ==================================================
        # ALLOWED HOSTS
        # ==================================================

        allowed_hosts = getattr(
            settings,
            "ALLOWED_HOSTS",
            [],
        )

        if is_production:

            if not allowed_hosts:
                errors.append(
                    "ALLOWED_HOSTS is required "
                    "in production."
                )

            if "*" in allowed_hosts:
                errors.append(
                    "Wildcard ALLOWED_HOSTS "
                    "is not allowed in production."
                )

        # ==================================================
        # MONGODB
        # ==================================================

        mongodb_uri = os.getenv(
            "MONGODB_URI"
        )

        mongodb_database = os.getenv(
            "MONGODB_DATABASE"
        )

        if not mongodb_uri:
            errors.append(
                "MONGODB_URI is required."
            )

        if not mongodb_database:
            errors.append(
                "MONGODB_DATABASE is required."
            )

        # ==================================================
        # EMAIL
        # ==================================================

        email_mode = getattr(
            settings,
            "EMAIL_MODE",
            None,
        )

        if email_mode not in {
            "development",
            "production",
        }:
            errors.append(
                "Invalid EMAIL_MODE."
            )

        if is_production:

            if (
                email_mode
                !=
                "production"
            ):
                errors.append(
                    "EMAIL_MODE must be production "
                    "when APP_ENV=production."
                )

            smtp_required = [
                "SMTP_HOST",
                "SMTP_PORT",
                "SMTP_USERNAME",
                "SMTP_PASSWORD",
                "DEFAULT_FROM_EMAIL",
            ]

            for name in smtp_required:

                if not os.getenv(
                    name
                ):
                    errors.append(
                        f"{name} is required "
                        "in production."
                    )

        # ==================================================
        # HTTPS SECURITY
        # ==================================================

        if is_production:

            if not getattr(
                settings,
                "SECURE_SSL_REDIRECT",
                False,
            ):
                errors.append(
                    "SECURE_SSL_REDIRECT must be True "
                    "in production."
                )

            if not getattr(
                settings,
                "SESSION_COOKIE_SECURE",
                False,
            ):
                errors.append(
                    "SESSION_COOKIE_SECURE must be True "
                    "in production."
                )

            if not getattr(
                settings,
                "CSRF_COOKIE_SECURE",
                False,
            ):
                errors.append(
                    "CSRF_COOKIE_SECURE must be True "
                    "in production."
                )

        # ==================================================
        # BASE SECURITY
        # ==================================================

        if not getattr(
            settings,
            "SECURE_CONTENT_TYPE_NOSNIFF",
            False,
        ):
            errors.append(
                "SECURE_CONTENT_TYPE_NOSNIFF "
                "must be enabled."
            )

        if (
            getattr(
                settings,
                "X_FRAME_OPTIONS",
                None,
            )
            !=
            "DENY"
        ):
            errors.append(
                "X_FRAME_OPTIONS must be DENY."
            )

        # ==================================================
        # RESULT
        # ==================================================

        return {
            "valid":
                len(
                    errors
                )
                ==
                0,

            "errors":
                errors,

            "environment":
                app_env,

            "production":
                is_production,
        }