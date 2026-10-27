from math import ceil


class APIPaginationError(
    ValueError
):

    def __init__(
        self,
        *,
        message="Invalid pagination.",
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


class APIPaginationService:

    DEFAULT_PAGE = 1
    DEFAULT_PAGE_SIZE = 25
    MAX_PAGE_SIZE = 100

    @staticmethod
    def _parse_positive_integer(
        value,
        *,
        field_name,
        default,
        maximum=None,
    ):
        # ==================================================
        # DEFAULT
        # ==================================================

        if value is None:

            return default

        value = str(
            value
        ).strip()

        if not value:

            return default

        # ==================================================
        # INTEGER FORMAT
        # ==================================================

        try:

            parsed_value = int(
                value
            )

        except (
            TypeError,
            ValueError,
        ):

            raise APIPaginationError(
                details={
                    field_name: [
                        (
                            f"{field_name} must "
                            "be an integer."
                        )
                    ],
                },
            )

        # Prevent values such as 1.0 from
        # being accepted as an integer.

        if str(
            parsed_value
        ) != value:

            raise APIPaginationError(
                details={
                    field_name: [
                        (
                            f"{field_name} must "
                            "be an integer."
                        )
                    ],
                },
            )

        # ==================================================
        # POSITIVE VALUE
        # ==================================================

        if parsed_value < 1:

            raise APIPaginationError(
                details={
                    field_name: [
                        (
                            f"{field_name} must "
                            "be greater than zero."
                        )
                    ],
                },
            )

        # ==================================================
        # MAXIMUM
        # ==================================================

        if (
            maximum is not None
            and
            parsed_value > maximum
        ):

            raise APIPaginationError(
                details={
                    field_name: [
                        (
                            f"{field_name} cannot "
                            f"exceed {maximum}."
                        )
                    ],
                },
            )

        return parsed_value

    @staticmethod
    def parse(
        request,
        *,
        default_page_size=None,
        maximum_page_size=None,
    ):
        if default_page_size is None:

            default_page_size = (
                APIPaginationService
                .DEFAULT_PAGE_SIZE
            )

        if maximum_page_size is None:

            maximum_page_size = (
                APIPaginationService
                .MAX_PAGE_SIZE
            )

        page = (
            APIPaginationService
            ._parse_positive_integer(
                request.GET.get(
                    "page"
                ),
                field_name="page",
                default=(
                    APIPaginationService
                    .DEFAULT_PAGE
                ),
            )
        )

        page_size = (
            APIPaginationService
            ._parse_positive_integer(
                request.GET.get(
                    "page_size"
                ),
                field_name="page_size",
                default=default_page_size,
                maximum=maximum_page_size,
            )
        )

        return {
            "page":
                page,

            "page_size":
                page_size,

            "offset":
                (
                    page
                    -
                    1
                )
                *
                page_size,
        }

    @staticmethod
    def paginate_queryset(
        queryset,
        request,
        *,
        default_page_size=None,
        maximum_page_size=None,
    ):
        pagination = (
            APIPaginationService
            .parse(
                request,
                default_page_size=(
                    default_page_size
                ),
                maximum_page_size=(
                    maximum_page_size
                ),
            )
        )

        page = pagination[
            "page"
        ]

        page_size = pagination[
            "page_size"
        ]

        offset = pagination[
            "offset"
        ]

        # ==================================================
        # TOTAL
        # ==================================================

        total_items = queryset.count()

        total_pages = (
            ceil(
                total_items
                /
                page_size
            )
            if total_items
            else 0
        )

        # ==================================================
        # PAGE ITEMS
        # ==================================================

        items = list(
            queryset
            .skip(
                offset
            )
            .limit(
                page_size
            )
        )

        # ==================================================
        # NAVIGATION
        # ==================================================

        has_previous = (
            total_items > 0
            and
            page > 1
            and
            page <= (
                total_pages
                +
                1
            )
        )

        has_next = (
            total_items > 0
            and
            page < total_pages
        )

        return {
            "items":
                items,

            "pagination": {
                "page":
                    page,

                "page_size":
                    page_size,

                "returned_items":
                    len(
                        items
                    ),

                "total_items":
                    total_items,

                "total_pages":
                    total_pages,

                "has_previous":
                    has_previous,

                "has_next":
                    has_next,

                "previous_page": (
                    page
                    -
                    1
                    if has_previous
                    else None
                ),

                "next_page": (
                    page
                    +
                    1
                    if has_next
                    else None
                ),
            },
        }