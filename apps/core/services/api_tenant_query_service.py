from bson import ObjectId
from bson.errors import InvalidId

from apps.organizations.api_context_service import (
    APIOrganizationContextService,
)


class APITenantQueryConfigurationError(
    ValueError
):

    pass


class APITenantQueryService:

    @staticmethod
    def _resolve_context(
        request,
        *,
        organization_context=None,
    ):
        if organization_context is None:

            organization_context = (
                APIOrganizationContextService
                .resolve(
                    request
                )
            )

        user = organization_context.get(
            "user"
        )

        organization = (
            organization_context.get(
                "organization"
            )
        )

        if not user:

            raise PermissionError(
                "Not authenticated."
            )

        if not organization:

            raise PermissionError(
                "Organization context unavailable."
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
    def _validate_organization_field(
        queryset,
        organization_field,
    ):
        organization_field = str(
            organization_field
            or
            ""
        ).strip()

        if not organization_field:

            raise (
                APITenantQueryConfigurationError(
                    (
                        "organization_field "
                        "is required."
                    )
                )
            )

        document_class = getattr(
            queryset,
            "_document",
            None,
        )

        if document_class is None:

            raise (
                APITenantQueryConfigurationError(
                    (
                        "A MongoEngine queryset "
                        "is required."
                    )
                )
            )

        document_fields = getattr(
            document_class,
            "_fields",
            {},
        )

        if (
            organization_field
            not in document_fields
        ):

            raise (
                APITenantQueryConfigurationError(
                    (
                        f"{document_class.__name__} "
                        "does not contain tenant field "
                        f"'{organization_field}'."
                    )
                )
            )

        return organization_field

    @staticmethod
    def scope_queryset(
        queryset,
        request,
        *,
        organization_context=None,
        organization_field="organization",
    ):
        context = (
            APITenantQueryService
            ._resolve_context(
                request,
                organization_context=(
                    organization_context
                ),
            )
        )

        organization_field = (
            APITenantQueryService
            ._validate_organization_field(
                queryset,
                organization_field,
            )
        )

        organization = context[
            "organization"
        ]

        tenant_queryset = (
            queryset.filter(
                **{
                    organization_field:
                        organization,
                }
            )
        )

        return {
            "queryset":
                tenant_queryset,

            "user":
                context[
                    "user"
                ],

            "organization":
                organization,

            "organization_id":
                context[
                    "organization_id"
                ],

            "organization_field":
                organization_field,
        }

    @staticmethod
    def get_document(
        queryset,
        request,
        document_id,
        *,
        organization_context=None,
        organization_field="organization",
    ):
        scoped_result = (
            APITenantQueryService
            .scope_queryset(
                queryset,
                request,
                organization_context=(
                    organization_context
                ),
                organization_field=(
                    organization_field
                ),
            )
        )

        try:

            normalized_id = ObjectId(
                str(
                    document_id
                )
            )

        except (
            InvalidId,
            TypeError,
            ValueError,
        ):

            return {
                **scoped_result,

                "document":
                    None,
            }

        document = (
            scoped_result[
                "queryset"
            ]
            .filter(
                id=normalized_id
            )
            .first()
        )

        return {
            **scoped_result,

            "document":
                document,
        }

    @staticmethod
    def require_document(
        queryset,
        request,
        document_id,
        *,
        organization_context=None,
        organization_field="organization",
    ):
        result = (
            APITenantQueryService
            .get_document(
                queryset,
                request,
                document_id,
                organization_context=(
                    organization_context
                ),
                organization_field=(
                    organization_field
                ),
            )
        )

        if not result[
            "document"
        ]:

            raise LookupError(
                "Resource not found."
            )

        return result

    @staticmethod
    def belongs_to_organization(
        document,
        organization,
        *,
        organization_field="organization",
    ):
        if (
            not document
            or
            not organization
        ):

            return False

        document_organization = getattr(
            document,
            organization_field,
            None,
        )

        if not document_organization:
            return False

        return (
            str(
                document_organization.id
            )
            ==
            str(
                organization.id
            )
        )