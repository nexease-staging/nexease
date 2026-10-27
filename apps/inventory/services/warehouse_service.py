from apps.inventory.models import Warehouse
from apps.inventory.repositories.warehouse_repository import (
    WarehouseRepository,
)
from datetime import datetime
class WarehouseService:

    @staticmethod
    def _check_permission(user, permission_code):
        """
        Check whether the user has the required permission.
        """

        if not user:
            raise PermissionError(
                "User not found."
            )

        if not user.is_authenticated:
            raise PermissionError(
                "User is not authenticated."
            )

        if not user.is_active:
            raise PermissionError(
                "User is inactive."
            )

        if not user.has_permission(
            permission_code
        ):
            raise PermissionError(
                f"Permission denied: {permission_code}"
            )

    @staticmethod
    def create_warehouse(
        *,
        user,
        organization,
        name,
        code,
        address="",
        city="",
        state="",
        country="India",
        pincode="",
    ):
        """
        Create a warehouse within an organization.
        """

        # 1. Permission check
        WarehouseService._check_permission(
            user,
            "warehouses.create",
        )

        # 2. User must belong to an organization
        if not user.organization:
            raise ValueError(
                "User has no organization."
            )

        # 3. Tenant security check
        if user.organization.id != organization.id:
            raise PermissionError(
                "User does not belong to this organization."
            )

        # 4. Clean input
        name = name.strip()
        code = code.strip()

        # 5. Required fields
        if not name:
            raise ValueError(
                "Warehouse name is required."
            )

        if not code:
            raise ValueError(
                "Warehouse code is required."
            )

        # 6. Duplicate code check
        existing_code = (
            WarehouseRepository.get_by_code(
                organization=organization,
                code=code,
            )
        )

        if existing_code:
            raise ValueError(
                f"Warehouse with code '{code}' "
                "already exists in this organization."
            )

        # 7. Duplicate name check
        existing_name = (
            WarehouseRepository.get_by_name(
                organization=organization,
                name=name,
            )
        )

        if existing_name:
            raise ValueError(
                f"Warehouse with name '{name}' "
                "already exists in this organization."
            )

        # 8. Create warehouse
        warehouse = Warehouse(
            organization=organization,
            name=name,
            code=code,
            address=address.strip(),
            city=city.strip(),
            state=state.strip(),
            country=country.strip(),
            pincode=pincode.strip(),
            is_active=True,
        )

        warehouse.save()

        return warehouse

    @staticmethod
    def list_warehouses(
        *,
        user,
        organization,
    ):
        """
        Return warehouses belonging to an organization.
        """

        WarehouseService._check_permission(
            user,
            "warehouses.read",
        )

        if not user.organization:
            raise ValueError(
                "User has no organisation."
            )

        if user.organization.id != organization.id:
            raise PermissionError(
                "User does not belong to this organization."
            )

        return WarehouseRepository.list_by_organization(
            organization=organization,
        )

    @staticmethod
    def get_warehouse(
        *,
        user,
        organization,
        warehouse_id,
    ):
        """
        Retrieve a single warehouse belonging
        to the user's organization.
        """

        WarehouseService._check_permission(
            user,
            "warehouses.read",
        )

        if not user.organization:
            raise ValueError(
                "User has no organization."
            )

        if user.organization.id != organization.id:
            raise PermissionError(
                "User does not belong to this organization."
            )

        warehouse = WarehouseRepository.get_by_id(
            organization=organization,
            warehouse_id=warehouse_id,
        )

        if not warehouse:
            raise ValueError(
                "Warehouse not found."
            )

        return warehouse

    @staticmethod
    def update_warehouse(
        *,
        user,
        organization,
        warehouse_id,
        name,
        code,
        address="",
        city="",
        state="",
        country="India",
        pincode="",
        is_active=True,
    ):
        """
        Update a warehouse belonging to the user's organization.
        """

        # 1. Permission check
        WarehouseService._check_permission(
            user,
            "warehouses.update",
        )

        # 2. User must belong to an organization
        if not user.organization:
            raise ValueError(
                "User has no organization."
            )

        # 3. Tenant security check
        if user.organization.id != organization.id:
            raise PermissionError(
                "User does not belong to this organization."
            )

        # 4. Find warehouse
        warehouse = WarehouseRepository.get_by_id(
            organization=organization,
            warehouse_id=warehouse_id,
        )

        if not warehouse:
            raise ValueError(
                "Warehouse not found."
            )

        # 5. Clean input
        name = name.strip()
        code = code.strip()

        # 6. Required fields
        if not name:
            raise ValueError(
                "Warehouse name is required."
            )

        if not code:
            raise ValueError(
                "Warehouse code is required."
            )

        # 7. Check duplicate code
        existing_code = WarehouseRepository.get_by_code(
            organization=organization,
            code=code,
        )

        if (
            existing_code
            and existing_code.id != warehouse.id
        ):
            raise ValueError(
                f"Warehouse with code '{code}' "
                "already exists in this organization."
            )

        # 8. Check duplicate name
        existing_name = WarehouseRepository.get_by_name(
            organization=organization,
            name=name,
        )

        if (
            existing_name
            and existing_name.id != warehouse.id
        ):
            raise ValueError(
                f"Warehouse with name '{name}' "
                "already exists in this organization."
            )

        # 9. Update warehouse
        return WarehouseRepository.update_warehouse(
            warehouse=warehouse,
            name=name,
            code=code,
            address=address.strip(),
            city=city.strip(),
            state=state.strip(),
            country=country.strip(),
            pincode=pincode.strip(),
            is_active=is_active,
        )


    @staticmethod
    def deactivate_warehouse(
        *,
        user,
        organization,
        warehouse_id,
    ):
        """
        Deactivate a warehouse belonging to the user's organization.
        """

        WarehouseService._check_permission(
            user,
            "warehouses.update",
        )

        if not user.organization:
            raise ValueError(
                "User has no organization."
            )

        if user.organization.id != organization.id:
            raise PermissionError(
                "User does not belong to this organization."
            )

        warehouse = WarehouseRepository.get_by_id(
            organization=organization,
            warehouse_id=warehouse_id,
        )

        if not warehouse:
            raise ValueError(
                "Warehouse not found."
            )

        if not warehouse.is_active:
            raise ValueError(
                "Warehouse is already inactive."
            )

        warehouse.is_active = False
        warehouse.updated_at = datetime.utcnow()
        warehouse.save()

        return warehouse


    @staticmethod
    def activate_warehouse(
        *,
        user,
        organization,
        warehouse_id,
    ):
        """
        Activate a warehouse belonging to the user's organization.
        """

        WarehouseService._check_permission(
            user,
            "warehouses.update",
        )

        if not user.organization:
            raise ValueError(
                "User has no organization."
            )

        if user.organization.id != organization.id:
            raise PermissionError(
                "User does not belong to this organization."
            )

        warehouse = WarehouseRepository.get_by_id(
            organization=organization,
            warehouse_id=warehouse_id,
        )

        if not warehouse:
            raise ValueError(
                "Warehouse not found."
            )

        if warehouse.is_active:
            raise ValueError(
                "Warehouse is already active."
            )

        warehouse.is_active = True
        warehouse.updated_at = datetime.utcnow()
        warehouse.save()

        return warehouse