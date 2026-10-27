from apps.authorization.models import (
    Permission,
)


class AuthorizationService:

    @staticmethod
    def has_permission(
        user,
        permission_code,
    ):
        # ==================================================
        # USER
        # ==================================================

        if not user:
            return False

        if not getattr(
            user,
            "is_active",
            False,
        ):
            return False

        # ==================================================
        # ORGANIZATION
        # ==================================================

        organization = getattr(
            user,
            "organization",
            None,
        )

        if not organization:
            return False

        if not getattr(
            organization,
            "is_active",
            False,
        ):
            return False

        # ==================================================
        # ROLE
        # ==================================================

        role = getattr(
            user,
            "role",
            None,
        )

        if not role:
            return False

        if not getattr(
            role,
            "is_active",
            False,
        ):
            return False

        # ==================================================
        # ROLE TENANT BOUNDARY
        # ==================================================

        role_organization = getattr(
            role,
            "organization",
            None,
        )

        if not role_organization:
            return False

        if (
            str(
                role_organization.id
            )
            !=
            str(
                organization.id
            )
        ):
            return False

        # ==================================================
        # PERMISSION CODE
        # ==================================================

        if not permission_code:
            return False

        permission_code = (
            str(
                permission_code
            )
            .strip()
        )

        if not permission_code:
            return False

        # ==================================================
        # ACTIVE PERMISSION
        # ==================================================

        permission = (
            Permission.objects(
                code=permission_code,
                is_active=True,
            )
            .only(
                "id"
            )
            .first()
        )

        if not permission:
            return False

        required_id = str(
            permission.id
        )

        # ==================================================
        # ROLE PERMISSION REFERENCES
        # ==================================================

        raw_permissions = (
            role._data.get(
                "permissions"
            )
            or
            []
        )

        for reference in raw_permissions:

            reference_id = getattr(
                reference,
                "id",
                reference,
            )

            if (
                str(
                    reference_id
                )
                ==
                required_id
            ):

                return True

        return False