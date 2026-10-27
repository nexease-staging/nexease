from datetime import datetime

from mongoengine.errors import (
    NotUniqueError,
    ValidationError,
)

from apps.accounts.models import User
from apps.authorization.models import (
    Permission,
    Role,
)
from apps.authorization.roles import (
    ROLE_CATALOG,
)
from apps.organizations.models import (
    Organization,
)


class OrganizationSignupError(Exception):
    pass


class OrganizationSignupService:

    @staticmethod
    def normalize_email(
        value,
    ):
        if not isinstance(
            value,
            str,
        ):
            return ""

        return (
            value
            .strip()
            .lower()
        )

    @staticmethod
    def create_organization_account(
        *,
        organization_name,
        organization_email,
        first_name,
        last_name,
        user_email,
        password,
        business_scope="mixed",
        phone="",
        country="India",
        currency="INR",
        timezone="Asia/Kolkata",
    ):
        # ==================================================
        # NORMALIZE
        # ==================================================

        from apps.business.profiles import PROFILES
        if business_scope not in PROFILES:
            raise OrganizationSignupError("Choose a valid business scope.")
        organization_name = (
            organization_name.strip()
            if isinstance(
                organization_name,
                str,
            )
            else
            ""
        )

        organization_email = (
            OrganizationSignupService
            .normalize_email(
                organization_email
            )
        )

        user_email = (
            OrganizationSignupService
            .normalize_email(
                user_email
            )
        )

        first_name = (
            first_name.strip()
            if isinstance(
                first_name,
                str,
            )
            else
            ""
        )

        last_name = (
            last_name.strip()
            if isinstance(
                last_name,
                str,
            )
            else
            ""
        )

        phone = (
            phone.strip()
            if isinstance(
                phone,
                str,
            )
            else
            ""
        )

        # ==================================================
        # DUPLICATE USER
        # ==================================================

        existing_user = (
            User.objects(
                email=user_email
            )
            .first()
        )

        if existing_user:
            raise OrganizationSignupError(
                "An account with this email "
                "already exists."
            )

        # ==================================================
        # ADMIN ROLE DEFINITION
        # ==================================================

        admin_definition = (
            ROLE_CATALOG[
                "admin"
            ]
        )

        required_permission_codes = (
            admin_definition[
                "permissions"
            ]
        )

        permissions = list(
            Permission.objects(
                code__in=(
                    required_permission_codes
                ),
                is_active=True,
            )
        )

        permissions_by_code = {
            permission.code:
                permission

            for permission
            in permissions
        }

        missing_permissions = sorted(
            set(
                required_permission_codes
            )
            -
            set(
                permissions_by_code
            )
        )

        if missing_permissions:
            raise OrganizationSignupError(
                (
                    "Organization signup is "
                    "temporarily unavailable because "
                    "required permissions are missing."
                )
            )

        ordered_permissions = [
            permissions_by_code[
                permission_code
            ]

            for permission_code
            in required_permission_codes
        ]

        # ==================================================
        # CREATE RECORDS
        #
        # MongoEngine does not give us a portable transaction
        # here unless the deployment explicitly uses a MongoDB
        # transaction/session architecture.
        #
        # Therefore creation is compensated in reverse order
        # if a later operation fails.
        # ==================================================

        organization = None
        admin_role = None
        user = None

        try:

            organization = Organization(
                name=organization_name,
                business_scope=business_scope,
                email=organization_email,
                phone=phone,
                country=country,
                currency=currency,
                timezone=timezone,
                is_active=True,
            )

            organization.save(
                force_insert=True
            )

            admin_role = Role(
                organization=organization,
                name=admin_definition[
                    "name"
                ],
                description=(
                    admin_definition[
                        "description"
                    ]
                ),
                is_system=bool(
                    admin_definition[
                        "is_system"
                    ]
                ),
                permissions=(
                    ordered_permissions
                ),
                is_active=True,
            )

            admin_role.save(
                force_insert=True
            )

            user = User(
                organization=organization,
                role=admin_role,
                email=user_email,
                first_name=first_name,
                last_name=last_name,
                is_active=True,
            )

            user.set_password(
                password
            )

            user.save(
                force_insert=True
            )

            return {
                "organization":
                    organization,

                "role":
                    admin_role,

                "user":
                    user,
            }

        except (
            NotUniqueError,
            ValidationError,
        ) as exc:

            OrganizationSignupService._rollback(
                user=user,
                role=admin_role,
                organization=organization,
            )

            raise OrganizationSignupError(
                "Unable to create organization account."
            ) from exc

        except Exception:

            OrganizationSignupService._rollback(
                user=user,
                role=admin_role,
                organization=organization,
            )

            raise

    @staticmethod
    def _rollback(
        *,
        user,
        role,
        organization,
    ):
        if user is not None:
            try:
                user.delete()
            except Exception:
                pass

        if role is not None:
            try:
                role.delete()
            except Exception:
                pass

        if organization is not None:
            try:
                organization.delete()
            except Exception:
                pass