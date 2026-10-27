from apps.finance.models import (
    DocumentAccessLog,
)


class DocumentAuditService:

    @staticmethod
    def log_pdf_download(
        *,
        user,
        organization,
        document_type,
        document_id,
        document_number,
    ):
        if not user:
            raise ValueError(
                "User is required."
            )

        if not organization:
            raise ValueError(
                "Organization is required."
            )

        if not document_type:
            raise ValueError(
                "Document type is required."
            )

        if not document_id:
            raise ValueError(
                "Document ID is required."
            )

        if not document_number:
            raise ValueError(
                "Document number is required."
            )

        if not user.organization:
            raise ValueError(
                "User has no organization."
            )

        if (
            user.organization.id
            != organization.id
        ):
            raise PermissionError(
                "User does not belong "
                "to this organization."
            )

        log = DocumentAccessLog(
            organization=organization,
            user=user,
            document_type=(
                document_type
                .strip()
                .upper()
            ),
            document_id=str(
                document_id
            ),
            document_number=(
                str(
                    document_number
                ).strip()
            ),
            action="PDF_DOWNLOAD",
        )

        log.save()

        return log