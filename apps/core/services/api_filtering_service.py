from bson import (
    ObjectId,
)
from bson.errors import (
    InvalidId,
)
class APIFilteringError(
    ValueError
):

    def __init__(
        self,
        *,
        message="Invalid filters.",
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


class APIFilteringService:

    ALLOWED_LOOKUPS = {
        "exact",
        "iexact",
        "contains",
        "icontains",
        "in",
        "gt",
        "gte",
        "lt",
        "lte",
        "ne",
    }

    DEFAULT_IGNORED_PARAMETERS = {
        "page",
        "page_size",
        "sort",
        "search",
    }

    @staticmethod
    def _parse_string(
        value,
        *,
        parameter_name,
    ):
        value = str(
            value
            or
            ""
        ).strip()

        if not value:

            raise APIFilteringError(
                details={
                    parameter_name: [
                        (
                            f"{parameter_name} "
                            "cannot be empty."
                        )
                    ],
                },
            )

        return value

    @staticmethod
    def _parse_boolean(
        value,
        *,
        parameter_name,
    ):
        normalized_value = (
            str(
                value
                or
                ""
            )
            .strip()
            .lower()
        )

        if normalized_value == "true":
            return True

        if normalized_value == "false":
            return False

        raise APIFilteringError(
            details={
                parameter_name: [
                    (
                        f"{parameter_name} must "
                        "be true or false."
                    )
                ],
            },
        )

    @staticmethod
    def _parse_integer(
        value,
        *,
        parameter_name,
    ):
        value = str(
            value
            or
            ""
        ).strip()

        try:

            parsed_value = int(
                value
            )

        except (
            TypeError,
            ValueError,
        ):

            raise APIFilteringError(
                details={
                    parameter_name: [
                        (
                            f"{parameter_name} "
                            "must be an integer."
                        )
                    ],
                },
            )

        if str(
            parsed_value
        ) != value:

            raise APIFilteringError(
                details={
                    parameter_name: [
                        (
                            f"{parameter_name} "
                            "must be an integer."
                        )
                    ],
                },
            )

        return parsed_value

    @staticmethod
    def _parse_object_id(
        value,
        *,
        parameter_name,
    ):
        value = str(
            value
            or
            ""
        ).strip()

        try:

            return ObjectId(
                value
            )

        except (
            InvalidId,
            TypeError,
            ValueError,
        ) as exc:

            raise APIFilteringError(
                details={
                    parameter_name: [
                        (
                            f"{parameter_name} must "
                            "be a valid identifier."
                        )
                    ],
                },
            ) from exc
    @staticmethod
    def _parse_csv(
        value,
        *,
        parameter_name,
    ):
        raw_values = str(
            value
            or
            ""
        ).split(
            ","
        )

        parsed_values = []

        for raw_value in raw_values:

            parsed_value = (
                str(
                    raw_value
                )
                .strip()
            )

            if parsed_value:

                parsed_values.append(
                    parsed_value
                )

        if not parsed_values:

            raise APIFilteringError(
                details={
                    parameter_name: [
                        (
                            f"{parameter_name} must "
                            "contain at least one value."
                        )
                    ],
                },
            )

        return list(
            dict.fromkeys(
                parsed_values
            )
        )

    @staticmethod
    def _parse_value(
        value,
        *,
        parameter_name,
        parser,
    ):
        if callable(
            parser
        ):

            try:

                return parser(
                    value
                )

            except APIFilteringError:
                raise

            except Exception:

                raise APIFilteringError(
                    details={
                        parameter_name: [
                            (
                                f"{parameter_name} "
                                "is invalid."
                            )
                        ],
                    },
                )

        if parser == "string":

            return (
                APIFilteringService
                ._parse_string(
                    value,
                    parameter_name=(
                        parameter_name
                    ),
                )
            )

        if parser == "boolean":

            return (
                APIFilteringService
                ._parse_boolean(
                    value,
                    parameter_name=(
                        parameter_name
                    ),
                )
            )

        if parser == "integer":

            return (
                APIFilteringService
                ._parse_integer(
                    value,
                    parameter_name=(
                        parameter_name
                    ),
                )
            )

        if parser == "object_id":

            return (
                APIFilteringService
                ._parse_object_id(
                    value,
                    parameter_name=(
                        parameter_name
                    ),
                )
            )
        if parser == "csv":

            return (
                APIFilteringService
                ._parse_csv(
                    value,
                    parameter_name=(
                        parameter_name
                    ),
                )
            )

        raise ValueError(
            (
                "Unsupported internal filter "
                f"parser: {parser}"
            )
        )

    @staticmethod
    def _serialize_applied_value(
        value,
    ):
        if isinstance(
            value,
            ObjectId,
        ):
            return str(
                value
            )

        if isinstance(
            value,
            list,
        ):
            return [
                (
                    APIFilteringService
                    ._serialize_applied_value(
                        item
                    )
                )
                for item in value
            ]

        return value

    @staticmethod
    def apply(
        queryset,
        request,
        *,
        allowed_filters,
        ignored_parameters=None,
    ):
        if ignored_parameters is None:

            ignored_parameters = set(
                APIFilteringService
                .DEFAULT_IGNORED_PARAMETERS
            )

        else:

            ignored_parameters = set(
                ignored_parameters
            )

        supplied_parameters = set(
            request.GET.keys()
        )

        allowed_parameters = set(
            allowed_filters.keys()
        )

        unknown_parameters = (
            supplied_parameters
            -
            allowed_parameters
            -
            ignored_parameters
        )

        if unknown_parameters:

            details = {}

            for parameter_name in sorted(
                unknown_parameters
            ):

                details[
                    parameter_name
                ] = [
                    "Unknown filter parameter."
                ]

            raise APIFilteringError(
                message=(
                    "Unsupported filter "
                    "parameters were supplied."
                ),
                details=details,
            )

        mongo_filters = {}

        applied_filters = {}

        for (
            parameter_name,
            configuration,
        ) in allowed_filters.items():

            if (
                parameter_name
                not in request.GET
            ):

                continue

            field_name = configuration.get(
                "field"
            )

            lookup = configuration.get(
                "lookup",
                "exact",
            )

            parser = configuration.get(
                "parser",
                "string",
            )

            if not field_name:

                raise ValueError(
                    (
                        "Filter configuration "
                        f"for {parameter_name} "
                        "requires a field."
                    )
                )

            if (
                lookup
                not in
                APIFilteringService
                .ALLOWED_LOOKUPS
            ):

                raise ValueError(
                    (
                        "Unsupported internal "
                        f"lookup: {lookup}"
                    )
                )

            parsed_value = (
                APIFilteringService
                ._parse_value(
                    request.GET.get(
                        parameter_name
                    ),
                    parameter_name=(
                        parameter_name
                    ),
                    parser=parser,
                )
            )

            allowed_values = (
                configuration.get(
                    "allowed_values"
                )
            )

            if allowed_values is not None:

                allowed_values = set(
                    allowed_values
                )

                values_to_validate = (
                    parsed_value
                    if isinstance(
                        parsed_value,
                        list,
                    )
                    else [
                        parsed_value
                    ]
                )

                invalid_values = [
                    value
                    for value
                    in values_to_validate
                    if value
                    not in allowed_values
                ]

                if invalid_values:

                    raise APIFilteringError(
                        details={
                            parameter_name: [
                                (
                                    "Unsupported value: "
                                    +
                                    ", ".join(
                                        str(
                                            value
                                        )
                                        for value
                                        in invalid_values
                                    )
                                )
                            ],
                        },
                    )

            mongo_field = (
                field_name
                if lookup == "exact"
                else (
                    f"{field_name}"
                    f"__"
                    f"{lookup}"
                )
            )

            mongo_filters[
                mongo_field
            ] = parsed_value

            applied_filters[
                parameter_name
            ] = (
                APIFilteringService
                ._serialize_applied_value(
                    parsed_value
                )
            )

        if mongo_filters:

            queryset = queryset.filter(
                **mongo_filters
            )

        return {
            "queryset":
                queryset,

            "applied_filters":
                applied_filters,
        }