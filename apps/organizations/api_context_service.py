from apps.accounts.services import (
    AuthenticationService,
)


class APIOrganizationContextService:

    @staticmethod
    def resolve(
        request,
    ):
        # ==================================================
        # AUTHENTICATED USER
        # ==================================================

        user = (
            AuthenticationService
            .get_user(
                request
            )
        )

        if not user:

            raise PermissionError(
                "Not authenticated."
            )

        # ==================================================
        # ORGANIZATION FROM USER
        #
        # Never accept organization_id from:
        # - request body
        # - query parameters
        # - headers
        # - URL parameters
        # ==================================================

        organization = getattr(
            user,
            "organization",
            None,
        )

        if not organization:

            raise PermissionError(
                "Organization context unavailable."
            )

        # ==================================================
        # ACTIVE TENANT
        # ==================================================

        if not getattr(
            organization,
            "is_active",
            False,
        ):

            raise PermissionError(
                "Organization is inactive."
            )

        return {
            "user":
                user,

            "organization":
                organization,

            "organization_id":
                str(
                    organization.id
                ),
        }

    @staticmethod
    def get_user(
        request,
    ):
        context = (
            APIOrganizationContextService
            .resolve(
                request
            )
        )

        return context[
            "user"
        ]

    @staticmethod
    def get_organization(
        request,
    ):
        context = (
            APIOrganizationContextService
            .resolve(
                request
            )
        )

        return context[
            "organization"
        ]

    @staticmethod
    def get_organization_id(
        request,
    ):
        context = (
            APIOrganizationContextService
            .resolve(
                request
            )
        )

        return context[
            "organization_id"
        ]