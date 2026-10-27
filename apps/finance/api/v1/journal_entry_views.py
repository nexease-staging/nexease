import json

from apps.authorization.services import (
    AuthorizationService,
)
from apps.core.api.decorators import (
    api_login_required,
    api_rate_limit,
)
from apps.core.services.api_query_pipeline_service import (
    APIQueryPipelineError,
    APIQueryPipelineService,
)
from apps.core.services.api_response_service import (
    APIResponseService,
)
from apps.finance.api.v1.serializers import (
    JournalEntryAPISerializer,
)
from apps.finance.repositories.journal_entry_repository import (
    JournalEntryRepository,
)
from apps.finance.services.journal_entry_api_service import (
    JournalEntryAPIService,
    JournalEntryAPIStateError,
    JournalEntryAPIValidationError,
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
        return (
            json.loads(
                request.body
                or
                b"{}"
            ),
            None,
        )

    except (
        json.JSONDecodeError,
        UnicodeDecodeError,
    ):
        return (
            None,
            APIResponseService
            .validation_error(
                message="Malformed JSON body.",
                details={
                    "body": [
                        (
                            "Request body must "
                            "contain valid JSON."
                        ),
                    ],
                },
                request=request,
            ),
        )


@api_login_required
@api_rate_limit(
    scope="journal_entries.collection",
    limit=120,
    window_seconds=60,
)
def journal_entry_collection_api(
    request,
):
    if request.method == "GET":
        if not (
            AuthorizationService
            .has_permission(
                request.api_user,
                "journal_entries.read",
            )
        ):
            return (
                APIResponseService
                .forbidden(
                    message="Permission denied.",
                    request=request,
                )
            )

        queryset = (
            JournalEntryRepository
            .queryset_for_organization(
                organization=(
                    request.api_organization
                ),
            )
        )

        try:
            pipeline_result = (
                APIQueryPipelineService
                .execute(
                    queryset,
                    request,
                    allowed_filters={
                        "status": {
                            "field":
                                "status",
                            "parser":
                                "string",
                        },
                        "source_type": {
                            "field":
                                "source_type",
                            "parser":
                                "string",
                        },
                        "source_id": {
                            "field":
                                "source_id",
                            "parser":
                                "string",
                        },
                    },
                    search_fields=[
                        "journal_number",
                        "description",
                        "source_type",
                        "source_id",
                    ],
                    allowed_sort_fields={
                        "journal_number":
                            "journal_number",
                        "journal_date":
                            "journal_date",
                        "description":
                            "description",
                        "source_type":
                            "source_type",
                        "status":
                            "status",
                        "total_debit":
                            "total_debit",
                        "total_credit":
                            "total_credit",
                        "created_at":
                            "created_at",
                        "updated_at":
                            "updated_at",
                        "posted_at":
                            "posted_at",
                        "reversed_at":
                            "reversed_at",
                    },
                    default_sort=[
                        "-journal_date",
                        "-created_at",
                    ],
                    stable_sort_field="id",
                    default_page_size=25,
                    maximum_page_size=100,
                )
            )

        except APIQueryPipelineError as exc:
            return (
                APIResponseService
                .validation_error(
                    message=exc.message,
                    details={
                        "component":
                            exc.component,
                        "fields":
                            exc.details,
                    },
                    request=request,
                )
            )

        return (
            APIResponseService
            .success(
                data={
                    "journal_entries": (
                        JournalEntryAPISerializer
                        .serialize_many(
                            pipeline_result[
                                "items"
                            ]
                        )
                    ),
                    "pagination":
                        pipeline_result[
                            "pagination"
                        ],
                    "query":
                        pipeline_result[
                            "query"
                        ],
                },
                request=request,
            )
        )

    if request.method == "POST":
        if not (
            AuthorizationService
            .has_permission(
                request.api_user,
                "journal_entries.create",
            )
        ):
            return (
                APIResponseService
                .forbidden(
                    message="Permission denied.",
                    request=request,
                )
            )

        payload, error_response = (
            _json_body(
                request
            )
        )

        if error_response:
            return error_response

        try:
            journal = (
                JournalEntryAPIService
                .create_journal(
                    user=request.api_user,
                    organization=(
                        request.api_organization
                    ),
                    payload=payload,
                )
            )

        except (
            JournalEntryAPIValidationError
        ) as exc:
            return (
                APIResponseService
                .validation_error(
                    message=exc.message,
                    details=exc.details,
                    request=request,
                )
            )

        except (
            JournalEntryAPIStateError
        ) as exc:
            return (
                APIResponseService
                .unprocessable_entity(
                    message=exc.message,
                    details=exc.details,
                    request=request,
                )
            )

        except PermissionError:
            return (
                APIResponseService
                .forbidden(
                    message="Permission denied.",
                    request=request,
                )
            )

        return (
            APIResponseService
            .success(
                data={
                    "journal_entry": (
                        JournalEntryAPISerializer
                        .serialize_detail(
                            journal
                        )
                    ),
                },
                message=(
                    "Journal entry created "
                    "successfully."
                ),
                status=201,
                request=request,
            )
        )

    return (
        APIResponseService
        .method_not_allowed(
            message=(
                "Use GET to list journal entries "
                "or POST to create one."
            ),
            request=request,
        )
    )


@api_login_required
@api_rate_limit(
    scope="journal_entries.detail",
    limit=120,
    window_seconds=60,
)
def journal_entry_detail_api(
    request,
    journal_id,
):
    if request.method == "GET":
        permission_code = (
            "journal_entries.read"
        )

    elif request.method == "PATCH":
        permission_code = (
            "journal_entries.create"
        )

    else:
        return (
            APIResponseService
            .method_not_allowed(
                message=(
                    "Use GET to retrieve a journal "
                    "entry or PATCH to update its "
                    "draft."
                ),
                request=request,
            )
        )

    if not (
        AuthorizationService
        .has_permission(
            request.api_user,
            permission_code,
        )
    ):
        return (
            APIResponseService
            .forbidden(
                message="Permission denied.",
                request=request,
            )
        )

    if request.method == "GET":
        try:
            journal = (
                JournalEntryAPIService
                .get_journal(
                    organization=(
                        request.api_organization
                    ),
                    journal_id=journal_id,
                )
            )

        except (
            JournalEntryAPIValidationError
        ) as exc:
            return (
                APIResponseService
                .validation_error(
                    message=exc.message,
                    details=exc.details,
                    request=request,
                )
            )

        except LookupError:
            return (
                APIResponseService
                .not_found(
                    message=(
                        "Journal entry not found."
                    ),
                    request=request,
                )
            )

        return (
            APIResponseService
            .success(
                data={
                    "journal_entry": (
                        JournalEntryAPISerializer
                        .serialize_detail(
                            journal
                        )
                    ),
                },
                request=request,
            )
        )

    payload, error_response = (
        _json_body(
            request
        )
    )

    if error_response:
        return error_response

    try:
        journal = (
            JournalEntryAPIService
            .update_journal(
                user=request.api_user,
                organization=(
                    request.api_organization
                ),
                journal_id=journal_id,
                payload=payload,
            )
        )

    except (
        JournalEntryAPIValidationError
    ) as exc:
        return (
            APIResponseService
            .validation_error(
                message=exc.message,
                details=exc.details,
                request=request,
            )
        )

    except LookupError:
        return (
            APIResponseService
            .not_found(
                message="Journal entry not found.",
                request=request,
            )
        )

    except (
        JournalEntryAPIStateError
    ) as exc:
        return (
            APIResponseService
            .unprocessable_entity(
                message=exc.message,
                details=exc.details,
                request=request,
            )
        )

    except PermissionError:
        return (
            APIResponseService
            .forbidden(
                message="Permission denied.",
                request=request,
            )
        )

    return (
        APIResponseService
        .success(
            data={
                "journal_entry": (
                    JournalEntryAPISerializer
                    .serialize_detail(
                        journal
                    )
                ),
            },
            message=(
                "Journal entry updated "
                "successfully."
            ),
            request=request,
        )
    )


@api_login_required
@api_rate_limit(
    scope="journal_entries.post",
    limit=60,
    window_seconds=60,
)
def journal_entry_post_api(
    request,
    journal_id,
):
    if request.method != "POST":
        return (
            APIResponseService
            .method_not_allowed(
                message=(
                    "Use POST to post a "
                    "journal entry."
                ),
                request=request,
            )
        )

    if not (
        AuthorizationService
        .has_permission(
            request.api_user,
            "journal_entries.post",
        )
    ):
        return (
            APIResponseService
            .forbidden(
                message="Permission denied.",
                request=request,
            )
        )

    try:
        journal = (
            JournalEntryAPIService
            .post_journal(
                user=request.api_user,
                organization=(
                    request.api_organization
                ),
                journal_id=journal_id,
            )
        )

    except (
        JournalEntryAPIValidationError
    ) as exc:
        return (
            APIResponseService
            .validation_error(
                message=exc.message,
                details=exc.details,
                request=request,
            )
        )

    except LookupError:
        return (
            APIResponseService
            .not_found(
                message="Journal entry not found.",
                request=request,
            )
        )

    except (
        JournalEntryAPIStateError
    ) as exc:
        return (
            APIResponseService
            .unprocessable_entity(
                message=exc.message,
                details=exc.details,
                request=request,
            )
        )

    except PermissionError:
        return (
            APIResponseService
            .forbidden(
                message="Permission denied.",
                request=request,
            )
        )

    return (
        APIResponseService
        .success(
            data={
                "journal_entry": (
                    JournalEntryAPISerializer
                    .serialize_detail(
                        journal
                    )
                ),
            },
            message=(
                "Journal entry posted "
                "successfully."
            ),
            request=request,
        )
    )


@api_login_required
@api_rate_limit(
    scope="journal_entries.reverse",
    limit=30,
    window_seconds=60,
)
def journal_entry_reverse_api(
    request,
    journal_id,
):
    if request.method != "POST":
        return (
            APIResponseService
            .method_not_allowed(
                message=(
                    "Use POST to reverse a "
                    "journal entry."
                ),
                request=request,
            )
        )

    if not (
        AuthorizationService
        .has_permission(
            request.api_user,
            "journal_entries.reverse",
        )
    ):
        return (
            APIResponseService
            .forbidden(
                message="Permission denied.",
                request=request,
            )
        )

    payload, error_response = (
        _json_body(
            request
        )
    )

    if error_response:
        return error_response

    try:
        result = (
            JournalEntryAPIService
            .reverse_journal(
                user=request.api_user,
                organization=(
                    request.api_organization
                ),
                journal_id=journal_id,
                payload=payload,
            )
        )

    except (
        JournalEntryAPIValidationError
    ) as exc:
        return (
            APIResponseService
            .validation_error(
                message=exc.message,
                details=exc.details,
                request=request,
            )
        )

    except LookupError:
        return (
            APIResponseService
            .not_found(
                message="Journal entry not found.",
                request=request,
            )
        )

    except (
        JournalEntryAPIStateError
    ) as exc:
        return (
            APIResponseService
            .unprocessable_entity(
                message=exc.message,
                details=exc.details,
                request=request,
            )
        )

    except PermissionError:
        return (
            APIResponseService
            .forbidden(
                message="Permission denied.",
                request=request,
            )
        )

    return (
        APIResponseService
        .success(
            data={
                "original": (
                    JournalEntryAPISerializer
                    .serialize_detail(
                        result[
                            "original"
                        ]
                    )
                ),
                "reversal": (
                    JournalEntryAPISerializer
                    .serialize_detail(
                        result[
                            "reversal"
                        ]
                    )
                ),
            },
            message=(
                "Journal entry reversed "
                "successfully."
            ),
            status=201,
            request=request,
        )
    )