from apps.core.repositories.background_upload_repository import (
    BackgroundUploadRepository,
)
from apps.core.services.background_upload_service import (
    BackgroundUploadService,
)

from apps.migration.repositories.migration_batch_repository import (
    MigrationBatchRepository,
)
from apps.migration.services.migration_batch_service import (
    MigrationBatchService,
)
from apps.migration.services.migration_file_parser import (
    MigrationFileParser,
)
from apps.migration.services.migration_preview_service import (
    MigrationPreviewError,
    MigrationPreviewService,
)
from apps.migration.services.migration_import_service import (
    MigrationImportError,
    MigrationImportService,
)
from apps.core.services.background_job_service import (
    BackgroundJobService,
)

class MigrationAPIValidationError(ValueError):
    """
    Validation error raised by the migration API service.

    The API layer can expose the error message and structured
    field-level validation details.
    """

    def __init__(
        self,
        message,
        *,
        details=None,
    ):
        self.message = str(
            message
        )

        self.details = (
            details
            if isinstance(details, dict)
            else {}
        )

        super().__init__(
            self.message
        )


class MigrationAPIService:
    """
    Application/API orchestration service for data migration.

    This service provides the boundary between the migration HTTP API
    and the lower-level migration services/repositories.

    Responsibilities:

    - validate API-level input
    - scope migration operations to an organization
    - create migration batches
    - list migration batches
    - retrieve migration batches
    - upload migration source files
    - parse uploaded files
    - attach successful uploads to migration batches
    - clean up failed uploads

    Migration business rules remain in the underlying migration
    services and repositories.
    """

    DEFAULT_LIST_LIMIT = 100
    MIN_LIST_LIMIT = 1
    MAX_LIST_LIMIT = 100

    ALLOWED_SOURCE_SYSTEMS = {
        "GENERIC",
        "ZOHO_INVENTORY",
    }

    ALLOWED_MIGRATION_TYPES = {
        "CATEGORIES",
        "PRODUCTS",
        "CUSTOMERS",
        "SUPPLIERS",
        "WAREHOUSES",
        "INVENTORY",
        "SALES_ORDERS",
        "PURCHASE_ORDERS",
        "SALES_INVOICES",
    }

    ALLOWED_MIGRATION_OPTIONS = {
        "skip_duplicates",
    }
    # ==================================================
    # INTERNAL VALIDATION HELPERS
    # ==================================================

    @staticmethod
    def _require_organization(
        organization,
    ):
        if not organization:
            raise PermissionError(
                "Organization context is required."
            )

        return organization

    @staticmethod
    def _require_user(
        user,
    ):
        if not user:
            raise PermissionError(
                "Authentication is required."
            )

        return user

    @staticmethod
    def _validate_limit(
        limit,
    ):
        if (
            isinstance(limit, bool)
            or not isinstance(limit, int)
            or limit < 1
            or limit > 100
        ):
            raise MigrationAPIValidationError(
                "Migration validation failed.",
                details={
                    "limit": [
                        (
                            "Limit must be an integer "
                            "between 1 and 100."
                        )
                    ],
                },
            )

        return limit

    @staticmethod
    def _validate_create_payload(
        payload,
    ):
        if not isinstance(payload, dict):
            raise MigrationAPIValidationError(
                "Migration validation failed.",
                details={
                    "payload": [
                        (
                            "Migration payload must "
                            "be an object."
                        )
                    ],
                },
            )

        allowed_fields = {
            "source_system",
            "migration_type",
            "mapping",
            "options",
        }

        unsupported_fields = sorted(
            set(payload.keys())
            - allowed_fields
        )

        if unsupported_fields:
            raise MigrationAPIValidationError(
                "Migration validation failed.",
                details={
                    "fields": [
                        (
                            "Unsupported field(s): "
                            + ", ".join(
                                unsupported_fields
                            )
                        )
                    ],
                },
            )

        errors = {}

        source_system = payload.get(
            "source_system"
        )

        migration_type = payload.get(
            "migration_type"
        )

        mapping = payload.get(
            "mapping",
            {},
        )

        options = payload.get(
            "options",
            {},
        )

        if (
            not isinstance(
                source_system,
                str,
            )
            or not source_system.strip()
        ):
            errors[
                "source_system"
            ] = [
                (
                    "Migration source system "
                    "is required."
                )
            ]

        elif (
            source_system.strip().upper()
            not in
            MigrationAPIService
            .ALLOWED_SOURCE_SYSTEMS
        ):
            errors[
                "source_system"
            ] = [
                (
                    "Invalid migration "
                    "source system."
                )
            ]

        if (
            not isinstance(
                migration_type,
                str,
            )
            or not migration_type.strip()
        ):
            errors[
                "migration_type"
            ] = [
                (
                    "Migration type "
                    "is required."
                )
            ]

        elif (
            migration_type.strip().upper()
            not in
            MigrationAPIService
            .ALLOWED_MIGRATION_TYPES
        ):
            errors[
                "migration_type"
            ] = [
                "Invalid migration type."
            ]

        if not isinstance(
            mapping,
            dict,
        ):
            errors[
                "mapping"
            ] = [
                (
                    "Migration mapping "
                    "must be an object."
                )
            ]

        if not isinstance(
            options,
            dict,
        ):
            errors[
                "options"
            ] = [
                (
                    "Migration options "
                    "must be an object."
                )
            ]

        else:
            unsupported_options = sorted(
                set(options.keys())
                - MigrationAPIService
                .ALLOWED_MIGRATION_OPTIONS
            )

            if unsupported_options:
                errors[
                    "options"
                ] = [
                    (
                        "Unsupported migration "
                        "option(s): "
                        + ", ".join(
                            unsupported_options
                        )
                    )
                ]

            elif (
                "skip_duplicates" in options
                and not isinstance(
                    options[
                        "skip_duplicates"
                    ],
                    bool,
                )
            ):
                errors[
                    "options"
                ] = [
                    (
                        "Migration option "
                        "'skip_duplicates' "
                        "must be a boolean."
                    )
                ]

        if errors:
            raise MigrationAPIValidationError(
                "Migration validation failed.",
                details=errors,
            )

        return {
            "source_system":
                source_system
                .strip()
                .upper(),
            "migration_type":
                migration_type
                .strip()
                .upper(),
            "mapping":
                mapping,
            "options":
                options,
        }

    @staticmethod
    def _validate_uploaded_file(
        uploaded_file,
    ):
        if uploaded_file is None:
            raise MigrationAPIValidationError(
                "Migration validation failed.",
                details={
                    "file": [
                        (
                            "Migration file "
                            "is required."
                        )
                    ],
                },
            )

        filename = getattr(
            uploaded_file,
            "name",
            "",
        )

        if not isinstance(
            filename,
            str,
        ):
            filename = ""

        normalized_filename = (
            filename
            .strip()
            .lower()
        )

        if not (
            normalized_filename.endswith(
                ".csv"
            )
            or
            normalized_filename.endswith(
                ".xlsx"
            )
        ):
            raise MigrationAPIValidationError(
                "Migration validation failed.",
                details={
                    "file": [
                        (
                            "Only CSV and XLSX "
                            "migration files "
                            "are supported."
                        )
                    ],
                },
            )

        return uploaded_file

    # ==================================================
    # SERIALIZATION
    # ==================================================

    @staticmethod
    def serialize_batch(
        batch,
    ):
        """
        Convert a migration batch into the public API representation.

        Internal organization/user document objects are deliberately
        not exposed.
        """

        if batch is None:
            return None

        def serialize_datetime(
            value,
        ):
            if value is None:
                return None

            isoformat = getattr(
                value,
                "isoformat",
                None,
            )

            if callable(isoformat):
                return isoformat()

            return str(value)

        created_by = getattr(
            batch,
            "created_by",
            None,
        )

        created_by_id = None

        if created_by is not None:
            created_by_id = str(
                getattr(
                    created_by,
                    "id",
                    created_by,
                )
            )

        return {
            "id": str(
                getattr(
                    batch,
                    "id",
                    "",
                )
            ),
            "source_system": getattr(
                batch,
                "source_system",
                None,
            ),
            "migration_type": getattr(
                batch,
                "migration_type",
                None,
            ),
            "status": getattr(
                batch,
                "status",
                None,
            ),
            "mapping": (
                getattr(
                    batch,
                    "mapping",
                    None,
                )
                or {}
            ),
            "options": (
                getattr(
                    batch,
                    "options",
                    None,
                )
                or {}
            ),
            "upload_id": getattr(
                batch,
                "upload_id",
                None,
            ),
            "job_id": getattr(
                batch,
                "job_id",
                None,
            ),
            "total_rows": getattr(
                batch,
                "total_rows",
                0,
            ),
            "valid_rows": getattr(
                batch,
                "valid_rows",
                0,
            ),
            "invalid_rows": getattr(
                batch,
                "invalid_rows",
                0,
            ),
            "imported_rows": getattr(
                batch,
                "imported_rows",
                0,
            ),
            "skipped_rows": getattr(
                batch,
                "skipped_rows",
                0,
            ),
            "failed_rows": getattr(
                batch,
                "failed_rows",
                0,
            ),
            "created_by":
                created_by_id,
            "created_at":
                serialize_datetime(
                    getattr(
                        batch,
                        "created_at",
                        None,
                    )
                ),
            "updated_at":
                serialize_datetime(
                    getattr(
                        batch,
                        "updated_at",
                        None,
                    )
                ),
            "started_at":
                serialize_datetime(
                    getattr(
                        batch,
                        "started_at",
                        None,
                    )
                ),
            "completed_at":
                serialize_datetime(
                    getattr(
                        batch,
                        "completed_at",
                        None,
                    )
                ),
        }

    # ==================================================
    # LIST BATCHES
    # ==================================================

    @staticmethod
    def list_batches(
        *,
        organization,
        limit=100,
    ):
        MigrationAPIService._require_organization(
            organization
        )

        normalized_limit = (
            MigrationAPIService
            ._validate_limit(
                limit
            )
        )

        return list(
            MigrationBatchRepository
            .list_by_organization(
                organization=organization,
                limit=normalized_limit,
            )
        )

    # ==================================================
    # CREATE BATCH
    # ==================================================

    @staticmethod
    def create_batch(
        *,
        organization,
        created_by,
        payload,
    ):
        MigrationAPIService._require_organization(
            organization
        )

        MigrationAPIService._require_user(
            created_by
        )

        normalized = (
            MigrationAPIService
            ._validate_create_payload(
                payload
            )
        )

        return (
            MigrationBatchService
            .create_batch(
                organization=organization,
                created_by=created_by,
                source_system=(
                    normalized[
                        "source_system"
                    ]
                ),
                migration_type=(
                    normalized[
                        "migration_type"
                    ]
                ),
                mapping=(
                    normalized[
                        "mapping"
                    ]
                ),
                options=(
                    normalized[
                        "options"
                    ]
                ),
            )
        )

    # ==================================================
    # GET BATCH
    # ==================================================

    @staticmethod
    def get_batch(
        *,
        organization,
        batch_id,
    ):
        MigrationAPIService._require_organization(
            organization
        )

        if not batch_id:
            raise LookupError(
                "Migration batch not found."
            )

        batch = (
            MigrationBatchService
            .get_batch(
                organization=organization,
                batch_id=batch_id,
            )
        )

        if not batch:
            raise LookupError(
                "Migration batch not found."
            )

        return batch

    # ==================================================
    # UPLOAD FILE
    # ==================================================

    @staticmethod
    def upload_file(
        *,
        user,
        batch,
        uploaded_file,
    ):
        """
        Store, parse and attach a migration source file.

        The upload is attached to the migration batch only
        after parsing succeeds.

        If parsing or attachment fails after the upload has
        been created, the upload is marked FAILED.
        """

        MigrationAPIService._require_user(
            user
        )

        if batch is None:
            raise LookupError(
                "Migration batch not found."
            )

        organization = getattr(
            batch,
            "organization",
            None,
        )

        MigrationAPIService._require_organization(
            organization
        )

        user_organization = getattr(
            user,
            "organization",
            None,
        )

        if (
            user_organization is not None
            and str(
                getattr(
                    user_organization,
                    "id",
                    user_organization,
                )
            )
            !=
            str(
                getattr(
                    organization,
                    "id",
                    organization,
                )
            )
        ):
            raise LookupError(
                "Migration batch not found."
            )

        MigrationAPIService._validate_uploaded_file(
            uploaded_file
        )

        if getattr(
            batch,
            "status",
            None,
        ) != "CREATED":
            raise MigrationAPIValidationError(
                "Migration validation failed.",
                details={
                    "migration": [
                        (
                            "A file can only be "
                            "uploaded to a newly "
                            "created migration."
                        )
                    ],
                },
            )

        upload = None

        try:
            upload = (
                BackgroundUploadService
                .create_data_migration_upload(
                    organization=organization,
                    uploaded_by=user,
                    uploaded_file=uploaded_file,
                )
            )

            parsed_file = (
                MigrationFileParser
                .parse(
                    filename=upload.filename,
                    content=upload.content,
                )
            )

            batch = (
                MigrationBatchService
                .attach_upload(
                    batch=batch,
                    upload_id=upload.id,
                )
            )

        except Exception:
            if upload is not None:
                (
                    BackgroundUploadRepository
                    .mark_failed(
                        upload=upload,
                    )
                )

            raise

        return {
            "batch": batch,
            "upload": upload,
            "file": parsed_file,
        }

    # ==================================================
    # VALIDATE MIGRATION
    # ==================================================

    @staticmethod
    def validate_batch(
        *,
        organization,
        batch_id,
    ):
        """
        Validate an uploaded migration batch.

        The preview service owns the complete validation workflow:

        - retrieve the uploaded source file
        - parse all rows
        - validate mapping
        - apply mapping
        - validate individual rows
        - update migration lifecycle state
        - persist validation results
        """

        MigrationAPIService._require_organization(
            organization
        )

        if not batch_id:
            raise LookupError(
                "Migration batch not found."
            )

        batch = (
            MigrationBatchService
            .get_batch(
                organization=organization,
                batch_id=batch_id,
            )
        )

        if batch is None:
            raise LookupError(
                "Migration batch not found."
            )

        try:
            validation = (
                MigrationPreviewService
                .validate_batch(
                    batch=batch,
                    organization=organization,
                )
            )

        except MigrationPreviewError as exc:
            raise MigrationAPIValidationError(
                str(exc),
                details={
                    "migration": [
                        str(exc)
                    ],
                },
            ) from exc

        except ValueError as exc:
            raise MigrationAPIValidationError(
                str(exc),
                details={
                    "migration": [
                        str(exc)
                    ],
                },
            ) from exc

        return {
            "batch": batch,
            "validation": (
                batch.validation_result
            ),
        }

    @staticmethod
    def import_batch(
        *,
        organization,
        batch_id,
    ):
        if organization is None:
            raise PermissionError(
                "Organization context unavailable."
            )

        batch_id = str(
            batch_id
            or
            ""
        ).strip()

        if not batch_id:
            raise LookupError(
                "Migration batch not found."
            )

        batch = (
            MigrationBatchService
            .get_batch(
                organization=organization,
                batch_id=batch_id,
            )
        )

        if not batch:
            raise LookupError(
                "Migration batch not found."
            )

        try:
            return (
                MigrationImportService
                .import_batch(
                    organization=organization,
                    batch=batch,
                )
            )

        except MigrationImportError as exc:
            raise MigrationAPIValidationError(
                "Migration import failed.",
                details={
                    "migration": [
                        str(exc)
                    ],
                },
            ) from exc

    @staticmethod
    def queue_validation(
        *,
        organization,
        created_by,
        batch_id,
    ):
        batch = (
            MigrationAPIService
            .get_batch(
                organization=organization,
                batch_id=batch_id,
            )
        )

        job = (
            BackgroundJobService
            .create_job(
                organization=organization,
                created_by=created_by,
                job_type=(
                    "DATA_MIGRATION_VALIDATE"
                ),
                payload={
                    "batch_id":
                        str(batch.id),
                },
                idempotency_key=(
                    "DATA_MIGRATION_VALIDATE:"
                    f"{batch.id}"
                ),
            )
        )

        (
            MigrationBatchRepository
            .set_job(
                batch=batch,
                job_id=job.id,
            )
        )

        return {
            "batch": batch,
            "job": job,
        }

    @staticmethod
    def queue_import(
        *,
        organization,
        created_by,
        batch_id,
    ):
        batch = (
            MigrationAPIService
            .get_batch(
                organization=organization,
                batch_id=batch_id,
            )
        )

        job = (
            BackgroundJobService
            .create_job(
                organization=organization,
                created_by=created_by,
                job_type=(
                    "DATA_MIGRATION_IMPORT"
                ),
                payload={
                    "batch_id":
                        str(batch.id),
                },
                idempotency_key=(
                    "DATA_MIGRATION_IMPORT:"
                    f"{batch.id}"
                ),
            )
        )

        (
            MigrationBatchRepository
            .set_job(
                batch=batch,
                job_id=job.id,
            )
        )

        return {
            "batch": batch,
            "job": job,
        }