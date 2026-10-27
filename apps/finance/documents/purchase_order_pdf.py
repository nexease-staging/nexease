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


class PurchaseOrderNumberedCanvas(
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


class PurchaseOrderPDF:

    @staticmethod
    def _build_styles(
    ):
        styles = (
            getSampleStyleSheet()
        )

        styles.add(
            ParagraphStyle(
                name="POCompany",
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
                name="POTitle",
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
                name="POSmall",
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
                name="POSmallRight",
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
                name="POSection",
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
                name="POTable",
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
                name="POTableRight",
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
        purchase_order,
        styles,
    ):
        organization = (
            purchase_order.organization
        )

        left = [
            Paragraph(
                PDFUtils.safe_text(
                    organization.name
                ),
                styles[
                    "POCompany"
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
                            "POSmall"
                        ],
                    )
                )

        right = [
            Paragraph(
                "PURCHASE ORDER",
                styles[
                    "POTitle"
                ],
            ),
            Spacer(
                1,
                2 * mm,
            ),
            Paragraph(
                (
                    "<b>PO #:</b> "
                    f"{purchase_order.po_number}"
                ),
                styles[
                    "POSmallRight"
                ],
            ),
            Paragraph(
                (
                    "<b>Status:</b> "
                    f"{purchase_order.status}"
                ),
                styles[
                    "POSmallRight"
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
    def _order_meta(
        *,
        purchase_order,
        styles,
    ):
        expected_date = (
            PDFUtils.date(
                purchase_order
                .expected_delivery_date
            )
            or "-"
        )

        data = [
            [
                Paragraph(
                    "<b>Order Date</b>",
                    styles[
                        "POSmall"
                    ],
                ),
                Paragraph(
                    PDFUtils.date(
                        purchase_order.order_date
                    ),
                    styles[
                        "POSmall"
                    ],
                ),
                Paragraph(
                    "<b>Expected Delivery</b>",
                    styles[
                        "POSmall"
                    ],
                ),
                Paragraph(
                    expected_date,
                    styles[
                        "POSmall"
                    ],
                ),
            ],
            [
                Paragraph(
                    "<b>Supplier Code</b>",
                    styles[
                        "POSmall"
                    ],
                ),
                Paragraph(
                    PDFUtils.safe_text(
                        purchase_order
                        .supplier
                        .code,
                        "-",
                    ),
                    styles[
                        "POSmall"
                    ],
                ),
                Paragraph(
                    "<b>Currency</b>",
                    styles[
                        "POSmall"
                    ],
                ),
                Paragraph(
                    PDFUtils.safe_text(
                        purchase_order
                        .organization
                        .currency,
                        "INR",
                    ),
                    styles[
                        "POSmall"
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
        purchase_order,
        styles,
    ):
        supplier = (
            purchase_order.supplier
        )

        if not supplier:
            raise ValueError(
                "Purchase order has no supplier."
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
                        "POSection"
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
                        "POSmall"
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
                            "POSmall"
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
                            "POSmall"
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
                            "POSmall"
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
                            "POSmall"
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
                            "POSmall"
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
        purchase_order,
        styles,
    ):
        currency = (
            purchase_order
            .organization
            .currency
            or "INR"
        )

        rows = [
            [
                Paragraph(
                    "<b>SKU</b>",
                    styles[
                        "POTable"
                    ],
                ),
                Paragraph(
                    "<b>Item</b>",
                    styles[
                        "POTable"
                    ],
                ),
                Paragraph(
                    "<b>Qty</b>",
                    styles[
                        "POTableRight"
                    ],
                ),
                Paragraph(
                    "<b>Received</b>",
                    styles[
                        "POTableRight"
                    ],
                ),
                Paragraph(
                    "<b>Rate</b>",
                    styles[
                        "POTableRight"
                    ],
                ),
                Paragraph(
                    "<b>Tax %</b>",
                    styles[
                        "POTableRight"
                    ],
                ),
                Paragraph(
                    "<b>Discount</b>",
                    styles[
                        "POTableRight"
                    ],
                ),
                Paragraph(
                    "<b>Amount</b>",
                    styles[
                        "POTableRight"
                    ],
                ),
            ]
        ]

        for item in (
            purchase_order.items
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
                            "POTable"
                        ],
                    ),
                    Paragraph(
                        item_name,
                        styles[
                            "POTable"
                        ],
                    ),
                    Paragraph(
                        PDFUtils.decimal(
                            item.quantity
                        ),
                        styles[
                            "POTableRight"
                        ],
                    ),
                    Paragraph(
                        PDFUtils.decimal(
                            item
                            .received_quantity
                        ),
                        styles[
                            "POTableRight"
                        ],
                    ),
                    Paragraph(
                        PDFUtils.money(
                            item.unit_price,
                            currency,
                        ),
                        styles[
                            "POTableRight"
                        ],
                    ),
                    Paragraph(
                        PDFUtils.decimal(
                            item.tax_rate
                        ),
                        styles[
                            "POTableRight"
                        ],
                    ),
                    Paragraph(
                        PDFUtils.money(
                            item.discount,
                            currency,
                        ),
                        styles[
                            "POTableRight"
                        ],
                    ),
                    Paragraph(
                        PDFUtils.money(
                            item.total,
                            currency,
                        ),
                        styles[
                            "POTableRight"
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
                17 * mm,
                25 * mm,
                14 * mm,
                24 * mm,
                31 * mm,
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
        purchase_order,
        styles,
    ):
        currency = (
            purchase_order
            .organization
            .currency
            or "INR"
        )

        values = [
            (
                "Subtotal",
                purchase_order.subtotal,
            ),
            (
                "Discount",
                purchase_order
                .discount_amount,
            ),
            (
                "Tax",
                purchase_order.tax_amount,
            ),
            (
                "Total",
                purchase_order.total_amount,
            ),
        ]

        rows = []

        for index, (
            label,
            value,
        ) in enumerate(
            values
        ):

            is_total = (
                index
                ==
                len(values) - 1
            )

            label_text = (
                f"<b>{label}</b>"
                if is_total
                else label
            )

            value_text = (
                PDFUtils.money(
                    value,
                    currency,
                )
            )

            if is_total:

                value_text = (
                    f"<b>{value_text}</b>"
                )

            rows.append(
                [
                    Paragraph(
                        label_text,
                        styles[
                            "POSmallRight"
                        ],
                    ),
                    Paragraph(
                        value_text,
                        styles[
                            "POSmallRight"
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
                        (0, -1),
                        (-1, -1),
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
                "purchase order"
            ),
        )

        canvas_object.restoreState()

    @staticmethod
    def generate(
        *,
        purchase_order,
    ):
        """
        Generate Purchase Order PDF bytes.
        """

        if not purchase_order:

            raise ValueError(
                "Purchase order is required."
            )

        if not purchase_order.organization:

            raise ValueError(
                "Purchase order has no "
                "organization."
            )

        if not purchase_order.supplier:

            raise ValueError(
                "Purchase order has no supplier."
            )

        if not purchase_order.items:

            raise ValueError(
                "Purchase order must contain "
                "at least one item."
            )

        if not purchase_order.po_number:

            raise ValueError(
                "Purchase order number "
                "is required."
            )

        styles = (
            PurchaseOrderPDF
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
                f"Purchase Order "
                f"{purchase_order.po_number}"
            ),
            author=(
                purchase_order
                .organization
                .name
            ),
        )

        story = []

        story.append(
            PurchaseOrderPDF
            ._company_header(
                purchase_order=(
                    purchase_order
                ),
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
            PurchaseOrderPDF
            ._order_meta(
                purchase_order=(
                    purchase_order
                ),
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
            PurchaseOrderPDF
            ._supplier_block(
                purchase_order=(
                    purchase_order
                ),
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
            PurchaseOrderPDF
            ._items_table(
                purchase_order=(
                    purchase_order
                ),
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
            PurchaseOrderPDF
            ._totals(
                purchase_order=(
                    purchase_order
                ),
                styles=styles,
            )
        ]

        if purchase_order.notes:

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
                        "POSection"
                    ],
                )
            )

            summary.append(
                Paragraph(
                    PDFUtils.safe_text(
                        purchase_order.notes
                    ),
                    styles[
                        "POSmall"
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
                PurchaseOrderPDF
                ._draw_page_frame
            ),
            onLaterPages=(
                PurchaseOrderPDF
                ._draw_page_frame
            ),
            canvasmaker=(
                PurchaseOrderNumberedCanvas
            ),
        )

        pdf_bytes = (
            buffer.getvalue()
        )

        buffer.close()

        if not pdf_bytes:

            raise ValueError(
                "Purchase Order PDF "
                "generation failed."
            )

        return pdf_bytes