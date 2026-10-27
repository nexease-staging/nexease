from django.apps import AppConfig

from apps.core.services.environment_validation_service import (
    EnvironmentValidationService,
)


class CoreConfig(AppConfig):

    default_auto_field = (
        "django.db.models.BigAutoField"
    )

    name = "apps.core"

    verbose_name = "Core"

    def ready(
        self,
    ):
        # ==================================================
        # ENVIRONMENT VALIDATION
        # ==================================================

        result = (
            EnvironmentValidationService
            .validate()
        )

        if not result[
            "valid"
        ]:

            errors = (
                result[
                    "errors"
                ]
            )

            formatted_errors = (
                "\n".join(
                    f"- {error}"
                    for error
                    in errors
                )
            )

            raise RuntimeError(
                "\n"
                "Environment validation failed:\n"
                f"{formatted_errors}"
            )

        # ==================================================
        # GRACEFUL SHUTDOWN SIGNAL
        # ==================================================

        from django.conf import settings

        from apps.core.services.shutdown_signal_service import (
            ShutdownSignalService,
        )

        if getattr(
            settings,
            "IS_PRODUCTION",
            False,
        ):

            ShutdownSignalService.register()