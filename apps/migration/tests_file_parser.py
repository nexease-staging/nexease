from io import BytesIO
from unittest import TestCase

from openpyxl import Workbook

from apps.migration.services.migration_file_parser import (
    MigrationFileParser,
    MigrationFileParserError,
)


class MigrationFileParserTestCase(
    TestCase,
):

    def test_parse_csv(
        self,
    ):
        content = (
            "SKU,Product Name,Unit\n"
            "P-001,Keyboard,PCS\n"
            "P-002,Mouse,PCS\n"
        ).encode("utf-8")

        result = (
            MigrationFileParser.parse(
                filename="products.csv",
                content=content,
            )
        )

        self.assertEqual(
            result["extension"],
            ".csv",
        )

        self.assertEqual(
            result["columns"],
            [
                "SKU",
                "Product Name",
                "Unit",
            ],
        )

        self.assertEqual(
            result["total_rows"],
            2,
        )

        self.assertEqual(
            result["sample_rows"][0][
                "SKU"
            ],
            "P-001",
        )

    def test_csv_ignores_blank_rows(
        self,
    ):
        content = (
            "SKU,Name\n"
            "P-001,Keyboard\n"
            ",\n"
            "P-002,Mouse\n"
        ).encode("utf-8")

        result = (
            MigrationFileParser.parse(
                filename="products.csv",
                content=content,
            )
        )

        self.assertEqual(
            result["total_rows"],
            2,
        )

    def test_csv_normalizes_headers(
        self,
    ):
        content = (
            " SKU , Product   Name \n"
            "P-001,Keyboard\n"
        ).encode("utf-8")

        result = (
            MigrationFileParser.parse(
                filename="products.csv",
                content=content,
            )
        )

        self.assertEqual(
            result["columns"],
            [
                "SKU",
                "Product Name",
            ],
        )

    def test_duplicate_headers_rejected(
        self,
    ):
        content = (
            "SKU,sku\n"
            "P-001,P-002\n"
        ).encode("utf-8")

        with self.assertRaises(
            MigrationFileParserError
        ):
            MigrationFileParser.parse(
                filename="products.csv",
                content=content,
            )

    def test_blank_header_rejected(
        self,
    ):
        content = (
            "SKU,,Unit\n"
            "P-001,Keyboard,PCS\n"
        ).encode("utf-8")

        with self.assertRaises(
            MigrationFileParserError
        ):
            MigrationFileParser.parse(
                filename="products.csv",
                content=content,
            )

    def test_unsupported_extension_rejected(
        self,
    ):
        with self.assertRaises(
            MigrationFileParserError
        ):
            MigrationFileParser.parse(
                filename="products.xls",
                content=b"test",
            )

    def test_empty_file_rejected(
        self,
    ):
        with self.assertRaises(
            MigrationFileParserError
        ):
            MigrationFileParser.parse(
                filename="products.csv",
                content=b"",
            )

    def test_parse_xlsx(
        self,
    ):
        workbook = Workbook()
        worksheet = workbook.active

        worksheet.title = "Products"

        worksheet.append(
            [
                "SKU",
                "Product Name",
                "Price",
            ]
        )

        worksheet.append(
            [
                "P-001",
                "Keyboard",
                1200,
            ]
        )

        worksheet.append(
            [
                "P-002",
                "Mouse",
                500,
            ]
        )

        buffer = BytesIO()
        workbook.save(buffer)
        workbook.close()

        result = (
            MigrationFileParser.parse(
                filename="products.xlsx",
                content=buffer.getvalue(),
            )
        )

        self.assertEqual(
            result["sheet_name"],
            "Products",
        )

        self.assertEqual(
            result["total_rows"],
            2,
        )

        self.assertEqual(
            result["sample_rows"][1][
                "Product Name"
            ],
            "Mouse",
        )

    def test_sample_limit(
        self,
    ):
        content = (
            "SKU,Name\n"
            "1,A\n"
            "2,B\n"
            "3,C\n"
            "4,D\n"
        ).encode("utf-8")

        result = (
            MigrationFileParser.parse(
                filename="products.csv",
                content=content,
                sample_limit=2,
            )
        )

        self.assertEqual(
            result["total_rows"],
            4,
        )

        self.assertEqual(
            len(
                result["sample_rows"]
            ),
            2,
        )

    def test_invalid_sample_limit_rejected(
        self,
    ):
        with self.assertRaises(
            MigrationFileParserError
        ):
            MigrationFileParser.parse(
                filename="products.csv",
                content=b"SKU\nP-001\n",
                sample_limit=0,
            )

    def test_read_all_csv_rows(
        self,
    ):
        content = (
            "SKU,Name,Unit\n"
            "ITEM-001,Keyboard,PCS\n"
            "ITEM-002,Mouse,PCS\n"
            "ITEM-003,Monitor,PCS\n"
        ).encode("utf-8")

        result = (
            MigrationFileParser
            .read_rows(
                filename="products.csv",
                content=content,
            )
        )

        self.assertEqual(
            result["columns"],
            [
                "SKU",
                "Name",
                "Unit",
            ],
        )

        self.assertEqual(
            result["total_rows"],
            3,
        )

        self.assertEqual(
            len(result["rows"]),
            3,
        )

        self.assertEqual(
            result["rows"][2]["SKU"],
            "ITEM-003",
        )

        self.assertIsNone(
            result["sheet_name"]
        )

    def test_read_all_xlsx_rows(
        self,
    ):
        from io import BytesIO

        from openpyxl import Workbook

        workbook = Workbook()

        worksheet = workbook.active
        worksheet.title = "Products"

        worksheet.append(
            [
                "SKU",
                "Name",
                "Unit",
            ]
        )

        worksheet.append(
            [
                "ITEM-001",
                "Keyboard",
                "PCS",
            ]
        )

        worksheet.append(
            [
                "ITEM-002",
                "Mouse",
                "PCS",
            ]
        )

        worksheet.append(
            [
                "ITEM-003",
                "Monitor",
                "PCS",
            ]
        )

        buffer = BytesIO()

        workbook.save(buffer)
        workbook.close()

        result = (
            MigrationFileParser
            .read_rows(
                filename="products.xlsx",
                content=buffer.getvalue(),
            )
        )

        self.assertEqual(
            result["total_rows"],
            3,
        )

        self.assertEqual(
            len(result["rows"]),
            3,
        )

        self.assertEqual(
            result["rows"][1]["Name"],
            "Mouse",
        )

        self.assertEqual(
            result["sheet_name"],
            "Products",
        )

    def test_read_rows_not_limited_to_preview_size(
        self,
    ):
        lines = [
            "SKU,Name,Unit",
        ]

        for index in range(1, 51):
            lines.append(
                (
                    f"ITEM-{index:03d},"
                    f"Product {index},"
                    "PCS"
                )
            )

        content = (
            "\n".join(lines)
            .encode("utf-8")
        )

        result = (
            MigrationFileParser
            .read_rows(
                filename="products.csv",
                content=content,
            )
        )

        self.assertEqual(
            result["total_rows"],
            50,
        )

        self.assertEqual(
            len(result["rows"]),
            50,
        )

        self.assertEqual(
            result["rows"][49]["SKU"],
            "ITEM-050",
        )