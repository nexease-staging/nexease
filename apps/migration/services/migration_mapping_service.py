from apps.migration.services.migration_schema_service import (
    MigrationSchemaService,
)


class MigrationMappingError(
    ValueError,
):
    pass


class MigrationMappingService:

    @staticmethod
    def normalize(
        value,
    ):
        return " ".join(
            str(value or "")
            .strip()
            .casefold()
            .replace("_", " ")
            .replace("-", " ")
            .split()
        )

    @classmethod
    def suggest_mapping(
        cls,
        *,
        migration_type,
        source_columns,
    ):
        if not isinstance(
            source_columns,
            (
                list,
                tuple,
            ),
        ):
            raise MigrationMappingError(
                "Source columns must be "
                "a list or tuple."
            )

        fields = (
            MigrationSchemaService
            .get_fields(
                migration_type
            )
        )

        normalized_sources = {}

        for column in source_columns:
            column = str(
                column or ""
            ).strip()

            if not column:
                continue

            normalized_sources[
                cls.normalize(column)
            ] = column

        mapping = {}

        for (
            target_field,
            definition,
        ) in fields.items():

            candidates = [
                target_field,
                definition.get(
                    "label",
                    "",
                ),
                *definition.get(
                    "aliases",
                    (),
                ),
            ]

            matched_column = None

            for candidate in candidates:
                normalized_candidate = (
                    cls.normalize(
                        candidate
                    )
                )

                if (
                    normalized_candidate
                    in normalized_sources
                ):
                    matched_column = (
                        normalized_sources[
                            normalized_candidate
                        ]
                    )
                    break

            if matched_column:
                mapping[
                    target_field
                ] = matched_column

        return mapping

    @classmethod
    def validate_mapping(
        cls,
        *,
        migration_type,
        source_columns,
        mapping,
    ):
        if not isinstance(
            mapping,
            dict,
        ):
            raise MigrationMappingError(
                "Mapping must be a dictionary."
            )

        fields = (
            MigrationSchemaService
            .get_fields(
                migration_type
            )
        )

        source_lookup = {
            cls.normalize(column):
                str(column).strip()
            for column in source_columns
        }

        errors = []

        for (
            target_field,
            source_column,
        ) in mapping.items():

            if target_field not in fields:
                errors.append(
                    {
                        "field":
                            target_field,
                        "code":
                            "UNKNOWN_TARGET_FIELD",
                        "message":
                            (
                                "Unknown target "
                                "field."
                            ),
                    }
                )

                continue

            normalized_source = (
                cls.normalize(
                    source_column
                )
            )

            if (
                normalized_source
                not in source_lookup
            ):
                errors.append(
                    {
                        "field":
                            target_field,
                        "code":
                            "SOURCE_COLUMN_NOT_FOUND",
                        "message":
                            (
                                "Mapped source "
                                "column was not "
                                "found in the file."
                            ),
                    }
                )

        required_fields = (
            MigrationSchemaService
            .required_fields(
                migration_type
            )
        )

        for field_name in required_fields:
            source_column = mapping.get(
                field_name
            )

            if not str(
                source_column or ""
            ).strip():
                errors.append(
                    {
                        "field":
                            field_name,
                        "code":
                            "REQUIRED_MAPPING_MISSING",
                        "message":
                            (
                                "Required field "
                                "has not been mapped."
                            ),
                    }
                )

        used_sources = {}

        for (
            target_field,
            source_column,
        ) in mapping.items():

            normalized_source = (
                cls.normalize(
                    source_column
                )
            )

            if not normalized_source:
                continue

            used_sources.setdefault(
                normalized_source,
                [],
            ).append(
                target_field
            )

        for (
            source_column,
            target_fields,
        ) in used_sources.items():

            if len(target_fields) <= 1:
                continue

            errors.append(
                {
                    "field": None,
                    "code":
                        "SOURCE_COLUMN_REUSED",
                    "message": (
                        "One source column "
                        "cannot be mapped to "
                        "multiple destination "
                        "fields."
                    ),
                    "source_column":
                        source_column,
                    "target_fields":
                        target_fields,
                }
            )

        return {
            "valid":
                not errors,
            "errors":
                errors,
        }

    @classmethod
    def apply_mapping(
        cls,
        *,
        rows,
        mapping,
    ):
        if not isinstance(
            rows,
            (
                list,
                tuple,
            ),
        ):
            raise MigrationMappingError(
                "Rows must be a list or tuple."
            )

        if not isinstance(
            mapping,
            dict,
        ):
            raise MigrationMappingError(
                "Mapping must be a dictionary."
            )

        mapped_rows = []

        for row in rows:
            if not isinstance(
                row,
                dict,
            ):
                raise MigrationMappingError(
                    "Each source row must "
                    "be a dictionary."
                )

            mapped_row = {}

            for (
                target_field,
                source_column,
            ) in mapping.items():
                mapped_row[
                    target_field
                ] = row.get(
                    source_column
                )

            mapped_rows.append(
                mapped_row
            )

        return mapped_rows