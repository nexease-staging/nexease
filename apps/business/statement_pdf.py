"""Shareable PDFs for statements and Tally vouchers, plus NexEase party statements.

Same look as the invoice templates (NX font, the business's accent colour and logo), A4.
"""
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from . import doc_templates as dt  # registers the NX fonts

D0 = Decimal(0)
IST = timedelta(hours=5, minutes=30)
CENT = Decimal("0.01")


def money(v, sign=False):
    v = Decimal(str(v or 0)).quantize(CENT)
    text = dt.indian_money(abs(v)) if hasattr(dt, "indian_money") else f"{abs(v):,.2f}"
    return ("-" if sign and v < 0 else "") + text


def drcr(v):
    v = Decimal(str(v or 0))
    return f"{money(v)} {'Dr' if v >= 0 else 'Cr'}"


def short_date(value):
    text = nice_date(value)
    return text[:-4] + text[-2:] if len(text) == 11 else text


def nice_date(value):
    if not value:
        return ""
    if isinstance(value, str):
        try:
            value = date.fromisoformat(value[:10])
        except ValueError:
            return value
    return value.strftime("%d %b %Y")


class Kit:
    def __init__(self, org):
        self.org = org
        brand = dt.branding(org)
        self.brand = brand
        self.accent = colors.HexColor(brand.get("accent") or brand.get("accent_color") or "#14234B")
        base = ParagraphStyle("b", fontName="NX", fontSize=8.6, leading=11, textColor=colors.HexColor("#1f2937"))
        self.s = {
            "cell": base, "small": ParagraphStyle("s", parent=base, fontSize=7.6, leading=9.6, textColor=colors.HexColor("#4b5563")),
            "right": ParagraphStyle("r", parent=base, alignment=2), "bold": ParagraphStyle("bd", parent=base, fontName="NX-Bold"),
            "boldr": ParagraphStyle("bdr", parent=base, fontName="NX-Bold", alignment=2),
            "title": ParagraphStyle("t", parent=base, fontName="NX-Bold", fontSize=15, leading=19, textColor=self.accent),
            "org": ParagraphStyle("o", parent=base, fontName="NX-Bold", fontSize=12.5, leading=16),
            "head": ParagraphStyle("h", parent=base, fontName="NX-Bold", fontSize=7.8, textColor=colors.white),
            "headr": ParagraphStyle("hr", parent=base, fontName="NX-Bold", fontSize=7.8, textColor=colors.white, alignment=2),
            "section": ParagraphStyle("sec", parent=base, fontName="NX-Bold", fontSize=10, leading=13, textColor=self.accent, spaceBefore=6),
        }

    def p(self, value, style="cell"):
        return Paragraph(escape(str(value if value not in (None, "") else "")).replace("\n", "<br/>"), self.s[style])

    def header(self, title, subtitle, seller=None):
        reg = dt.registration(self.org)
        seller = seller or dt.seller_block(self.org, reg)
        lines = [self.p(seller["name"], "org")]
        if seller.get("address"):
            lines.append(self.p(seller["address"], "small"))
        contact = " · ".join(x for x in [seller.get("phone"), seller.get("email")] if x)
        if contact:
            lines.append(self.p(contact, "small"))
        if seller.get("gstin"):
            lines.append(self.p("GSTIN " + seller["gstin"], "small"))
        logo = dt.logo_image(self.brand.get("logo"), 34 * mm, 18 * mm) if self.brand.get("logo") else None
        right = [self.p(title, "title"), self.p(subtitle, "small")]
        left = [logo] + lines if logo else lines
        t = Table([[left, right]], colWidths=[110 * mm, 70 * mm])
        t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("ALIGN", (1, 0), (1, 0), "RIGHT"), ("LEFTPADDING", (0, 0), (-1, -1), 0),
                               ("RIGHTPADDING", (0, 0), (-1, -1), 0), ("LINEBELOW", (0, 0), (-1, 0), 1.2, self.accent), ("BOTTOMPADDING", (0, 0), (-1, -1), 8)]))
        return [t, Spacer(1, 8)]

    def grid(self, head, rows, widths, numeric=(), total=None):
        data = [[self.p(h, "headr" if i in numeric else "head") for i, h in enumerate(head)]]
        for r in rows:
            data.append([c if not isinstance(c, (str, int, float, Decimal)) else self.p(c, "right" if i in numeric else "cell") for i, c in enumerate(r)])
        if total:
            data.append([self.p(c, "boldr" if i in numeric else "bold") for i, c in enumerate(total)])
        t = Table(data, colWidths=widths, repeatRows=1)
        style = [("BACKGROUND", (0, 0), (-1, 0), self.accent), ("VALIGN", (0, 0), (-1, -1), "TOP"), ("LINEBELOW", (0, 1), (-1, -1), 0.3, colors.HexColor("#e5e7eb")),
                 ("TOPPADDING", (0, 0), (-1, -1), 3.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5), ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4)]
        for i in range(1, len(data)):
            if i % 2 == 0:
                style.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor("#f8fafc")))
        if total:
            style += [("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#eef2f7")), ("LINEABOVE", (0, -1), (-1, -1), 0.8, self.accent)]
        t.setStyle(TableStyle(style))
        return t

    def build(self, story, footer):
        buf = BytesIO()
        accent = self.accent

        def page(canvas, doc):
            canvas.saveState()
            canvas.setFont("NX", 7)
            canvas.setFillColor(colors.HexColor("#6b7280"))
            canvas.drawString(15 * mm, 9 * mm, footer)
            canvas.drawRightString(195 * mm, 9 * mm, f"Page {doc.page}")
            canvas.setStrokeColor(accent)
            canvas.line(15 * mm, 12 * mm, 195 * mm, 12 * mm)
            canvas.restoreState()
        doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=15 * mm, rightMargin=15 * mm, topMargin=14 * mm, bottomMargin=18 * mm, title=footer)
        doc.build(story, onFirstPage=page, onLaterPages=page)
        return buf.getvalue()


def generated_note():
    return f"Generated on {(datetime.utcnow() + IST).strftime('%d %b %Y, %I:%M %p')} IST"


def statement_pdf(org, data):
    """data: title, party{name, gstin, address, phone, email}, from, to, opening, closing (debit +), rows[], bills[], source."""
    k = Kit(org)
    party = data["party"]
    story = k.header(data.get("title") or "Statement of account", f"{nice_date(data['from'])} to {nice_date(data['to'])}")
    info = [[k.p("To", "small"), k.p("", "small")],
            [[k.p(party["name"], "bold")] + [k.p(x, "small") for x in [party.get("address"), " · ".join(y for y in [party.get("phone"), party.get("email")] if y),
                                                                          ("GSTIN " + party["gstin"]) if party.get("gstin") else ""] if x],
             k.grid(["Account summary", ""], [["Opening balance", drcr(data["opening"])], ["Total debit", money(data.get("debit", 0))], ["Total credit", money(data.get("credit", 0))]],
                    [40 * mm, 38 * mm], numeric=(1,), total=["Closing balance", drcr(data["closing"])])]]
    t = Table(info, colWidths=[98 * mm, 82 * mm])
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 2)]))
    story += [t, Spacer(1, 10), k.p("Ledger", "section"), Spacer(1, 3)]
    rows = [[short_date(data["from"]), "", "", "Opening balance", "", "", drcr(data["opening"])]]
    rows += [[short_date(r["date"]), r.get("type", ""), r.get("number", ""), r.get("particulars") or r.get("narration") or "", money(r["debit"]) if r.get("debit") else "",
              money(r["credit"]) if r.get("credit") else "", drcr(r["balance"])] for r in data["rows"]]
    story.append(k.grid(["Date", "Type", "No.", "Particulars", "Debit", "Credit", "Balance"], rows,
                        [20 * mm, 24 * mm, 22 * mm, 48 * mm, 22 * mm, 22 * mm, 22 * mm], numeric=(4, 5, 6),
                        total=["", "", "", "Closing balance", money(data.get("debit", 0)), money(data.get("credit", 0)), drcr(data["closing"])]))
    bills = data.get("bills") or []
    if bills:
        story += [Spacer(1, 12), k.p("Pending bills", "section"), Spacer(1, 3)]
        total = sum((abs(Decimal(str(b["amount"]))) for b in bills), D0)
        story.append(k.grid(["Bill", "Bill date", "Due date", "Overdue", "Pending amount"],
                            [[b["name"], nice_date(b["date"]), nice_date(b.get("due")), f"{b['overdue_days']} days" if b.get("overdue_days") else "—", money(abs(Decimal(str(b["amount"]))))] for b in bills],
                            [40 * mm, 32 * mm, 32 * mm, 34 * mm, 42 * mm], numeric=(3, 4), total=["Total", "", "", "", money(total)]))
    if data.get("note"):
        story += [Spacer(1, 10), k.p(data["note"], "small")]
    story += [Spacer(1, 14), k.p("Please verify and let us know of any difference within 7 days. This is a computer-generated statement.", "small")]
    return k.build(story, f"{party['name']} · {data.get('source') or 'NexEase'} · {generated_note()}")


def voucher_pdf(org, v, company=""):
    """A Tally voucher (from tally_api.voucher data)."""
    k = Kit(org)
    story = k.header(v.get("type") or "Voucher", f"No. {v.get('number') or '—'} · {nice_date(v.get('date'))}")
    meta = [["Party", v.get("party") or "—"], ["Date", nice_date(v.get("date"))], ["Amount", money(v.get("amount"))]]
    if v.get("party_gstin"):
        meta.append(["Party GSTIN", v["party_gstin"]])
    if v.get("reference"):
        meta.append(["Reference", v["reference"]])
    story += [k.grid(["Details", ""], meta, [40 * mm, 140 * mm]), Spacer(1, 10)]
    inv = v.get("inventory") or []
    if inv:
        story += [k.p("Items", "section"), Spacer(1, 3), k.grid(["Item", "Quantity", "Rate", "Amount"],
                                                                 [[i["item"], f"{i.get('qty', '')} {i.get('unit', '')}".strip(), money(i.get("rate")), money(i.get("amount"))] for i in inv],
                                                                 [82 * mm, 32 * mm, 30 * mm, 36 * mm], numeric=(1, 2, 3)), Spacer(1, 10)]
    entries = v.get("entries") or []
    dr = sum((Decimal(str(e["debit"] or 0)) for e in entries), D0)
    cr = sum((Decimal(str(e["credit"] or 0)) for e in entries), D0)
    story += [k.p("Accounts", "section"), Spacer(1, 3), k.grid(["Ledger", "Debit", "Credit"], [[e["ledger"], money(e["debit"]) if e["debit"] else "", money(e["credit"]) if e["credit"] else ""] for e in entries],
                                                                [110 * mm, 35 * mm, 35 * mm], numeric=(1, 2), total=["Total", money(dr), money(cr)])]
    if v.get("narration"):
        story += [Spacer(1, 8), k.p("Narration: " + v["narration"], "small")]
    return k.build(story, f"{v.get('type', 'Voucher')} {v.get('number', '')} · {company or 'Tally'} · {generated_note()}")


# --------------------------------------------------------------------------------------------
# NexEase party statement (customer or supplier) from NexEase's own documents
# --------------------------------------------------------------------------------------------

def _utc(day, end=False):
    return datetime.combine(day + timedelta(days=1) if end else day, time.min) - IST


def _day(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return (value + IST).date()
    return value


def party_statement(org, side, party, start, end):
    """side 'customer' | 'supplier'. Debit-positive balance (a supplier balance is usually Cr)."""
    from apps.purchasing.models import SupplierPayment, VendorBill, VendorDebitNote
    from apps.sales.models import CreditNote, CustomerPayment, Invoice
    from .payments_hub import SIDES
    entries = []
    if side == "customer":
        for d in Invoice.objects(organization=org, customer=party, status__in=["ISSUED", "PARTIALLY_PAID", "PAID"]).only("invoice_date", "invoice_number", "total_amount"):
            entries.append((_day(d.invoice_date), "Sales invoice", d.invoice_number, "Sales", Decimal(d.total_amount or 0)))
        for d in CreditNote.objects(organization=org, customer=party, status__nin=["DRAFT", "CANCELLED"]).only("credit_note_date", "credit_note_number", "total_amount"):
            entries.append((_day(d.credit_note_date), "Credit note", d.credit_note_number, "Sales return", -Decimal(d.total_amount or 0)))
        for d in CustomerPayment.objects(organization=org, customer=party).only("payment_date", "payment_number", "amount", "payment_method"):
            entries.append((_day(d.payment_date), "Receipt", d.payment_number, (d.payment_method or "").replace("_", " ").title(), -Decimal(d.amount or 0)))
        open_rows = SIDES["receivable"].rows(org, SIDES["receivable"].open_documents(org, [party.id]))
    else:
        for d in VendorBill.objects(organization=org, supplier=party, status__in=["POSTED", "PARTIALLY_PAID", "PAID"]).only("bill_date", "bill_number", "supplier_invoice_number", "total_amount"):
            entries.append((_day(d.bill_date), "Purchase bill", d.supplier_invoice_number or d.bill_number, "Purchase", -Decimal(d.total_amount or 0)))
        for d in VendorDebitNote.objects(organization=org, supplier=party, status__nin=["DRAFT", "CANCELLED"]).only("debit_note_date", "debit_note_number", "total_amount"):
            entries.append((_day(d.debit_note_date), "Debit note", d.debit_note_number, "Purchase return", Decimal(d.total_amount or 0)))
        for d in SupplierPayment.objects(organization=org, supplier=party).only("payment_date", "payment_number", "amount", "payment_method"):
            entries.append((_day(d.payment_date), "Payment", d.payment_number, (d.payment_method or "").replace("_", " ").title(), Decimal(d.amount or 0)))
        open_rows = SIDES["payable"].rows(org, SIDES["payable"].open_documents(org, [party.id]))
    entries = [e for e in entries if e[0]]
    entries.sort(key=lambda e: (e[0], e[2] or ""))
    opening = sum((e[4] for e in entries if e[0] < start), D0)
    balance, rows, debit, credit = opening, [], D0, D0
    for day, kind, number, particulars, amt in entries:
        if day < start or day > end:
            continue
        balance += amt
        debit += amt if amt > 0 else D0
        credit += -amt if amt < 0 else D0
        rows.append({"date": day.isoformat(), "type": kind, "number": number, "particulars": particulars, "debit": float(amt) if amt > 0 else 0,
                     "credit": float(-amt) if amt < 0 else 0, "balance": float(balance)})
    bills = [{"name": r["number"], "date": r["date"], "due": r["due_date"], "overdue_days": r["days_overdue"], "amount": float(r["outstanding"])} for r in open_rows]
    address = party.billing_address if side == "customer" else party.address
    return {"title": "Statement of account", "party": {"name": party.name, "gstin": party.gstin or "", "address": ", ".join(x for x in [address, party.city, party.state, party.pincode] if x),
                                                     "phone": party.phone or "", "email": party.email or ""},
            "from": start.isoformat(), "to": end.isoformat(), "opening": float(opening), "closing": float(balance), "debit": float(debit), "credit": float(credit),
            "rows": rows, "bills": bills, "source": "NexEase", "outstanding": float(sum((Decimal(str(b["amount"])) for b in bills), D0))}
