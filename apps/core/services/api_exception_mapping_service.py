import json

from django.core.exceptions import (
    PermissionDenied,
    ValidationError as DjangoValidationError,
)
from django.http import Http404

from mongoengine.errors import (
    NotUniqueError,
    ValidationError as MongoValidationError,
)
from pymongo.errors import (
    DuplicateKeyError,
)

from apps.core.api_exceptions import (
    APIException,
)
from apps.core.services.api_filtering_service import (
    APIFilteringError,
)
from apps.core.services.api_pagination_service import (
    APIPaginationError,
)
from apps.core.services.api_query_pipeline_service import (
    APIQueryPipelineError,
)
from apps.core.services.api_rate_limit_service import (
    APIRateLimitUnavailable,
)
from apps.core.services.api_response_service import (
    APIResponseService,
)
from apps.core.services.api_search_service import (
    APISearchError,
)
from apps.core.services.api_sorting_service import (
    APISortingError,
)
from apps.core.services.mongodb_error_logging_service import (
    MongoDBErrorLoggingService,
)


class APIExceptionMappingService:

    @staticmethod
    def _django_validation_details(
        exception,
    ):
        if hasattr(
            exception,
            "message_dict",
        ):

            return {
                str(
                    field
                ):
                    [
                        str(
                            message
                        )
                        for message
                        in messages
                    ]
                for field, messages
                in exception.message_dict.items()
            }

        if hasattr(
            exception,
            "messages",
        ):

            return {
                "non_field_errors": [
                    str(
                        message
                    )
                    for message
                    in exception.messages
                ],
            }

        return None

    @staticmethod
    def _mongo_validation_details(
        exception,
    ):
        try:

            error_data = (
                exception.to_dict()
            )

        except Exception:

            error_data = None

        if not error_data:
            return None

        return {
            "fields":
                error_data,
        }

    @staticmethod
    def map(
        exception,
        *,
        request,
    ):
        # ==================================================
        # EXPLICIT API EXCEPTIONS
        # ==================================================

        if isinstance(
            exception,
            APIException,
        ):

            return (
                APIResponseService
                .error(
                    code=exception.code,
                    message=exception.message,
                    status=exception.status,
                    details=exception.details,
                    request=request,
                )
            )

        # ==================================================
        # JSON
        # ==================================================

        if isinstance(
            exception,
            (
                json.JSONDecodeError,
                UnicodeDecodeError,
            ),
        ):

            return (
                APIResponseService
                .bad_request(
                    message="Invalid JSON body.",
                    request=request,
                )
            )

        # ==================================================
        # QUERY PIPELINE
        # ==================================================

        if isinstance(
            exception,
            APIQueryPipelineError,
        ):

            return (
                APIResponseService
                .validation_error(
                    message=exception.message,
                    details={
                        "component":
                            exception.component,

                        "fields":
                            exception.details,
                    },
                    request=request,
                )
            )

        if isinstance(
            exception,
            (
                APIFilteringError,
                APIPaginationError,
                APISearchError,
                APISortingError,
            ),
        ):

            return (
                APIResponseService
                .validation_error(
                    message=exception.message,
                    details=exception.details,
                    request=request,
                )
            )

        # ==================================================
        # DJANGO VALIDATION
        # ==================================================

        if isinstance(
            exception,
            DjangoValidationError,
        ):

            return (
                APIResponseService
                .validation_error(
                    message="Validation failed.",
                    details=(
                        APIExceptionMappingService
                        ._django_validation_details(
                            exception
                        )
                    ),
                    request=request,
                )
            )

        # ==================================================
        # MONGOENGINE VALIDATION
        # ==================================================

        if isinstance(
            exception,
            MongoValidationError,
        ):

            return (
                APIResponseService
                .validation_error(
                    message="Validation failed.",
                    details=(
                        APIExceptionMappingService
                        ._mongo_validation_details(
                            exception
                        )
                    ),
                    request=request,
                )
            )

        # ==================================================
        # AUTHORIZATION
        # ==================================================

        if isinstance(
            exception,
            PermissionDenied,
        ):

            return (
                APIResponseService
                .forbidden(
                    message="Permission denied.",
                    request=request,
                )
            )

        # ==================================================
        # NOT FOUND
        # ==================================================

        if isinstance(
            exception,
            Http404,
        ):

            return (
                APIResponseService
                .not_found(
                    message="Resource not found.",
                    request=request,
                )
            )

        # ==================================================
        # CONFLICT
        # ==================================================

        if isinstance(
            exception,
            (
                NotUniqueError,
                DuplicateKeyError,
            ),
        ):

            return (
                APIResponseService
                .conflict(
                    message=(
                        "A resource with the same "
                        "unique value already exists."
                    ),
                    request=request,
                )
            )

        # ==================================================
        # DATABASE / RATE-LIMIT STORAGE
        # ==================================================

        if (
            MongoDBErrorLoggingService
            .is_mongodb_error(
                exception
            )
            or
            isinstance(
                exception,
                APIRateLimitUnavailable,
            )
        ):

            return (
                APIResponseService
                .service_unavailable(
                    message=(
                        "A required backend service "
                        "is temporarily unavailable."
                    ),
                    request=request,
                )
            )

        # No known mapping.

        return None