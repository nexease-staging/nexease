from pymongo.errors import (
    AutoReconnect,
    ConnectionFailure,
    NetworkTimeout,
    OperationFailure,
    PyMongoError,
    ServerSelectionTimeoutError,
)

from apps.core.services.application_logging_service import (
    ApplicationLoggingService,
)


class MongoDBErrorLoggingService:

    SAFE_ERROR_TYPES = (
        AutoReconnect,
        ConnectionFailure,
        NetworkTimeout,
        OperationFailure,
        ServerSelectionTimeoutError,
        PyMongoError,
    )

    @staticmethod
    def log_exception(
        *,
        exception,
        request=None,
        module="database",
        action="mongodb_operation",
        user=None,
        organization=None,
        extra_context=None,
    ):
        if exception is None:
            return None

        request_id = (
            getattr(
                request,
                "request_id",
                None,
            )
            if request
            else None
        )

        if user is None and request is not None:

            candidate_user = getattr(
                request,
                "user",
                None,
            )

            if (
                candidate_user is not None
                and
                getattr(
                    candidate_user,
                    "is_authenticated",
                    False,
                )
            ):
                user = candidate_user

        if (
            organization is None
            and
            user is not None
        ):
            organization = getattr(
                user,
                "organization",
                None,
            )

        error_type = (
            type(
                exception
            )
            .__name__
        )

        context = {}

        if extra_context:

            context.update(
                extra_context
            )

        return ApplicationLoggingService.log(
            level="ERROR",
            message="MongoDB operation failed.",
            module=module,
            action=action,
            status="failed",
            user=user,
            organization=organization,
            request_id=request_id,
            error_type=error_type,
            database="mongodb",
            **context,
        )

    @staticmethod
    def is_mongodb_error(
        exception,
    ):
        return isinstance(
            exception,
            MongoDBErrorLoggingService
            .SAFE_ERROR_TYPES,
        )