class PDFSecurity:

    @staticmethod
    def validate_user(
        user,
    ):
        if not user:
            raise PermissionError(
                "Not authenticated."
            )

        if not user.is_authenticated:
            raise PermissionError(
                "Not authenticated."
            )

        if not user.is_active:
            raise PermissionError(
                "Inactive user."
            )

        if not user.organization:
            raise PermissionError(
                "User has no organization."
            )

        return True

    @staticmethod
    def require_permission(
        *,
        user,
        permission_code,
    ):
        """
        Validate authentication, active status,
        tenant membership and permission.
        """

        PDFSecurity.validate_user(
            user
        )

        if not permission_code:
            raise ValueError(
                "Permission code is required."
            )

        if not user.has_permission(
            permission_code
        ):
            raise PermissionError(
                "Permission denied."
            )

        return True