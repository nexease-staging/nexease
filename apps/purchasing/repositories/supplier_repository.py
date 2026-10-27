from datetime import datetime

from apps.purchasing.models import Supplier


class SupplierRepository:

    @staticmethod
    def create_supplier(
        *,
        organization,
        name,
        code,
        email="",
        phone="",
        gstin="",
        address="",
        city="",
        state="",
        country="India",
        pincode="",
    ):
        """
        Create a supplier for an organization.
        """

        supplier = Supplier(
            organization=organization,
            name=name,
            code=code,
            email=email or None,
            phone=phone,
            gstin=gstin,
            address=address,
            city=city,
            state=state,
            country=country,
            pincode=pincode,
        )

        supplier.save()

        return supplier

    @staticmethod
    def get_by_id(
        *,
        organization,
        supplier_id,
    ):
        """
        Get a supplier within an organization.
        """

        return Supplier.objects(
            organization=organization,
            id=supplier_id,
        ).first()

    @staticmethod
    def get_by_code(
        *,
        organization,
        code,
    ):
        """
        Get supplier using supplier code.
        """

        return Supplier.objects(
            organization=organization,
            code=code,
        ).first()

    @staticmethod
    def list_by_organization(
        *,
        organization,
        active_only=False,
    ):
        """
        List suppliers belonging to an organization.
        """

        query = Supplier.objects(
            organization=organization,
        )

        if active_only:
            query = query.filter(
                is_active=True,
            )

        return query.order_by(
            "-created_at"
        )

    @staticmethod
    def update_supplier(
        *,
        supplier,
        name=None,
        email=None,
        phone=None,
        gstin=None,
        address=None,
        city=None,
        state=None,
        country=None,
        pincode=None,
    ):
        """
        Update supplier master information.

        Supplier code is intentionally not changed here.
        """

        if name is not None:
            supplier.name = name

        if email is not None:
            supplier.email = email or None

        if phone is not None:
            supplier.phone = phone

        if gstin is not None:
            supplier.gstin = gstin

        if address is not None:
            supplier.address = address

        if city is not None:
            supplier.city = city

        if state is not None:
            supplier.state = state

        if country is not None:
            supplier.country = country

        if pincode is not None:
            supplier.pincode = pincode

        supplier.updated_at = datetime.utcnow()

        supplier.save()

        return supplier

    @staticmethod
    def set_active_status(
        *,
        supplier,
        is_active,
    ):
        """
        Activate or deactivate a supplier.
        """

        supplier.is_active = is_active
        supplier.updated_at = datetime.utcnow()

        supplier.save()

        return supplier

    @staticmethod
    def queryset_for_organization(
        *,
        organization,
    ):
        return Supplier.objects(
            organization=organization,
        )

    @staticmethod
    def code_exists(
        *,
        organization,
        code,
        exclude_supplier_id=None,
    ):
        queryset = Supplier.objects(
            organization=organization,
            code=code,
        )

        if exclude_supplier_id:
            queryset = queryset.filter(
                id__ne=exclude_supplier_id,
            )

        return (
            queryset
            .only(
                "id"
            )
            .first()
            is not None
        )