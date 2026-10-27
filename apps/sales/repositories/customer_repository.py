from datetime import datetime

from apps.sales.models import Customer


class CustomerRepository:

    @staticmethod
    def create_customer(
        *,
        organization,
        name,
        code,
        email="",
        phone="",
        gstin="",
        billing_address="",
        shipping_address="",
        city="",
        state="",
        country="India",
        pincode="",
    ):
        customer = Customer(
            organization=organization,
            name=name,
            code=code,
            email=email or None,
            phone=phone,
            gstin=gstin,
            billing_address=billing_address,
            shipping_address=shipping_address,
            city=city,
            state=state,
            country=country,
            pincode=pincode,
        )

        customer.save()

        return customer

    @staticmethod
    def get_by_id(
        *,
        organization,
        customer_id,
    ):
        return Customer.objects(
            organization=organization,
            id=customer_id,
        ).first()

    @staticmethod
    def get_by_code(
        *,
        organization,
        code,
    ):
        return Customer.objects(
            organization=organization,
            code=code,
        ).first()

    @staticmethod
    def list_by_organization(
        *,
        organization,
        active_only=False,
    ):
        query = Customer.objects(
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
    def update_customer(
        *,
        customer,
        name=None,
        email=None,
        phone=None,
        gstin=None,
        billing_address=None,
        shipping_address=None,
        city=None,
        state=None,
        country=None,
        pincode=None,
    ):
        if name is not None:
            customer.name = name

        if email is not None:
            customer.email = email or None

        if phone is not None:
            customer.phone = phone

        if gstin is not None:
            customer.gstin = gstin

        if billing_address is not None:
            customer.billing_address = (
                billing_address
            )

        if shipping_address is not None:
            customer.shipping_address = (
                shipping_address
            )

        if city is not None:
            customer.city = city

        if state is not None:
            customer.state = state

        if country is not None:
            customer.country = country

        if pincode is not None:
            customer.pincode = pincode

        customer.updated_at = (
            datetime.utcnow()
        )

        customer.save()

        return customer

    @staticmethod
    def set_active_status(
        *,
        customer,
        is_active,
    ):
        customer.is_active = is_active
        customer.updated_at = (
            datetime.utcnow()
        )

        customer.save()

        return customer

    @staticmethod
    def queryset_for_organization(
        *,
        organization,
    ):
        return Customer.objects(
            organization=organization,
        )

    @staticmethod
    def code_exists(
        *,
        organization,
        code,
        exclude_customer_id=None,
    ):
        queryset = Customer.objects(
            organization=organization,
            code=code,
        )

        if exclude_customer_id:
            queryset = queryset.filter(
                id__ne=exclude_customer_id,
            )

        return (
            queryset
            .only(
                "id"
            )
            .first()
            is not None
        )