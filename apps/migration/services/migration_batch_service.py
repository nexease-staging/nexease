from apps.migration.repositories.migration_batch_repository import (
    MigrationBatchRepository,
)
from datetime import datetime

class MigrationBatchService:

    ALLOWED_SOURCE_SYSTEMS = {
        "GENERIC",
        "ZOHO_INVENTORY",
        "TALLY",
        "BUSY",
        "QUICKBOOKS",
        "ODOO",
        "SAP",
        "OTHER",
    }

    ALLOWED_MIGRATION_TYPES = {
        "CATEGORIES",
        "PRODUCTS",
        "CUSTOMERS",
        "SUPPLIERS",
        "WAREHOUSES",
        "INVENTORY",
        "SALES_ORDERS",
        "INVOICES",
        "CUSTOMER_PAYMENTS",
        "PURCHASE_ORDERS",
        "SALES_INVOICES",
        "GOODS_RECEIPTS",
        "EMPLOYEES", "VENDOR_BILLS",
        "SUPPLIER_PAYMENTS",
    }

    @staticmethod
    def create_batch(
        *,
        organization,
        created_by,
        source_system,
        migration_type,
        mapping=None,
        options=None,
    ):
        if organization is None:
            raise ValueError(
                "Organization is required."
            )

        if created_by is None:
            raise ValueError(
                "Created by user is required."
            )

        if not created_by.is_active:
            raise ValueError(
                "User is inactive."
            )

        if (
            str(created_by.organization.id)
            !=
            str(organization.id)
        ):
            raise PermissionError(
                "User does not belong to "
                "this organization."
            )

        source_system = (
            str(source_system or "")
            .strip()
            .upper()
        )

        if (
            source_system
            not in
            MigrationBatchService
            .ALLOWED_SOURCE_SYSTEMS
        ):
            raise ValueError(
                "Invalid migration source system."
            )

        migration_type = (
            str(migration_type or "")
            .strip()
            .upper()
        )

        if (
            migration_type
            not in
            MigrationBatchService
            .ALLOWED_MIGRATION_TYPES
        ):
            raise ValueError(
                "Invalid migration type."
            )

        if (
            mapping is not None
            and not isinstance(
                mapping,
                dict,
            )
        ):
            raise ValueError(
                "Migration mapping must "
                "be a dictionary."
            )

        if (
            options is not None
            and not isinstance(
                options,
                dict,
            )
        ):
            raise ValueError(
                "Migration options must "
                "be a dictionary."
            )

        return (
            MigrationBatchRepository
            .create(
                organization=organization,
                created_by=created_by,
                source_system=source_system,
                migration_type=migration_type,
                mapping=mapping,
                options=options,
            )
        )

    @staticmethod
    def get_batch(
        *,
        organization,
        batch_id,
    ):
        if organization is None:
            raise ValueError(
                "Organization is required."
            )

        if not batch_id:
            raise ValueError(
                "Migration batch ID is required."
            )

        return (
            MigrationBatchRepository
            .get_by_id(
                organization=organization,
                batch_id=batch_id,
            )
        )

    @staticmethod
    def attach_upload(
        *,
        batch,
        upload_id,
    ):
        if batch is None:
            raise ValueError(
                "Migration batch is required."
            )

        if batch.status != "CREATED":
            raise ValueError(
                "Upload can only be attached "
                "to a newly created migration."
            )

        upload_id = str(
            upload_id or ""
        ).strip()

        if not upload_id:
            raise ValueError(
                "Upload ID is required."
            )

        return (
            MigrationBatchRepository
            .set_upload(
                batch=batch,
                upload_id=upload_id,
            )
        )

    @staticmethod
    def start_validation(
        *,
        batch,
    ):
        if batch is None:
            raise ValueError(
                "Migration batch is required."
            )

        if batch.status != "UPLOADED":
            raise ValueError(
                "Only an uploaded migration "
                "can be validated."
            )

        return (
            MigrationBatchRepository
            .mark_validating(
                batch=batch,
            )
        )

    @staticmethod
    def complete_validation(
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

        if batch.status != "VALIDATING":
            raise ValueError(
                "Migration is not currently "
                "being validated."
            )

        values = (
            total_rows,
            valid_rows,
            invalid_rows,
        )

        if any(
            not isinstance(value, int)
            or value < 0
            for value in values
        ):
            raise ValueError(
                "Migration row counts must "
                "be non-negative integers."
            )

        if (
            valid_rows + invalid_rows
            != total_rows
        ):
            raise ValueError(
                "Valid and invalid row counts "
                "must equal total rows."
            )

        if (
            validation_result is not None
            and not isinstance(
                validation_result,
                dict,
            )
        ):
            raise ValueError(
                "Validation result must "
                "be a dictionary."
            )

        return (
            MigrationBatchRepository
            .mark_validated(
                batch=batch,
                total_rows=total_rows,
                valid_rows=valid_rows,
                invalid_rows=invalid_rows,
                validation_result=(
                    validation_result
                ),
            )
        )

    @staticmethod
    def fail_validation(
        *,
        batch,
        error_summary,
    ):
        if batch is None:
            raise ValueError(
                "Migration batch is required."
            )

        if batch.status != "VALIDATING":
            raise ValueError(
                "Migration batch must be in "
                "VALIDATING status."
            )

        error_summary = str(
            error_summary or ""
        ).strip()

        if not error_summary:
            error_summary = (
                "Migration validation failed."
            )

        return (
            MigrationBatchRepository
            .mark_failed(
                batch=batch,
                error_summary={
                    "message":
                        error_summary,
                    "stage":
                        "VALIDATION",
                },
                expected_status=(
                    "VALIDATING"
                ),
            )
        )

    @staticmethod
    def start_import(
        *,
        batch,
    ):
        if batch is None:
            raise ValueError(
                "Migration batch is required."
            )

        if batch.status != "VALIDATED":
            raise ValueError(
                "Only a validated migration "
                "can be imported."
            )

        if batch.invalid_rows > 0:
            raise ValueError(
                "Migration contains invalid rows. "
                "Resolve validation errors before "
                "starting the import."
            )

        return (
            MigrationBatchRepository
            .mark_importing(
                batch=batch,
            )
        )

    @staticmethod
    def complete_import(
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

        if batch.status != "IMPORTING":
            raise ValueError(
                "Migration is not currently "
                "being imported."
            )

        values = (
            imported_rows,
            skipped_rows,
            failed_rows,
        )

        if any(
            not isinstance(value, int)
            or value < 0
            for value in values
        ):
            raise ValueError(
                "Import row counts must "
                "be non-negative integers."
            )

        if (
            imported_rows
            + skipped_rows
            + failed_rows
            > batch.valid_rows
        ):
            raise ValueError(
                "Import row counts cannot "
                "exceed validated rows."
            )

        if (
            import_result is not None
            and not isinstance(
                import_result,
                dict,
            )
        ):
            raise ValueError(
                "Import result must "
                "be a dictionary."
            )

        return (
            MigrationBatchRepository
            .mark_completed(
                batch=batch,
                imported_rows=imported_rows,
                skipped_rows=skipped_rows,
                failed_rows=failed_rows,
                import_result=import_result,
            )
        )

    @staticmethod
    def fail_import(
        *,
        batch,
        error_summary,
    ):
        if batch is None:
            raise ValueError(
                "Migration batch is required."
            )

        if batch.status != "IMPORTING":
            raise ValueError(
                "Migration batch must be in "
                "IMPORTING status."
            )

        error_summary = str(
            error_summary or ""
        ).strip()

        if not error_summary:
            error_summary = (
                "Migration import failed."
            )

        return (
            MigrationBatchRepository
            .mark_failed(
                batch=batch,
                error_summary={
                    "message":
                        error_summary,
                    "stage":
                        "IMPORT",
                },
                expected_status=(
                    "IMPORTING"
                ),
            )
        )