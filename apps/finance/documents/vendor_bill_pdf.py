from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import (
    ParagraphStyle,
    getSampleStyleSheet,
)
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from apps.finance.documents.pdf_utils import (
    PDFUtils,
)


class VendorBillNumberedCanvas(
    canvas.Canvas
):
    """
    Add Page X of Y numbering.
    """

    def __init__(
        self,
        *args,
        **kwargs,
    ):
        super().__init__(
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
        text = (
            f"Page "
            f"{self._pageNumber} "
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


class VendorBillPDF:

    @staticmethod
    def _build_styles(
    ):
        styles = (
            getSampleStyleSheet()
        )

        styles.add(
            ParagraphStyle(
                name="VBCompany",
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
                name="VBTitle",
                parent=styles[
                    "Heading1"
                ],
                fontName=(
                    "Helvetica-Bold"
                ),
                fontSize=19,
                leading=22,
                alignment=TA_RIGHT,
            )
        )

        styles.add(
            ParagraphStyle(
                name="VBSmall",
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
                name="VBSmallRight",
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
                name="VBSection",
                parent=styles[
                    "Normal"
                ],
                fontName=(
                    "Helvetica-Bold"
                ),
                fontSize=9,
                leading=12,
            )
        )

        styles.add(
            ParagraphStyle(
                name="VBTable",
                parent=styles[
                    "Normal"
                ],
                fontName="Helvetica",
                fontSize=7.4,
                leading=9,
                wordWrap="CJK",
            )
        )

        styles.add(
            ParagraphStyle(
                name="VBTableRight",
                parent=styles[
                    "Normal"
                ],
                fontName="Helvetica",
                fontSize=7.4,
                leading=9,
                alignment=TA_RIGHT,
                wordWrap="CJK",
            )
        )

        return styles

    @staticmethod
    def _company_header(
        *,
        vendor_bill,
        styles,
    ):
        organization = (
            vendor_bill.organization
        )

        left = [
            Paragraph(
                PDFUtils.safe_text(
                    organization.name
                ),
                styles[
                    "VBCompany"
                ],
            )
        ]

        for value in [
            organization.address,
            organization.country,
            organization.email,
            organization.phone,
        ]:

            if value:

                left.append(
                    Paragraph(
                        PDFUtils.safe_text(
                            value
                        ),
                        styles[
                            "VBSmall"
                        ],
                    )
                )

        right = [
            Paragraph(
                "VENDOR BILL",
                styles[
                    "VBTitle"
                ],
            ),
            Spacer(
                1,
                2 * mm,
            ),
            Paragraph(
                (
                    "<b>Bill #:</b> "
                    f"{vendor_bill.bill_number}"
                ),
                styles[
                    "VBSmallRight"
                ],
            ),
            Paragraph(
                (
                    "<b>Status:</b> "
                    f"{vendor_bill.status}"
                ),
                styles[
                    "VBSmallRight"
                ],
            ),
        ]

        table = Table(
            [
                [
                    left,
                    right,
                ]
            ],
            colWidths=[
                105 * mm,
                75 * mm,
            ],
        )

        table.setStyle(
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

        return table

    @staticmethod
    def _bill_meta(
        *,
        vendor_bill,
        styles,
    ):
        po_number = "-"

        if vendor_bill.purchase_order:
            po_number = (
                vendor_bill
                .purchase_order
                .po_number
            )

        due_date = (
            PDFUtils.date(
                vendor_bill.due_date
            )
            or "-"
        )

        supplier_invoice = (
            vendor_bill
            .supplier_invoice_number
            or "-"
        )

        data = [
            [
                Paragraph(
                    "<b>Bill Date</b>",
                    styles[
                        "VBSmall"
                    ],
                ),
                Paragraph(
                    PDFUtils.date(
                        vendor_bill.bill_date
                    ),
                    styles[
                        "VBSmall"
                    ],
                ),
                Paragraph(
                    "<b>Due Date</b>",
                    styles[
                        "VBSmall"
                    ],
                ),
                Paragraph(
                    due_date,
                    styles[
                        "VBSmall"
                    ],
                ),
            ],
            [
                Paragraph(
                    "<b>Supplier Invoice</b>",
                    styles[
                        "VBSmall"
                    ],
                ),
                Paragraph(
                    PDFUtils.safe_text(
                        supplier_invoice,
                        "-",
                    ),
                    styles[
                        "VBSmall"
                    ],
                ),
                Paragraph(
                    "<b>Purchase Order</b>",
                    styles[
                        "VBSmall"
                    ],
                ),
                Paragraph(
                    PDFUtils.safe_text(
                        po_number,
                        "-",
                    ),
                    styles[
                        "VBSmall"
                    ],
                ),
            ],
            [
                Paragraph(
                    "<b>Currency</b>",
                    styles[
                        "VBSmall"
                    ],
                ),
                Paragraph(
                    PDFUtils.safe_text(
                        vendor_bill
                        .organization
                        .currency,
                        "INR",
                    ),
                    styles[
                        "VBSmall"
                    ],
                ),
                Paragraph(
                    "<b>Balance Status</b>",
                    styles[
                        "VBSmall"
                    ],
                ),
                Paragraph(
                    (
                        "PAID"
                        if (
                            vendor_bill
                            .balance_due
                            == 0
                        )
                        else "OUTSTANDING"
                    ),
                    styles[
                        "VBSmall"
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
                        0.3,
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
    def _supplier_block(
        *,
        vendor_bill,
        styles,
    ):
        address = ", ".join(
            str(value).strip()
            for value in [
                vendor_bill
                .supplier_address,

                vendor_bill
                .supplier_city,

                vendor_bill
                .supplier_state,

                vendor_bill
                .supplier_pincode,

                vendor_bill
                .supplier_country,
            ]
            if value
        )

        data = [
            [
                Paragraph(
                    "SUPPLIER",
                    styles[
                        "VBSection"
                    ],
                )
            ],
            [
                Paragraph(
                    (
                        f"<b>"
                        f"{PDFUtils.safe_text(vendor_bill.supplier_name)}"
                        f"</b>"
                    ),
                    styles[
                        "VBSmall"
                    ],
                )
            ],
        ]

        if address:

            data.append(
                [
                    Paragraph(
                        address,
                        styles[
                            "VBSmall"
                        ],
                    )
                ]
            )

        if vendor_bill.supplier_gstin:

            data.append(
                [
                    Paragraph(
                        (
                            "<b>GSTIN:</b> "
                            f"{vendor_bill.supplier_gstin}"
                        ),
                        styles[
                            "VBSmall"
                        ],
                    )
                ]
            )

        if vendor_bill.supplier:

            if (
                vendor_bill
                .supplier
                .email
            ):

                data.append(
                    [
                        Paragraph(
                            (
                                "<b>Email:</b> "
                                f"{vendor_bill.supplier.email}"
                            ),
                            styles[
                                "VBSmall"
                            ],
                        )
                    ]
                )

            if (
                vendor_bill
                .supplier
                .phone
            ):

                data.append(
                    [
                        Paragraph(
                            (
                                "<b>Phone:</b> "
                                f"{vendor_bill.supplier.phone}"
                            ),
                            styles[
                                "VBSmall"
                            ],
                        )
                    ]
                )

        table = Table(
            data,
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
    def _items_table(
        *,
        vendor_bill,
        styles,
    ):
        currency = (
            vendor_bill
            .organization
            .currency
            or "INR"
        )

        rows = [
            [
                Paragraph(
                    "<b>SKU</b>",
                    styles[
                        "VBTable"
                    ],
                ),
                Paragraph(
                    "<b>Item</b>",
                    styles[
                        "VBTable"
                    ],
                ),
                Paragraph(
                    "<b>Qty</b>",
                    styles[
                        "VBTableRight"
                    ],
                ),
                Paragraph(
                    "<b>Rate</b>",
                    styles[
                        "VBTableRight"
                    ],
                ),
                Paragraph(
                    "<b>Tax %</b>",
                    styles[
                        "VBTableRight"
                    ],
                ),
                Paragraph(
                    "<b>Discount</b>",
                    styles[
                        "VBTableRight"
                    ],
                ),
                Paragraph(
                    "<b>Tax Amt</b>",
                    styles[
                        "VBTableRight"
                    ],
                ),
                Paragraph(
                    "<b>Total</b>",
                    styles[
                        "VBTableRight"
                    ],
                ),
            ]
        ]

        for item in (
            vendor_bill.items
        ):

            product = (
                item.product
            )

            sku = getattr(
                product,
                "sku",
                "-",
            )

            name = getattr(
                product,
                "name",
                "Product",
            )

            description = getattr(
                product,
                "description",
                "",
            )

            unit = getattr(
                product,
                "unit",
                "",
            )

            item_name = (
                PDFUtils.safe_text(
                    name
                )
            )

            if description:

                item_name += (
                    "<br/>"
                    "<font size='6.5'>"
                    f"{PDFUtils.safe_text(description)}"
                    "</font>"
                )

            if unit:

                item_name += (
                    "<br/>"
                    "<font size='6.5'>"
                    f"Unit: {unit}"
                    "</font>"
                )

            rows.append(
                [
                    Paragraph(
                        PDFUtils.safe_text(
                            sku,
                            "-",
                        ),
                        styles[
                            "VBTable"
                        ],
                    ),
                    Paragraph(
                        item_name,
                        styles[
                            "VBTable"
                        ],
                    ),
                    Paragraph(
                        PDFUtils.decimal(
                            item.quantity
                        ),
                        styles[
                            "VBTableRight"
                        ],
                    ),
                    Paragraph(
                        PDFUtils.money(
                            item.unit_price,
                            currency,
                        ),
                        styles[
                            "VBTableRight"
                        ],
                    ),
                    Paragraph(
                        PDFUtils.decimal(
                            item.tax_rate
                        ),
                        styles[
                            "VBTableRight"
                        ],
                    ),
                    Paragraph(
                        PDFUtils.money(
                            item.discount,
                            currency,
                        ),
                        styles[
                            "VBTableRight"
                        ],
                    ),
                    Paragraph(
                        PDFUtils.money(
                            item.line_tax,
                            currency,
                        ),
                        styles[
                            "VBTableRight"
                        ],
                    ),
                    Paragraph(
                        PDFUtils.money(
                            item.line_total,
                            currency,
                        ),
                        styles[
                            "VBTableRight"
                        ],
                    ),
                ]
            )

        table = Table(
            rows,
            repeatRows=1,
            colWidths=[
                17 * mm,
                39 * mm,
                13 * mm,
                25 * mm,
                14 * mm,
                23 * mm,
                22 * mm,
                27 * mm,
            ],
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
    def _totals(
        *,
        vendor_bill,
        styles,
    ):
        currency = (
            vendor_bill
            .organization
            .currency
            or "INR"
        )

        values = [
            (
                "Subtotal",
                vendor_bill.subtotal,
            ),
            (
                "Discount",
                vendor_bill
                .discount_amount,
            ),
            (
                "Tax",
                vendor_bill.tax_amount,
            ),
            (
                "Total",
                vendor_bill.total_amount,
            ),
            (
                "Amount Paid",
                vendor_bill.amount_paid,
            ),
            (
                "Balance Due",
                vendor_bill.balance_due,
            ),
        ]

        rows = []

        for index, (
            label,
            value,
        ) in enumerate(
            values
        ):

            bold = (
                index
                in {
                    3,
                    5,
                }
            )

            label_text = (
                f"<b>{label}</b>"
                if bold
                else label
            )

            value_text = (
                PDFUtils.money(
                    value,
                    currency,
                )
            )

            if bold:

                value_text = (
                    f"<b>{value_text}</b>"
                )

            rows.append(
                [
                    Paragraph(
                        label_text,
                        styles[
                            "VBSmallRight"
                        ],
                    ),
                    Paragraph(
                        value_text,
                        styles[
                            "VBSmallRight"
                        ],
                    ),
                ]
            )

        table = Table(
            rows,
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
                        0.8,
                        colors.black,
                    ),
                    (
                        "LINEABOVE",
                        (0, 5),
                        (-1, 5),
                        0.8,
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
            (
                "Computer-generated "
                "vendor bill"
            ),
        )

        canvas_object.restoreState()

    @staticmethod
    def generate(
        *,
        vendor_bill,
    ):
        """
        Generate Vendor Bill PDF bytes.
        """

        if not vendor_bill:

            raise ValueError(
                "Vendor bill is required."
            )

        if not vendor_bill.organization:

            raise ValueError(
                "Vendor bill has no "
                "organization."
            )

        if not vendor_bill.bill_number:

            raise ValueError(
                "Vendor bill number "
                "is required."
            )

        if not vendor_bill.supplier:

            raise ValueError(
                "Vendor bill has no supplier."
            )

        if not vendor_bill.items:

            raise ValueError(
                "Vendor bill must contain "
                "at least one item."
            )

        styles = (
            VendorBillPDF
            ._build_styles()
        )

        buffer = BytesIO()

        document = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=15 * mm,
            leftMargin=15 * mm,
            topMargin=15 * mm,
            bottomMargin=18 * mm,
            title=(
                f"Vendor Bill "
                f"{vendor_bill.bill_number}"
            ),
            author=(
                vendor_bill
                .organization
                .name
            ),
        )

        story = []

        story.append(
            VendorBillPDF
            ._company_header(
                vendor_bill=vendor_bill,
                styles=styles,
            )
        )

        story.append(
            Spacer(
                1,
                7 * mm,
            )
        )

        story.append(
            VendorBillPDF
            ._bill_meta(
                vendor_bill=vendor_bill,
                styles=styles,
            )
        )

        story.append(
            Spacer(
                1,
                6 * mm,
            )
        )

        story.append(
            VendorBillPDF
            ._supplier_block(
                vendor_bill=vendor_bill,
                styles=styles,
            )
        )

        story.append(
            Spacer(
                1,
                7 * mm,
            )
        )

        story.append(
            VendorBillPDF
            ._items_table(
                vendor_bill=vendor_bill,
                styles=styles,
            )
        )

        story.append(
            Spacer(
                1,
                7 * mm,
            )
        )

        summary = [
            VendorBillPDF
            ._totals(
                vendor_bill=vendor_bill,
                styles=styles,
            )
        ]

        if vendor_bill.notes:

            summary.append(
                Spacer(
                    1,
                    7 * mm,
                )
            )

            summary.append(
                Paragraph(
                    "<b>Notes</b>",
                    styles[
                        "VBSection"
                    ],
                )
            )

            summary.append(
                Paragraph(
                    PDFUtils.safe_text(
                        vendor_bill.notes
                    ),
                    styles[
                        "VBSmall"
                    ],
                )
            )

        story.append(
            KeepTogether(
                summary
            )
        )

        document.build(
            story,
            onFirstPage=(
                VendorBillPDF
                ._draw_page_frame
            ),
            onLaterPages=(
                VendorBillPDF
                ._draw_page_frame
            ),
            canvasmaker=(
                VendorBillNumberedCanvas
            ),
        )

        pdf_bytes = (
            buffer.getvalue()
        )

        buffer.close()

        if not pdf_bytes:

            raise ValueError(
                "Vendor Bill PDF "
                "generation failed."
            )

        return pdf_bytes