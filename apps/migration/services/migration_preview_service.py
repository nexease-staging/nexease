from apps.core.repositories.background_upload_repository import (
    BackgroundUploadRepository,
)
from apps.migration.services.migration_batch_service import (
    MigrationBatchService,
)
from apps.migration.services.migration_file_parser import (
    MigrationFileParser,
)
from apps.migration.services.migration_mapping_service import (
    MigrationMappingService,
)
from apps.migration.services.migration_row_validation_service import (
    MigrationRowValidationService,
)


class MigrationPreviewError(
    ValueError,
):
    pass


class MigrationPreviewService:

    @classmethod
    def validate_batch(
        cls,
        *,
        batch,
        organization,
    ):
        # ==================================================
        # BASIC CONTEXT
        # ==================================================

        if batch is None:
            raise MigrationPreviewError(
                "Migration batch is required."
            )

        if organization is None:
            raise MigrationPreviewError(
                "Organization is required."
            )

        if (
            batch.organization
            !=
            organization
        ):
            raise MigrationPreviewError(
                "Migration batch does not belong "
                "to this organization."
            )

        if batch.status != "UPLOADED":
            raise MigrationPreviewError(
                "Migration batch must be in "
                "UPLOADED status."
            )

        upload_id = str(
            batch.upload_id or ""
        ).strip()

        if not upload_id:
            raise MigrationPreviewError(
                "Migration batch does not have "
                "an upload."
            )

        # ==================================================
        # TENANT-SCOPED UPLOAD
        # ==================================================

        upload = (
            BackgroundUploadRepository
            .get_by_id(
                organization=organization,
                upload_id=upload_id,
            )
        )

        if upload is None:
            raise MigrationPreviewError(
                "Migration upload was not found."
            )

        if upload.purpose != "DATA_MIGRATION":
            raise MigrationPreviewError(
                "Upload is not a data "
                "migration file."
            )

        if upload.status != "AVAILABLE":
            raise MigrationPreviewError(
                "Migration upload is not "
                "available."
            )

        if not upload.content:
            raise MigrationPreviewError(
                "Migration upload is empty."
            )

        # ==================================================
        # COMPLETE FILE PARSE
        # ==================================================

        parsed = (
            MigrationFileParser
            .read_rows(
                filename=upload.filename,
                content=upload.content,
            )
        )

        source_columns = (
            parsed["columns"]
        )

        source_rows = (
            parsed["rows"]
        )

        # ==================================================
        # MAPPING
        # ==================================================

        mapping = dict(
            batch.mapping
            or
            {}
        )

        # ==================================================
        # AUTOMATIC MAPPING
        # ==================================================

        mapping = {**MigrationMappingService.suggest_mapping(migration_type=batch.migration_type, source_columns=source_columns), **mapping}

        mapping_validation = (
            MigrationMappingService
            .validate_mapping(
                migration_type=(
                    batch.migration_type
                ),
                source_columns=(
                    source_columns
                ),
                mapping=mapping,
            )
        )

        if not mapping_validation[
            "valid"
        ]:
            raise MigrationPreviewError(
                "Migration mapping is invalid."
            )

        mapped_rows = (
            MigrationMappingService
            .apply_mapping(
                rows=source_rows,
                mapping=mapping,
            )
        )

        # ==================================================
        # START VALIDATION
        # ==================================================

        MigrationBatchService.start_validation(
            batch=batch,
        )

        batch.status = "VALIDATING"

        try:
            validation = (
                MigrationRowValidationService
                .validate_rows(
                    organization=organization,
                    migration_type=(
                        batch.migration_type
                    ),
                    rows=mapped_rows,
                    skip_duplicates=bool(
                        (
                            getattr(
                                batch,
                                "options",
                                None,
                            )
                            or {}
                        ).get(
                            "skip_duplicates",
                            False,
                        )
                    ),
                )
            )

        except Exception as exc:
            MigrationBatchService.fail_validation(
                batch=batch,
                error_summary=str(exc),
            )

            raise

        # ==================================================
        # COMPLETE VALIDATION
        # ==================================================

        summary = {
            "migration_type":
                validation[
                    "migration_type"
                ],
            "total_rows":
                validation[
                    "total_rows"
                ],
            "valid_rows":
                validation[
                    "valid_rows"
                ],
            "invalid_rows":
                validation[
                    "invalid_rows"
                ],
            "can_import":
                validation[
                    "can_import"
                ],
            "columns":
                source_columns,
            "mapping":
                mapping,
            "sheet_name":
                parsed.get(
                    "sheet_name"
                ),
            "rows":
                validation[
                    "rows"
                ],
        }

        MigrationBatchService.complete_validation(
            batch=batch,
            total_rows=(
                validation[
                    "total_rows"
                ]
            ),
            valid_rows=(
                validation[
                    "valid_rows"
                ]
            ),
            invalid_rows=(
                validation[
                    "invalid_rows"
                ]
            ),
            validation_result=summary,
        )

        return summary