from pathlib import Path

from apps.core.repositories.background_upload_repository import (
    BackgroundUploadRepository,
)


class BackgroundUploadService:

    MAX_DATA_MIGRATION_SIZE = (
        10 * 1024 * 1024
    )

    ALLOWED_DATA_MIGRATION_EXTENSIONS = {
        ".csv",
        ".xlsx",
    }
    MAX_BANK_STATEMENT_SIZE = (
        5 * 1024 * 1024
    )

    ALLOWED_BANK_STATEMENT_EXTENSIONS = {
        ".csv",
        ".xlsx",
    }

    @staticmethod
    def create_data_migration_upload(
        *,
        organization,
        uploaded_by,
        uploaded_file,
    ):
        if organization is None:
            raise ValueError(
                "Organization is required."
            )

        if uploaded_by is None:
            raise ValueError(
                "Uploaded by user is required."
            )

        if uploaded_file is None:
            raise ValueError(
                "Migration file is required."
            )

        filename = str(
            getattr(
                uploaded_file,
                "name",
                "",
            )
            or ""
        ).strip()

        if not filename:
            raise ValueError(
                "Migration filename is required."
            )

        extension = (
            Path(filename)
            .suffix
            .lower()
        )

        if (
            extension
            not in
            BackgroundUploadService
            .ALLOWED_DATA_MIGRATION_EXTENSIONS
        ):
            raise ValueError(
                "Only CSV and XLSX migration "
                "files are supported."
            )

        file_size = getattr(
            uploaded_file,
            "size",
            None,
        )

        if (
            file_size is not None
            and file_size
            > BackgroundUploadService
            .MAX_DATA_MIGRATION_SIZE
        ):
            raise ValueError(
                "Migration file cannot "
                "exceed 10 MB."
            )

        content = b"".join(
            uploaded_file.chunks()
        )

        if not content:
            raise ValueError(
                "Migration file is empty."
            )

        if (
            len(content)
            > BackgroundUploadService
            .MAX_DATA_MIGRATION_SIZE
        ):
            raise ValueError(
                "Migration file cannot "
                "exceed 10 MB."
            )

        return (
            BackgroundUploadRepository
            .create(
                organization=organization,
                uploaded_by=uploaded_by,
                purpose="DATA_MIGRATION",
                filename=filename,
                content_type=(
                    getattr(
                        uploaded_file,
                        "content_type",
                        "",
                    )
                    or ""
                ),
                extension=extension,
                content=content,
            )
        )

    @staticmethod
    def store_bank_statement(
        *,
        organization,
        uploaded_by,
        uploaded_file,
    ):
        if organization is None:
            raise ValueError(
                "Organization is required."
            )

        if uploaded_by is None:
            raise ValueError(
                "Uploaded by user is required."
            )

        if uploaded_file is None:
            raise ValueError(
                "A CSV or XLSX file is required."
            )

        filename = str(
            uploaded_file.name or ""
        ).strip()

        if not filename:
            raise ValueError(
                "Uploaded filename is required."
            )

        extension = (
            Path(filename)
            .suffix
            .lower()
        )

        if (
            extension
            not in
            BackgroundUploadService
            .ALLOWED_BANK_STATEMENT_EXTENSIONS
        ):
            raise ValueError(
                "Only CSV and XLSX bank "
                "statement files are supported."
            )

        if (
            uploaded_file.size
            > BackgroundUploadService
            .MAX_BANK_STATEMENT_SIZE
        ):
            raise ValueError(
                "Bank statement file cannot "
                "exceed 5 MB."
            )

        content = b"".join(
            uploaded_file.chunks()
        )

        if not content:
            raise ValueError(
                "Bank statement file is empty."
            )

        if (
            len(content)
            > BackgroundUploadService
            .MAX_BANK_STATEMENT_SIZE
        ):
            raise ValueError(
                "Bank statement file cannot "
                "exceed 5 MB."
            )

        return (
            BackgroundUploadRepository
            .create(
                organization=organization,
                uploaded_by=uploaded_by,
                purpose=(
                    "BANK_STATEMENT_IMPORT"
                ),
                filename=filename,
                content_type=(
                    uploaded_file.content_type
                    or ""
                ),
                extension=extension,
                content=content,
            )
        )