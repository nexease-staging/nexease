from datetime import datetime

from mongoengine.errors import (
    NotUniqueError,
    ValidationError,
)

from apps.products.models import (
    Category,
)
from apps.products.repositories.category_repository import (
    CategoryRepository,
)


class CategoryAPIValidationError(Exception):

    def __init__(
        self,
        message,
        *,
        details=None,
    ):
        super().__init__(message)

        self.message = message
        self.details = details or {}


class CategoryAPIService:

    CREATE_FIELDS = {
        "name",
        "description",
    }

    UPDATE_FIELDS = {
        "name",
        "description",
    }

    @staticmethod
    def _normalize_name(
        value,
    ):
        if not isinstance(
            value,
            str,
        ):
            return ""

        return value.strip()

    @staticmethod
    def _normalize_description(
        value,
    ):
        if value is None:
            return ""

        if not isinstance(
            value,
            str,
        ):
            return None

        return value.strip()

    @classmethod
    def _validate_name(
        cls,
        value,
    ):
        name = cls._normalize_name(
            value
        )

        if not name:
            raise CategoryAPIValidationError(
                "Category validation failed.",
                details={
                    "name": [
                        "Category name is required."
                    ],
                },
            )

        if len(name) > 100:
            raise CategoryAPIValidationError(
                "Category validation failed.",
                details={
                    "name": [
                        (
                            "Category name must not "
                            "exceed 100 characters."
                        )
                    ],
                },
            )

        return name

    @classmethod
    def _validate_description(
        cls,
        value,
    ):
        description = (
            cls._normalize_description(
                value
            )
        )

        if description is None:
            raise CategoryAPIValidationError(
                "Category validation failed.",
                details={
                    "description": [
                        (
                            "Description must be "
                            "a string."
                        )
                    ],
                },
            )

        if len(description) > 500:
            raise CategoryAPIValidationError(
                "Category validation failed.",
                details={
                    "description": [
                        (
                            "Description must not "
                            "exceed 500 characters."
                        )
                    ],
                },
            )

        return description

    @staticmethod
    def _validate_payload_object(
        payload,
    ):
        if not isinstance(
            payload,
            dict,
        ):
            raise CategoryAPIValidationError(
                "Category validation failed.",
                details={
                    "payload": [
                        "JSON body must be an object."
                    ],
                },
            )

    @classmethod
    def _validate_allowed_fields(
        cls,
        payload,
        *,
        allowed_fields,
    ):
        unexpected_fields = sorted(
            set(payload.keys())
            -
            allowed_fields
        )

        if unexpected_fields:
            raise CategoryAPIValidationError(
                "Category validation failed.",
                details={
                    "fields": [
                        (
                            "Unsupported field: "
                            f"{field}"
                        )
                        for field
                        in unexpected_fields
                    ],
                },
            )

    @staticmethod
    def _ensure_unique_name(
        *,
        organization,
        name,
        exclude_category_id=None,
    ):
        existing = (
            CategoryRepository
            .get_by_name(
                organization=organization,
                name=name,
            )
        )

        if (
            existing
            and
            (
                exclude_category_id is None
                or
                str(existing.id)
                !=
                str(exclude_category_id)
            )
        ):
            raise CategoryAPIValidationError(
                "Category validation failed.",
                details={
                    "name": [
                        (
                            "A category with this "
                            "name already exists."
                        )
                    ],
                },
            )

    @staticmethod
    def get_category(
        *,
        organization,
        category_id,
    ):
        category = (
            CategoryRepository
            .get_by_id(
                organization=organization,
                category_id=category_id,
            )
        )

        if not category:
            raise LookupError(
                "Category not found."
            )

        return category

    @classmethod
    def create_category(
        cls,
        *,
        organization,
        payload,
    ):
        cls._validate_payload_object(
            payload
        )

        cls._validate_allowed_fields(
            payload,
            allowed_fields=(
                cls.CREATE_FIELDS
            ),
        )

        name = cls._validate_name(
            payload.get("name")
        )

        description = (
            cls._validate_description(
                payload.get(
                    "description",
                    "",
                )
            )
        )

        cls._ensure_unique_name(
            organization=organization,
            name=name,
        )

        now = datetime.utcnow()

        category = Category(
            organization=organization,
            name=name,
            description=description,
            is_active=True,
            created_at=now,
            updated_at=now,
        )

        try:
            category.save(
                force_insert=True
            )

        except NotUniqueError:
            raise CategoryAPIValidationError(
                "Category validation failed.",
                details={
                    "name": [
                        (
                            "A category with this "
                            "name already exists."
                        )
                    ],
                },
            )

        except ValidationError as exc:
            raise CategoryAPIValidationError(
                "Category validation failed.",
                details={
                    "category": [
                        str(exc)
                    ],
                },
            )

        return category

    @classmethod
    def update_category(
        cls,
        *,
        organization,
        category_id,
        payload,
    ):
        cls._validate_payload_object(
            payload
        )

        cls._validate_allowed_fields(
            payload,
            allowed_fields=(
                cls.UPDATE_FIELDS
            ),
        )

        if not payload:
            raise CategoryAPIValidationError(
                "Category validation failed.",
                details={
                    "payload": [
                        (
                            "At least one field "
                            "must be provided."
                        )
                    ],
                },
            )

        category = cls.get_category(
            organization=organization,
            category_id=category_id,
        )

        if "name" in payload:
            name = cls._validate_name(
                payload.get("name")
            )

            cls._ensure_unique_name(
                organization=organization,
                name=name,
                exclude_category_id=(
                    category.id
                ),
            )

            category.name = name

        if "description" in payload:
            category.description = (
                cls._validate_description(
                    payload.get(
                        "description"
                    )
                )
            )

        category.updated_at = (
            datetime.utcnow()
        )

        try:
            category.save()

        except NotUniqueError:
            raise CategoryAPIValidationError(
                "Category validation failed.",
                details={
                    "name": [
                        (
                            "A category with this "
                            "name already exists."
                        )
                    ],
                },
            )

        except ValidationError as exc:
            raise CategoryAPIValidationError(
                "Category validation failed.",
                details={
                    "category": [
                        str(exc)
                    ],
                },
            )

        return category

    @classmethod
    def activate_category(
        cls,
        *,
        organization,
        category_id,
    ):
        category = cls.get_category(
            organization=organization,
            category_id=category_id,
        )

        if category.is_active:
            return category

        category.is_active = True
        category.updated_at = (
            datetime.utcnow()
        )
        category.save()

        return category

    @classmethod
    def deactivate_category(
        cls,
        *,
        organization,
        category_id,
    ):
        category = cls.get_category(
            organization=organization,
            category_id=category_id,
        )

        if not category.is_active:
            return category

        category.is_active = False
        category.updated_at = (
            datetime.utcnow()
        )
        category.save()

        return category