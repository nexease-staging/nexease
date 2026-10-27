from datetime import datetime

from mongoengine.errors import (
    NotUniqueError,
)

from apps.authorization.models import (
    Permission,
    Role,
)
from apps.core.services.application_logging_service import (
    ApplicationLoggingService,
)


class RoleValidationError(
    ValueError
):

    def __init__(
        self,
        *,
        message="Validation failed.",
        details=None,
    ):
        super().__init__(
            message
        )

        self.message = message
        self.details = details or {}


class RoleStateValidationError(
    ValueError
):

    def __init__(
        self,
        *,
        message=(
            "Role state could not "
            "be changed."
        ),
        details=None,
    ):
        super().__init__(
            message
        )

        self.message = message
        self.details = details or {}


class RoleManagementService:

    CREATION_FIELDS = {
        "name",
        "description",
        "permission_codes",
    }

    UPDATE_FIELDS = {
        "name",
        "description",
    }

    @staticmethod
    def _validate_organization(
        organization,
    ):
        if not organization:
            raise PermissionError(
                "Organization context unavailable."
            )

        if not getattr(
            organization,
            "is_active",
            False,
        ):
            raise PermissionError(
                "Organization is inactive."
            )

    @staticmethod
    def _validate_role_tenant(
        *,
        organization,
        role,
    ):
        (
            RoleManagementService
            ._validate_organization(
                organization
            )
        )

        if not role:
            raise LookupError(
                "Role not found."
            )

        role_organization = getattr(
            role,
            "organization",
            None,
        )

        if (
            not role_organization
            or
            str(role_organization.id)
            !=
            str(organization.id)
        ):
            raise PermissionError(
                "Invalid role organization context."
            )

    @staticmethod
    def _normalize_name(
        value,
    ):
        if not isinstance(
            value,
            str,
        ):
            raise RoleValidationError(
                details={
                    "name": [
                        "name must be a string."
                    ],
                },
            )

        value = value.strip()

        if not value:
            raise RoleValidationError(
                details={
                    "name": [
                        "name is required."
                    ],
                },
            )

        if len(value) > 100:
            raise RoleValidationError(
                details={
                    "name": [
                        (
                            "name cannot exceed "
                            "100 characters."
                        )
                    ],
                },
            )

        return value

    @staticmethod
    def _normalize_description(
        value,
    ):
        if value is None:
            return None

        if not isinstance(
            value,
            str,
        ):
            raise RoleValidationError(
                details={
                    "description": [
                        (
                            "description must be "
                            "a string or null."
                        )
                    ],
                },
            )

        value = value.strip()

        if len(value) > 500:
            raise RoleValidationError(
                details={
                    "description": [
                        (
                            "description cannot exceed "
                            "500 characters."
                        )
                    ],
                },
            )

        return value or None

    @staticmethod
    def _resolve_permissions(
        permission_codes,
    ):
        if permission_codes is None:
            return []

        if not isinstance(
            permission_codes,
            list,
        ):
            raise RoleValidationError(
                details={
                    "permission_codes": [
                        (
                            "permission_codes must "
                            "be a list."
                        )
                    ],
                },
            )

        normalized_codes = []
        invalid_items = []

        for index, code in enumerate(
            permission_codes
        ):
            if not isinstance(
                code,
                str,
            ):
                invalid_items.append(
                    index
                )

                continue

            code = code.strip()

            if not code:
                invalid_items.append(
                    index
                )

                continue

            normalized_codes.append(
                code
            )

        if invalid_items:
            raise RoleValidationError(
                details={
                    "permission_codes": [
                        (
                            "Every permission code "
                            "must be a non-empty string."
                        )
                    ],
                },
            )

        duplicate_codes = sorted({
            code

            for code in normalized_codes

            if normalized_codes.count(
                code
            ) > 1
        })

        if duplicate_codes:
            raise RoleValidationError(
                details={
                    "permission_codes": [
                        (
                            "Duplicate permission "
                            "codes are not allowed: "
                            +
                            ", ".join(
                                duplicate_codes
                            )
                        )
                    ],
                },
            )

        if not normalized_codes:
            return []

        permissions = list(
            Permission.objects(
                code__in=normalized_codes,
                is_active=True,
            )
        )

        permissions_by_code = {
            permission.code:
                permission

            for permission in permissions
        }

        missing_codes = sorted(
            set(normalized_codes)
            -
            set(permissions_by_code)
        )

        if missing_codes:
            raise RoleValidationError(
                details={
                    "permission_codes": [
                        (
                            "Unknown or inactive "
                            "permissions: "
                            +
                            ", ".join(
                                missing_codes
                            )
                        )
                    ],
                },
            )

        return [
            permissions_by_code[
                code
            ]

            for code in sorted(
                normalized_codes
            )
        ]

    @staticmethod
    def validate_creation_payload(
        *,
        organization,
        payload,
    ):
        (
            RoleManagementService
            ._validate_organization(
                organization
            )
        )

        if not isinstance(
            payload,
            dict,
        ):
            raise RoleValidationError(
                details={
                    "body": [
                        (
                            "JSON body must "
                            "be an object."
                        )
                    ],
                },
            )

        if not payload:
            raise RoleValidationError(
                details={
                    "body": [
                        (
                            "Role creation data "
                            "is required."
                        )
                    ],
                },
            )

        unknown_fields = (
            set(payload)
            -
            RoleManagementService
            .CREATION_FIELDS
        )

        if unknown_fields:
            raise RoleValidationError(
                message=(
                    "Unsupported role fields "
                    "were supplied."
                ),
                details={
                    field_name: [
                        (
                            "This field cannot be "
                            "provided during role "
                            "creation."
                        )
                    ]

                    for field_name in sorted(
                        unknown_fields
                    )
                },
            )

        validation_errors = {}

        try:
            name = (
                RoleManagementService
                ._normalize_name(
                    payload.get(
                        "name"
                    )
                )
            )

        except RoleValidationError as exc:
            validation_errors.update(
                exc.details
            )

            name = None

        try:
            description = (
                RoleManagementService
                ._normalize_description(
                    payload.get(
                        "description"
                    )
                )
            )

        except RoleValidationError as exc:
            validation_errors.update(
                exc.details
            )

            description = None

        try:
            permissions = (
                RoleManagementService
                ._resolve_permissions(
                    payload.get(
                        "permission_codes",
                        [],
                    )
                )
            )

        except RoleValidationError as exc:
            validation_errors.update(
                exc.details
            )

            permissions = []

        if name:
            duplicate = (
                Role.objects(
                    organization=organization,
                    name__iexact=name,
                )
                .only(
                    "id"
                )
                .first()
            )

            if duplicate:
                validation_errors[
                    "name"
                ] = [
                    (
                        "A role with this name "
                        "already exists."
                    )
                ]

        if validation_errors:
            raise RoleValidationError(
                details=validation_errors,
            )

        return {
            "name":
                name,

            "description":
                description,

            "permissions":
                permissions,
        }

    @staticmethod
    def create_role(
        *,
        organization,
        payload,
        actor=None,
        request=None,
    ):
        validated = (
            RoleManagementService
            .validate_creation_payload(
                organization=organization,
                payload=payload,
            )
        )

        role = Role(
            organization=organization,
            name=validated["name"],
            description=(
                validated["description"]
            ),
            is_system=False,
            permissions=(
                validated["permissions"]
            ),
            is_active=True,
        )

        try:
            role.save(
                force_insert=True
            )

        except NotUniqueError as exc:
            raise RoleValidationError(
                details={
                    "name": [
                        (
                            "A role with this name "
                            "already exists."
                        )
                    ],
                },
            ) from exc

        ApplicationLoggingService.log(
            level="INFO",
            message="Organization role created.",
            module="authorization",
            action="role_create",
            status="success",
            user=actor,
            organization=organization,
            request_id=(
                getattr(
                    request,
                    "request_id",
                    None,
                )
                if request
                else None
            ),
            created_role_id=str(
                role.id
            ),
            created_role_name=(
                role.name
            ),
            permission_count=len(
                role.permissions
                or
                []
            ),
        )

        return role

    @staticmethod
    def validate_update_payload(
        *,
        organization,
        role,
        payload,
    ):
        (
            RoleManagementService
            ._validate_role_tenant(
                organization=organization,
                role=role,
            )
        )

        if getattr(
            role,
            "is_system",
            False,
        ):
            raise RoleStateValidationError(
                message=(
                    "System roles cannot "
                    "be modified."
                ),
                details={
                    "role": [
                        (
                            "Create a custom role "
                            "for organization-specific "
                            "access."
                        )
                    ],
                },
            )

        if not isinstance(
            payload,
            dict,
        ):
            raise RoleValidationError(
                details={
                    "body": [
                        (
                            "JSON body must "
                            "be an object."
                        )
                    ],
                },
            )

        if not payload:
            raise RoleValidationError(
                details={
                    "body": [
                        (
                            "At least one editable "
                            "field is required."
                        )
                    ],
                },
            )

        unknown_fields = (
            set(payload)
            -
            RoleManagementService
            .UPDATE_FIELDS
        )

        if unknown_fields:
            raise RoleValidationError(
                message=(
                    "Unsupported role fields "
                    "were supplied."
                ),
                details={
                    field_name: [
                        "This field cannot be updated."
                    ]

                    for field_name in sorted(
                        unknown_fields
                    )
                },
            )

        updates = {}
        validation_errors = {}

        if "name" in payload:
            try:
                name = (
                    RoleManagementService
                    ._normalize_name(
                        payload["name"]
                    )
                )

            except RoleValidationError as exc:
                validation_errors.update(
                    exc.details
                )

            else:
                duplicate = (
                    Role.objects(
                        organization=organization,
                        name__iexact=name,
                        id__ne=role.id,
                    )
                    .only(
                        "id"
                    )
                    .first()
                )

                if duplicate:
                    validation_errors[
                        "name"
                    ] = [
                        (
                            "A role with this name "
                            "already exists."
                        )
                    ]

                else:
                    updates[
                        "name"
                    ] = name

        if "description" in payload:
            try:
                updates[
                    "description"
                ] = (
                    RoleManagementService
                    ._normalize_description(
                        payload[
                            "description"
                        ]
                    )
                )

            except RoleValidationError as exc:
                validation_errors.update(
                    exc.details
                )

        if validation_errors:
            raise RoleValidationError(
                details=validation_errors,
            )

        return updates

    @staticmethod
    def update_role(
        *,
        organization,
        role,
        payload,
        actor=None,
        request=None,
    ):
        updates = (
            RoleManagementService
            .validate_update_payload(
                organization=organization,
                role=role,
                payload=payload,
            )
        )

        mongo_updates = {
            f"set__{field_name}":
                value

            for field_name, value
            in updates.items()
        }

        mongo_updates[
            "set__updated_at"
        ] = datetime.utcnow()

        try:
            updated_role = (
                Role.objects(
                    id=role.id,
                    organization=organization,
                    is_system=False,
                )
                .modify(
                    new=True,
                    **mongo_updates,
                )
            )

        except NotUniqueError as exc:
            raise RoleValidationError(
                details={
                    "name": [
                        (
                            "A role with this name "
                            "already exists."
                        )
                    ],
                },
            ) from exc

        if not updated_role:
            raise LookupError(
                "Role not found."
            )

        ApplicationLoggingService.log(
            level="INFO",
            message="Organization role updated.",
            module="authorization",
            action="role_update",
            status="success",
            user=actor,
            organization=organization,
            request_id=(
                getattr(
                    request,
                    "request_id",
                    None,
                )
                if request
                else None
            ),
            updated_role_id=str(
                updated_role.id
            ),
            updated_fields=sorted(
                updates
            ),
        )

        return updated_role

    @staticmethod
    def assign_permissions(
        *,
        organization,
        role,
        payload,
        actor=None,
        request=None,
    ):
        (
            RoleManagementService
            ._validate_role_tenant(
                organization=organization,
                role=role,
            )
        )

        if getattr(
            role,
            "is_system",
            False,
        ):
            raise RoleStateValidationError(
                message=(
                    "System-role permissions "
                    "cannot be modified."
                ),
                details={
                    "role": [
                        (
                            "Create a custom role "
                            "for organization-specific "
                            "permissions."
                        )
                    ],
                },
            )

        if not isinstance(
            payload,
            dict,
        ):
            raise RoleValidationError(
                details={
                    "body": [
                        (
                            "JSON body must "
                            "be an object."
                        )
                    ],
                },
            )

        allowed_fields = {
            "permission_codes",
        }

        unknown_fields = (
            set(payload)
            -
            allowed_fields
        )

        if unknown_fields:
            raise RoleValidationError(
                message=(
                    "Unsupported permission-assignment "
                    "fields were supplied."
                ),
                details={
                    field_name: [
                        (
                            "This field cannot be "
                            "provided during permission "
                            "assignment."
                        )
                    ]

                    for field_name in sorted(
                        unknown_fields
                    )
                },
            )

        if (
            "permission_codes"
            not in payload
        ):
            raise RoleValidationError(
                details={
                    "permission_codes": [
                        (
                            "permission_codes "
                            "is required."
                        )
                    ],
                },
            )

        permissions = (
            RoleManagementService
            ._resolve_permissions(
                payload[
                    "permission_codes"
                ]
            )
        )

        updated_role = (
            Role.objects(
                id=role.id,
                organization=organization,
                is_system=False,
            )
            .modify(
                new=True,
                set__permissions=permissions,
                set__updated_at=(
                    datetime.utcnow()
                ),
            )
        )

        if not updated_role:
            raise LookupError(
                "Role not found."
            )

        ApplicationLoggingService.log(
            level="INFO",
            message=(
                "Organization role permissions "
                "updated."
            ),
            module="authorization",
            action="role_assign_permissions",
            status="success",
            user=actor,
            organization=organization,
            request_id=(
                getattr(
                    request,
                    "request_id",
                    None,
                )
                if request
                else None
            ),
            updated_role_id=str(
                updated_role.id
            ),
            permission_count=len(
                permissions
            ),
            permission_codes=[
                permission.code

                for permission
                in permissions
            ],
        )

        return updated_role

    @staticmethod
    def activate_role(
        *,
        organization,
        role,
        actor=None,
        request=None,
    ):
        (
            RoleManagementService
            ._validate_role_tenant(
                organization=organization,
                role=role,
            )
        )

        if getattr(
            role,
            "is_active",
            False,
        ):
            return {
                "role":
                    role,

                "state_changed":
                    False,
            }

        updated_role = (
            Role.objects(
                id=role.id,
                organization=organization,
                is_active=False,
            )
            .modify(
                new=True,
                set__is_active=True,
                set__updated_at=(
                    datetime.utcnow()
                ),
            )
        )

        if not updated_role:
            refreshed_role = (
                Role.objects(
                    id=role.id,
                    organization=organization,
                )
                .first()
            )

            if (
                refreshed_role
                and
                refreshed_role.is_active
            ):
                return {
                    "role":
                        refreshed_role,

                    "state_changed":
                        False,
                }

            raise LookupError(
                "Role not found."
            )

        ApplicationLoggingService.log(
            level="INFO",
            message="Organization role activated.",
            module="authorization",
            action="role_activate",
            status="success",
            user=actor,
            organization=organization,
            request_id=(
                getattr(
                    request,
                    "request_id",
                    None,
                )
                if request
                else None
            ),
            activated_role_id=str(
                updated_role.id
            ),
            activated_role_name=(
                updated_role.name
            ),
        )

        return {
            "role":
                updated_role,

            "state_changed":
                True,
        }

    @staticmethod
    def deactivate_role(
        *,
        organization,
        role,
        actor=None,
        request=None,
    ):
        (
            RoleManagementService
            ._validate_role_tenant(
                organization=organization,
                role=role,
            )
        )

        if getattr(
            role,
            "is_system",
            False,
        ):
            raise RoleStateValidationError(
                message=(
                    "System roles cannot "
                    "be deactivated."
                ),
                details={
                    "role": [
                        (
                            "System roles are protected "
                            "by the application."
                        )
                    ],
                },
            )

        if not getattr(
            role,
            "is_active",
            False,
        ):
            return {
                "role":
                    role,

                "state_changed":
                    False,

                "assigned_active_users":
                    0,
            }

        # Avoid an import cycle:
        # User imports Role from authorization.models.
        from apps.accounts.models import User

        assigned_active_users = (
            User.objects(
                organization=organization,
                role=role,
                is_active=True,
            )
            .count()
        )

        if assigned_active_users:
            raise RoleStateValidationError(
                message=(
                    "The role cannot be deactivated "
                    "while assigned to active users."
                ),
                details={
                    "role": [
                        (
                            "Reassign or deactivate "
                            f"{assigned_active_users} "
                            "active user(s) first."
                        )
                    ],
                },
            )

        updated_role = (
            Role.objects(
                id=role.id,
                organization=organization,
                is_active=True,
                is_system=False,
            )
            .modify(
                new=True,
                set__is_active=False,
                set__updated_at=(
                    datetime.utcnow()
                ),
            )
        )

        if not updated_role:
            refreshed_role = (
                Role.objects(
                    id=role.id,
                    organization=organization,
                )
                .first()
            )

            if (
                refreshed_role
                and
                not refreshed_role.is_active
            ):
                return {
                    "role":
                        refreshed_role,

                    "state_changed":
                        False,

                    "assigned_active_users":
                        0,
                }

            raise LookupError(
                "Role not found."
            )

        ApplicationLoggingService.log(
            level="INFO",
            message=(
                "Organization role deactivated."
            ),
            module="authorization",
            action="role_deactivate",
            status="success",
            user=actor,
            organization=organization,
            request_id=(
                getattr(
                    request,
                    "request_id",
                    None,
                )
                if request
                else None
            ),
            deactivated_role_id=str(
                updated_role.id
            ),
            deactivated_role_name=(
                updated_role.name
            ),
        )

        return {
            "role":
                updated_role,

            "state_changed":
                True,

            "assigned_active_users":
                0,
        }