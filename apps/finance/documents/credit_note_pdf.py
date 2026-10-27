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


class CreditNoteNumberedCanvas(
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


class CreditNotePDF:

    @staticmethod
    def _build_styles(
    ):
        styles = (
            getSampleStyleSheet()
        )

        styles.add(
            ParagraphStyle(
                name="CNCompany",
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
                name="CNTitle",
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
                name="CNSmall",
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
                name="CNSmallRight",
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
                name="CNSection",
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
                name="CNTable",
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
                name="CNTableRight",
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
        credit_note,
        styles,
    ):
        organization = (
            credit_note.organization
        )

        left = [
            Paragraph(
                PDFUtils.safe_text(
                    organization.name
                ),
                styles[
                    "CNCompany"
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
                            "CNSmall"
                        ],
                    )
                )

        right = [
            Paragraph(
                "CREDIT NOTE",
                styles[
                    "CNTitle"
                ],
            ),
            Spacer(
                1,
                2 * mm,
            ),
            Paragraph(
                (
                    "<b>Credit Note #:</b> "
                    f"{credit_note.credit_note_number}"
                ),
                styles[
                    "CNSmallRight"
                ],
            ),
            Paragraph(
                (
                    "<b>Status:</b> "
                    f"{credit_note.status}"
                ),
                styles[
                    "CNSmallRight"
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
    def _credit_note_meta(
        *,
        credit_note,
        styles,
    ):
        invoice_number = "-"

        if credit_note.invoice:
            invoice_number = (
                credit_note
                .invoice
                .invoice_number
            )

        return_number = "-"

        if credit_note.sales_return:
            return_number = (
                credit_note
                .sales_return
                .return_number
            )

        data = [
            [
                Paragraph(
                    "<b>Credit Note Date</b>",
                    styles[
                        "CNSmall"
                    ],
                ),
                Paragraph(
                    PDFUtils.date(
                        credit_note
                        .credit_note_date
                    ),
                    styles[
                        "CNSmall"
                    ],
                ),
                Paragraph(
                    "<b>Invoice</b>",
                    styles[
                        "CNSmall"
                    ],
                ),
                Paragraph(
                    PDFUtils.safe_text(
                        invoice_number,
                        "-",
                    ),
                    styles[
                        "CNSmall"
                    ],
                ),
            ],
            [
                Paragraph(
                    "<b>Sales Return</b>",
                    styles[
                        "CNSmall"
                    ],
                ),
                Paragraph(
                    PDFUtils.safe_text(
                        return_number,
                        "-",
                    ),
                    styles[
                        "CNSmall"
                    ],
                ),
                Paragraph(
                    "<b>Currency</b>",
                    styles[
                        "CNSmall"
                    ],
                ),
                Paragraph(
                    PDFUtils.safe_text(
                        credit_note
                        .organization
                        .currency,
                        "INR",
                    ),
                    styles[
                        "CNSmall"
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
    def _customer_block(
        *,
        credit_note,
        styles,
    ):
        customer = (
            credit_note.customer
        )

        if not customer:
            raise ValueError(
                "Credit note has no customer."
            )

        address = ", ".join(
            str(value).strip()
            for value in [
                customer.billing_address,
                customer.city,
                customer.state,
                customer.pincode,
                customer.country,
            ]
            if value
        )

        data = [
            [
                Paragraph(
                    "CUSTOMER",
                    styles[
                        "CNSection"
                    ],
                )
            ],
            [
                Paragraph(
                    (
                        f"<b>"
                        f"{PDFUtils.safe_text(customer.name)}"
                        f"</b>"
                    ),
                    styles[
                        "CNSmall"
                    ],
                )
            ],
        ]

        if customer.code:

            data.append(
                [
                    Paragraph(
                        (
                            "<b>Customer Code:</b> "
                            f"{customer.code}"
                        ),
                        styles[
                            "CNSmall"
                        ],
                    )
                ]
            )

        if address:

            data.append(
                [
                    Paragraph(
                        address,
                        styles[
                            "CNSmall"
                        ],
                    )
                ]
            )

        if customer.gstin:

            data.append(
                [
                    Paragraph(
                        (
                            "<b>GSTIN:</b> "
                            f"{customer.gstin}"
                        ),
                        styles[
                            "CNSmall"
                        ],
                    )
                ]
            )

        if customer.email:

            data.append(
                [
                    Paragraph(
                        (
                            "<b>Email:</b> "
                            f"{customer.email}"
                        ),
                        styles[
                            "CNSmall"
                        ],
                    )
                ]
            )

        if customer.phone:

            data.append(
                [
                    Paragraph(
                        (
                            "<b>Phone:</b> "
                            f"{customer.phone}"
                        ),
                        styles[
                            "CNSmall"
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
    def _reason_block(
        *,
        credit_note,
        styles,
    ):
        if not credit_note.reason:
            return None

        table = Table(
            [
                [
                    Paragraph(
                        "REASON",
                        styles[
                            "CNSection"
                        ],
                    )
                ],
                [
                    Paragraph(
                        PDFUtils.safe_text(
                            credit_note.reason
                        ),
                        styles[
                            "CNSmall"
                        ],
                    )
                ],
            ],
            colWidths=[
                180 * mm,
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
                            "#F4F4F4"
                        ),
                    ),
                    (
                        "BOX",
                        (0, 0),
                        (-1, -1),
                        0.4,
                        colors.HexColor(
                            "#D5D5D5"
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
        credit_note,
        styles,
    ):
        currency = (
            credit_note
            .organization
            .currency
            or "INR"
        )

        rows = [
            [
                Paragraph(
                    "<b>SKU</b>",
                    styles[
                        "CNTable"
                    ],
                ),
                Paragraph(
                    "<b>Item</b>",
                    styles[
                        "CNTable"
                    ],
                ),
                Paragraph(
                    "<b>Qty</b>",
                    styles[
                        "CNTableRight"
                    ],
                ),
                Paragraph(
                    "<b>Rate</b>",
                    styles[
                        "CNTableRight"
                    ],
                ),
                Paragraph(
                    "<b>Tax %</b>",
                    styles[
                        "CNTableRight"
                    ],
                ),
                Paragraph(
                    "<b>Discount</b>",
                    styles[
                        "CNTableRight"
                    ],
                ),
                Paragraph(
                    "<b>Tax Amt</b>",
                    styles[
                        "CNTableRight"
                    ],
                ),
                Paragraph(
                    "<b>Total</b>",
                    styles[
                        "CNTableRight"
                    ],
                ),
            ]
        ]

        for item in (
            credit_note.items
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
                            "CNTable"
                        ],
                    ),
                    Paragraph(
                        item_name,
                        styles[
                            "CNTable"
                        ],
                    ),
                    Paragraph(
                        PDFUtils.decimal(
                            item.quantity
                        ),
                        styles[
                            "CNTableRight"
                        ],
                    ),
                    Paragraph(
                        PDFUtils.money(
                            item.unit_price,
                            currency,
                        ),
                        styles[
                            "CNTableRight"
                        ],
                    ),
                    Paragraph(
                        PDFUtils.decimal(
                            item.tax_rate
                        ),
                        styles[
                            "CNTableRight"
                        ],
                    ),
                    Paragraph(
                        PDFUtils.money(
                            item.discount,
                            currency,
                        ),
                        styles[
                            "CNTableRight"
                        ],
                    ),
                    Paragraph(
                        PDFUtils.money(
                            item.line_tax,
                            currency,
                        ),
                        styles[
                            "CNTableRight"
                        ],
                    ),
                    Paragraph(
                        PDFUtils.money(
                            item.line_total,
                            currency,
                        ),
                        styles[
                            "CNTableRight"
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
        credit_note,
        styles,
    ):
        currency = (
            credit_note
            .organization
            .currency
            or "INR"
        )

        values = [
            (
                "Subtotal",
                credit_note.subtotal,
            ),
            (
                "Discount",
                credit_note
                .discount_amount,
            ),
            (
                "Tax",
                credit_note.tax_amount,
            ),
            (
                "Credit Note Total",
                credit_note.total_amount,
            ),
            (
                "Applied Amount",
                credit_note.applied_amount,
            ),
            (
                "Remaining Credit",
                credit_note.remaining_credit,
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
                            "CNSmallRight"
                        ],
                    ),
                    Paragraph(
                        value_text,
                        styles[
                            "CNSmallRight"
                        ],
                    ),
                ]
            )

        table = Table(
            rows,
            colWidths=[
                38 * mm,
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
                "credit note"
            ),
        )

        canvas_object.restoreState()

    @staticmethod
    def generate(
        *,
        credit_note,
    ):
        """
        Generate Credit Note PDF bytes.
        """

        if not credit_note:

            raise ValueError(
                "Credit note is required."
            )

        if not credit_note.organization:

            raise ValueError(
                "Credit note has no "
                "organization."
            )

        if not credit_note.credit_note_number:

            raise ValueError(
                "Credit note number "
                "is required."
            )

        if not credit_note.customer:

            raise ValueError(
                "Credit note has no customer."
            )

        if not credit_note.items:

            raise ValueError(
                "Credit note must contain "
                "at least one item."
            )

        styles = (
            CreditNotePDF
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
                f"Credit Note "
                f"{credit_note.credit_note_number}"
            ),
            author=(
                credit_note
                .organization
                .name
            ),
        )

        story = []

        story.append(
            CreditNotePDF
            ._company_header(
                credit_note=credit_note,
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
            CreditNotePDF
            ._credit_note_meta(
                credit_note=credit_note,
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
            CreditNotePDF
            ._customer_block(
                credit_note=credit_note,
                styles=styles,
            )
        )

        reason_block = (
            CreditNotePDF
            ._reason_block(
                credit_note=credit_note,
                styles=styles,
            )
        )

        if reason_block:

            story.append(
                Spacer(
                    1,
                    5 * mm,
                )
            )

            story.append(
                reason_block
            )

        story.append(
            Spacer(
                1,
                7 * mm,
            )
        )

        story.append(
            CreditNotePDF
            ._items_table(
                credit_note=credit_note,
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
            CreditNotePDF
            ._totals(
                credit_note=credit_note,
                styles=styles,
            )
        ]

        if credit_note.notes:

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
                        "CNSection"
                    ],
                )
            )

            summary.append(
                Paragraph(
                    PDFUtils.safe_text(
                        credit_note.notes
                    ),
                    styles[
                        "CNSmall"
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
                CreditNotePDF
                ._draw_page_frame
            ),
            onLaterPages=(
                CreditNotePDF
                ._draw_page_frame
            ),
            canvasmaker=(
                CreditNoteNumberedCanvas
            ),
        )

        pdf_bytes = (
            buffer.getvalue()
        )

        buffer.close()

        if not pdf_bytes:

            raise ValueError(
                "Credit Note PDF "
                "generation failed."
            )

        return pdf_bytes