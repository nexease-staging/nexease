from apps.authorization.services import (
    AuthorizationService,
)
from apps.organizations.api_context_service import (
    APIOrganizationContextService,
)


class APIPermissionContextService:

    @staticmethod
    def resolve(
        request,
        *,
        organization_context=None,
    ):
        # ==================================================
        # ORGANIZATION CONTEXT
        # ==================================================

        if organization_context is None:

            organization_context = (
                APIOrganizationContextService
                .resolve(
                    request
                )
            )

        user = organization_context[
            "user"
        ]

        organization = organization_context[
            "organization"
        ]

        # ==================================================
        # ROLE
        # ==================================================

        role = getattr(
            user,
            "role",
            None,
        )

        if not role:

            return {
                "user":
                    user,

                "organization":
                    organization,

                "role":
                    None,

                "permission_codes":
                    [],

                "permissions_by_module":
                    {},
            }

        if not getattr(
            role,
            "is_active",
            False,
        ):

            return {
                "user":
                    user,

                "organization":
                    organization,

                "role":
                    None,

                "permission_codes":
                    [],

                "permissions_by_module":
                    {},
            }

        # ==================================================
        # ROLE TENANT BOUNDARY
        # ==================================================

        role_organization = getattr(
            role,
            "organization",
            None,
        )

        if (
            not role_organization
            or
            str(
                role_organization.id
            )
            !=
            str(
                organization.id
            )
        ):

            raise PermissionError(
                "Invalid role organization context."
            )

        # ==================================================
        # ACTIVE PERMISSIONS
        # ==================================================

        permission_codes = []

        permissions_by_module = {}

        for permission in (
            getattr(
                role,
                "permissions",
                [],
            )
            or
            []
        ):

            if not permission:
                continue

            if not getattr(
                permission,
                "is_active",
                False,
            ):
                continue

            code = getattr(
                permission,
                "code",
                None,
            )

            module = getattr(
                permission,
                "module",
                None,
            )

            if not code:
                continue

            code = str(
                code
            ).strip()

            if not code:
                continue

            permission_codes.append(
                code
            )

            module_key = (
                str(
                    module
                    or
                    "general"
                )
                .strip()
                .lower()
            )

            permissions_by_module.setdefault(
                module_key,
                [],
            )

            permissions_by_module[
                module_key
            ].append(
                code
            )

        permission_codes = sorted(
            set(
                permission_codes
            )
        )

        permissions_by_module = {
            module: sorted(
                set(
                    codes
                )
            )
            for module, codes
            in sorted(
                permissions_by_module.items()
            )
        }

        return {
            "user":
                user,

            "organization":
                organization,

            "role":
                role,

            "permission_codes":
                permission_codes,

            "permissions_by_module":
                permissions_by_module,
        }

    @staticmethod
    def has_permission(
        request,
        permission_code,
    ):
        context = (
            APIPermissionContextService
            .resolve(
                request
            )
        )

        return (
            AuthorizationService
            .has_permission(
                context[
                    "user"
                ],
                permission_code,
            )
        )

    @staticmethod
    def require_permission(
        request,
        permission_code,
    ):
        context = (
            APIPermissionContextService
            .resolve(
                request
            )
        )

        allowed = (
            AuthorizationService
            .has_permission(
                context[
                    "user"
                ],
                permission_code,
            )
        )

        if not allowed:

            raise PermissionError(
                "Permission denied."
            )

        return context