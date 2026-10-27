import re

from mongoengine.queryset.visitor import (
    Q,
)


class APISearchError(
    ValueError
):

    def __init__(
        self,
        *,
        message="Invalid search.",
        details=None,
    ):
        super().__init__(
            message
        )

        self.message = message

        self.details = (
            details
            or
            {}
        )


class APISearchService:

    DEFAULT_PARAMETER = "search"
    MIN_LENGTH = 2
    MAX_LENGTH = 100

    @staticmethod
    def _normalize(
        value,
    ):
        value = str(
            value
            or
            ""
        )

        # Collapse repeated whitespace.

        value = " ".join(
            value.split()
        )

        return value.strip()

    @staticmethod
    def apply(
        queryset,
        request,
        *,
        search_fields,
        parameter_name=None,
        minimum_length=None,
        maximum_length=None,
    ):
        if parameter_name is None:

            parameter_name = (
                APISearchService
                .DEFAULT_PARAMETER
            )

        if minimum_length is None:

            minimum_length = (
                APISearchService
                .MIN_LENGTH
            )

        if maximum_length is None:

            maximum_length = (
                APISearchService
                .MAX_LENGTH
            )

        # ==================================================
        # INTERNAL CONFIGURATION
        # ==================================================

        search_fields = [
            str(
                field
            ).strip()
            for field
            in (
                search_fields
                or
                []
            )
            if str(
                field
            ).strip()
        ]

        search_fields = list(
            dict.fromkeys(
                search_fields
            )
        )

        if not search_fields:

            raise ValueError(
                (
                    "At least one internal "
                    "search field is required."
                )
            )

        # ==================================================
        # SEARCH NOT SUPPLIED
        # ==================================================

        if parameter_name not in request.GET:

            return {
                "queryset":
                    queryset,

                "search_term":
                    None,

                "search_fields":
                    search_fields,

                "applied":
                    False,
            }

        # ==================================================
        # NORMALIZE
        # ==================================================

        search_term = (
            APISearchService
            ._normalize(
                request.GET.get(
                    parameter_name
                )
            )
        )

        # ==================================================
        # VALIDATION
        # ==================================================

        if not search_term:

            raise APISearchError(
                details={
                    parameter_name: [
                        (
                            f"{parameter_name} "
                            "cannot be empty."
                        )
                    ],
                },
            )

        if (
            len(
                search_term
            )
            <
            minimum_length
        ):

            raise APISearchError(
                details={
                    parameter_name: [
                        (
                            f"{parameter_name} must "
                            f"contain at least "
                            f"{minimum_length} characters."
                        )
                    ],
                },
            )

        if (
            len(
                search_term
            )
            >
            maximum_length
        ):

            raise APISearchError(
                details={
                    parameter_name: [
                        (
                            f"{parameter_name} cannot "
                            f"exceed "
                            f"{maximum_length} characters."
                        )
                    ],
                },
            )

        if "\x00" in search_term:

            raise APISearchError(
                details={
                    parameter_name: [
                        (
                            f"{parameter_name} contains "
                            "an invalid character."
                        )
                    ],
                },
            )

        # ==================================================
        # SAFE REGEX
        #
        # Escaping ensures values such as:
        # .*
        # $
        # [a-z]
        # are treated as literal text.
        # ==================================================

        safe_pattern = re.escape(
            search_term
        )

        search_query = None

        for field_name in search_fields:

            field_query = Q(
                **{
                    (
                        f"{field_name}"
                        "__iregex"
                    ):
                        safe_pattern,
                }
            )

            if search_query is None:

                search_query = (
                    field_query
                )

            else:

                search_query = (
                    search_query
                    |
                    field_query
                )

        queryset = queryset.filter(
            search_query
        )

        return {
            "queryset":
                queryset,

            "search_term":
                search_term,

            "search_fields":
                search_fields,

            "applied":
                True,
        }