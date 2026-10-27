from mongoengine.errors import (
    ValidationError,
)

from apps.products.models import (
    Category,
)


class CategoryRepository:

    @staticmethod
    def list_by_organization(
        *,
        organization,
    ):
        return (
            Category.objects(
                organization=organization,
            )
            .order_by(
                "name",
                "id",
            )
        )

    @staticmethod
    def list_active(
        *,
        organization,
    ):
        return (
            Category.objects(
                organization=organization,
                is_active=True,
            )
            .order_by(
                "name",
                "id",
            )
        )

    @staticmethod
    def get_by_id(
        *,
        organization,
        category_id,
    ):
        try:

            return (
                Category.objects(
                    organization=organization,
                    id=category_id,
                )
                .first()
            )

        except (
            ValidationError,
            TypeError,
            ValueError,
        ):

            return None

    @staticmethod
    def get_active_by_id(
        *,
        organization,
        category_id,
    ):
        try:

            return (
                Category.objects(
                    organization=organization,
                    id=category_id,
                    is_active=True,
                )
                .first()
            )

        except (
            ValidationError,
            TypeError,
            ValueError,
        ):

            return None

    @staticmethod
    def get_by_name(
        *,
        organization,
        name,
    ):
        return (
            Category.objects(
                organization=organization,
                name=name,
            )
            .first()
        )

    @staticmethod
    def get_active_by_name(
        *,
        organization,
        name,
    ):
        return (
            Category.objects(
                organization=organization,
                name=name,
                is_active=True,
            )
            .first()
        )
