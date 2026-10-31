from io import BytesIO
from decimal import Decimal

from reportlab.lib import colors
from reportlab.lib.enums import (
    TA_LEFT,
    TA_RIGHT,
    TA_CENTER,
)
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import (
    ParagraphStyle,
    getSampleStyleSheet,
)
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
    KeepTogether,
)

from apps.finance.documents.pdf_utils import (
    PDFUtils,
)


class NumberedCanvas(canvas.Canvas):
    """
    Canvas that adds:
        Page X of Y
    to every page.
    """

    def __init__(
        self,
        *args,
        **kwargs,
    ):
        canvas.Canvas.__init__(
            self,
            *args,
            **kwargs,
        )

        self._saved_page_states = []

    def showPage(
        self,
    ):
        self._saved_page_states.append(
            dict(
                self.__dict__
            )
        )

        self._startPage()

    def save(
        self,
    ):
        page_count = len(
            self._saved_page_states
        )

        for state in (
            self._saved_page_states
        ):

            self.__dict__.update(
                state
            )

            self._draw_page_number(
                page_count
            )

            canvas.Canvas.showPage(
                self
            )

        canvas.Canvas.save(
            self
        )

    def _draw_page_number(
        self,
        page_count,
    ):
        page_number = (
            self._pageNumber
        )

        text = (
            f"Page "
            f"{page_number} "
            f"of "
            f"{page_count}"
        )

        self.setFont(
            "Helvetica",
            8,
        )

        self.drawRightString(
            195 * mm,
            10 * mm,
            text,
        )


class InvoicePDF:

    PAGE_WIDTH, PAGE_HEIGHT = A4

    @staticmethod
    def _safe_decimal(
        value,
    ):
        if value is None:
            return Decimal("0.00")

        return Decimal(
            str(value)
        )

    @staticmethod
    def _product_value(
        product,
        field_name,
        default="",
    ):
        if not product:
            return default

        value = getattr(
            product,
            field_name,
            default,
        )

        if value is None:
            return default

        return value

    @staticmethod
    def _item_value(
        item,
        field_name,
        default=None,
    ):
        value = getattr(
            item,
            field_name,
            default,
        )

        if value is None:
            return default

        return value

    @staticmethod
    def _build_styles():

        styles = (
            getSampleStyleSheet()
        )

        styles.add(
            ParagraphStyle(
                name="InvoiceCompany",
                parent=styles[
                    "Heading1"
                ],
                fontName=(
                    "Helvetica-Bold"
                ),
                fontSize=16,
                leading=19,
                spaceAfter=3,
            )
        )

        styles.add(
            ParagraphStyle(
                name="InvoiceTitle",
                parent=styles[
                    "Heading1"
                ],
                fontName=(
                    "Helvetica-Bold"
                ),
                fontSize=20,
                leading=23,
                alignment=TA_RIGHT,
            )
        )

        styles.add(
            ParagraphStyle(
                name="InvoiceSmall",
                parent=styles[
                    "Normal"
                ],
                fontName="Helvetica",
                fontSize=8.5,
                leading=11,
            )
        )

        styles.add(
            ParagraphStyle(
                name="InvoiceSmallRight",
                parent=styles[
                    "Normal"
                ],
                fontName="Helvetica",
                fontSize=8.5,
                leading=11,
                alignment=TA_RIGHT,
            )
        )

        styles.add(
            ParagraphStyle(
                name="InvoiceSmallCenter",
                parent=styles[
                    "Normal"
                ],
                fontName="Helvetica",
                fontSize=8.5,
                leading=11,
                alignment=TA_CENTER,
            )
        )

        styles.add(
            ParagraphStyle(
                name="InvoiceSection",
                parent=styles[
                    "Normal"
                ],
                fontName=(
                    "Helvetica-Bold"
                ),
                fontSize=9,
                leading=12,
                spaceAfter=3,
            )
        )

        styles.add(
            ParagraphStyle(
                name="InvoiceTable",
                parent=styles[
                    "Normal"
                ],
                fontName="Helvetica",
                fontSize=7.2,
                leading=8.8,
                wordWrap="CJK",
            )
        )

        styles.add(
            ParagraphStyle(
                name="InvoiceTableRight",
                parent=styles[
                    "Normal"
                ],
                fontName="Helvetica",
                fontSize=7.2,
                leading=8.8,
                alignment=TA_RIGHT,
                wordWrap="CJK",
            )
        )

        return styles

    @staticmethod
    def _build_company_header(
        *,
        invoice,
        styles,
    ):

        organization = (
            invoice.organization
        )

        company_lines = [
            Paragraph(
                PDFUtils.safe_text(
                    organization.name
                ),
                styles[
                    "InvoiceCompany"
                ],
            ),
        ]

        company_details = []

        if organization.address:

            company_details.append(
                PDFUtils.safe_text(
                    organization.address
                )
            )

        if organization.country:

            company_details.append(
                PDFUtils.safe_text(
                    organization.country
                )
            )

        if organization.email:

            company_details.append(
                PDFUtils.safe_text(
                    organization.email
                )
            )

        if organization.phone:

            company_details.append(
                PDFUtils.safe_text(
                    organization.phone
                )
            )

        for detail in company_details:

            company_lines.append(
                Paragraph(
                    detail,
                    styles[
                        "InvoiceSmall"
                    ],
                )
            )

        invoice_title = [
            Paragraph(
                "INVOICE",
                styles[
                    "InvoiceTitle"
                ],
            ),
            Spacer(
                1,
                2 * mm,
            ),
            Paragraph(
                (
                    "<b>Invoice #:</b> "
                    f"{invoice.invoice_number}"
                ),
                styles[
                    "InvoiceSmallRight"
                ],
            ),
            Paragraph(
                (
                    "<b>Status:</b> "
                    f"{invoice.status}"
                ),
                styles[
                    "InvoiceSmallRight"
                ],
            ),
        ]

        header = Table(
            [
                [
                    company_lines,
                    invoice_title,
                ]
            ],
            colWidths=[
                105 * mm,
                75 * mm,
            ],
        )

        header.setStyle(
            TableStyle(
                [
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "TOP",
                    ),
                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        0,
                    ),
                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        0,
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        0,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        0,
                    ),
                ]
            )
        )

        return header

    @staticmethod
    def _build_invoice_meta(
        *,
        invoice,
        styles,
    ):

        order_number = ""

        if invoice.sales_order:

            order_number = getattr(
                invoice.sales_order,
                "so_number",
                "",
            )

        data = [
            [
                Paragraph(
                    "<b>Invoice Date</b>",
                    styles[
                        "InvoiceSmall"
                    ],
                ),
                Paragraph(
                    PDFUtils.date(
                        invoice.invoice_date
                    ),
                    styles[
                        "InvoiceSmall"
                    ],
                ),
                Paragraph(
                    "<b>Due Date</b>",
                    styles[
                        "InvoiceSmall"
                    ],
                ),
                Paragraph(
                    PDFUtils.date(
                        invoice.due_date
                    ),
                    styles[
                        "InvoiceSmall"
                    ],
                ),
            ],
            [
                Paragraph(
                    "<b>Sales Order</b>",
                    styles[
                        "InvoiceSmall"
                    ],
                ),
                Paragraph(
                    PDFUtils.safe_text(
                        order_number,
                        "-",
                    ),
                    styles[
                        "InvoiceSmall"
                    ],
                ),
                Paragraph(
                    "<b>Currency</b>",
                    styles[
                        "InvoiceSmall"
                    ],
                ),
                Paragraph(
                    PDFUtils.safe_text(
                        invoice.organization.currency,
                        "INR",
                    ),
                    styles[
                        "InvoiceSmall"
                    ],
                ),
            ],
        ]

        table = Table(
            data,
            colWidths=[
                30 * mm,
                55 * mm,
                30 * mm,
                65 * mm,
            ],
        )

        table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (0, -1),
                        colors.HexColor(
                            "#F2F2F2"
                        ),
                    ),
                    (
                        "BACKGROUND",
                        (2, 0),
                        (2, -1),
                        colors.HexColor(
                            "#F2F2F2"
                        ),
                    ),
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.25,
                        colors.HexColor(
                            "#D9D9D9"
                        ),
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "MIDDLE",
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        5,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        5,
                    ),
                ]
            )
        )

        return table

    @staticmethod
    def _build_bill_to(
        *,
        invoice,
        styles,
    ):

        address_parts = [
            invoice.billing_address,
            invoice.billing_city,
            invoice.billing_state,
            invoice.billing_pincode,
            invoice.billing_country,
        ]

        address = ", ".join(
            str(value).strip()
            for value
            in address_parts
            if value
        )

        bill_to = [
            [
                Paragraph(
                    "BILL TO",
                    styles[
                        "InvoiceSection"
                    ],
                )
            ],
            [
                Paragraph(
                    (
                        "<b>"
                        f"{PDFUtils.safe_text(invoice.billing_name)}"
                        "</b>"
                    ),
                    styles[
                        "InvoiceSmall"
                    ],
                )
            ],
        ]

        if address:

            bill_to.append(
                [
                    Paragraph(
                        address,
                        styles[
                            "InvoiceSmall"
                        ],
                    )
                ]
            )

        if invoice.customer_gstin:

            bill_to.append(
                [
                    Paragraph(
                        (
                            "<b>GSTIN:</b> "
                            f"{invoice.customer_gstin}"
                        ),
                        styles[
                            "InvoiceSmall"
                        ],
                    )
                ]
            )

        table = Table(
            bill_to,
            colWidths=[
                180 * mm,
            ],
        )

        table.setStyle(
            TableStyle(
                [
                    (
                        "BOX",
                        (0, 0),
                        (-1, -1),
                        0.5,
                        colors.HexColor(
                            "#D0D0D0"
                        ),
                    ),
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.HexColor(
                            "#F4F4F4"
                        ),
                    ),
                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        7,
                    ),
                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        7,
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        5,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        5,
                    ),
                ]
            )
        )

        return table

    @staticmethod
    def _build_items(
        *,
        invoice,
        styles,
    ):

        currency = (
            invoice.organization.currency
            or "INR"
        )

        has_hsn = any(
            bool(
                InvoicePDF
                ._product_value(
                    getattr(
                        item,
                        "product",
                        None,
                    ),
                    "hsn_code",
                    "",
                )
            )
            for item
            in invoice.items
        )

        if has_hsn:

            header = [
                "SKU",
                "Item",
                "HSN",
                "Qty",
                "Rate",
                "Tax %",
                "Discount",
                "Amount",
            ]

        else:

            header = [
                "SKU",
                "Item",
                "Qty",
                "Rate",
                "Tax %",
                "Discount",
                "Amount",
            ]

        rows = [
            [
                Paragraph(
                    f"<b>{value}</b>",
                    styles[
                        "InvoiceTable"
                    ],
                )
                for value
                in header
            ]
        ]

        for item in invoice.items:

            product = getattr(
                item,
                "product",
                None,
            )

            sku = (
                InvoicePDF
                ._product_value(
                    product,
                    "sku",
                    "",
                )
            )

            product_name = (
                InvoicePDF
                ._product_value(
                    product,
                    "name",
                    "Product",
                )
            )

            hsn_code = (
                InvoicePDF
                ._product_value(
                    product,
                    "hsn_code",
                    "",
                )
            )

            quantity = (
                InvoicePDF
                ._item_value(
                    item,
                    "quantity",
                    Decimal("0.00"),
                )
            )

            unit_price = (
                InvoicePDF
                ._item_value(
                    item,
                    "unit_price",
                    Decimal("0.00"),
                )
            )

            tax_rate = (
                InvoicePDF
                ._item_value(
                    item,
                    "tax_rate",
                    Decimal("0.00"),
                )
            )

            discount = (
                InvoicePDF
                ._item_value(
                    item,
                    "discount",
                    Decimal("0.00"),
                )
            )

            line_total = (
                InvoicePDF
                ._item_value(
                    item,
                    "line_total",
                    None,
                )
            )

            if line_total is None:

                line_total = (
                    quantity
                    * unit_price
                )

            base_row = [
                Paragraph(
                    PDFUtils.safe_text(
                        sku,
                        "-",
                    ),
                    styles[
                        "InvoiceTable"
                    ],
                ),
                Paragraph(
                    PDFUtils.safe_text(
                        product_name,
                        "Product",
                    ) + ("<br/><font size='7' color='#526170'>" + PDFUtils.safe_text(item.description).replace("\n","<br/>") + "</font>" if getattr(item,'show_description',False) and getattr(item,'description','') else ''),
                    styles[
                        "InvoiceTable"
                    ],
                ),
            ]

            if has_hsn:

                base_row.append(
                    Paragraph(
                        PDFUtils.safe_text(
                            hsn_code,
                            "-",
                        ),
                        styles[
                            "InvoiceTable"
                        ],
                    )
                )

            base_row.extend(
                [
                    Paragraph(
                        PDFUtils.decimal(
                            quantity
                        ),
                        styles[
                            "InvoiceTableRight"
                        ],
                    ),
                    Paragraph(
                        PDFUtils.money(
                            unit_price,
                            currency,
                        ),
                        styles[
                            "InvoiceTableRight"
                        ],
                    ),
                    Paragraph(
                        PDFUtils.decimal(
                            tax_rate
                        ),
                        styles[
                            "InvoiceTableRight"
                        ],
                    ),
                    Paragraph(
                        PDFUtils.money(
                            discount,
                            currency,
                        ),
                        styles[
                            "InvoiceTableRight"
                        ],
                    ),
                    Paragraph(
                        PDFUtils.money(
                            line_total,
                            currency,
                        ),
                        styles[
                            "InvoiceTableRight"
                        ],
                    ),
                ]
            )

            rows.append(
                base_row
            )

        if has_hsn:

            col_widths = [
                17 * mm,
                38 * mm,
                15 * mm,
                14 * mm,
                25 * mm,
                16 * mm,
                25 * mm,
                30 * mm,
            ]

        else:

            col_widths = [
                20 * mm,
                47 * mm,
                15 * mm,
                27 * mm,
                17 * mm,
                25 * mm,
                29 * mm,
            ]

        table = Table(
            rows,
            repeatRows=1,
            colWidths=col_widths,
        )

        table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.HexColor(
                            "#E8E8E8"
                        ),
                    ),
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.35,
                        colors.HexColor(
                            "#CCCCCC"
                        ),
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "TOP",
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        5,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        5,
                    ),
                ]
            )
        )

        return table

    @staticmethod
    def _build_totals(
        *,
        invoice,
        styles,
    ):

        currency = (
            invoice.organization.currency
            or "INR"
        )

        data = [
            [
                "Subtotal",
                PDFUtils.money(
                    invoice.subtotal,
                    currency,
                ),
            ],
            [
                "Discount",
                PDFUtils.money(
                    invoice.discount_amount,
                    currency,
                ),
            ],
            [
                "Tax",
                PDFUtils.money(
                    invoice.tax_amount,
                    currency,
                ),
            ],
            [
                "Total",
                PDFUtils.money(
                    invoice.total_amount,
                    currency,
                ),
            ],
            [
                "Amount Paid",
                PDFUtils.money(
                    invoice.amount_paid,
                    currency,
                ),
            ],
            [
                "Balance Due",
                PDFUtils.money(
                    invoice.balance_due,
                    currency,
                ),
            ],
        ]

        formatted = []

        for index, row in enumerate(
            data
        ):

            formatted.append(
                [
                    Paragraph(
                        (
                            f"<b>{row[0]}</b>"
                            if index
                            in {
                                3,
                                5,
                            }
                            else row[0]
                        ),
                        styles[
                            "InvoiceSmallRight"
                        ],
                    ),
                    Paragraph(
                        (
                            f"<b>{row[1]}</b>"
                            if index
                            in {
                                3,
                                5,
                            }
                            else row[1]
                        ),
                        styles[
                            "InvoiceSmallRight"
                        ],
                    ),
                ]
            )

        table = Table(
            formatted,
            colWidths=[
                35 * mm,
                45 * mm,
            ],
            hAlign="RIGHT",
        )

        table.setStyle(
            TableStyle(
                [
                    (
                        "LINEABOVE",
                        (0, 3),
                        (-1, 3),
                        0.75,
                        colors.black,
                    ),
                    (
                        "LINEABOVE",
                        (0, 5),
                        (-1, 5),
                        0.75,
                        colors.black,
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        4,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        4,
                    ),
                ]
            )
        )

        return table

    @staticmethod
    def _draw_page_frame(
        canvas_object,
        document,
    ):

        canvas_object.saveState()

        canvas_object.setStrokeColor(
            colors.HexColor(
                "#DDDDDD"
            )
        )

        canvas_object.setLineWidth(
            0.4
        )

        canvas_object.line(
            15 * mm,
            14 * mm,
            195 * mm,
            14 * mm,
        )

        canvas_object.setFont(
            "Helvetica",
            7.5,
        )

        canvas_object.setFillColor(
            colors.HexColor(
                "#666666"
            )
        )

        canvas_object.drawString(
            15 * mm,
            9 * mm,
            "Computer-generated document",
        )

        canvas_object.restoreState()

    @staticmethod
    def generate(
        *,
        invoice,
    ):

        from apps.business.print_documents import invoice_pdf
        return invoice_pdf(invoice)
