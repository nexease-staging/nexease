from datetime import (
    date,
    datetime,
    timezone,
)
from decimal import Decimal
from enum import Enum

from mongoengine import Document


class APISerializationError(
    ValueError
):

    pass


class APISerializationService:

    @staticmethod
    def serialize_datetime(
        value,
    ):
        if value is None:
            return None

        if not isinstance(
            value,
            datetime,
        ):

            raise APISerializationError(
                "Expected a datetime value."
            )

        if value.tzinfo is None:

            value = value.replace(
                tzinfo=timezone.utc
            )

        else:

            value = value.astimezone(
                timezone.utc
            )

        return (
            value.isoformat()
            .replace(
                "+00:00",
                "Z",
            )
        )

    @staticmethod
    def serialize_date(
        value,
    ):
        if value is None:
            return None

        if (
            not isinstance(
                value,
                date,
            )
            or
            isinstance(
                value,
                datetime,
            )
        ):

            raise APISerializationError(
                "Expected a date value."
            )

        return value.isoformat()

    @staticmethod
    def serialize_decimal(
        value,
    ):
        if value is None:
            return None

        if not isinstance(
            value,
            Decimal,
        ):

            try:

                value = Decimal(
                    str(
                        value
                    )
                )

            except Exception as exc:

                raise APISerializationError(
                    "Invalid decimal value."
                ) from exc

        return format(
            value,
            "f",
        )

    @staticmethod
    def serialize_identifier(
        value,
    ):
        if value is None:
            return None

        return str(
            value
        )

    @staticmethod
    def serialize_value(
        value,
    ):
        # ==================================================
        # NULL
        # ==================================================

        if value is None:
            return None

        # ==================================================
        # DOCUMENT PROTECTION
        # ==================================================

        if isinstance(
            value,
            Document,
        ):

            raise APISerializationError(
                (
                    "MongoEngine documents require "
                    "an explicit serializer."
                )
            )

        # ==================================================
        # PRIMITIVES
        # ==================================================

        if isinstance(
            value,
            (
                str,
                int,
                float,
                bool,
            ),
        ):

            return value

        # ==================================================
        # DOMAIN TYPES
        # ==================================================

        if isinstance(
            value,
            Decimal,
        ):

            return (
                APISerializationService
                .serialize_decimal(
                    value
                )
            )

        if isinstance(
            value,
            datetime,
        ):

            return (
                APISerializationService
                .serialize_datetime(
                    value
                )
            )

        if isinstance(
            value,
            date,
        ):

            return (
                APISerializationService
                .serialize_date(
                    value
                )
            )

        if isinstance(
            value,
            Enum,
        ):

            return (
                APISerializationService
                .serialize_value(
                    value.value
                )
            )

        # ==================================================
        # COLLECTIONS
        # ==================================================

        if isinstance(
            value,
            dict,
        ):

            return {
                str(
                    key
                ):
                    (
                        APISerializationService
                        .serialize_value(
                            item
                        )
                    )
                for key, item
                in value.items()
            }

        if isinstance(
            value,
            (
                list,
                tuple,
                set,
            ),
        ):

            return [
                (
                    APISerializationService
                    .serialize_value(
                        item
                    )
                )
                for item
                in value
            ]

        # ObjectId and similar identifier values.

        if (
            value.__class__.__name__
            in {
                "ObjectId",
                "UUID",
            }
        ):

            return str(
                value
            )

        raise APISerializationError(
            (
                "Unsupported serialization "
                f"type: "
                f"{value.__class__.__name__}"
            )
        )

    @staticmethod
    def serialize_collection(
        items,
        *,
        serializer,
    ):
        if not callable(
            serializer
        ):

            raise ValueError(
                "serializer must be callable."
            )

        return [
            serializer(
                item
            )
            for item
            in items
        ]