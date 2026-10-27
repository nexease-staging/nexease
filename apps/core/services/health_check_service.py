from datetime import datetime

from mongoengine.connection import (
    get_connection,
)
from pymongo import timeout
from apps.core.services.mongodb_error_logging_service import (
    MongoDBErrorLoggingService,
)

from apps.core.services.shutdown_state_service import (
    ShutdownStateService,
)

class HealthCheckService:

    MONGODB_HEALTH_TIMEOUT_SECONDS = 3

    @staticmethod
    def check_application():
        return {
            "status":
                "ok",

            "service":
                "django-ims",

            "timestamp":
                datetime.utcnow()
                .isoformat(),
        }

    @staticmethod
    def check_mongodb():
        try:

            client = (
                get_connection(
                    "default"
                )
            )

            with timeout(
                HealthCheckService
                .MONGODB_HEALTH_TIMEOUT_SECONDS
            ):

                result = (
                    client.admin.command(
                        "ping"
                    )
                )

            healthy = (
                result.get(
                    "ok"
                )
                ==
                1
            )

            return {
                "status": (
                    "ok"
                    if healthy
                    else "error"
                ),

                "healthy":
                    healthy,
            }

        except Exception as exc:

            if (
                MongoDBErrorLoggingService
                .is_mongodb_error(
                    exc
                )
            ):

                MongoDBErrorLoggingService.log_exception(
                    exception=exc,
                    module="health",
                    action="mongodb_health_check",
                )

            return {
                "status":
                    "error",

                "healthy":
                    False,

                "error_type":
                    type(
                        exc
                    )
                    .__name__,
            }

    @staticmethod
    def check():
        application = (
            HealthCheckService
            .check_application()
        )

        mongodb = (
            HealthCheckService
            .check_mongodb()
        )

        healthy = (
            application[
                "status"
            ]
            ==
            "ok"
            and
            mongodb[
                "healthy"
            ]
            is True
        )

        return {
            "status": (
                "ok"
                if healthy
                else "degraded"
            ),

            "healthy":
                healthy,

            "application":
                application,

            "mongodb":
                mongodb,
        }

    @staticmethod
    def check_liveness():
        return {
            "status":
                "ok",

            "healthy":
                True,

            "service":
                "django-ims",
        }

    @staticmethod
    def check_readiness():
        # ==================================================
        # SHUTDOWN STATE
        # ==================================================

        if (
            ShutdownStateService
            .is_shutting_down()
        ):

            return {
                "status":
                    "not_ready",

                "ready":
                    False,

                "reason":
                    "shutting_down",

                "mongodb": {
                    "status":
                        "not_checked",

                    "healthy":
                        False,
                },
            }

        # ==================================================
        # MONGODB
        # ==================================================

        mongodb = (
            HealthCheckService
            .check_mongodb()
        )

        ready = (
            mongodb.get(
                "healthy"
            )
            is True
        )

        return {
            "status": (
                "ready"
                if ready
                else "not_ready"
            ),

            "ready":
                ready,

            "mongodb": {
                "status":
                    mongodb.get(
                        "status"
                    ),

                "healthy":
                    mongodb.get(
                        "healthy"
                    ),
            },
        }