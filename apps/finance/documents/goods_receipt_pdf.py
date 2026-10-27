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
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from apps.finance.documents.pdf_utils import (
    PDFUtils,
)


class GoodsReceiptCanvas(
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


class GoodsReceiptPDF:

    @staticmethod
    def _build_styles():
        styles = (
            getSampleStyleSheet()
        )

        styles.add(
            ParagraphStyle(
                name="GRNCompany",
                parent=styles["Heading1"],
                fontName="Helvetica-Bold",
                fontSize=16,
                leading=19,
            )
        )

        styles.add(
            ParagraphStyle(
                name="GRNTitle",
                parent=styles["Heading1"],
                fontName="Helvetica-Bold",
                fontSize=19,
                leading=22,
                alignment=TA_RIGHT,
            )
        )

        styles.add(
            ParagraphStyle(
                name="GRNSmall",
                parent=styles["Normal"],
                fontName="Helvetica",
                fontSize=8.5,
                leading=11,
            )
        )

        styles.add(
            ParagraphStyle(
                name="GRNSmallRight",
                parent=styles["Normal"],
                fontName="Helvetica",
                fontSize=8.5,
                leading=11,
                alignment=TA_RIGHT,
            )
        )

        styles.add(
            ParagraphStyle(
                name="GRNSection",
                parent=styles["Normal"],
                fontName="Helvetica-Bold",
                fontSize=9,
                leading=12,
            )
        )

        styles.add(
            ParagraphStyle(
                name="GRNTable",
                parent=styles["Normal"],
                fontName="Helvetica",
                fontSize=7.5,
                leading=9,
                wordWrap="CJK",
            )
        )

        styles.add(
            ParagraphStyle(
                name="GRNTableRight",
                parent=styles["Normal"],
                fontName="Helvetica",
                fontSize=7.5,
                leading=9,
                alignment=TA_RIGHT,
            )
        )

        return styles

    @staticmethod
    def _company_header(
        *,
        goods_receipt,
        styles,
    ):
        organization = (
            goods_receipt.organization
        )

        left = [
            Paragraph(
                PDFUtils.safe_text(
                    organization.name
                ),
                styles["GRNCompany"],
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
                        styles["GRNSmall"],
                    )
                )

        right = [
            Paragraph(
                "GOODS RECEIPT NOTE",
                styles["GRNTitle"],
            ),
            Spacer(
                1,
                2 * mm,
            ),
            Paragraph(
                (
                    "<b>GRN #:</b> "
                    f"{goods_receipt.grn_number}"
                ),
                styles["GRNSmallRight"],
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
        goods_receipt,
        styles,
    ):
        po_number = "-"

        if goods_receipt.purchase_order:
            po_number = (
                goods_receipt
                .purchase_order
                .po_number
            )

        received_by = "-"

        if goods_receipt.received_by:
            received_by = getattr(
                goods_receipt.received_by,
                "email",
                str(
                    goods_receipt.received_by
                ),
            )

        warehouse_text = "-"

        if goods_receipt.warehouse:
            warehouse_text = (
                f"{goods_receipt.warehouse.name} "
                f"({goods_receipt.warehouse.code})"
            )

        data = [
            [
                Paragraph(
                    "<b>Received Date</b>",
                    styles["GRNSmall"],
                ),
                Paragraph(
                    PDFUtils.datetime(
                        goods_receipt.received_at
                    ),
                    styles["GRNSmall"],
                ),
                Paragraph(
                    "<b>Purchase Order</b>",
                    styles["GRNSmall"],
                ),
                Paragraph(
                    PDFUtils.safe_text(
                        po_number,
                        "-",
                    ),
                    styles["GRNSmall"],
                ),
            ],
            [
                Paragraph(
                    "<b>Warehouse</b>",
                    styles["GRNSmall"],
                ),
                Paragraph(
                    PDFUtils.safe_text(
                        warehouse_text,
                        "-",
                    ),
                    styles["GRNSmall"],
                ),
                Paragraph(
                    "<b>Received By</b>",
                    styles["GRNSmall"],
                ),
                Paragraph(
                    PDFUtils.safe_text(
                        received_by,
                        "-",
                    ),
                    styles["GRNSmall"],
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
        goods_receipt,
        styles,
    ):
        supplier = (
            goods_receipt.supplier
        )

        if not supplier:
            raise ValueError(
                "Goods receipt has no supplier."
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
                    styles["GRNSection"],
                )
            ],
            [
                Paragraph(
                    (
                        f"<b>"
                        f"{PDFUtils.safe_text(supplier.name)}"
                        f"</b>"
                    ),
                    styles["GRNSmall"],
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
                        styles["GRNSmall"],
                    )
                ]
            )

        if address:
            data.append(
                [
                    Paragraph(
                        address,
                        styles["GRNSmall"],
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
                        styles["GRNSmall"],
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
    def _warehouse_block(
        *,
        goods_receipt,
        styles,
    ):
        warehouse = (
            goods_receipt.warehouse
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
                    "RECEIVING WAREHOUSE",
                    styles["GRNSection"],
                )
            ],
            [
                Paragraph(
                    (
                        f"<b>{warehouse.name}</b> "
                        f"({warehouse.code})"
                    ),
                    styles["GRNSmall"],
                )
            ],
        ]

        if address:
            data.append(
                [
                    Paragraph(
                        address,
                        styles["GRNSmall"],
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
                        0.4,
                        colors.HexColor(
                            "#D5D5D5"
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
        goods_receipt,
        styles,
    ):
        rows = [
            [
                Paragraph(
                    "<b>SKU</b>",
                    styles["GRNTable"],
                ),
                Paragraph(
                    "<b>Item</b>",
                    styles["GRNTable"],
                ),
                Paragraph(
                    "<b>Unit</b>",
                    styles["GRNTable"],
                ),
                Paragraph(
                    "<b>Barcode</b>",
                    styles["GRNTable"],
                ),
                Paragraph(
                    "<b>Quantity Received</b>",
                    styles["GRNTableRight"],
                ),
            ]
        ]

        for item in (
            goods_receipt.items
        ):
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
                        styles["GRNTable"],
                    ),
                    Paragraph(
                        item_name,
                        styles["GRNTable"],
                    ),
                    Paragraph(
                        PDFUtils.safe_text(
                            getattr(
                                product,
                                "unit",
                                "-",
                            ),
                            "-",
                        ),
                        styles["GRNTable"],
                    ),
                    Paragraph(
                        PDFUtils.safe_text(
                            getattr(
                                product,
                                "barcode",
                                "-",
                            ),
                            "-",
                        ),
                        styles["GRNTable"],
                    ),
                    Paragraph(
                        PDFUtils.decimal(
                            item.quantity_received
                        ),
                        styles["GRNTableRight"],
                    ),
                ]
            )

        table = Table(
            rows,
            repeatRows=1,
            colWidths=[
                25 * mm,
                65 * mm,
                25 * mm,
                35 * mm,
                30 * mm,
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
                "goods receipt note"
            ),
        )

        canvas_object.restoreState()

    @staticmethod
    def generate(
        *,
        goods_receipt,
    ):
        if not goods_receipt:
            raise ValueError(
                "Goods receipt is required."
            )

        if not goods_receipt.organization:
            raise ValueError(
                "Goods receipt has no "
                "organization."
            )

        if not goods_receipt.grn_number:
            raise ValueError(
                "GRN number is required."
            )

        if not goods_receipt.supplier:
            raise ValueError(
                "Goods receipt has no supplier."
            )

        if not goods_receipt.warehouse:
            raise ValueError(
                "Goods receipt has no warehouse."
            )

        if not goods_receipt.items:
            raise ValueError(
                "Goods receipt must contain "
                "at least one item."
            )

        styles = (
            GoodsReceiptPDF
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
                f"Goods Receipt "
                f"{goods_receipt.grn_number}"
            ),
            author=(
                goods_receipt.organization.name
            ),
        )

        story = [
            GoodsReceiptPDF
            ._company_header(
                goods_receipt=goods_receipt,
                styles=styles,
            ),
            Spacer(
                1,
                7 * mm,
            ),
            GoodsReceiptPDF
            ._meta(
                goods_receipt=goods_receipt,
                styles=styles,
            ),
            Spacer(
                1,
                6 * mm,
            ),
            GoodsReceiptPDF
            ._supplier_block(
                goods_receipt=goods_receipt,
                styles=styles,
            ),
        ]

        warehouse_block = (
            GoodsReceiptPDF
            ._warehouse_block(
                goods_receipt=goods_receipt,
                styles=styles,
            )
        )

        if warehouse_block:
            story.extend(
                [
                    Spacer(
                        1,
                        5 * mm,
                    ),
                    warehouse_block,
                ]
            )

        story.extend(
            [
                Spacer(
                    1,
                    7 * mm,
                ),
                GoodsReceiptPDF
                ._items_table(
                    goods_receipt=goods_receipt,
                    styles=styles,
                ),
            ]
        )

        if goods_receipt.notes:
            story.extend(
                [
                    Spacer(
                        1,
                        7 * mm,
                    ),
                    Paragraph(
                        "<b>Notes</b>",
                        styles["GRNSection"],
                    ),
                    Paragraph(
                        PDFUtils.safe_text(
                            goods_receipt.notes
                        ),
                        styles["GRNSmall"],
                    ),
                ]
            )

        document.build(
            story,
            onFirstPage=(
                GoodsReceiptPDF
                ._draw_page_frame
            ),
            onLaterPages=(
                GoodsReceiptPDF
                ._draw_page_frame
            ),
            canvasmaker=(
                GoodsReceiptCanvas
            ),
        )

        pdf_bytes = (
            buffer.getvalue()
        )

        buffer.close()

        if not pdf_bytes:
            raise ValueError(
                "Goods Receipt PDF "
                "generation failed."
            )

        return pdf_bytes