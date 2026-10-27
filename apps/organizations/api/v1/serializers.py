from apps.core.services.api_serialization_service import (
    APISerializationService,
)


class OrganizationAPISerializer:

    @staticmethod
    def serialize_summary(
        organization,
    ):
        if not organization:
            return None

        return {
            "business_scope": getattr(organization, "business_scope", "mixed"),
            "id":
                (
                    APISerializationService
                    .serialize_identifier(
                        organization.id
                    )
                ),

            "name":
                organization.name,

            "country":
                organization.country,

            "currency":
                organization.currency,

            "timezone":
                organization.timezone,

            "is_active":
                bool(
                    organization.is_active
                ),
        }

    @staticmethod
    def serialize_detail(
        organization,
    ):
        if not organization:
            return None

        summary = (
            OrganizationAPISerializer
            .serialize_summary(
                organization
            )
        )

        return {
            **summary,

            "email":
                organization.email,

            "phone":
                (
                    organization.phone
                    or
                    None
                ),

            "address":
                (
                    organization.address
                    or
                    None
                ),

            "created_at":
                (
                    APISerializationService
                    .serialize_datetime(
                        organization.created_at
                    )
                ),

            "updated_at":
                (
                    APISerializationService
                    .serialize_datetime(
                        organization.updated_at
                    )
                ),
        }