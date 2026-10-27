from bson import ObjectId
from bson.errors import InvalidId

from apps.finance.documents.pdf_security import PDFSecurity
from apps.finance.services.document_attachment_service import (
    DocumentAttachmentService,
)
from apps.finance.services.document_audit_service import (
    DocumentAuditService,
)
from apps.finance.services.document_email_config_service import (
    DocumentEmailConfigService,
)
from apps.finance.services.generic_document_email_service import (
    GenericDocumentEmailService,
)


class DocumentAPIValidationError(ValueError):
    pass


class DocumentAPIService:

    @staticmethod
    def _normalize_document_type(document_type):
        try:
            return (
                DocumentEmailConfigService
                .normalize_document_type(
                    document_type
                )
            )
        except ValueError as exc:
            raise DocumentAPIValidationError(
                str(exc)
            ) from exc

    @staticmethod
    def _normalize_document_id(document_id):
        if document_id is None:
            raise DocumentAPIValidationError(
                "Document ID is required."
            )

        normalized = str(document_id).strip()

        if not normalized:
            raise DocumentAPIValidationError(
                "Document ID is required."
            )

        try:
            ObjectId(normalized)
        except (
            InvalidId,
            TypeError,
        ) as exc:
            raise DocumentAPIValidationError(
                "Invalid document ID."
            ) from exc

        return normalized

    @staticmethod
    def _check_context(
        *,
        user,
        organization,
    ):
        if not user:
            raise DocumentAPIValidationError(
                "User is required."
            )

        if not organization:
            raise DocumentAPIValidationError(
                "Organization is required."
            )

        user_organization = getattr(
            user,
            "organization",
            None,
        )

        if not user_organization:
            raise PermissionError(
                "User has no organization."
            )

        if (
            str(user_organization.id)
            !=
            str(organization.id)
        ):
            raise PermissionError(
                "User does not belong to this organization."
            )

    @staticmethod
    def _get_document_context(
        *,
        user,
        organization,
        document_type,
        document_id,
    ):
        DocumentAPIService._check_context(
            user=user,
            organization=organization,
        )

        normalized_type = (
            DocumentAPIService
            ._normalize_document_type(
                document_type
            )
        )

        normalized_id = (
            DocumentAPIService
            ._normalize_document_id(
                document_id
            )
        )

        config = (
            DocumentEmailConfigService
            .get_config(
                normalized_type
            )
        )

        PDFSecurity.require_permission(
            user=user,
            permission_code=config[
                "permission"
            ],
        )

        document = (
            DocumentEmailConfigService
            .get_document(
                organization=organization,
                document_type=normalized_type,
                document_id=normalized_id,
            )
        )

        if not document:
            return None

        delivery_data = (
            DocumentEmailConfigService
            .get_delivery_data(
                document_type=normalized_type,
                document=document,
            )
        )

        return {
            "document_type":
                normalized_type,

            "document_id":
                normalized_id,

            "document":
                document,

            "document_number":
                delivery_data[
                    "document_number"
                ],

            "permission":
                config[
                    "permission"
                ],

            "delivery_data":
                delivery_data,
        }

    @staticmethod
    def generate_pdf(
        *,
        user,
        organization,
        document_type,
        document_id,
    ):
        context = (
            DocumentAPIService
            ._get_document_context(
                user=user,
                organization=organization,
                document_type=document_type,
                document_id=document_id,
            )
        )

        if context is None:
            return None

        attachment = (
            DocumentAttachmentService
            .generate(
                document_type=context[
                    "document_type"
                ],
                document=context[
                    "document"
                ],
                document_number=context[
                    "document_number"
                ],
            )
        )

        DocumentAuditService.log_pdf_download(
            user=user,
            organization=organization,
            document_type=context[
                "document_type"
            ],
            document_id=context[
                "document_id"
            ],
            document_number=context[
                "document_number"
            ],
        )

        return {
            "document_type":
                context[
                    "document_type"
                ],

            "document_id":
                context[
                    "document_id"
                ],

            "document_number":
                context[
                    "document_number"
                ],

            "filename":
                attachment[
                    "filename"
                ],

            "content_type":
                attachment[
                    "content_type"
                ],

            "content":
                attachment[
                    "content"
                ],

            "size":
                attachment[
                    "size"
                ],
        }

    @staticmethod
    def send_email(
        *,
        user,
        organization,
        document_type,
        document_id,
        recipient_email=None,
        subject=None,
        message=None,
        background_job_key=None,
    ):
        DocumentAPIService._check_context(
            user=user,
            organization=organization,
        )

        normalized_type = (
            DocumentAPIService
            ._normalize_document_type(
                document_type
            )
        )

        normalized_id = (
            DocumentAPIService
            ._normalize_document_id(
                document_id
            )
        )

        return (
            GenericDocumentEmailService
            .send(
                user=user,
                organization=organization,
                document_type=normalized_type,
                document_id=normalized_id,
                recipient_email_override=(
                    recipient_email
                ),
                subject_override=subject,
                body_override=message,
                background_job_key=background_job_key,
            )
        )