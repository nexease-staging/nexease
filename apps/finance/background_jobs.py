import tempfile
from pathlib import Path
from apps.finance.services.document_api_service import (
    DocumentAPIService,
)
from apps.core.repositories.background_upload_repository import (
    BackgroundUploadRepository,
)
from apps.core.services.background_job_executor import (
    BackgroundJobExecutor,
)
from apps.finance.importers.bank_statement_parser import (
    BankStatementParser,
)
from apps.finance.services.bank_statement_api_service import (
    BankStatementAPIService,
)


def execute_bank_statement_import(
    *,
    job,
):
    payload = job.payload or {}

    upload_id = str(
        payload.get(
            "upload_id",
            "",
        )
    ).strip()

    if not upload_id:
        raise ValueError(
            "Bank statement upload ID "
            "is required."
        )

    upload = (
        BackgroundUploadRepository
        .get_by_id(
            organization=job.organization,
            upload_id=upload_id,
        )
    )

    if upload is None:
        raise LookupError(
            "Bank statement upload "
            "was not found."
        )

    if (
        upload.purpose
        != "BANK_STATEMENT_IMPORT"
    ):
        raise ValueError(
            "Upload is not a bank "
            "statement import."
        )

    #
    # Critical idempotency guard:
    #
    # If a previous execution already created
    # the statement but the worker crashed
    # before marking the BackgroundJob
    # successful, simply return the stored
    # result rather than importing again.
    #
    if upload.status == "CONSUMED":
        result = upload.result or {}

        if result.get(
            "bank_statement_id"
        ):
            return result

        raise ValueError(
            "Bank statement upload was "
            "already consumed."
        )

    if upload.status != "AVAILABLE":
        raise ValueError(
            "Bank statement upload is "
            "not available for processing."
        )

    temporary_path = None

    try:
        with tempfile.NamedTemporaryFile(
            suffix=upload.extension,
            delete=False,
        ) as temporary_file:
            temporary_path = Path(
                temporary_file.name
            )

            temporary_file.write(
                bytes(
                    upload.content
                )
            )

        if upload.extension == ".csv":
            raw_lines = (
                BankStatementParser
                .parse_csv(
                    str(
                        temporary_path
                    )
                )
            )

            source_type = "CSV"

        elif upload.extension == ".xlsx":
            raw_lines = (
                BankStatementParser
                .parse_xlsx(
                    str(
                        temporary_path
                    )
                )
            )

            source_type = "XLSX"

        else:
            raise ValueError(
                "Unsupported bank statement "
                "file extension."
            )

        statement = (
            BankStatementAPIService
            .create_statement(
                user=job.created_by,
                organization=job.organization,

                bank_account_id=(
                    payload.get(
                        "bank_account_id"
                    )
                ),

                statement_start_date=(
                    payload.get(
                        "statement_start_date"
                    )
                ),

                statement_end_date=(
                    payload.get(
                        "statement_end_date"
                    )
                ),

                opening_balance=(
                    payload.get(
                        "opening_balance"
                    )
                ),

                closing_balance=(
                    payload.get(
                        "closing_balance"
                    )
                ),

                raw_lines=raw_lines,
                source_type=source_type,
                source_filename=(
                    upload.filename
                ),
            )
        )

        result = {
            "bank_statement_id":
                str(statement.id),
        }

        (
            BackgroundUploadRepository
            .mark_consumed(
                upload=upload,
                result=result,
            )
        )

        return result

    finally:
        if (
            temporary_path
            and temporary_path.exists()
        ):
            temporary_path.unlink(
                missing_ok=True
            )

def execute_document_email(
    *,
    job,
):
    payload = job.payload or {}

    document_type = str(
        payload.get(
            "document_type",
            "",
        )
    ).strip()

    document_id = str(
        payload.get(
            "document_id",
            "",
        )
    ).strip()

    if not document_type:
        raise ValueError(
            "Document type is required."
        )

    if not document_id:
        raise ValueError(
            "Document ID is required."
        )

    result = (
        DocumentAPIService
        .send_email(
            user=job.created_by,
            organization=job.organization,
            document_type=document_type,
            document_id=document_id,
            recipient_email=(
                payload.get(
                    "recipient_email"
                )
            ),
            subject=(
                payload.get(
                    "subject"
                )
            ),
            message=(
                payload.get(
                    "message"
                )
            ),
            background_job_key=(
                job.idempotency_key
            ),
        )
    )

    if result is None:
        raise LookupError(
            "Document was not found."
        )

    delivery = result.get(
        "delivery"
    )

    return {
        "document_type": document_type,
        "document_id": document_id,
        "recipient": (
            delivery.recipient
            if delivery
            else result.get(
                "recipient"
            )
        ),
        "sent_count": result.get(
            "sent_count"
        ),
        "delivery_id": (
            str(delivery.id)
            if delivery
            else None
        ),
        "delivery_status": (
            delivery.status
            if delivery
            else None
        ),
    }

def register_finance_background_jobs():
    registered = set(
        BackgroundJobExecutor
        .registered_job_types()
    )

    if (
        "BANK_STATEMENT_IMPORT"
        not in registered
    ):
        BackgroundJobExecutor.register(
            "BANK_STATEMENT_IMPORT",
            execute_bank_statement_import,
        )

    if (
        "DOCUMENT_EMAIL"
        not in registered
    ):
        BackgroundJobExecutor.register(
            "DOCUMENT_EMAIL",
            execute_document_email,
        )