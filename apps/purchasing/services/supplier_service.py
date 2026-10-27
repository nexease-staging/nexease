from apps.authorization.services import AuthorizationService

from apps.purchasing.repositories.supplier_repository import (
    SupplierRepository,
)


class SupplierService:

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
    def create_supplier(
        *,
        user,
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
        SupplierService._check_permission(
            user,
            "suppliers.create",
        )

        SupplierService._check_organization(
            user,
            organization,
        )

        name = name.strip()
        code = code.strip().upper()

        if not name:
            raise ValueError(
                "Supplier name is required."
            )

        if not code:
            raise ValueError(
                "Supplier code is required."
            )

        existing = SupplierRepository.get_by_code(
            organization=organization,
            code=code,
        )

        if existing:
            raise ValueError(
                f"Supplier with code '{code}' already exists."
            )

        return SupplierRepository.create_supplier(
            organization=organization,
            name=name,
            code=code,
            email=email.strip(),
            phone=phone.strip(),
            gstin=gstin.strip().upper(),
            address=address.strip(),
            city=city.strip(),
            state=state.strip(),
            country=country.strip(),
            pincode=pincode.strip(),
        )

    @staticmethod
    def get_supplier(
        *,
        user,
        organization,
        supplier_id,
    ):
        SupplierService._check_permission(
            user,
            "suppliers.read",
        )

        SupplierService._check_organization(
            user,
            organization,
        )

        supplier = SupplierRepository.get_by_id(
            organization=organization,
            supplier_id=supplier_id,
        )

        if not supplier:
            raise ValueError(
                "Supplier not found."
            )

        return supplier

    @staticmethod
    def list_suppliers(
        *,
        user,
        organization,
        active_only=False,
    ):
        SupplierService._check_permission(
            user,
            "suppliers.read",
        )

        SupplierService._check_organization(
            user,
            organization,
        )

        return SupplierRepository.list_by_organization(
            organization=organization,
            active_only=active_only,
        )

    @staticmethod
    def update_supplier(
        *,
        user,
        organization,
        supplier_id,
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
        SupplierService._check_permission(
            user,
            "suppliers.update",
        )

        SupplierService._check_organization(
            user,
            organization,
        )

        supplier = SupplierRepository.get_by_id(
            organization=organization,
            supplier_id=supplier_id,
        )

        if not supplier:
            raise ValueError(
                "Supplier not found."
            )

        if name is not None:
            name = name.strip()

            if not name:
                raise ValueError(
                    "Supplier name cannot be empty."
                )

        return SupplierRepository.update_supplier(
            supplier=supplier,
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
            address=(
                address.strip()
                if address is not None
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
    def deactivate_supplier(
        *,
        user,
        organization,
        supplier_id,
    ):
        SupplierService._check_permission(
            user,
            "suppliers.update",
        )

        SupplierService._check_organization(
            user,
            organization,
        )

        supplier = SupplierRepository.get_by_id(
            organization=organization,
            supplier_id=supplier_id,
        )

        if not supplier:
            raise ValueError(
                "Supplier not found."
            )

        if not supplier.is_active:
            raise ValueError(
                "Supplier is already inactive."
            )

        return SupplierRepository.set_active_status(
            supplier=supplier,
            is_active=False,
        )

    @staticmethod
    def activate_supplier(
        *,
        user,
        organization,
        supplier_id,
    ):
        SupplierService._check_permission(
            user,
            "suppliers.update",
        )

        SupplierService._check_organization(
            user,
            organization,
        )

        supplier = SupplierRepository.get_by_id(
            organization=organization,
            supplier_id=supplier_id,
        )

        if not supplier:
            raise ValueError(
                "Supplier not found."
            )

        if supplier.is_active:
            raise ValueError(
                "Supplier is already active."
            )

        return SupplierRepository.set_active_status(
            supplier=supplier,
            is_active=True,
        )