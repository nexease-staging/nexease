from apps.core.services.api_serialization_service import (
    APISerializationService,
)
from apps.organizations.api.v1.serializers import (
    OrganizationAPISerializer,
)

class UserAPISerializer:

    @staticmethod
    def serialize_identity(
        user,
    ):
        if not user:
            return None

        first_name = (
            user.first_name
            or
            ""
        )

        last_name = (
            user.last_name
            or
            ""
        )

        full_name = (
            f"{first_name} {last_name}"
            .strip()
        )

        return {
            "id":
                (
                    APISerializationService
                    .serialize_identifier(
                        user.id
                    )
                ),

            "email":
                user.email,

            "first_name":
                first_name,

            "last_name":
                last_name,

            "full_name":
                full_name,

            "is_active":
                bool(
                    user.is_active
                ),
        }

    @staticmethod
    def serialize_role_reference(
        role,
    ):
        if not role:
            return None

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

            "is_active":
                bool(
                    role.is_active
                ),
        }

    @staticmethod
    def serialize_summary(
        user,
    ):
        if not user:
            return None

        identity = (
            UserAPISerializer
            .serialize_identity(
                user
            )
        )

        role = getattr(
            user,
            "role",
            None,
        )

        return {
            **identity,

            "role":
                (
                    UserAPISerializer
                    .serialize_role_reference(
                        role
                    )
                ),
        }

    @staticmethod
    def serialize_detail(
        user,
    ):
        if not user:
            return None

        summary = (
            UserAPISerializer
            .serialize_summary(
                user
            )
        )

        organization = getattr(
            user,
            "organization",
            None,
        )

        return {
            **summary,

            "organization": (
                OrganizationAPISerializer
                .serialize_summary(
                    organization
                )
            ),

            "created_at":
                (
                    APISerializationService
                    .serialize_datetime(
                        user.created_at
                    )
                ),

            "updated_at":
                (
                    APISerializationService
                    .serialize_datetime(
                        user.updated_at
                    )
                ),
        }
    
class AccountAPISerializer:

    @staticmethod
    def serialize_user(
        user,
    ):
        return (
            UserAPISerializer
            .serialize_identity(
                user
            )
        )

    @staticmethod
    def serialize_organization(
        organization,
    ):
        return (
            OrganizationAPISerializer
            .serialize_summary(
                organization
            )
        )

    @staticmethod
    def serialize_role(
        role,
        *,
        permission_codes=None,
        permissions_by_module=None,
    ):
        if not role:
            return None

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

            "is_active":
                bool(
                    role.is_active
                ),

            "permissions":
                list(
                    permission_codes
                    or
                    []
                ),

            "permissions_by_module":
                dict(
                    permissions_by_module
                    or
                    {}
                ),
        }

    @staticmethod
    def serialize_authentication_context(
        *,
        user,
        organization,
        role,
        permission_codes=None,
        permissions_by_module=None,
        authenticated=True,
    ):
        return {
            "authentication": {
                "type":
                    "session",

                "authenticated":
                    bool(
                        authenticated
                    ),
            },

            "user": (
                AccountAPISerializer
                .serialize_user(
                    user
                )
            ),

            "organization": (
                AccountAPISerializer
                .serialize_organization(
                    organization
                )
            ),

            "role": (
                AccountAPISerializer
                .serialize_role(
                    role,
                    permission_codes=(
                        permission_codes
                    ),
                    permissions_by_module=(
                        permissions_by_module
                    ),
                )
            ),
        }