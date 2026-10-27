from apps.core.services.background_job_executor import (
    BackgroundJobExecutor,
)
from apps.migration.services.migration_api_service import (
    MigrationAPIService,
)


def _get_batch_id(
    *,
    job,
):
    payload = job.payload or {}

    batch_id = str(
        payload.get(
            "batch_id",
            "",
        )
        or
        ""
    ).strip()

    if not batch_id:
        raise ValueError(
            "Migration batch ID is required."
        )

    return batch_id


def execute_migration_validation(
    *,
    job,
):
    batch_id = _get_batch_id(
        job=job,
    )

    result = (
        MigrationAPIService
        .validate_batch(
            organization=job.organization,
            batch_id=batch_id,
        )
    )

    batch = result["batch"]
    validation = result["validation"]

    return {
        "batch_id": str(batch.id),
        "status": str(batch.status),
        "migration_type": str(
            batch.migration_type
        ),
        "total_rows": validation.get(
            "total_rows",
            0,
        ),
        "valid_rows": validation.get(
            "valid_rows",
            0,
        ),
        "invalid_rows": validation.get(
            "invalid_rows",
            0,
        ),
        "can_import": bool(
            validation.get(
                "can_import",
                False,
            )
        ),
    }


def execute_migration_import(
    *,
    job,
):
    batch_id = _get_batch_id(
        job=job,
    )

    result = (
        MigrationAPIService
        .import_batch(
            organization=job.organization,
            batch_id=batch_id,
        )
    )

    if not isinstance(
        result,
        dict,
    ):
        raise ValueError(
            "Migration import returned "
            "an invalid result."
        )

    return result


def register_migration_background_jobs():
    registered = set(
        BackgroundJobExecutor
        .registered_job_types()
    )

    if (
        "DATA_MIGRATION_VALIDATE"
        not in registered
    ):
        BackgroundJobExecutor.register(
            "DATA_MIGRATION_VALIDATE",
            execute_migration_validation,
        )

    if (
        "DATA_MIGRATION_IMPORT"
        not in registered
    ):
        BackgroundJobExecutor.register(
            "DATA_MIGRATION_IMPORT",
            execute_migration_import,
        )