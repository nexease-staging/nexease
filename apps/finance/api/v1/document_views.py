import json
from uuid import uuid4

from uuid import uuid4

from apps.core.services.background_job_service import (
    BackgroundJobService,
)

from apps.finance.api.v1.serializers import (
    DocumentEmailRequestAPISerializer,
)
from django.http import HttpResponse

from apps.authorization.services import (
    AuthorizationService,
)

from apps.core.api.decorators import (
    api_login_required,
    api_rate_limit,
)

from apps.core.services.api_response_service import (
    APIResponseService,
)

from apps.finance.services.document_api_service import (
    DocumentAPIService,
    DocumentAPIValidationError,
)

from apps.finance.services.document_email_config_service import (
    DocumentEmailConfigService,
)


@api_login_required
@api_rate_limit(
    scope="documents.read",
    limit=120,
    window_seconds=60,
)
def document_pdf_api(
    request,
    document_type,
    document_id,
):
    if request.method != "GET":
        return (
            APIResponseService
            .method_not_allowed(
                message=(
                    "Use GET to download the document PDF."
                ),
                request=request,
            )
        )

    user = request.api_user

    organization = getattr(
        user,
        "organization",
        None,
    )

    try:
        normalized_type = (
            DocumentEmailConfigService
            .normalize_document_type(
                document_type
            )
        )

        config = (
            DocumentEmailConfigService
            .get_config(
                normalized_type
            )
        )

        permission_code = (
            config[
                "permission"
            ]
        )

        if not (
            AuthorizationService
            .has_permission(
                user,
                permission_code,
            )
        ):
            return (
                APIResponseService
                .forbidden(
                    message=(
                        "Permission denied: "
                        f"{permission_code}"
                    ),
                    request=request,
                )
            )

        result = (
            DocumentAPIService
            .generate_pdf(
                user=user,
                organization=organization,
                document_type=normalized_type,
                document_id=document_id,
            )
        )

        if result is None:
            return (
                APIResponseService
                .not_found(
                    message="Document not found.",
                    request=request,
                )
            )

        response = HttpResponse(
            result[
                "content"
            ],
            content_type=result[
                "content_type"
            ],
        )

        response[
            "Content-Disposition"
        ] = (
            'attachment; filename="'
            f'{result["filename"]}'
            '"'
        )

        response[
            "Content-Length"
        ] = str(
            result[
                "size"
            ]
        )

        return response

    except DocumentAPIValidationError as exc:
        return (
            APIResponseService
            .validation_error(
                message=str(
                    exc
                ),
                request=request,
            )
        )

    except PermissionError as exc:
        return (
            APIResponseService
            .forbidden(
                message=str(
                    exc
                ),
                request=request,
            )
        )

    except ValueError as exc:
        return (
            APIResponseService
            .validation_error(
                message=str(
                    exc
                ),
                request=request,
            )
        )

    except Exception:
        return (
            APIResponseService
            .internal_error(
                message=(
                    "Document PDF generation failed."
                ),
                request=request,
            )
        )

def _json_body(
    request,
):
    content_type = (
        request.content_type
        or
        ""
    ).lower()

    if (
        "application/json"
        not in content_type
    ):
        return (
            None,
            APIResponseService
            .validation_error(
                message=(
                    "Content-Type must be "
                    "application/json."
                ),
                details={
                    "content_type": [
                        (
                            "Send the request body "
                            "as JSON."
                        ),
                    ],
                },
                request=request,
            ),
        )

    try:
        payload = json.loads(
            request.body.decode(
                "utf-8"
            )
            or
            "{}"
        )

    except (
        UnicodeDecodeError,
        json.JSONDecodeError,
    ):
        return (
            None,
            APIResponseService
            .validation_error(
                message=(
                    "Invalid JSON request body."
                ),
                request=request,
            ),
        )

    return (
        payload,
        None,
    )

@api_login_required
@api_rate_limit(
    scope="documents.email",
    limit=60,
    window_seconds=60,
)
def document_email_api(
    request,
    document_type,
    document_id,
):
    if request.method != "POST":
        return (
            APIResponseService
            .method_not_allowed(
                message=(
                    "Use POST to send the "
                    "document by email."
                ),
                request=request,
            )
        )

    user = request.api_user

    organization = getattr(
        user,
        "organization",
        None,
    )

    payload, error_response = (
        _json_body(
            request
        )
    )

    if error_response:
        return error_response

    try:
        data = (
            DocumentEmailRequestAPISerializer
            .deserialize(
                payload
            )
        )

        normalized_type = (
            DocumentEmailConfigService
            .normalize_document_type(
                document_type
            )
        )

        config = (
            DocumentEmailConfigService
            .get_config(
                normalized_type
            )
        )

        permission_code = (
            config[
                "permission"
            ]
        )

        if not (
            AuthorizationService
            .has_permission(
                user,
                permission_code,
            )
        ):
            return (
                APIResponseService
                .forbidden(
                    message=(
                        "Permission denied: "
                        f"{permission_code}"
                    ),
                    request=request,
                )
            )

        document = (
            DocumentEmailConfigService
            .get_document(
                organization=organization,
                document_type=normalized_type,
                document_id=document_id,
            )
        )

        if document is None:
            return (
                APIResponseService
                .not_found(
                    message=(
                        "Document not found."
                    ),
                    request=request,
                )
            )

        job = (
            BackgroundJobService
            .create_job(
                organization=organization,
                created_by=user,
                job_type="DOCUMENT_EMAIL",

                payload={
                    "document_type":
                        normalized_type,

                    "document_id":
                        str(
                            document_id
                        ),

                    "recipient_email":
                        data[
                            "recipient_email"
                        ],

                    "subject":
                        data[
                            "subject"
                        ],

                    "message":
                        data[
                            "message"
                        ],
                },

                idempotency_key=(
                    "DOCUMENT_EMAIL:"
                    f"{uuid4().hex}"
                ),
            )
        )

        response_data = {
            "job": {
                "id":
                    str(
                        job.id
                    ),

                "job_type":
                    job.job_type,

                "status":
                    job.status,

                "attempts":
                    job.attempts,

                "max_attempts":
                    job.max_attempts,

                "created_at": (
                    job.created_at.isoformat()
                    if job.created_at
                    else None
                ),
            },

            "document_type":
                normalized_type,

            "document_id":
                str(
                    document_id
                ),
        }

        return (
            APIResponseService
            .success(
                data=response_data,
                message=(
                    "Document email queued "
                    "successfully."
                ),
                request=request,
                status=202,
            )
        )

    except DocumentAPIValidationError as exc:
        return (
            APIResponseService
            .validation_error(
                message=str(
                    exc
                ),
                request=request,
            )
        )

    except PermissionError as exc:
        return (
            APIResponseService
            .forbidden(
                message=str(
                    exc
                ),
                request=request,
            )
        )

    except ValueError as exc:
        return (
            APIResponseService
            .validation_error(
                message=str(
                    exc
                ),
                request=request,
            )
        )

    except Exception:
        return (
            APIResponseService
            .internal_error(
                message=(
                    "Document email queueing failed."
                ),
                request=request,
            )
        )