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


class CustomerPaymentReceiptCanvas(
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


class CustomerPaymentReceiptPDF:

    @staticmethod
    def _build_styles(
    ):
        styles = (
            getSampleStyleSheet()
        )

        styles.add(
            ParagraphStyle(
                name="CPRCompany",
                parent=styles[
                    "Heading1"
                ],
                fontName=(
                    "Helvetica-Bold"
                ),
                fontSize=16,
                leading=19,
            )
        )

        styles.add(
            ParagraphStyle(
                name="CPRTitle",
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
                name="CPRSmall",
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
                name="CPRSmallRight",
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
                name="CPRSection",
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
                name="CPRTable",
                parent=styles[
                    "Normal"
                ],
                fontName="Helvetica",
                fontSize=7.5,
                leading=9,
            )
        )

        styles.add(
            ParagraphStyle(
                name="CPRTableRight",
                parent=styles[
                    "Normal"
                ],
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
                styles[
                    "CPRCompany"
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
                            "CPRSmall"
                        ],
                    )
                )

        right = [
            Paragraph(
                "PAYMENT RECEIPT",
                styles[
                    "CPRTitle"
                ],
            ),
            Spacer(
                1,
                2 * mm,
            ),
            Paragraph(
                (
                    "<b>Receipt #:</b> "
                    f"{payment.payment_number}"
                ),
                styles[
                    "CPRSmallRight"
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
    def _payment_meta(
        *,
        payment,
        styles,
    ):
        bank_account = (
            payment.bank_account
        )

        bank_text = "-"

        if bank_account:

            bank_text = (
                bank_account.account_name
            )

            if bank_account.bank_name:

                bank_text += (
                    f" - "
                    f"{bank_account.bank_name}"
                )

        data = [
            [
                Paragraph(
                    "<b>Payment Date</b>",
                    styles[
                        "CPRSmall"
                    ],
                ),
                Paragraph(
                    PDFUtils.date(
                        payment.payment_date
                    ),
                    styles[
                        "CPRSmall"
                    ],
                ),
                Paragraph(
                    "<b>Payment Method</b>",
                    styles[
                        "CPRSmall"
                    ],
                ),
                Paragraph(
                    PDFUtils.safe_text(
                        payment.payment_method,
                        "-",
                    ),
                    styles[
                        "CPRSmall"
                    ],
                ),
            ],
            [
                Paragraph(
                    "<b>Reference</b>",
                    styles[
                        "CPRSmall"
                    ],
                ),
                Paragraph(
                    PDFUtils.safe_text(
                        payment.reference_number,
                        "-",
                    ),
                    styles[
                        "CPRSmall"
                    ],
                ),
                Paragraph(
                    "<b>Account</b>",
                    styles[
                        "CPRSmall"
                    ],
                ),
                Paragraph(
                    PDFUtils.safe_text(
                        bank_text,
                        "-",
                    ),
                    styles[
                        "CPRSmall"
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
        payment,
        styles,
    ):
        customer = (
            payment.customer
        )

        if not customer:
            raise ValueError(
                "Customer payment "
                "has no customer."
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
                    "RECEIVED FROM",
                    styles[
                        "CPRSection"
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
                        "CPRSmall"
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
                            "CPRSmall"
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
                            "CPRSmall"
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
                            "CPRSmall"
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
                            "CPRSmall"
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
                            "CPRSmall"
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
                    "<b>Invoice</b>",
                    styles[
                        "CPRTable"
                    ],
                ),
                Paragraph(
                    "<b>Invoice Total</b>",
                    styles[
                        "CPRTableRight"
                    ],
                ),
                Paragraph(
                    "<b>Allocated</b>",
                    styles[
                        "CPRTableRight"
                    ],
                ),
                Paragraph(
                    "<b>Invoice Status</b>",
                    styles[
                        "CPRTable"
                    ],
                ),
            ]
        ]

        for allocation in (
            payment.allocations
        ):

            invoice = (
                allocation.invoice
            )

            rows.append(
                [
                    Paragraph(
                        PDFUtils.safe_text(
                            invoice.invoice_number
                            if invoice
                            else "-"
                        ),
                        styles[
                            "CPRTable"
                        ],
                    ),
                    Paragraph(
                        PDFUtils.money(
                            (
                                invoice.total_amount
                                if invoice
                                else 0
                            ),
                            currency,
                        ),
                        styles[
                            "CPRTableRight"
                        ],
                    ),
                    Paragraph(
                        PDFUtils.money(
                            allocation.amount,
                            currency,
                        ),
                        styles[
                            "CPRTableRight"
                        ],
                    ),
                    Paragraph(
                        PDFUtils.safe_text(
                            (
                                invoice.status
                                if invoice
                                else "-"
                            )
                        ),
                        styles[
                            "CPRTable"
                        ],
                    ),
                ]
            )

        table = Table(
            rows,
            repeatRows=1,
            colWidths=[
                50 * mm,
                45 * mm,
                45 * mm,
                40 * mm,
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
                    "<b>Amount Received</b>",
                    styles[
                        "CPRSmallRight"
                    ],
                ),
                Paragraph(
                    (
                        "<b>"
                        f"{PDFUtils.money(payment.amount, currency)}"
                        "</b>"
                    ),
                    styles[
                        "CPRSmallRight"
                    ],
                ),
            ],
            [
                Paragraph(
                    "Allocated Amount",
                    styles[
                        "CPRSmallRight"
                    ],
                ),
                Paragraph(
                    PDFUtils.money(
                        allocated_total,
                        currency,
                    ),
                    styles[
                        "CPRSmallRight"
                    ],
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
                "payment receipt"
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
                "Customer payment "
                "is required."
            )

        if not payment.organization:
            raise ValueError(
                "Customer payment has "
                "no organization."
            )

        if not payment.customer:
            raise ValueError(
                "Customer payment has "
                "no customer."
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
            CustomerPaymentReceiptPDF
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
                f"Payment Receipt "
                f"{payment.payment_number}"
            ),
            author=(
                payment.organization.name
            ),
        )

        story = [
            CustomerPaymentReceiptPDF
            ._company_header(
                payment=payment,
                styles=styles,
            ),
            Spacer(
                1,
                7 * mm,
            ),
            CustomerPaymentReceiptPDF
            ._payment_meta(
                payment=payment,
                styles=styles,
            ),
            Spacer(
                1,
                6 * mm,
            ),
            CustomerPaymentReceiptPDF
            ._customer_block(
                payment=payment,
                styles=styles,
            ),
            Spacer(
                1,
                7 * mm,
            ),
            Paragraph(
                "PAYMENT ALLOCATION",
                styles[
                    "CPRSection"
                ],
            ),
            Spacer(
                1,
                2 * mm,
            ),
            CustomerPaymentReceiptPDF
            ._allocations_table(
                payment=payment,
                styles=styles,
            ),
            Spacer(
                1,
                7 * mm,
            ),
            CustomerPaymentReceiptPDF
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
                        styles[
                            "CPRSection"
                        ],
                    ),
                    Paragraph(
                        PDFUtils.safe_text(
                            payment.notes
                        ),
                        styles[
                            "CPRSmall"
                        ],
                    ),
                ]
            )

        document.build(
            story,
            onFirstPage=(
                CustomerPaymentReceiptPDF
                ._draw_page_frame
            ),
            onLaterPages=(
                CustomerPaymentReceiptPDF
                ._draw_page_frame
            ),
            canvasmaker=(
                CustomerPaymentReceiptCanvas
            ),
        )

        pdf_bytes = (
            buffer.getvalue()
        )

        buffer.close()

        if not pdf_bytes:
            raise ValueError(
                "Payment receipt PDF "
                "generation failed."
            )

        return pdf_bytes