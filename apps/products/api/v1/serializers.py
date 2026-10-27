from apps.core.services.api_serialization_service import (
    APISerializationService,
)


class CategoryAPISerializer:

    @staticmethod
    def serialize_summary(
        category,
    ):
        if not category:
            return None

        return {
            "id": (
                APISerializationService
                .serialize_identifier(
                    category.id
                )
            ),
            "name":
                category.name,
            "description":
                (
                    category.description
                    or
                    None
                ),
            "is_active":
                bool(
                    category.is_active
                ),
        }

    @staticmethod
    def serialize_detail(
        category,
    ):
        if not category:
            return None

        summary = (
            CategoryAPISerializer
            .serialize_summary(
                category
            )
        )

        return {
            **summary,
            "created_at": (
                APISerializationService
                .serialize_datetime(
                    category.created_at
                )
            ),
            "updated_at": (
                APISerializationService
                .serialize_datetime(
                    category.updated_at
                )
            ),
        }


class ProductAPISerializer:

    @staticmethod
    def serialize_summary(
        product,
    ):
        if not product:
            return None

        return {
            "id": (
                APISerializationService
                .serialize_identifier(
                    product.id
                )
            ),
            "sku":
                product.sku,
            "name":
                product.name,
            "category": (
                CategoryAPISerializer
                .serialize_summary(
                    product.category
                )
            ),
            "brand":
                (
                    product.brand
                    or
                    None
                ),
            "unit":
                product.unit,
            "cost_price":
                str(
                    product.cost_price
                ),
            "selling_price":
                str(
                    product.selling_price
                ),
            "barcode":
                (
                    product.barcode
                    or
                    None
                ),
            "is_active":
                bool(
                    product.is_active
                ),
        }

    @staticmethod
    def serialize_detail(
        product,
    ):
        if not product:
            return None

        summary = (
            ProductAPISerializer
            .serialize_summary(
                product
            )
        )

        return {
            **summary,
            "description":
                (
                    product.description
                    or
                    None
                ),
            "created_at": (
                APISerializationService
                .serialize_datetime(
                    product.created_at
                )
            ),
            "updated_at": (
                APISerializationService
                .serialize_datetime(
                    product.updated_at
                )
            ),
        }

    @staticmethod
    def serialize_many(
        products,
    ):
        return [
            ProductAPISerializer
            .serialize_summary(
                product
            )
            for product in products
        ]