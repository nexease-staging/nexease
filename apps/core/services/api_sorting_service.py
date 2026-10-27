class APISortingError(
    ValueError
):

    def __init__(
        self,
        *,
        message="Invalid sorting.",
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


class APISortingService:

    MAX_SORT_FIELDS = 3

    @staticmethod
    def _parse_sort_tokens(
        raw_sort,
    ):
        raw_sort = str(
            raw_sort
            or
            ""
        ).strip()

        if not raw_sort:

            raise APISortingError(
                details={
                    "sort": [
                        (
                            "sort cannot "
                            "be empty."
                        )
                    ],
                },
            )

        raw_tokens = raw_sort.split(
            ","
        )

        sort_tokens = []

        for raw_token in raw_tokens:

            token = str(
                raw_token
            ).strip()

            if not token:

                raise APISortingError(
                    details={
                        "sort": [
                            (
                                "sort contains "
                                "an empty field."
                            )
                        ],
                    },
                )

            descending = token.startswith(
                "-"
            )

            alias = (
                token[
                    1:
                ]
                if descending
                else token
            )

            alias = alias.strip()

            if not alias:

                raise APISortingError(
                    details={
                        "sort": [
                            (
                                "A sort direction "
                                "must include a field."
                            )
                        ],
                    },
                )

            sort_tokens.append(
                {
                    "alias":
                        alias,

                    "descending":
                        descending,

                    "token":
                        (
                            f"-{alias}"
                            if descending
                            else alias
                        ),
                }
            )

        return sort_tokens

    @staticmethod
    def apply(
        queryset,
        request,
        *,
        allowed_fields,
        default_sort=None,
        stable_field="id",
        maximum_fields=None,
    ):
        if maximum_fields is None:

            maximum_fields = (
                APISortingService
                .MAX_SORT_FIELDS
            )

        # ==================================================
        # REQUESTED OR DEFAULT SORT
        # ==================================================

        raw_sort = request.GET.get(
            "sort"
        )

        using_default = (
            raw_sort is None
        )

        if using_default:

            if default_sort is None:

                default_sort = []

            if isinstance(
                default_sort,
                str,
            ):

                default_sort = [
                    default_sort
                ]

            sort_tokens = []

            for default_token in default_sort:

                parsed_tokens = (
                    APISortingService
                    ._parse_sort_tokens(
                        default_token
                    )
                )

                sort_tokens.extend(
                    parsed_tokens
                )

        else:

            sort_tokens = (
                APISortingService
                ._parse_sort_tokens(
                    raw_sort
                )
            )

        # ==================================================
        # MAXIMUM FIELDS
        # ==================================================

        if (
            len(
                sort_tokens
            )
            >
            maximum_fields
        ):

            raise APISortingError(
                details={
                    "sort": [
                        (
                            "sort cannot contain "
                            f"more than "
                            f"{maximum_fields} fields."
                        )
                    ],
                },
            )

        # ==================================================
        # VALIDATE ALIASES
        # ==================================================

        seen_aliases = set()

        applied_sort = []

        mongo_ordering = []

        for sort_token in sort_tokens:

            alias = sort_token[
                "alias"
            ]

            if alias in seen_aliases:

                raise APISortingError(
                    details={
                        "sort": [
                            (
                                "Duplicate or "
                                "conflicting sort "
                                f"field: {alias}."
                            )
                        ],
                    },
                )

            seen_aliases.add(
                alias
            )

            if alias not in allowed_fields:

                raise APISortingError(
                    details={
                        "sort": [
                            (
                                "Unsupported sort "
                                f"field: {alias}."
                            )
                        ],
                    },
                )

            model_field = allowed_fields[
                alias
            ]

            descending = sort_token[
                "descending"
            ]

            mongo_token = (
                f"-{model_field}"
                if descending
                else model_field
            )

            mongo_ordering.append(
                mongo_token
            )

            applied_sort.append(
                sort_token[
                    "token"
                ]
            )

        # ==================================================
        # STABLE TIE-BREAKER
        # ==================================================

        mapped_fields = {
            token.lstrip(
                "-"
            )
            for token
            in mongo_ordering
        }

        if (
            stable_field
            and
            stable_field
            not in mapped_fields
        ):

            mongo_ordering.append(
                stable_field
            )

        # ==================================================
        # APPLY
        # ==================================================

        if mongo_ordering:

            queryset = queryset.order_by(
                *mongo_ordering
            )

        return {
            "queryset":
                queryset,

            "applied_sort":
                applied_sort,

            "mongo_ordering":
                mongo_ordering,

            "using_default":
                using_default,
        }