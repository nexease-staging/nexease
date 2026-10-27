from apps.core.services.api_serialization_service import (
    APISerializationService,
)


class PermissionAPISerializer:

    @staticmethod
    def serialize_summary(
        permission,
    ):
        if not permission:
            return None

        return {
            "id":
                (
                    APISerializationService
                    .serialize_identifier(
                        permission.id
                    )
                ),

            "code":
                permission.code,

            "name":
                permission.name,

            "module":
                permission.module,

            "is_active":
                bool(
                    permission.is_active
                ),
        }

    @staticmethod
    def serialize_detail(
        permission,
    ):
        if not permission:
            return None

        summary = (
            PermissionAPISerializer
            .serialize_summary(
                permission
            )
        )

        return {
            **summary,

            "description":
                (
                    permission.description
                    or
                    None
                ),

            "created_at":
                (
                    APISerializationService
                    .serialize_datetime(
                        permission.created_at
                    )
                ),

            "updated_at":
                (
                    APISerializationService
                    .serialize_datetime(
                        permission.updated_at
                    )
                ),
        }


class RoleAPISerializer:

    @staticmethod
    def serialize_organization_reference(
        organization,
    ):
        if not organization:
            return None

        return {
            "id":
                (
                    APISerializationService
                    .serialize_identifier(
                        organization.id
                    )
                ),

            "name":
                organization.name,
        }

    @staticmethod
    def serialize_summary(
        role,
    ):
        if not role:
            return None

        permissions = (
            role.permissions
            or
            []
        )

        active_permissions = [
            permission

            for permission in permissions

            if getattr(
                permission,
                "is_active",
                False,
            )
        ]

        return {
            "id":
                (
                    APISerializationService
                    .serialize_identifier(
                        role.id
                    )
                ),

            "name":
                role.name,

            "description":
                (
                    role.description
                    or
                    None
                ),

            "is_system":
                bool(
                    role.is_system
                ),

            "is_active":
                bool(
                    role.is_active
                ),

            "permission_count":
                len(
                    active_permissions
                ),
        }

    @staticmethod
    def serialize_detail(
        role,
    ):
        if not role:
            return None

        summary = (
            RoleAPISerializer
            .serialize_summary(
                role
            )
        )

        organization = getattr(
            role,
            "organization",
            None,
        )

        permissions = sorted(
            (
                permission

                for permission
                in (
                    role.permissions
                    or
                    []
                )

                if getattr(
                    permission,
                    "is_active",
                    False,
                )
            ),
            key=lambda permission: (
                permission.module,
                permission.code,
            ),
        )

        serialized_permissions = [
            (
                PermissionAPISerializer
                .serialize_summary(
                    permission
                )
            )

            for permission
            in permissions
        ]

        permission_codes = [
            permission.code

            for permission
            in permissions
        ]

        permissions_by_module = {}

        for permission in permissions:
            permissions_by_module.setdefault(
                permission.module,
                [],
            ).append(
                permission.code
            )

        return {
            **summary,

            "organization":
                (
                    RoleAPISerializer
                    .serialize_organization_reference(
                        organization
                    )
                ),

            "permissions":
                serialized_permissions,

            "permission_codes":
                permission_codes,

            "permissions_by_module":
                permissions_by_module,

            "created_at":
                (
                    APISerializationService
                    .serialize_datetime(
                        role.created_at
                    )
                ),

            "updated_at":
                (
                    APISerializationService
                    .serialize_datetime(
                        role.updated_at
                    )
                ),
        }