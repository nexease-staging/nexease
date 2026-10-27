from datetime import datetime

from apps.core.background_upload_models import (
    BackgroundUpload,
)


class BackgroundUploadRepository:

    @staticmethod
    def create(
        *,
        organization,
        uploaded_by,
        purpose,
        filename,
        content_type,
        extension,
        content,
    ):
        now = datetime.utcnow()

        upload = BackgroundUpload(
            organization=organization,
            uploaded_by=uploaded_by,
            purpose=purpose,
            filename=filename,
            content_type=content_type or "",
            extension=extension,
            size=len(content),
            content=content,
            status="AVAILABLE",
            created_at=now,
            updated_at=now,
        )

        upload.save()

        return upload

    @staticmethod
    def get_by_id(
        *,
        organization,
        upload_id,
    ):
        return (
            BackgroundUpload.objects(
                organization=organization,
                id=upload_id,
            )
            .first()
        )

    @staticmethod
    def mark_consumed(
        *,
        upload,
        result=None,
    ):
        now = datetime.utcnow()

        upload.status = "CONSUMED"
        upload.result = result or {}
        upload.consumed_at = now
        upload.updated_at = now

        upload.save()

        return upload

    @staticmethod
    def mark_failed(
        *,
        upload,
    ):
        upload.status = "FAILED"
        upload.updated_at = datetime.utcnow()

        upload.save()

        return upload