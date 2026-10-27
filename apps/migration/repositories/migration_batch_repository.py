from datetime import date, datetime
from decimal import Decimal
from bson import ObjectId
from mongoengine import Document
from mongoengine.errors import (
    NotUniqueError,
    ValidationError,
)

from apps.migration.models import (
    MigrationBatch,
)


class MigrationBatchRepository:

    @staticmethod
    def create(
        *,
        organization,
        created_by,
        source_system,
        migration_type,
        mapping=None,
        options=None,
    ):
        batch = MigrationBatch(
            organization=organization,
            created_by=created_by,
            source_system=source_system,
            migration_type=migration_type,
            mapping=mapping or {},
            options=options or {},
            status="CREATED",
        )

        batch.save()

        return batch

    @staticmethod
    def get_by_id(
        *,
        organization,
        batch_id,
    ):
        try:
            return (
                MigrationBatch.objects(
                    organization=organization,
                    id=batch_id,
                )
                .first()
            )

        except (
            ValidationError,
            TypeError,
            ValueError,
        ):
            return None

    @staticmethod
    def list_by_organization(
        *,
        organization,
        limit=100,
    ):
        return (
            MigrationBatch.objects(
                organization=organization,
            )
            .order_by(
                "-created_at",
                "-id",
            )
            .limit(limit)
        )

    @staticmethod
    def list_by_user(
        *,
        organization,
        created_by,
        limit=100,
    ):
        return (
            MigrationBatch.objects(
                organization=organization,
                created_by=created_by,
            )
            .order_by(
                "-created_at",
                "-id",
            )
            .limit(limit)
        )

    @staticmethod
    def set_upload(
        *,
        batch,
        upload_id,
    ):
        batch.upload_id = str(
            upload_id
        )

        batch.status = "UPLOADED"
        batch.updated_at = datetime.utcnow()

        batch.save()

        return batch

    @staticmethod
    def set_job(
        *,
        batch,
        job_id,
    ):
        batch.job_id = str(
            job_id
        )

        batch.updated_at = datetime.utcnow()

        batch.save()

        return batch

    @staticmethod
    def update_mapping(
        *,
        batch,
        mapping,
    ):
        batch.mapping = (
            mapping
            if isinstance(mapping, dict)
            else {}
        )

        batch.updated_at = datetime.utcnow()

        batch.save()

        return batch

    @staticmethod
    def update_options(
        *,
        batch,
        options,
    ):
        batch.options = (
            options
            if isinstance(options, dict)
            else {}
        )

        batch.updated_at = datetime.utcnow()

        batch.save()

        return batch

    @staticmethod
    def update_status(
        *,
        batch,
        status,
    ):
        batch.status = status
        batch.updated_at = datetime.utcnow()

        batch.save()

        return batch

    @staticmethod
    def mark_validating(
        *,
        batch,
    ):
        if batch is None:
            raise ValueError(
                "Migration batch is required."
            )

        now = datetime.utcnow()

        updated_count = (
            MigrationBatch.objects(
                id=batch.id,
                organization=(
                    batch.organization
                ),
                status="UPLOADED",
            )
            .update_one(
                set__status="VALIDATING",
                set__updated_at=now,
            )
        )

        if updated_count != 1:
            raise ValueError(
                "Migration batch is no longer "
                "available for validation."
            )

        batch.status = "VALIDATING"
        batch.updated_at = now

        return batch

    @staticmethod
    def _to_bson_safe(
        value,
    ):
        """
        Recursively convert migration validation values
        into MongoDB/JSON-safe primitive values.

        Date and datetime values are represented as
        ISO-8601 strings.
        Decimal values are preserved as strings.
        MongoEngine documents are represented by their IDs.
        ObjectIds are represented as strings.
        """

        if isinstance(
            value,
            datetime,
        ):
            return value.isoformat()

        if isinstance(
            value,
            date,
        ):
            return value.isoformat()

        if isinstance(
            value,
            Decimal,
        ):
            return str(value)

        if isinstance(
            value,
            Document,
        ):
            return (
                str(value.id)
                if value.id is not None
                else None
            )

        if isinstance(
            value,
            ObjectId,
        ):
            return str(value)

        if isinstance(
            value,
            dict,
        ):
            return {
                key: (
                    MigrationBatchRepository
                    ._to_bson_safe(item)
                )
                for key, item
                in value.items()
            }

        if isinstance(
            value,
            (list, tuple),
        ):
            return [
                MigrationBatchRepository
                ._to_bson_safe(item)
                for item in value
            ]

        return value

    @staticmethod
    def mark_validated(
        *,
        batch,
        total_rows,
        valid_rows,
        invalid_rows,
        validation_result=None,
    ):
        if batch is None:
            raise ValueError(
                "Migration batch is required."
            )

        now = datetime.utcnow()

        validation_result = (
            validation_result
            if isinstance(
                validation_result,
                dict,
            )
            else {}
        )

        validation_result = (
            MigrationBatchRepository
            ._to_bson_safe(
                validation_result
            )
        )

        updated_count = (
            MigrationBatch.objects(
                id=batch.id,
                organization=(
                    batch.organization
                ),
                status="VALIDATING",
            )
            .update_one(
                set__status="VALIDATED",
                set__total_rows=total_rows,
                set__valid_rows=valid_rows,
                set__invalid_rows=invalid_rows,
                set__validation_result=(
                    validation_result
                ),
                set__updated_at=now,
            )
        )

        if updated_count != 1:
            raise ValueError(
                "Migration batch is no longer "
                "available to complete validation."
            )

        batch.status = "VALIDATED"

        batch.total_rows = total_rows
        batch.valid_rows = valid_rows
        batch.invalid_rows = invalid_rows

        batch.validation_result = (
            validation_result
        )

        batch.updated_at = now

        return batch

    @staticmethod
    def mark_importing(
        *,
        batch,
    ):
        if batch is None:
            raise ValueError(
                "Migration batch is required."
            )

        now = datetime.utcnow()

        updated_count = (
            MigrationBatch.objects(
                id=batch.id,
                organization=(
                    batch.organization
                ),
                status="VALIDATED",
            )
            .update_one(
                set__status="IMPORTING",
                set__started_at=now,
                set__updated_at=now,
            )
        )

        if updated_count != 1:
            raise ValueError(
                "Migration batch is no longer "
                "available for import."
            )

        batch.status = "IMPORTING"
        batch.started_at = now
        batch.updated_at = now

        return batch

    @staticmethod
    def mark_completed(
        *,
        batch,
        imported_rows,
        skipped_rows=0,
        failed_rows=0,
        import_result=None,
    ):
        if batch is None:
            raise ValueError(
                "Migration batch is required."
            )

        now = datetime.utcnow()

        import_result = (
            import_result
            if isinstance(
                import_result,
                dict,
            )
            else {}
        )

        status = (
            "COMPLETED_WITH_ERRORS"
            if failed_rows
            else "COMPLETED"
        )

        updated_count = (
            MigrationBatch.objects(
                id=batch.id,
                organization=(
                    batch.organization
                ),
                status="IMPORTING",
            )
            .update_one(
                set__status=status,
                set__imported_rows=(
                    imported_rows
                ),
                set__skipped_rows=(
                    skipped_rows
                ),
                set__failed_rows=(
                    failed_rows
                ),
                set__import_result=(
                    import_result
                ),
                set__completed_at=now,
                set__updated_at=now,
            )
        )

        if updated_count != 1:
            raise ValueError(
                "Migration batch is no longer "
                "available to complete import."
            )

        batch.status = status
        batch.imported_rows = imported_rows
        batch.skipped_rows = skipped_rows
        batch.failed_rows = failed_rows
        batch.import_result = import_result
        batch.completed_at = now
        batch.updated_at = now

        return batch

    @staticmethod
    def mark_failed(
        *,
        batch,
        error_summary=None,
        expected_status=None,
    ):
        if batch is None:
            raise ValueError(
                "Migration batch is required."
            )

        if expected_status not in {
            "VALIDATING",
            "IMPORTING",
        }:
            raise ValueError(
                "Expected migration status must "
                "be VALIDATING or IMPORTING."
            )

        now = datetime.utcnow()

        error_summary = (
            error_summary
            if isinstance(
                error_summary,
                dict,
            )
            else {}
        )

        updated_count = (
            MigrationBatch.objects(
                id=batch.id,
                organization=(
                    batch.organization
                ),
                status=expected_status,
            )
            .update_one(
                set__status="FAILED",
                set__error_summary=(
                    error_summary
                ),
                set__completed_at=now,
                set__updated_at=now,
            )
        )

        if updated_count != 1:
            raise ValueError(
                "Migration batch is no longer "
                "available to mark failed."
            )

        batch.status = "FAILED"
        batch.error_summary = error_summary
        batch.completed_at = now
        batch.updated_at = now

        return batch

    @staticmethod
    def mark_cancelled(
        *,
        batch,
    ):
        batch.status = "CANCELLED"

        batch.completed_at = (
            datetime.utcnow()
        )

        batch.updated_at = (
            datetime.utcnow()
        )

        batch.save()

        return batch