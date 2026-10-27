from io import BytesIO
from decimal import Decimal

from reportlab.lib import colors
from reportlab.lib.enums import (
    TA_RIGHT,
)
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


# ==================================================
# PAGE NUMBER CANVAS
# ==================================================

class SalesOrderNumberedCanvas(
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


# ==================================================
# SALES ORDER PDF
# ==================================================

class SalesOrderPDF:

    @staticmethod
    def _safe_decimal(
        value,
    ):
        if value is None:
            return Decimal(
                "0.00"
            )

        return Decimal(
            str(value)
        )

    @staticmethod
    def _build_styles(
    ):
        styles = (
            getSampleStyleSheet()
        )

        styles.add(
            ParagraphStyle(
                name="SOCompany",
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
                name="SOTitle",
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
                name="SOSmall",
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
                name="SOSmallRight",
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
                name="SOSection",
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
                name="SOTable",
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
                name="SOTableRight",
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
        sales_order,
        styles,
    ):
        organization = (
            sales_order.organization
        )

        left = [
            Paragraph(
                PDFUtils.safe_text(
                    organization.name
                ),
                styles[
                    "SOCompany"
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
                            "SOSmall"
                        ],
                    )
                )

        right = [
            Paragraph(
                "SALES ORDER",
                styles[
                    "SOTitle"
                ],
            ),
            Spacer(
                1,
                2 * mm,
            ),
            Paragraph(
                (
                    "<b>SO #:</b> "
                    f"{sales_order.so_number}"
                ),
                styles[
                    "SOSmallRight"
                ],
            ),
            Paragraph(
                (
                    "<b>Status:</b> "
                    f"{sales_order.status}"
                ),
                styles[
                    "SOSmallRight"
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
        sales_order,
        styles,
    ):
        warehouse = (
            sales_order.warehouse
        )

        warehouse_text = "-"

        if warehouse:

            warehouse_text = (
                f"{warehouse.name} "
                f"({warehouse.code})"
            )

        expected_date = (
            PDFUtils.date(
                sales_order
                .expected_delivery_date
            )
            or "-"
        )

        data = [
            [
                Paragraph(
                    "<b>Order Date</b>",
                    styles[
                        "SOSmall"
                    ],
                ),
                Paragraph(
                    PDFUtils.date(
                        sales_order.order_date
                    ),
                    styles[
                        "SOSmall"
                    ],
                ),
                Paragraph(
                    "<b>Expected Delivery</b>",
                    styles[
                        "SOSmall"
                    ],
                ),
                Paragraph(
                    expected_date,
                    styles[
                        "SOSmall"
                    ],
                ),
            ],
            [
                Paragraph(
                    "<b>Warehouse</b>",
                    styles[
                        "SOSmall"
                    ],
                ),
                Paragraph(
                    warehouse_text,
                    styles[
                        "SOSmall"
                    ],
                ),
                Paragraph(
                    "<b>Currency</b>",
                    styles[
                        "SOSmall"
                    ],
                ),
                Paragraph(
                    PDFUtils.safe_text(
                        sales_order
                        .organization
                        .currency,
                        "INR",
                    ),
                    styles[
                        "SOSmall"
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
        sales_order,
        styles,
    ):
        customer = (
            sales_order.customer
        )

        if not customer:
            raise ValueError(
                "Sales order has no customer."
            )

        billing_address = ", ".join(
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

        shipping_address = (
            customer.shipping_address
            or "-"
        )

        left = [
            Paragraph(
                "CUSTOMER / BILL TO",
                styles[
                    "SOSection"
                ],
            ),
            Paragraph(
                (
                    f"<b>"
                    f"{PDFUtils.safe_text(customer.name)}"
                    f"</b>"
                ),
                styles[
                    "SOSmall"
                ],
            ),
        ]

        if customer.code:

            left.append(
                Paragraph(
                    (
                        "<b>Customer Code:</b> "
                        f"{customer.code}"
                    ),
                    styles[
                        "SOSmall"
                    ],
                )
            )

        if billing_address:

            left.append(
                Paragraph(
                    billing_address,
                    styles[
                        "SOSmall"
                    ],
                )
            )

        if customer.gstin:

            left.append(
                Paragraph(
                    (
                        "<b>GSTIN:</b> "
                        f"{customer.gstin}"
                    ),
                    styles[
                        "SOSmall"
                    ],
                )
            )

        if customer.email:

            left.append(
                Paragraph(
                    (
                        "<b>Email:</b> "
                        f"{customer.email}"
                    ),
                    styles[
                        "SOSmall"
                    ],
                )
            )

        if customer.phone:

            left.append(
                Paragraph(
                    (
                        "<b>Phone:</b> "
                        f"{customer.phone}"
                    ),
                    styles[
                        "SOSmall"
                    ],
                )
            )

        right = [
            Paragraph(
                "SHIP TO",
                styles[
                    "SOSection"
                ],
            ),
            Paragraph(
                PDFUtils.safe_text(
                    shipping_address,
                    "-",
                ),
                styles[
                    "SOSmall"
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
                90 * mm,
                90 * mm,
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
                        "INNERGRID",
                        (0, 0),
                        (-1, -1),
                        0.25,
                        colors.HexColor(
                            "#DDDDDD"
                        ),
                    ),
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
                        6,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        6,
                    ),
                ]
            )
        )

        return table

    @staticmethod
    def _warehouse_block(
        *,
        sales_order,
        styles,
    ):
        warehouse = (
            sales_order.warehouse
        )

        if not warehouse:
            return None

        address = ", ".join(
            str(value).strip()
            for value in [
                warehouse.address,
                warehouse.city,
                warehouse.state,
                warehouse.pincode,
                warehouse.country,
            ]
            if value
        )

        data = [
            [
                Paragraph(
                    "FULFILMENT WAREHOUSE",
                    styles[
                        "SOSection"
                    ],
                )
            ],
            [
                Paragraph(
                    (
                        f"<b>{warehouse.name}</b> "
                        f"({warehouse.code})"
                    ),
                    styles[
                        "SOSmall"
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
                            "SOSmall"
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
        sales_order,
        styles,
    ):
        currency = (
            sales_order
            .organization
            .currency
            or "INR"
        )

        rows = [
            [
                Paragraph(
                    "<b>SKU</b>",
                    styles[
                        "SOTable"
                    ],
                ),
                Paragraph(
                    "<b>Item</b>",
                    styles[
                        "SOTable"
                    ],
                ),
                Paragraph(
                    "<b>Qty</b>",
                    styles[
                        "SOTableRight"
                    ],
                ),
                Paragraph(
                    "<b>Fulfilled</b>",
                    styles[
                        "SOTableRight"
                    ],
                ),
                Paragraph(
                    "<b>Rate</b>",
                    styles[
                        "SOTableRight"
                    ],
                ),
                Paragraph(
                    "<b>Tax %</b>",
                    styles[
                        "SOTableRight"
                    ],
                ),
                Paragraph(
                    "<b>Discount</b>",
                    styles[
                        "SOTableRight"
                    ],
                ),
                Paragraph(
                    "<b>Amount</b>",
                    styles[
                        "SOTableRight"
                    ],
                ),
            ]
        ]

        for item in sales_order.items:

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
                    f"<font size='6.5'>"
                    f"{PDFUtils.safe_text(description)}"
                    f"</font>"
                )

            if unit:

                item_name += (
                    "<br/>"
                    f"<font size='6.5'>"
                    f"Unit: {unit}"
                    f"</font>"
                )

            rows.append(
                [
                    Paragraph(
                        PDFUtils.safe_text(
                            sku,
                            "-",
                        ),
                        styles[
                            "SOTable"
                        ],
                    ),
                    Paragraph(
                        item_name,
                        styles[
                            "SOTable"
                        ],
                    ),
                    Paragraph(
                        PDFUtils.decimal(
                            item.quantity
                        ),
                        styles[
                            "SOTableRight"
                        ],
                    ),
                    Paragraph(
                        PDFUtils.decimal(
                            item
                            .fulfilled_quantity
                        ),
                        styles[
                            "SOTableRight"
                        ],
                    ),
                    Paragraph(
                        PDFUtils.money(
                            item.unit_price,
                            currency,
                        ),
                        styles[
                            "SOTableRight"
                        ],
                    ),
                    Paragraph(
                        PDFUtils.decimal(
                            item.tax_rate
                        ),
                        styles[
                            "SOTableRight"
                        ],
                    ),
                    Paragraph(
                        PDFUtils.money(
                            item.discount,
                            currency,
                        ),
                        styles[
                            "SOTableRight"
                        ],
                    ),
                    Paragraph(
                        PDFUtils.money(
                            item.line_total,
                            currency,
                        ),
                        styles[
                            "SOTableRight"
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
        sales_order,
        styles,
    ):
        currency = (
            sales_order
            .organization
            .currency
            or "INR"
        )

        values = [
            (
                "Subtotal",
                sales_order.subtotal,
            ),
            (
                "Discount",
                sales_order
                .discount_amount,
            ),
            (
                "Tax",
                sales_order.tax_amount,
            ),
            (
                "Total",
                sales_order.total_amount,
            ),
        ]

        rows = []

        for index, (
            label,
            value,
        ) in enumerate(values):

            bold = (
                index
                ==
                len(values) - 1
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
                            "SOSmallRight"
                        ],
                    ),
                    Paragraph(
                        value_text,
                        styles[
                            "SOSmallRight"
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
                "sales order"
            ),
        )

        canvas_object.restoreState()

    @staticmethod
    def generate(
        *,
        sales_order,
    ):
        """
        Generate Sales Order PDF bytes.
        """

        if not sales_order:

            raise ValueError(
                "Sales order is required."
            )

        if not sales_order.organization:

            raise ValueError(
                "Sales order has no "
                "organization."
            )

        if not sales_order.customer:

            raise ValueError(
                "Sales order has no customer."
            )

        if not sales_order.items:

            raise ValueError(
                "Sales order must contain "
                "at least one item."
            )

        if not sales_order.so_number:

            raise ValueError(
                "Sales order number "
                "is required."
            )

        styles = (
            SalesOrderPDF
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
                f"Sales Order "
                f"{sales_order.so_number}"
            ),
            author=(
                sales_order
                .organization
                .name
            ),
        )

        story = []

        story.append(
            SalesOrderPDF
            ._company_header(
                sales_order=sales_order,
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
            SalesOrderPDF
            ._order_meta(
                sales_order=sales_order,
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
            SalesOrderPDF
            ._customer_block(
                sales_order=sales_order,
                styles=styles,
            )
        )

        warehouse_block = (
            SalesOrderPDF
            ._warehouse_block(
                sales_order=sales_order,
                styles=styles,
            )
        )

        if warehouse_block:

            story.append(
                Spacer(
                    1,
                    5 * mm,
                )
            )

            story.append(
                warehouse_block
            )

        story.append(
            Spacer(
                1,
                7 * mm,
            )
        )

        story.append(
            SalesOrderPDF
            ._items_table(
                sales_order=sales_order,
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
            SalesOrderPDF
            ._totals(
                sales_order=sales_order,
                styles=styles,
            )
        ]

        if sales_order.notes:

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
                        "SOSection"
                    ],
                )
            )

            summary.append(
                Paragraph(
                    PDFUtils.safe_text(
                        sales_order.notes
                    ),
                    styles[
                        "SOSmall"
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
                SalesOrderPDF
                ._draw_page_frame
            ),
            onLaterPages=(
                SalesOrderPDF
                ._draw_page_frame
            ),
            canvasmaker=(
                SalesOrderNumberedCanvas
            ),
        )

        pdf_bytes = (
            buffer.getvalue()
        )

        buffer.close()

        if not pdf_bytes:

            raise ValueError(
                "Sales Order PDF "
                "generation failed."
            )

        return pdf_bytes