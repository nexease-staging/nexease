from bson import ObjectId
from bson.errors import InvalidId
from datetime import datetime
from django.contrib.auth.password_validation import (
    validate_password,
)
from django.core.exceptions import (
    ValidationError as DjangoValidationError,
)
from django.core.validators import (
    validate_email,
)

from apps.accounts.models import (
    User,
)
from apps.authorization.models import (
    Role,
)
from mongoengine.errors import (
    NotUniqueError,
)

from apps.core.services.application_logging_service import (
    ApplicationLoggingService,
)
from apps.accounts.services import (
    AuthenticationService,
)

class UserCreationValidationError(
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

        self.details = (
            details
            or
            {}
        )

class UserUpdateValidationError(
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

        self.details = (
            details
            or
            {}
        )
class UserStateValidationError(
    ValueError
):

    def __init__(
        self,
        *,
        message=(
            "User state could not "
            "be changed."
        ),
        details=None,
    ):
        super().__init__(
            message
        )

        self.message = message

        self.details = (
            details
            or
            {}
        )

class UserManagementService:

    CREATION_FIELDS = {
        "email",
        "first_name",
        "last_name",
        "password",
        "password_confirmation",
        "role_id",
    }
    UPDATE_FIELDS = {
        "email",
        "first_name",
        "last_name",
        "role_id",
    }

    @staticmethod
    def activate_user(
        *,
        organization,
        user,
        actor,
        request=None,
    ):
        # ==================================================
        # TENANT BOUNDARY
        # ==================================================

        if (
            not organization
            or
            not user
        ):

            raise PermissionError(
                "User context unavailable."
            )

        user_organization = getattr(
            user,
            "organization",
            None,
        )

        if (
            not user_organization
            or
            str(
                user_organization.id
            )
            !=
            str(
                organization.id
            )
        ):

            raise PermissionError(
                "Invalid user organization context."
            )

        # ==================================================
        # IDEMPOTENT ALREADY-ACTIVE RESULT
        # ==================================================

        if getattr(
            user,
            "is_active",
            False,
        ):

            return {
                "user":
                    user,

                "state_changed":
                    False,
            }

        # ==================================================
        # ACTIVE ROLE REQUIRED
        # ==================================================

        role = getattr(
            user,
            "role",
            None,
        )

        if (
            not role
            or
            not getattr(
                role,
                "is_active",
                False,
            )
        ):

            raise (
                UserStateValidationError(
                    message=(
                        "User cannot be activated "
                        "without an active role."
                    ),
                    details={
                        "role": [
                            (
                                "Assign an active role "
                                "before activating "
                                "the user."
                            )
                        ],
                    },
                )
            )

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

            raise (
                UserStateValidationError(
                    message=(
                        "User cannot be activated "
                        "with an invalid role."
                    ),
                    details={
                        "role": [
                            (
                                "The assigned role must "
                                "belong to the current "
                                "organization."
                            )
                        ],
                    },
                )
            )

        # ==================================================
        # ATOMIC TENANT-SCOPED ACTIVATION
        # ==================================================

        updated_user = (
            User.objects(
                id=user.id,
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

        if not updated_user:

            # The state may have changed concurrently.
            refreshed_user = (
                User.objects(
                    id=user.id,
                    organization=organization,
                )
                .first()
            )

            if (
                refreshed_user
                and
                refreshed_user.is_active
            ):

                return {
                    "user":
                        refreshed_user,

                    "state_changed":
                        False,
                }

            raise LookupError(
                "User not found."
            )

        # ==================================================
        # AUDIT LOG
        # ==================================================

        ApplicationLoggingService.log(
            level="INFO",
            message="Organization user activated.",
            module="accounts",
            action="user_activate",
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
            activated_user_id=str(
                updated_user.id
            ),
            activated_user_email=(
                updated_user.email
            ),
        )

        return {
            "user":
                updated_user,

            "state_changed":
                True,
        }

    @staticmethod
    def _normalize_required_string(
        value,
        *,
        field_name,
        maximum_length,
    ):
        if not isinstance(
            value,
            str,
        ):

            raise (
                UserCreationValidationError(
                    details={
                        field_name: [
                            (
                                f"{field_name} "
                                "must be a string."
                            )
                        ],
                    },
                )
            )

        value = value.strip()

        if not value:

            raise (
                UserCreationValidationError(
                    details={
                        field_name: [
                            (
                                f"{field_name} "
                                "is required."
                            )
                        ],
                    },
                )
            )

        if (
            len(
                value
            )
            >
            maximum_length
        ):

            raise (
                UserCreationValidationError(
                    details={
                        field_name: [
                            (
                                f"{field_name} cannot "
                                f"exceed "
                                f"{maximum_length} "
                                "characters."
                            )
                        ],
                    },
                )
            )

        return value

    @staticmethod
    def validate_creation_payload(
        *,
        organization,
        payload,
    ):
        # ==================================================
        # ORGANIZATION CONTEXT
        # ==================================================

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

        # ==================================================
        # BODY
        # ==================================================

        if not isinstance(
            payload,
            dict,
        ):

            raise (
                UserCreationValidationError(
                    details={
                        "body": [
                            (
                                "JSON body must "
                                "be an object."
                            )
                        ],
                    },
                )
            )

        if not payload:

            raise (
                UserCreationValidationError(
                    details={
                        "body": [
                            (
                                "User creation data "
                                "is required."
                            )
                        ],
                    },
                )
            )

        # ==================================================
        # FIELD WHITELIST
        # ==================================================

        unknown_fields = (
            set(
                payload.keys()
            )
            -
            UserManagementService
            .CREATION_FIELDS
        )

        if unknown_fields:

            details = {}

            for field_name in sorted(
                unknown_fields
            ):

                details[
                    field_name
                ] = [
                    (
                        "This field cannot be "
                        "provided during user "
                        "creation."
                    )
                ]

            raise (
                UserCreationValidationError(
                    message=(
                        "Unsupported user fields "
                        "were supplied."
                    ),
                    details=details,
                )
            )

        validation_errors = {}

        # ==================================================
        # EMAIL
        # ==================================================

        try:

            email = (
                UserManagementService
                ._normalize_required_string(
                    payload.get(
                        "email"
                    ),
                    field_name="email",
                    maximum_length=254,
                )
                .lower()
            )

        except UserCreationValidationError as exc:

            validation_errors.update(
                exc.details
            )

            email = None

        if email:

            try:

                validate_email(
                    email
                )

            except DjangoValidationError:

                validation_errors[
                    "email"
                ] = [
                    (
                        "Enter a valid "
                        "email address."
                    )
                ]

            else:

                existing_user = (
                    User.objects(
                        email__iexact=email
                    )
                    .only(
                        "id"
                    )
                    .first()
                )

                if existing_user:

                    validation_errors[
                        "email"
                    ] = [
                        (
                            "A user with this "
                            "email already exists."
                        )
                    ]

        # ==================================================
        # FIRST NAME
        # ==================================================

        try:

            first_name = (
                UserManagementService
                ._normalize_required_string(
                    payload.get(
                        "first_name"
                    ),
                    field_name="first_name",
                    maximum_length=100,
                )
            )

        except UserCreationValidationError as exc:

            validation_errors.update(
                exc.details
            )

            first_name = None

        # ==================================================
        # LAST NAME
        # ==================================================

        try:

            last_name = (
                UserManagementService
                ._normalize_required_string(
                    payload.get(
                        "last_name"
                    ),
                    field_name="last_name",
                    maximum_length=100,
                )
            )

        except UserCreationValidationError as exc:

            validation_errors.update(
                exc.details
            )

            last_name = None

        # ==================================================
        # PASSWORD
        #
        # Do not strip passwords. Spaces may be intentional.
        # ==================================================

        password = payload.get(
            "password"
        )

        password_confirmation = (
            payload.get(
                "password_confirmation"
            )
        )

        if (
            not isinstance(
                password,
                str,
            )
            or
            not password
        ):

            validation_errors[
                "password"
            ] = [
                "password is required."
            ]

        elif len(
            password
        ) > 128:

            validation_errors[
                "password"
            ] = [
                (
                    "password cannot exceed "
                    "128 characters."
                )
            ]

        else:

            try:

                validate_password(
                    password
                )

            except DjangoValidationError as exc:

                validation_errors[
                    "password"
                ] = [
                    str(
                        message
                    )
                    for message
                    in exc.messages
                ]

        if (
            not isinstance(
                password_confirmation,
                str,
            )
            or
            not password_confirmation
        ):

            validation_errors[
                "password_confirmation"
            ] = [
                (
                    "password_confirmation "
                    "is required."
                )
            ]

        elif (
            isinstance(
                password,
                str,
            )
            and
            password
            !=
            password_confirmation
        ):

            validation_errors[
                "password_confirmation"
            ] = [
                "Passwords do not match."
            ]

        # ==================================================
        # ROLE
        # ==================================================

        role_id = payload.get(
            "role_id"
        )

        role = None

        try:

            normalized_role_id = ObjectId(
                str(
                    role_id
                )
            )

        except (
            InvalidId,
            TypeError,
            ValueError,
        ):

            validation_errors[
                "role_id"
            ] = [
                (
                    "Select a valid active role "
                    "from this organization."
                )
            ]

        else:

            role = (
                Role.objects(
                    id=normalized_role_id,
                    organization=organization,
                    is_active=True,
                )
                .first()
            )

            if not role:

                validation_errors[
                    "role_id"
                ] = [
                    (
                        "Select a valid active role "
                        "from this organization."
                    )
                ]

        # ==================================================
        # FINAL RESULT
        # ==================================================

        if validation_errors:

            raise (
                UserCreationValidationError(
                    details=validation_errors,
                )
            )

        return {
            "email":
                email,

            "first_name":
                first_name,

            "last_name":
                last_name,

            "password":
                password,

            "role":
                role,
        }

    @staticmethod
    def create_user(
        *,
        organization,
        payload,
        actor=None,
        request=None,
    ):
        # ==================================================
        # VALIDATION
        # ==================================================

        validated = (
            UserManagementService
            .validate_creation_payload(
                organization=organization,
                payload=payload,
            )
        )

        # ==================================================
        # DOCUMENT
        # ==================================================

        user = User(
            organization=organization,
            role=validated[
                "role"
            ],
            email=validated[
                "email"
            ],
            first_name=validated[
                "first_name"
            ],
            last_name=validated[
                "last_name"
            ],
            is_active=True,
        )

        # ==================================================
        # PASSWORD HASH
        # ==================================================

        user.set_password(
            validated[
                "password"
            ]
        )

        # ==================================================
        # SAVE
        # ==================================================

        try:

            user.save(
                force_insert=True
            )

        except NotUniqueError as exc:

            raise (
                UserCreationValidationError(
                    details={
                        "email": [
                            (
                                "A user with this "
                                "email already exists."
                            )
                        ],
                    },
                )
            ) from exc

        # ==================================================
        # OPERATIONAL AUDIT LOG
        #
        # Passwords and password hashes are never logged.
        # ==================================================

        ApplicationLoggingService.log(
            level="INFO",
            message="Organization user created.",
            module="accounts",
            action="user_create",
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
            created_user_id=str(
                user.id
            ),
            created_user_email=(
                user.email
            ),
            assigned_role_id=(
                str(
                    user.role.id
                )
                if user.role
                else None
            ),
        )

        return user

    @staticmethod
    def validate_update_payload(
        *,
        organization,
        user,
        actor,
        payload,
    ):
        # ==================================================
        # TENANT BOUNDARY
        # ==================================================

        if (
            not organization
            or
            not user
        ):

            raise PermissionError(
                "User context unavailable."
            )

        user_organization = getattr(
            user,
            "organization",
            None,
        )

        if (
            not user_organization
            or
            str(
                user_organization.id
            )
            !=
            str(
                organization.id
            )
        ):

            raise PermissionError(
                "Invalid user organization context."
            )

        # ==================================================
        # BODY
        # ==================================================

        if not isinstance(
            payload,
            dict,
        ):

            raise (
                UserUpdateValidationError(
                    details={
                        "body": [
                            (
                                "JSON body must "
                                "be an object."
                            )
                        ],
                    },
                )
            )

        if not payload:

            raise (
                UserUpdateValidationError(
                    details={
                        "body": [
                            (
                                "At least one editable "
                                "field is required."
                            )
                        ],
                    },
                )
            )

        # ==================================================
        # FIELD WHITELIST
        # ==================================================

        unknown_fields = (
            set(
                payload.keys()
            )
            -
            UserManagementService
            .UPDATE_FIELDS
        )

        if unknown_fields:

            details = {}

            for field_name in sorted(
                unknown_fields
            ):

                details[
                    field_name
                ] = [
                    "This field cannot be updated."
                ]

            raise (
                UserUpdateValidationError(
                    message=(
                        "Unsupported user fields "
                        "were supplied."
                    ),
                    details=details,
                )
            )

        updates = {}
        validation_errors = {}

        # ==================================================
        # EMAIL
        # ==================================================

        if "email" in payload:

            try:

                email = (
                    UserManagementService
                    ._normalize_required_string(
                        payload[
                            "email"
                        ],
                        field_name="email",
                        maximum_length=254,
                    )
                    .lower()
                )

            except UserCreationValidationError as exc:

                validation_errors.update(
                    exc.details
                )

                email = None

            if email:

                try:

                    validate_email(
                        email
                    )

                except DjangoValidationError:

                    validation_errors[
                        "email"
                    ] = [
                        (
                            "Enter a valid "
                            "email address."
                        )
                    ]

                else:

                    duplicate = (
                        User.objects(
                            email__iexact=email,
                            id__ne=user.id,
                        )
                        .only(
                            "id"
                        )
                        .first()
                    )

                    if duplicate:

                        validation_errors[
                            "email"
                        ] = [
                            (
                                "A user with this "
                                "email already exists."
                            )
                        ]

                    else:

                        updates[
                            "email"
                        ] = email

        # ==================================================
        # FIRST NAME
        # ==================================================

        if "first_name" in payload:

            try:

                updates[
                    "first_name"
                ] = (
                    UserManagementService
                    ._normalize_required_string(
                        payload[
                            "first_name"
                        ],
                        field_name="first_name",
                        maximum_length=100,
                    )
                )

            except UserCreationValidationError as exc:

                validation_errors.update(
                    exc.details
                )

        # ==================================================
        # LAST NAME
        # ==================================================

        if "last_name" in payload:

            try:

                updates[
                    "last_name"
                ] = (
                    UserManagementService
                    ._normalize_required_string(
                        payload[
                            "last_name"
                        ],
                        field_name="last_name",
                        maximum_length=100,
                    )
                )

            except UserCreationValidationError as exc:

                validation_errors.update(
                    exc.details
                )

        # ==================================================
        # ROLE
        # ==================================================

        if "role_id" in payload:

            role_id = payload[
                "role_id"
            ]

            role = None

            try:

                normalized_role_id = ObjectId(
                    str(
                        role_id
                    )
                )

            except (
                InvalidId,
                TypeError,
                ValueError,
            ):

                validation_errors[
                    "role_id"
                ] = [
                    (
                        "Select a valid active role "
                        "from this organization."
                    )
                ]

            else:

                role = (
                    Role.objects(
                        id=normalized_role_id,
                        organization=organization,
                        is_active=True,
                    )
                    .first()
                )

                if not role:

                    validation_errors[
                        "role_id"
                    ] = [
                        (
                            "Select a valid active role "
                            "from this organization."
                        )
                    ]

                else:

                    current_role = getattr(
                        user,
                        "role",
                        None,
                    )

                    actor_is_target = (
                        actor
                        and
                        str(
                            actor.id
                        )
                        ==
                        str(
                            user.id
                        )
                    )

                    role_is_changing = (
                        not current_role
                        or
                        str(
                            current_role.id
                        )
                        !=
                        str(
                            role.id
                        )
                    )

                    if (
                        actor_is_target
                        and
                        role_is_changing
                    ):

                        validation_errors[
                            "role_id"
                        ] = [
                            (
                                "You cannot change "
                                "your own role."
                            )
                        ]

                    else:

                        updates[
                            "role"
                        ] = role

        # ==================================================
        # FINAL VALIDATION
        # ==================================================

        if validation_errors:

            raise (
                UserUpdateValidationError(
                    details=validation_errors,
                )
            )

        return updates


    @staticmethod
    def update_user(
        *,
        organization,
        user,
        actor,
        payload,
        request=None,
    ):
        # ==================================================
        # VALIDATION
        # ==================================================

        updates = (
            UserManagementService
            .validate_update_payload(
                organization=organization,
                user=user,
                actor=actor,
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

        # ==================================================
        # ATOMIC TENANT-SCOPED UPDATE
        # ==================================================

        try:

            updated_user = (
                User.objects(
                    id=user.id,
                    organization=organization,
                )
                .modify(
                    new=True,
                    **mongo_updates,
                )
            )

        except NotUniqueError as exc:

            raise (
                UserUpdateValidationError(
                    details={
                        "email": [
                            (
                                "A user with this "
                                "email already exists."
                            )
                        ],
                    },
                )
            ) from exc

        if not updated_user:

            raise LookupError(
                "User not found."
            )

        # ==================================================
        # AUDIT LOG
        # ==================================================

        ApplicationLoggingService.log(
            level="INFO",
            message="Organization user updated.",
            module="accounts",
            action="user_update",
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
            updated_user_id=str(
                updated_user.id
            ),
            updated_fields=sorted(
                updates.keys()
            ),
        )

        return updated_user

    @staticmethod
    def deactivate_user(
        *,
        organization,
        user,
        actor,
        request=None,
    ):
        # ==================================================
        # TENANT BOUNDARY
        # ==================================================

        if (
            not organization
            or
            not user
        ):

            raise PermissionError(
                "User context unavailable."
            )

        user_organization = getattr(
            user,
            "organization",
            None,
        )

        if (
            not user_organization
            or
            str(
                user_organization.id
            )
            !=
            str(
                organization.id
            )
        ):

            raise PermissionError(
                "Invalid user organization context."
            )

        # ==================================================
        # SELF-DEACTIVATION PROTECTION
        # ==================================================

        if (
            actor
            and
            str(
                actor.id
            )
            ==
            str(
                user.id
            )
        ):

            raise (
                UserStateValidationError(
                    message=(
                        "You cannot deactivate "
                        "your own account."
                    ),
                    details={
                        "user": [
                            (
                                "Ask another administrator "
                                "to deactivate this account."
                            )
                        ],
                    },
                )
            )

        # ==================================================
        # IDEMPOTENT ALREADY-INACTIVE RESULT
        # ==================================================

        if not getattr(
            user,
            "is_active",
            False,
        ):

            return {
                "user":
                    user,

                "state_changed":
                    False,

                "sessions_revoked":
                    0,
            }

        # ==================================================
        # LAST ACTIVE ADMIN PROTECTION
        # ==================================================

        role = getattr(
            user,
            "role",
            None,
        )

        if (
            role
            and
            getattr(
                role,
                "is_active",
                False,
            )
            and
            str(
                role.name
            ).strip().lower()
            ==
            "admin"
        ):

            active_admin_count = (
                User.objects(
                    organization=organization,
                    role=role,
                    is_active=True,
                )
                .count()
            )

            if active_admin_count <= 1:

                raise (
                    UserStateValidationError(
                        message=(
                            "The last active Admin "
                            "cannot be deactivated."
                        ),
                        details={
                            "user": [
                                (
                                    "Activate or create "
                                    "another Admin first."
                                )
                            ],
                        },
                    )
                )

        # ==================================================
        # ATOMIC TENANT-SCOPED DEACTIVATION
        # ==================================================

        updated_user = (
            User.objects(
                id=user.id,
                organization=organization,
                is_active=True,
            )
            .modify(
                new=True,
                set__is_active=False,
                set__updated_at=(
                    datetime.utcnow()
                ),
            )
        )

        if not updated_user:

            refreshed_user = (
                User.objects(
                    id=user.id,
                    organization=organization,
                )
                .first()
            )

            if (
                refreshed_user
                and
                not refreshed_user.is_active
            ):

                return {
                    "user":
                        refreshed_user,

                    "state_changed":
                        False,

                    "sessions_revoked":
                        0,
                }

            raise LookupError(
                "User not found."
            )

        # ==================================================
        # REVOKE TARGET USER SESSIONS
        # ==================================================

        sessions_revoked = (
            AuthenticationService
            .revoke_user_sessions(
                updated_user
            )
        )

        # ==================================================
        # AUDIT LOG
        # ==================================================

        ApplicationLoggingService.log(
            level="INFO",
            message="Organization user deactivated.",
            module="accounts",
            action="user_deactivate",
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
            deactivated_user_id=str(
                updated_user.id
            ),
            deactivated_user_email=(
                updated_user.email
            ),
            sessions_revoked=(
                sessions_revoked
            ),
        )

        return {
            "user":
                updated_user,

            "state_changed":
                True,

            "sessions_revoked":
                sessions_revoked,
        }