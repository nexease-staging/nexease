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


class SupplierPaymentReceiptCanvas(
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


class SupplierPaymentReceiptPDF:

    @staticmethod
    def _build_styles():
        styles = (
            getSampleStyleSheet()
        )

        styles.add(
            ParagraphStyle(
                name="SPRCompany",
                parent=styles["Heading1"],
                fontName="Helvetica-Bold",
                fontSize=16,
                leading=19,
            )
        )

        styles.add(
            ParagraphStyle(
                name="SPRTitle",
                parent=styles["Heading1"],
                fontName="Helvetica-Bold",
                fontSize=19,
                leading=22,
                alignment=TA_RIGHT,
            )
        )

        styles.add(
            ParagraphStyle(
                name="SPRSmall",
                parent=styles["Normal"],
                fontName="Helvetica",
                fontSize=8.5,
                leading=11,
            )
        )

        styles.add(
            ParagraphStyle(
                name="SPRSmallRight",
                parent=styles["Normal"],
                fontName="Helvetica",
                fontSize=8.5,
                leading=11,
                alignment=TA_RIGHT,
            )
        )

        styles.add(
            ParagraphStyle(
                name="SPRSection",
                parent=styles["Normal"],
                fontName="Helvetica-Bold",
                fontSize=9,
                leading=12,
            )
        )

        styles.add(
            ParagraphStyle(
                name="SPRTable",
                parent=styles["Normal"],
                fontName="Helvetica",
                fontSize=7.5,
                leading=9,
            )
        )

        styles.add(
            ParagraphStyle(
                name="SPRTableRight",
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
        payment,
        styles,
    ):
        organization = (
            payment.organization
        )

        left = [
            Paragraph(
                PDFUtils.safe_text(
                    organization.name
                ),
                styles["SPRCompany"],
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
                        styles["SPRSmall"],
                    )
                )

        right = [
            Paragraph(
                "SUPPLIER PAYMENT",
                styles["SPRTitle"],
            ),
            Spacer(
                1,
                2 * mm,
            ),
            Paragraph(
                (
                    "<b>Payment #:</b> "
                    f"{payment.payment_number}"
                ),
                styles["SPRSmallRight"],
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
    def _payment_meta(
        *,
        payment,
        styles,
    ):
        bank_account = (
            payment.bank_account
        )

        account_text = "-"

        if bank_account:
            account_text = (
                bank_account.account_name
            )

            if bank_account.account_type:
                account_text += (
                    f" ({bank_account.account_type})"
                )

            if bank_account.bank_name:
                account_text += (
                    f" - {bank_account.bank_name}"
                )

        data = [
            [
                Paragraph(
                    "<b>Payment Date</b>",
                    styles["SPRSmall"],
                ),
                Paragraph(
                    PDFUtils.date(
                        payment.payment_date
                    ),
                    styles["SPRSmall"],
                ),
                Paragraph(
                    "<b>Payment Method</b>",
                    styles["SPRSmall"],
                ),
                Paragraph(
                    PDFUtils.safe_text(
                        payment.payment_method,
                        "-",
                    ),
                    styles["SPRSmall"],
                ),
            ],
            [
                Paragraph(
                    "<b>Reference</b>",
                    styles["SPRSmall"],
                ),
                Paragraph(
                    PDFUtils.safe_text(
                        payment.reference_number,
                        "-",
                    ),
                    styles["SPRSmall"],
                ),
                Paragraph(
                    "<b>Payment Account</b>",
                    styles["SPRSmall"],
                ),
                Paragraph(
                    PDFUtils.safe_text(
                        account_text,
                        "-",
                    ),
                    styles["SPRSmall"],
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
                        colors.HexColor("#F2F2F2"),
                    ),
                    (
                        "BACKGROUND",
                        (2, 0),
                        (2, -1),
                        colors.HexColor("#F2F2F2"),
                    ),
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.3,
                        colors.HexColor("#D9D9D9"),
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
        payment,
        styles,
    ):
        supplier = (
            payment.supplier
        )

        if not supplier:
            raise ValueError(
                "Supplier payment "
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
                    "PAID TO",
                    styles["SPRSection"],
                )
            ],
            [
                Paragraph(
                    (
                        f"<b>"
                        f"{PDFUtils.safe_text(supplier.name)}"
                        f"</b>"
                    ),
                    styles["SPRSmall"],
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
                        styles["SPRSmall"],
                    )
                ]
            )

        if address:
            data.append(
                [
                    Paragraph(
                        address,
                        styles["SPRSmall"],
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
                        styles["SPRSmall"],
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
                        styles["SPRSmall"],
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
                        styles["SPRSmall"],
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
                        colors.HexColor("#D0D0D0"),
                    ),
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.HexColor("#F4F4F4"),
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
    def _allocations_table(
        *,
        payment,
        styles,
    ):
        currency = (
            payment.organization.currency
            or "INR"
        )

        rows = [
            [
                Paragraph(
                    "<b>Vendor Bill</b>",
                    styles["SPRTable"],
                ),
                Paragraph(
                    "<b>Supplier Invoice</b>",
                    styles["SPRTable"],
                ),
                Paragraph(
                    "<b>Bill Total</b>",
                    styles["SPRTableRight"],
                ),
                Paragraph(
                    "<b>Allocated</b>",
                    styles["SPRTableRight"],
                ),
                Paragraph(
                    "<b>Status</b>",
                    styles["SPRTable"],
                ),
            ]
        ]

        for allocation in (
            payment.allocations
        ):
            bill = (
                allocation.vendor_bill
            )

            rows.append(
                [
                    Paragraph(
                        PDFUtils.safe_text(
                            (
                                bill.bill_number
                                if bill
                                else "-"
                            )
                        ),
                        styles["SPRTable"],
                    ),
                    Paragraph(
                        PDFUtils.safe_text(
                            (
                                bill.supplier_invoice_number
                                if bill
                                else "-"
                            ),
                            "-",
                        ),
                        styles["SPRTable"],
                    ),
                    Paragraph(
                        PDFUtils.money(
                            (
                                bill.total_amount
                                if bill
                                else 0
                            ),
                            currency,
                        ),
                        styles["SPRTableRight"],
                    ),
                    Paragraph(
                        PDFUtils.money(
                            allocation.amount,
                            currency,
                        ),
                        styles["SPRTableRight"],
                    ),
                    Paragraph(
                        PDFUtils.safe_text(
                            (
                                bill.status
                                if bill
                                else "-"
                            )
                        ),
                        styles["SPRTable"],
                    ),
                ]
            )

        table = Table(
            rows,
            repeatRows=1,
            colWidths=[
                38 * mm,
                48 * mm,
                33 * mm,
                33 * mm,
                28 * mm,
            ],
        )

        table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.HexColor("#E8E8E8"),
                    ),
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.35,
                        colors.HexColor("#CCCCCC"),
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
    def _amount_summary(
        *,
        payment,
        styles,
    ):
        currency = (
            payment.organization.currency
            or "INR"
        )

        allocated_total = sum(
            (
                allocation.amount
                for allocation
                in payment.allocations
            ),
            0,
        )

        rows = [
            [
                Paragraph(
                    "<b>Amount Paid</b>",
                    styles["SPRSmallRight"],
                ),
                Paragraph(
                    (
                        "<b>"
                        f"{PDFUtils.money(payment.amount, currency)}"
                        "</b>"
                    ),
                    styles["SPRSmallRight"],
                ),
            ],
            [
                Paragraph(
                    "Allocated Amount",
                    styles["SPRSmallRight"],
                ),
                Paragraph(
                    PDFUtils.money(
                        allocated_total,
                        currency,
                    ),
                    styles["SPRSmallRight"],
                ),
            ],
        ]

        table = Table(
            rows,
            colWidths=[
                40 * mm,
                45 * mm,
            ],
            hAlign="RIGHT",
        )

        table.setStyle(
            TableStyle(
                [
                    (
                        "LINEABOVE",
                        (0, 0),
                        (-1, 0),
                        0.8,
                        colors.black,
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
            colors.HexColor("#DDDDDD")
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
            colors.HexColor("#666666")
        )

        canvas_object.drawString(
            15 * mm,
            9 * mm,
            (
                "Computer-generated "
                "supplier payment receipt"
            ),
        )

        canvas_object.restoreState()

    @staticmethod
    def generate(
        *,
        payment,
    ):
        if not payment:
            raise ValueError(
                "Supplier payment "
                "is required."
            )

        if not payment.organization:
            raise ValueError(
                "Supplier payment has "
                "no organization."
            )

        if not payment.supplier:
            raise ValueError(
                "Supplier payment has "
                "no supplier."
            )

        if not payment.payment_number:
            raise ValueError(
                "Payment number "
                "is required."
            )

        if payment.amount <= 0:
            raise ValueError(
                "Payment amount must "
                "be greater than zero."
            )

        styles = (
            SupplierPaymentReceiptPDF
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
                f"Supplier Payment "
                f"{payment.payment_number}"
            ),
            author=(
                payment.organization.name
            ),
        )

        story = [
            SupplierPaymentReceiptPDF
            ._company_header(
                payment=payment,
                styles=styles,
            ),
            Spacer(
                1,
                7 * mm,
            ),
            SupplierPaymentReceiptPDF
            ._payment_meta(
                payment=payment,
                styles=styles,
            ),
            Spacer(
                1,
                6 * mm,
            ),
            SupplierPaymentReceiptPDF
            ._supplier_block(
                payment=payment,
                styles=styles,
            ),
            Spacer(
                1,
                7 * mm,
            ),
            Paragraph(
                "PAYMENT ALLOCATION",
                styles["SPRSection"],
            ),
            Spacer(
                1,
                2 * mm,
            ),
            SupplierPaymentReceiptPDF
            ._allocations_table(
                payment=payment,
                styles=styles,
            ),
            Spacer(
                1,
                7 * mm,
            ),
            SupplierPaymentReceiptPDF
            ._amount_summary(
                payment=payment,
                styles=styles,
            ),
        ]

        if payment.notes:
            story.extend(
                [
                    Spacer(
                        1,
                        7 * mm,
                    ),
                    Paragraph(
                        "<b>Notes</b>",
                        styles["SPRSection"],
                    ),
                    Paragraph(
                        PDFUtils.safe_text(
                            payment.notes
                        ),
                        styles["SPRSmall"],
                    ),
                ]
            )

        document.build(
            story,
            onFirstPage=(
                SupplierPaymentReceiptPDF
                ._draw_page_frame
            ),
            onLaterPages=(
                SupplierPaymentReceiptPDF
                ._draw_page_frame
            ),
            canvasmaker=(
                SupplierPaymentReceiptCanvas
            ),
        )

        pdf_bytes = (
            buffer.getvalue()
        )

        buffer.close()

        if not pdf_bytes:
            raise ValueError(
                "Supplier payment receipt "
                "PDF generation failed."
            )

        return pdf_bytes