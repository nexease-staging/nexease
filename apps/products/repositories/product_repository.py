from mongoengine.errors import (
    ValidationError,
)
from mongoengine.queryset.visitor import (
    Q,
)

from apps.products.models import (
    Product,
)


class ProductRepository:

    @staticmethod
    def queryset_for_organization(
        *,
        organization,
    ):
        return Product.objects(
            organization=organization,
        )

    @staticmethod
    def get_by_id(
        *,
        organization,
        product_id,
    ):
        try:

            return (
                ProductRepository
                .queryset_for_organization(
                    organization=organization,
                )
                .filter(
                    id=product_id,
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
    def get_by_sku(
        *,
        organization,
        sku,
    ):
        return (
            ProductRepository
            .queryset_for_organization(
                organization=organization,
            )
            .filter(
                sku=sku,
            )
            .first()
        )

    @staticmethod
    def sku_exists(
        *,
        organization,
        sku,
        exclude_product_id=None,
    ):
        queryset = (
            ProductRepository
            .queryset_for_organization(
                organization=organization,
            )
            .filter(
                sku=sku,
            )
        )

        if exclude_product_id:

            try:

                queryset = queryset.filter(
                    id__ne=exclude_product_id,
                )

            except (
                ValidationError,
                TypeError,
                ValueError,
            ):

                return False

        return queryset.first() is not None

    @staticmethod
    def list_by_organization(
        *,
        organization,
    ):
        return (
            ProductRepository
            .queryset_for_organization(
                organization=organization,
            )
            .order_by(
                "-created_at",
                "-id",
            )
        )

    @staticmethod
    def list_active(
        *,
        organization,
    ):
        return (
            ProductRepository
            .queryset_for_organization(
                organization=organization,
            )
            .filter(
                is_active=True,
            )
            .order_by(
                "-created_at",
                "-id",
            )
        )

    @staticmethod
    def search_by_name(
        *,
        organization,
        search_term,
    ):
        return (
            ProductRepository
            .queryset_for_organization(
                organization=organization,
            )
            .filter(
                name__icontains=search_term,
            )
            .order_by(
                "-created_at",
                "-id",
            )
        )

    @staticmethod
    def search(
        *,
        organization,
        search_term,
    ):
        search_query = (
            Q(
                sku__icontains=search_term
            )
            |
            Q(
                name__icontains=search_term
            )
            |
            Q(
                brand__icontains=search_term
            )
            |
            Q(
                barcode__icontains=search_term
            )
        )

        return (
            ProductRepository
            .queryset_for_organization(
                organization=organization,
            )
            .filter(
                search_query
            )
            .order_by(
                "-created_at",
                "-id",
            )
        )