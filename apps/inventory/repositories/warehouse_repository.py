from datetime import datetime

from mongoengine.errors import (
    ValidationError,
)

from apps.inventory.models import (
    Warehouse,
)


class WarehouseRepository:

    @staticmethod
    def queryset_for_organization(
        *,
        organization,
    ):
        return Warehouse.objects(
            organization=organization,
        )

    @staticmethod
    def get_by_id(
        *,
        organization,
        warehouse_id,
    ):
        try:

            return (
                WarehouseRepository
                .queryset_for_organization(
                    organization=organization,
                )
                .filter(
                    id=warehouse_id,
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
    def get_by_code(
        *,
        organization,
        code,
    ):
        return (
            WarehouseRepository
            .queryset_for_organization(
                organization=organization,
            )
            .filter(
                code=code,
            )
            .first()
        )

    @staticmethod
    def get_by_name(
        *,
        organization,
        name,
    ):
        return (
            WarehouseRepository
            .queryset_for_organization(
                organization=organization,
            )
            .filter(
                name=name,
            )
            .first()
        )

    @staticmethod
    def code_exists(
        *,
        organization,
        code,
        exclude_warehouse_id=None,
    ):
        queryset = (
            WarehouseRepository
            .queryset_for_organization(
                organization=organization,
            )
            .filter(
                code=code,
            )
        )

        if exclude_warehouse_id:

            try:

                queryset = queryset.filter(
                    id__ne=exclude_warehouse_id,
                )

            except (
                ValidationError,
                TypeError,
                ValueError,
            ):

                return False

        return queryset.first() is not None

    @staticmethod
    def name_exists(
        *,
        organization,
        name,
        exclude_warehouse_id=None,
    ):
        queryset = (
            WarehouseRepository
            .queryset_for_organization(
                organization=organization,
            )
            .filter(
                name=name,
            )
        )

        if exclude_warehouse_id:

            try:

                queryset = queryset.filter(
                    id__ne=exclude_warehouse_id,
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
            WarehouseRepository
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
            WarehouseRepository
            .queryset_for_organization(
                organization=organization,
            )
            .filter(
                is_active=True,
            )
            .order_by(
                "name",
                "id",
            )
        )

    @staticmethod
    def create_warehouse(
        *,
        organization,
        name,
        code,
        address="",
        city="",
        state="",
        country="India",
        pincode="",
    ):
        warehouse = Warehouse(
            organization=organization,
            name=name,
            code=code,
            address=address,
            city=city,
            state=state,
            country=country,
            pincode=pincode,
            is_active=True,
        )

        warehouse.save()

        return warehouse

    @staticmethod
    def update_warehouse(
        *,
        warehouse,
        name,
        code,
        address="",
        city="",
        state="",
        country="India",
        pincode="",
        is_active=None,
    ):
        warehouse.name = name
        warehouse.code = code
        warehouse.address = address
        warehouse.city = city
        warehouse.state = state
        warehouse.country = country
        warehouse.pincode = pincode

        if is_active is not None:
            warehouse.is_active = is_active

        warehouse.updated_at = (
            datetime.utcnow()
        )

        warehouse.save()

        return warehouse

    @staticmethod
    def activate(
        *,
        organization,
        warehouse_id,
    ):
        warehouse = (
            WarehouseRepository
            .get_by_id(
                organization=organization,
                warehouse_id=warehouse_id,
            )
        )

        if not warehouse:
            return None

        warehouse.is_active = True
        warehouse.updated_at = (
            datetime.utcnow()
        )

        warehouse.save()

        return warehouse

    @staticmethod
    def deactivate(
        *,
        organization,
        warehouse_id,
    ):
        warehouse = (
            WarehouseRepository
            .get_by_id(
                organization=organization,
                warehouse_id=warehouse_id,
            )
        )

        if not warehouse:
            return None

        warehouse.is_active = False
        warehouse.updated_at = (
            datetime.utcnow()
        )

        warehouse.save()

        return warehouse