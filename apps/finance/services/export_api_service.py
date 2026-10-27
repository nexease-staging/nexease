import csv
from io import BytesIO, StringIO
from datetime import date, datetime
from decimal import Decimal

from openpyxl import Workbook

from apps.finance.api.v1.serializers import (
    FinanceAuditAPISerializer,
    GeneralLedgerAPISerializer,
    TrialBalanceAPISerializer,
    CashFlowReportAPISerializer,
)
from apps.finance.services.accounting_report_api_service import (
    AccountingReportAPIService,
)
from apps.finance.services.financial_report_api_service import (
    FinancialReportAPIService,
)


class ExportAPIValidationError(
    ValueError
):

    def __init__(
        self,
        *,
        message="Export validation failed.",
        details=None,
    ):
        super().__init__(
            message
        )

        self.message = message
        self.details = details or {}


class ExportAPIService:

    SUPPORTED_FORMATS = {
        "csv",
        "xlsx",
    }

    RESOURCE_PERMISSIONS = {
        "GENERAL_LEDGER":
            "general_ledger.read",

        "TRIAL_BALANCE":
            "trial_balance.read",

        "CASH_FLOW":
            "bank_transactions.read",

        "FINANCE_AUDIT":
            "bank_transactions.read",
    }

    @staticmethod
    def _raise_field_error(
        field,
        message,
    ):
        raise (
            ExportAPIValidationError(
                details={
                    field: [
                        message,
                    ],
                },
            )
        )

    @staticmethod
    def normalize_resource_type(
        value,
    ):
        if (
            not isinstance(
                value,
                str,
            )
            or
            not value.strip()
        ):
            (
                ExportAPIService
                ._raise_field_error(
                    "resource_type",
                    "Resource type is required.",
                )
            )

        normalized = (
            value
            .strip()
            .replace("-", "_")
            .upper()
        )

        if (
            normalized
            not in
            ExportAPIService
            .RESOURCE_PERMISSIONS
        ):
            (
                ExportAPIService
                ._raise_field_error(
                    "resource_type",
                    (
                        "Unsupported export "
                        "resource type."
                    ),
                )
            )

        return normalized

    @staticmethod
    def normalize_format(
        value,
    ):
        normalized = (
            str(
                value
                or
                "csv"
            )
            .strip()
            .lower()
        )

        if (
            normalized
            not in
            ExportAPIService
            .SUPPORTED_FORMATS
        ):
            (
                ExportAPIService
                ._raise_field_error(
                    "format",
                    (
                        "Export format must be "
                        "csv or xlsx."
                    ),
                )
            )

        return normalized

    @staticmethod
    def get_permission(
        resource_type,
    ):
        normalized = (
            ExportAPIService
            .normalize_resource_type(
                resource_type
            )
        )

        return (
            ExportAPIService
            .RESOURCE_PERMISSIONS[
                normalized
            ]
        )

    @staticmethod
    def _normalize_cell(
        value,
    ):
        if value is None:
            return ""

        if isinstance(
            value,
            Decimal,
        ):
            return str(
                value
            )

        if isinstance(
            value,
            (
                datetime,
                date,
            ),
        ):
            return (
                value
                .isoformat()
            )

        if isinstance(
            value,
            bool,
        ):
            return (
                "true"
                if value
                else "false"
            )

        return str(
            value
        )

    @staticmethod
    def _flatten(
        value,
        *,
        prefix="",
    ):
        row = {}

        if isinstance(
            value,
            dict,
        ):
            for key, item in (
                value.items()
            ):
                column = (
                    f"{prefix}.{key}"
                    if prefix
                    else str(key)
                )

                if isinstance(
                    item,
                    dict,
                ):
                    row.update(
                        ExportAPIService
                        ._flatten(
                            item,
                            prefix=column,
                        )
                    )

                elif isinstance(
                    item,
                    list,
                ):
                    row[
                        column
                    ] = "; ".join(
                        ExportAPIService
                        ._normalize_cell(
                            entry
                        )
                        for entry in item
                    )

                else:
                    row[
                        column
                    ] = (
                        ExportAPIService
                        ._normalize_cell(
                            item
                        )
                    )

            return row

        row[
            prefix
            or
            "value"
        ] = (
            ExportAPIService
            ._normalize_cell(
                value
            )
        )

        return row

    @staticmethod
    def _rows_from_serialized(
        serialized,
    ):
        if isinstance(
            serialized,
            list,
        ):
            return [
                (
                    ExportAPIService
                    ._flatten(
                        item
                    )
                    if isinstance(
                        item,
                        dict,
                    )
                    else {
                        "value": (
                            ExportAPIService
                            ._normalize_cell(
                                item
                            )
                        ),
                    }
                )
                for item in serialized
            ]

        if isinstance(
            serialized,
            dict,
        ):
            list_fields = [
                (
                    key,
                    value,
                )
                for key, value in (
                    serialized.items()
                )
                if isinstance(
                    value,
                    list,
                )
            ]

            if (
                len(
                    list_fields
                )
                == 1
            ):
                list_key, items = (
                    list_fields[
                        0
                    ]
                )

                metadata = {
                    key: value
                    for key, value in (
                        serialized.items()
                    )
                    if key != list_key
                }

                rows = []

                for item in items:
                    combined = {}

                    combined.update(
                        ExportAPIService
                        ._flatten(
                            metadata
                        )
                    )

                    if isinstance(
                        item,
                        dict,
                    ):
                        combined.update(
                            ExportAPIService
                            ._flatten(
                                item
                            )
                        )

                    else:
                        combined[
                            list_key
                        ] = (
                            ExportAPIService
                            ._normalize_cell(
                                item
                            )
                        )

                    rows.append(
                        combined
                    )

                if rows:
                    return rows

            return [
                ExportAPIService
                ._flatten(
                    serialized
                )
            ]

        return [
            {
                "value": (
                    ExportAPIService
                    ._normalize_cell(
                        serialized
                    )
                ),
            }
        ]

    @staticmethod
    def _build_csv(
        rows,
    ):
        output = StringIO(
            newline=""
        )

        headers = []

        for row in rows:
            for key in row:
                if key not in headers:
                    headers.append(
                        key
                    )

        writer = csv.DictWriter(
            output,
            fieldnames=headers,
            extrasaction="ignore",
        )

        writer.writeheader()

        for row in rows:
            writer.writerow(
                {
                    header: row.get(
                        header,
                        "",
                    )
                    for header in headers
                }
            )

        content = (
            output
            .getvalue()
            .encode(
                "utf-8-sig"
            )
        )

        return (
            content,
            "text/csv; charset=utf-8",
        )

    @staticmethod
    def _build_xlsx(
        rows,
        *,
        sheet_name,
    ):
        workbook = Workbook()

        worksheet = workbook.active

        worksheet.title = (
            sheet_name[
                :31
            ]
        )

        headers = []

        for row in rows:
            for key in row:
                if key not in headers:
                    headers.append(
                        key
                    )

        worksheet.append(
            headers
        )

        for row in rows:
            worksheet.append(
                [
                    row.get(
                        header,
                        "",
                    )
                    for header in headers
                ]
            )

        output = BytesIO()

        workbook.save(
            output
        )

        content = (
            output
            .getvalue()
        )

        return (
            content,
            (
                "application/vnd.openxmlformats-"
                "officedocument.spreadsheetml.sheet"
            ),
        )

    @staticmethod
    def _get_serialized_report(
        *,
        user,
        organization,
        resource_type,
        parameters,
    ):
        if (
            resource_type
            ==
            "GENERAL_LEDGER"
        ):
            account_id = (
                parameters.get(
                    "account_id"
                )
            )

            if not account_id:
                (
                    ExportAPIService
                    ._raise_field_error(
                        "account_id",
                        (
                            "This field is required "
                            "for general ledger export."
                        ),
                    )
                )

            result = (
                AccountingReportAPIService
                .get_general_ledger(
                    user=user,
                    organization=organization,
                    account_id=account_id,
                    start_date=(
                        parameters.get(
                            "start_date"
                        )
                    ),
                    end_date=(
                        parameters.get(
                            "end_date"
                        )
                    ),
                )
            )

            return (
                GeneralLedgerAPISerializer
                .serialize(
                    result
                )
            )

        if (
            resource_type
            ==
            "TRIAL_BALANCE"
        ):
            result = (
                AccountingReportAPIService
                .get_trial_balance(
                    user=user,
                    organization=organization,
                    as_of_date=(
                        parameters.get(
                            "as_of_date"
                        )
                    ),
                    include_zero_balances=(
                        parameters.get(
                            "include_zero_balances"
                        )
                    ),
                )
            )

            return (
                TrialBalanceAPISerializer
                .serialize(
                    result
                )
            )

        if (
            resource_type
            ==
            "CASH_FLOW"
        ):
            result = (
                FinancialReportAPIService
                .get_cash_flow(
                    user=user,
                    organization=organization,
                    start_date=(
                        parameters.get(
                            "start_date"
                        )
                    ),
                    end_date=(
                        parameters.get(
                            "end_date"
                        )
                    ),
                    bank_account_id=(
                        parameters.get(
                            "bank_account_id"
                        )
                    ),
                )
            )

            return (
                CashFlowReportAPISerializer
                .serialize(
                    result
                )
            )

        if (
            resource_type
            ==
            "FINANCE_AUDIT"
        ):
            result = (
                FinancialReportAPIService
                .get_finance_audit(
                    user=user,
                    organization=organization,
                )
            )

            return (
                FinanceAuditAPISerializer
                .serialize(
                    result
                )
            )

        (
            ExportAPIService
            ._raise_field_error(
                "resource_type",
                (
                    "Unsupported export "
                    "resource type."
                ),
            )
        )

    @staticmethod
    def export(
        *,
        user,
        organization,
        resource_type,
        export_format,
        parameters=None,
    ):
        normalized_resource = (
            ExportAPIService
            .normalize_resource_type(
                resource_type
            )
        )

        normalized_format = (
            ExportAPIService
            .normalize_format(
                export_format
            )
        )

        parameters = (
            parameters
            or
            {}
        )

        serialized = (
            ExportAPIService
            ._get_serialized_report(
                user=user,
                organization=organization,
                resource_type=(
                    normalized_resource
                ),
                parameters=parameters,
            )
        )

        rows = (
            ExportAPIService
            ._rows_from_serialized(
                serialized
            )
        )

        if not rows:
            rows = [
                {
                    "message":
                        "No data available.",
                }
            ]

        filename_base = (
            normalized_resource
            .lower()
        )

        if (
            normalized_format
            ==
            "csv"
        ):
            content, content_type = (
                ExportAPIService
                ._build_csv(
                    rows
                )
            )

        else:
            content, content_type = (
                ExportAPIService
                ._build_xlsx(
                    rows,
                    sheet_name=(
                        normalized_resource
                    ),
                )
            )

        filename = (
            f"{filename_base}."
            f"{normalized_format}"
        )

        return {
            "resource_type":
                normalized_resource,

            "format":
                normalized_format,

            "filename":
                filename,

            "content_type":
                content_type,

            "content":
                content,

            "size":
                len(
                    content
                ),
        }