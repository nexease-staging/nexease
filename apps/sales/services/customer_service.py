from apps.authorization.services import AuthorizationService

from apps.sales.repositories.customer_repository import (
    CustomerRepository,
)


class CustomerService:

    @staticmethod
    def _check_permission(
        user,
        permission_code,
    ):
        if not user:
            raise ValueError(
                "User is required."
            )

        if not user.is_active:
            raise ValueError(
                "User is inactive."
            )

        if not AuthorizationService.has_permission(
            user,
            permission_code,
        ):
            raise PermissionError(
                f"Permission denied: {permission_code}"
            )

    @staticmethod
    def _check_organization(
        user,
        organization,
    ):
        if not organization:
            raise ValueError(
                "Organization is required."
            )

        if not user.organization:
            raise ValueError(
                "User has no organization."
            )

        if user.organization.id != organization.id:
            raise PermissionError(
                "User does not belong to this organization."
            )

    @staticmethod
    def create_customer(
        *,
        user,
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
        CustomerService._check_permission(
            user,
            "customers.create",
        )

        CustomerService._check_organization(
            user,
            organization,
        )

        name = name.strip()
        code = code.strip().upper()

        if not name:
            raise ValueError(
                "Customer name is required."
            )

        if not code:
            raise ValueError(
                "Customer code is required."
            )

        existing = CustomerRepository.get_by_code(
            organization=organization,
            code=code,
        )

        if existing:
            raise ValueError(
                f"Customer with code '{code}' already exists."
            )

        return CustomerRepository.create_customer(
            organization=organization,
            name=name,
            code=code,
            email=email.strip(),
            phone=phone.strip(),
            gstin=gstin.strip().upper(),
            billing_address=billing_address.strip(),
            shipping_address=shipping_address.strip(),
            city=city.strip(),
            state=state.strip(),
            country=country.strip(),
            pincode=pincode.strip(),
        )

    @staticmethod
    def get_customer(
        *,
        user,
        organization,
        customer_id,
    ):
        CustomerService._check_permission(
            user,
            "customers.read",
        )

        CustomerService._check_organization(
            user,
            organization,
        )

        customer = CustomerRepository.get_by_id(
            organization=organization,
            customer_id=customer_id,
        )

        if not customer:
            raise ValueError(
                "Customer not found."
            )

        return customer

    @staticmethod
    def list_customers(
        *,
        user,
        organization,
        active_only=False,
    ):
        CustomerService._check_permission(
            user,
            "customers.read",
        )

        CustomerService._check_organization(
            user,
            organization,
        )

        return CustomerRepository.list_by_organization(
            organization=organization,
            active_only=active_only,
        )

    @staticmethod
    def update_customer(
        *,
        user,
        organization,
        customer_id,
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
        CustomerService._check_permission(
            user,
            "customers.update",
        )

        CustomerService._check_organization(
            user,
            organization,
        )

        customer = CustomerRepository.get_by_id(
            organization=organization,
            customer_id=customer_id,
        )

        if not customer:
            raise ValueError(
                "Customer not found."
            )

        if name is not None:
            name = name.strip()

            if not name:
                raise ValueError(
                    "Customer name cannot be empty."
                )

        return CustomerRepository.update_customer(
            customer=customer,
            name=name,
            email=(
                email.strip()
                if email is not None
                else None
            ),
            phone=(
                phone.strip()
                if phone is not None
                else None
            ),
            gstin=(
                gstin.strip().upper()
                if gstin is not None
                else None
            ),
            billing_address=(
                billing_address.strip()
                if billing_address is not None
                else None
            ),
            shipping_address=(
                shipping_address.strip()
                if shipping_address is not None
                else None
            ),
            city=(
                city.strip()
                if city is not None
                else None
            ),
            state=(
                state.strip()
                if state is not None
                else None
            ),
            country=(
                country.strip()
                if country is not None
                else None
            ),
            pincode=(
                pincode.strip()
                if pincode is not None
                else None
            ),
        )

    @staticmethod
    def deactivate_customer(
        *,
        user,
        organization,
        customer_id,
    ):
        CustomerService._check_permission(
            user,
            "customers.update",
        )

        CustomerService._check_organization(
            user,
            organization,
        )

        customer = CustomerRepository.get_by_id(
            organization=organization,
            customer_id=customer_id,
        )

        if not customer:
            raise ValueError(
                "Customer not found."
            )

        if not customer.is_active:
            raise ValueError(
                "Customer is already inactive."
            )

        return CustomerRepository.set_active_status(
            customer=customer,
            is_active=False,
        )

    @staticmethod
    def activate_customer(
        *,
        user,
        organization,
        customer_id,
    ):
        CustomerService._check_permission(
            user,
            "customers.update",
        )

        CustomerService._check_organization(
            user,
            organization,
        )

        customer = CustomerRepository.get_by_id(
            organization=organization,
            customer_id=customer_id,
        )

        if not customer:
            raise ValueError(
                "Customer not found."
            )

        if customer.is_active:
            raise ValueError(
                "Customer is already active."
            )

        return CustomerRepository.set_active_status(
            customer=customer,
            is_active=True,
        )