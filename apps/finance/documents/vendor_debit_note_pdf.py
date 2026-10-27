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


class VendorDebitNoteNumberedCanvas(
    canvas.Canvas
):

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
        self.setFont(
            "Helvetica",
            8,
        )

        self.drawRightString(
            195 * mm,
            10 * mm,
            (
                f"Page "
                f"{self._pageNumber} "
                f"of "
                f"{page_count}"
            ),
        )


class VendorDebitNotePDF:

    @staticmethod
    def _build_styles():
        styles = (
            getSampleStyleSheet()
        )

        styles.add(
            ParagraphStyle(
                name="VDNCompany",
                parent=styles["Heading1"],
                fontName="Helvetica-Bold",
                fontSize=16,
                leading=19,
            )
        )

        styles.add(
            ParagraphStyle(
                name="VDNTitle",
                parent=styles["Heading1"],
                fontName="Helvetica-Bold",
                fontSize=19,
                leading=22,
                alignment=TA_RIGHT,
            )
        )

        styles.add(
            ParagraphStyle(
                name="VDNSmall",
                parent=styles["Normal"],
                fontName="Helvetica",
                fontSize=8.5,
                leading=11,
            )
        )

        styles.add(
            ParagraphStyle(
                name="VDNSmallRight",
                parent=styles["Normal"],
                fontName="Helvetica",
                fontSize=8.5,
                leading=11,
                alignment=TA_RIGHT,
            )
        )

        styles.add(
            ParagraphStyle(
                name="VDNSection",
                parent=styles["Normal"],
                fontName="Helvetica-Bold",
                fontSize=9,
                leading=12,
            )
        )

        styles.add(
            ParagraphStyle(
                name="VDNTable",
                parent=styles["Normal"],
                fontName="Helvetica",
                fontSize=7.4,
                leading=9,
                wordWrap="CJK",
            )
        )

        styles.add(
            ParagraphStyle(
                name="VDNTableRight",
                parent=styles["Normal"],
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
        debit_note,
        styles,
    ):
        organization = (
            debit_note.organization
        )

        left = [
            Paragraph(
                PDFUtils.safe_text(
                    organization.name
                ),
                styles[
                    "VDNCompany"
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
                            "VDNSmall"
                        ],
                    )
                )

        right = [
            Paragraph(
                "VENDOR DEBIT NOTE",
                styles[
                    "VDNTitle"
                ],
            ),
            Spacer(
                1,
                2 * mm,
            ),
            Paragraph(
                (
                    "<b>Debit Note #:</b> "
                    f"{debit_note.debit_note_number}"
                ),
                styles[
                    "VDNSmallRight"
                ],
            ),
            Paragraph(
                (
                    "<b>Status:</b> "
                    f"{debit_note.status}"
                ),
                styles[
                    "VDNSmallRight"
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
    def _meta(
        *,
        debit_note,
        styles,
    ):
        bill_number = (
            debit_note.vendor_bill.bill_number
            if debit_note.vendor_bill
            else "-"
        )

        po_number = (
            debit_note.purchase_order.po_number
            if debit_note.purchase_order
            else "-"
        )

        return_number = (
            debit_note.purchase_return.return_number
            if debit_note.purchase_return
            else "-"
        )

        data = [
            [
                Paragraph(
                    "<b>Debit Note Date</b>",
                    styles[
                        "VDNSmall"
                    ],
                ),
                Paragraph(
                    PDFUtils.date(
                        debit_note.debit_note_date
                    ),
                    styles[
                        "VDNSmall"
                    ],
                ),
                Paragraph(
                    "<b>Vendor Bill</b>",
                    styles[
                        "VDNSmall"
                    ],
                ),
                Paragraph(
                    bill_number,
                    styles[
                        "VDNSmall"
                    ],
                ),
            ],
            [
                Paragraph(
                    "<b>Purchase Order</b>",
                    styles[
                        "VDNSmall"
                    ],
                ),
                Paragraph(
                    po_number,
                    styles[
                        "VDNSmall"
                    ],
                ),
                Paragraph(
                    "<b>Purchase Return</b>",
                    styles[
                        "VDNSmall"
                    ],
                ),
                Paragraph(
                    return_number,
                    styles[
                        "VDNSmall"
                    ],
                ),
            ],
            [
                Paragraph(
                    "<b>Currency</b>",
                    styles[
                        "VDNSmall"
                    ],
                ),
                Paragraph(
                    PDFUtils.safe_text(
                        debit_note
                        .organization
                        .currency,
                        "INR",
                    ),
                    styles[
                        "VDNSmall"
                    ],
                ),
                Paragraph(
                    "<b>Supplier</b>",
                    styles[
                        "VDNSmall"
                    ],
                ),
                Paragraph(
                    PDFUtils.safe_text(
                        debit_note.supplier.name
                        if debit_note.supplier
                        else "-"
                    ),
                    styles[
                        "VDNSmall"
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
        debit_note,
        styles,
    ):
        supplier = (
            debit_note.supplier
        )

        if not supplier:
            raise ValueError(
                "Vendor debit note "
                "has no supplier."
            )

        address = ", ".join(
            str(value).strip()
            for value in [
                supplier.address,
                supplier.city,
                supplier.state,
                supplier.pincode,
                supplier.country,
            ]
            if value
        )

        data = [
            [
                Paragraph(
                    "SUPPLIER",
                    styles[
                        "VDNSection"
                    ],
                )
            ],
            [
                Paragraph(
                    (
                        f"<b>"
                        f"{PDFUtils.safe_text(supplier.name)}"
                        f"</b>"
                    ),
                    styles[
                        "VDNSmall"
                    ],
                )
            ],
        ]

        if supplier.code:

            data.append(
                [
                    Paragraph(
                        (
                            "<b>Supplier Code:</b> "
                            f"{supplier.code}"
                        ),
                        styles[
                            "VDNSmall"
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
                            "VDNSmall"
                        ],
                    )
                ]
            )

        if supplier.gstin:

            data.append(
                [
                    Paragraph(
                        (
                            "<b>GSTIN:</b> "
                            f"{supplier.gstin}"
                        ),
                        styles[
                            "VDNSmall"
                        ],
                    )
                ]
            )

        if supplier.email:

            data.append(
                [
                    Paragraph(
                        (
                            "<b>Email:</b> "
                            f"{supplier.email}"
                        ),
                        styles[
                            "VDNSmall"
                        ],
                    )
                ]
            )

        if supplier.phone:

            data.append(
                [
                    Paragraph(
                        (
                            "<b>Phone:</b> "
                            f"{supplier.phone}"
                        ),
                        styles[
                            "VDNSmall"
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
        debit_note,
        styles,
    ):
        if not debit_note.reason:
            return None

        table = Table(
            [
                [
                    Paragraph(
                        "REASON",
                        styles[
                            "VDNSection"
                        ],
                    )
                ],
                [
                    Paragraph(
                        PDFUtils.safe_text(
                            debit_note.reason
                        ),
                        styles[
                            "VDNSmall"
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
        debit_note,
        styles,
    ):
        currency = (
            debit_note.organization.currency
            or "INR"
        )

        rows = [
            [
                Paragraph(
                    "<b>SKU</b>",
                    styles[
                        "VDNTable"
                    ],
                ),
                Paragraph(
                    "<b>Item</b>",
                    styles[
                        "VDNTable"
                    ],
                ),
                Paragraph(
                    "<b>Qty</b>",
                    styles[
                        "VDNTableRight"
                    ],
                ),
                Paragraph(
                    "<b>Rate</b>",
                    styles[
                        "VDNTableRight"
                    ],
                ),
                Paragraph(
                    "<b>Tax %</b>",
                    styles[
                        "VDNTableRight"
                    ],
                ),
                Paragraph(
                    "<b>Discount</b>",
                    styles[
                        "VDNTableRight"
                    ],
                ),
                Paragraph(
                    "<b>Tax Amt</b>",
                    styles[
                        "VDNTableRight"
                    ],
                ),
                Paragraph(
                    "<b>Total</b>",
                    styles[
                        "VDNTableRight"
                    ],
                ),
            ]
        ]

        for item in debit_note.items:

            product = (
                item.product
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
                            getattr(
                                product,
                                "sku",
                                "-",
                            ),
                            "-",
                        ),
                        styles[
                            "VDNTable"
                        ],
                    ),
                    Paragraph(
                        item_name,
                        styles[
                            "VDNTable"
                        ],
                    ),
                    Paragraph(
                        PDFUtils.decimal(
                            item.quantity
                        ),
                        styles[
                            "VDNTableRight"
                        ],
                    ),
                    Paragraph(
                        PDFUtils.money(
                            item.unit_price,
                            currency,
                        ),
                        styles[
                            "VDNTableRight"
                        ],
                    ),
                    Paragraph(
                        PDFUtils.decimal(
                            item.tax_rate
                        ),
                        styles[
                            "VDNTableRight"
                        ],
                    ),
                    Paragraph(
                        PDFUtils.money(
                            item.discount,
                            currency,
                        ),
                        styles[
                            "VDNTableRight"
                        ],
                    ),
                    Paragraph(
                        PDFUtils.money(
                            item.line_tax,
                            currency,
                        ),
                        styles[
                            "VDNTableRight"
                        ],
                    ),
                    Paragraph(
                        PDFUtils.money(
                            item.line_total,
                            currency,
                        ),
                        styles[
                            "VDNTableRight"
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
        debit_note,
        styles,
    ):
        currency = (
            debit_note.organization.currency
            or "INR"
        )

        values = [
            (
                "Subtotal",
                debit_note.subtotal,
            ),
            (
                "Discount",
                debit_note.discount_amount,
            ),
            (
                "Tax",
                debit_note.tax_amount,
            ),
            (
                "Debit Note Total",
                debit_note.total_amount,
            ),
            (
                "Applied Amount",
                debit_note.applied_amount,
            ),
            (
                "Remaining Credit",
                debit_note.remaining_credit,
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
                            "VDNSmallRight"
                        ],
                    ),
                    Paragraph(
                        value_text,
                        styles[
                            "VDNSmallRight"
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
                "vendor debit note"
            ),
        )

        canvas_object.restoreState()

    @staticmethod
    def generate(
        *,
        debit_note,
    ):

        if not debit_note:
            raise ValueError(
                "Vendor debit note "
                "is required."
            )

        if not debit_note.organization:
            raise ValueError(
                "Vendor debit note has "
                "no organization."
            )

        if not debit_note.debit_note_number:
            raise ValueError(
                "Vendor debit note number "
                "is required."
            )

        if not debit_note.supplier:
            raise ValueError(
                "Vendor debit note "
                "has no supplier."
            )

        if not debit_note.items:
            raise ValueError(
                "Vendor debit note must "
                "contain at least one item."
            )

        styles = (
            VendorDebitNotePDF
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
                f"Vendor Debit Note "
                f"{debit_note.debit_note_number}"
            ),
            author=(
                debit_note.organization.name
            ),
        )

        story = [
            VendorDebitNotePDF
            ._company_header(
                debit_note=debit_note,
                styles=styles,
            ),
            Spacer(
                1,
                7 * mm,
            ),
            VendorDebitNotePDF
            ._meta(
                debit_note=debit_note,
                styles=styles,
            ),
            Spacer(
                1,
                6 * mm,
            ),
            VendorDebitNotePDF
            ._supplier_block(
                debit_note=debit_note,
                styles=styles,
            ),
        ]

        reason_block = (
            VendorDebitNotePDF
            ._reason_block(
                debit_note=debit_note,
                styles=styles,
            )
        )

        if reason_block:

            story.extend(
                [
                    Spacer(
                        1,
                        5 * mm,
                    ),
                    reason_block,
                ]
            )

        story.extend(
            [
                Spacer(
                    1,
                    7 * mm,
                ),
                VendorDebitNotePDF
                ._items_table(
                    debit_note=debit_note,
                    styles=styles,
                ),
                Spacer(
                    1,
                    7 * mm,
                ),
            ]
        )

        summary = [
            VendorDebitNotePDF
            ._totals(
                debit_note=debit_note,
                styles=styles,
            )
        ]

        if debit_note.notes:

            summary.extend(
                [
                    Spacer(
                        1,
                        7 * mm,
                    ),
                    Paragraph(
                        "<b>Notes</b>",
                        styles[
                            "VDNSection"
                        ],
                    ),
                    Paragraph(
                        PDFUtils.safe_text(
                            debit_note.notes
                        ),
                        styles[
                            "VDNSmall"
                        ],
                    ),
                ]
            )

        story.append(
            KeepTogether(
                summary
            )
        )

        document.build(
            story,
            onFirstPage=(
                VendorDebitNotePDF
                ._draw_page_frame
            ),
            onLaterPages=(
                VendorDebitNotePDF
                ._draw_page_frame
            ),
            canvasmaker=(
                VendorDebitNoteNumberedCanvas
            ),
        )

        pdf_bytes = (
            buffer.getvalue()
        )

        buffer.close()

        if not pdf_bytes:
            raise ValueError(
                "Vendor Debit Note PDF "
                "generation failed."
            )

        return pdf_bytes