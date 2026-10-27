from apps.core.services.api_filtering_service import (
    APIFilteringError,
    APIFilteringService,
)
from apps.core.services.api_pagination_service import (
    APIPaginationError,
    APIPaginationService,
)
from apps.core.services.api_search_service import (
    APISearchError,
    APISearchService,
)
from apps.core.services.api_sorting_service import (
    APISortingError,
    APISortingService,
)


class APIQueryPipelineError(
    ValueError
):

    def __init__(
        self,
        *,
        component,
        message,
        details=None,
    ):
        super().__init__(
            message
        )

        self.component = component

        self.message = message

        self.details = (
            details
            or
            {}
        )


class APIQueryPipelineService:

    @staticmethod
    def execute(
        queryset,
        request,
        *,
        allowed_filters=None,
        search_fields=None,
        allowed_sort_fields=None,
        default_sort=None,
        stable_sort_field="id",
        default_page_size=None,
        maximum_page_size=None,
    ):
        allowed_filters = (
            allowed_filters
            or
            {}
        )

        search_fields = (
            search_fields
            or
            []
        )

        allowed_sort_fields = (
            allowed_sort_fields
            or
            {}
        )

        # ==================================================
        # FILTERING
        # ==================================================

        try:

            filtering_result = (
                APIFilteringService
                .apply(
                    queryset,
                    request,
                    allowed_filters=(
                        allowed_filters
                    ),
                )
            )

        except APIFilteringError as exc:

            raise APIQueryPipelineError(
                component="filtering",
                message=exc.message,
                details=exc.details,
            ) from exc

        queryset = filtering_result[
            "queryset"
        ]

        # ==================================================
        # SEARCH
        # ==================================================

        if (
            "search"
            in request.GET
            and
            not search_fields
        ):

            raise APIQueryPipelineError(
                component="search",
                message=(
                    "Search is not supported "
                    "for this endpoint."
                ),
                details={
                    "search": [
                        (
                            "Search is not supported "
                            "for this endpoint."
                        )
                    ],
                },
            )

        if search_fields:

            try:

                search_result = (
                    APISearchService
                    .apply(
                        queryset,
                        request,
                        search_fields=(
                            search_fields
                        ),
                    )
                )

            except APISearchError as exc:

                raise APIQueryPipelineError(
                    component="search",
                    message=exc.message,
                    details=exc.details,
                ) from exc

            queryset = search_result[
                "queryset"
            ]

        else:

            search_result = {
                "queryset":
                    queryset,

                "search_term":
                    None,

                "search_fields":
                    [],

                "applied":
                    False,
            }

        # ==================================================
        # SORTING
        # ==================================================

        try:

            sorting_result = (
                APISortingService
                .apply(
                    queryset,
                    request,
                    allowed_fields=(
                        allowed_sort_fields
                    ),
                    default_sort=(
                        default_sort
                    ),
                    stable_field=(
                        stable_sort_field
                    ),
                )
            )

        except APISortingError as exc:

            raise APIQueryPipelineError(
                component="sorting",
                message=exc.message,
                details=exc.details,
            ) from exc

        queryset = sorting_result[
            "queryset"
        ]

        # ==================================================
        # PAGINATION
        # ==================================================

        try:

            pagination_result = (
                APIPaginationService
                .paginate_queryset(
                    queryset,
                    request,
                    default_page_size=(
                        default_page_size
                    ),
                    maximum_page_size=(
                        maximum_page_size
                    ),
                )
            )

        except APIPaginationError as exc:

            raise APIQueryPipelineError(
                component="pagination",
                message=exc.message,
                details=exc.details,
            ) from exc

        # ==================================================
        # RESULT
        # ==================================================

        return {
            "items":
                pagination_result[
                    "items"
                ],

            "pagination":
                pagination_result[
                    "pagination"
                ],

            "query": {
                "filters":
                    filtering_result[
                        "applied_filters"
                    ],

                "search": {
                    "applied":
                        search_result[
                            "applied"
                        ],

                    "term":
                        search_result[
                            "search_term"
                        ],

                    "fields":
                        search_result[
                            "search_fields"
                        ],
                },

                "sorting": {
                    "fields":
                        sorting_result[
                            "applied_sort"
                        ],

                    "using_default":
                        sorting_result[
                            "using_default"
                        ],
                },
            },
        }