"""One set of print templates for every sales document.

The business picks a template once (Settings → Invoice formats) and it is used for tax invoices,
bills of supply, estimates / quotations, proforma / sales orders, credit notes and delivery challans.
Each document is first turned into a plain dictionary (see the `from_*` adapters) so all
templates show the same complete details:

seller and buyer with GSTIN, state and contact; ship-to; document number, dates, PO, place of
supply and reverse charge; lines with HSN/SAC, quantity, unit, rate, discount, taxable value, GST
rate and CGST/SGST or IGST; an HSN-wise tax summary; totals with round-off and amount in words;
bank details and a UPI QR code; terms, notes and the authorised signatory; IRN and QR for
registered e-invoices.
"""
import base64
from decimal import ROUND_HALF_UP, Decimal
from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from pathlib import Path
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from .professional_documents import amount_words
from .reference_invoice import indian_money

# DejaVu has the ₹ sign and Indian language glyphs; registering twice is harmless.
_FONTS = Path(__file__).with_name("fonts")
if "NX" not in pdfmetrics.getRegisteredFontNames():
    pdfmetrics.registerFont(TTFont("NX", str(_FONTS / "DejaVuSans.ttf")))
    pdfmetrics.registerFont(TTFont("NX-Bold", str(_FONTS / "DejaVuSans-Bold.ttf")))
    pdfmetrics.registerFontFamily("NX", normal="NX", bold="NX-Bold", italic="NX", boldItalic="NX-Bold")

D0 = Decimal(0)
CENT = Decimal("0.01")

TEMPLATES = [
    ("gst_classic", "GST Classic", "#1f2937", "gst_classic"),
    ("modern", "Modern band", "#0f766e", "modern"),
    ("minimal", "Minimal", "#334155", "minimal"),
    ("retail", "Retail detailed", "#006b58", "retail"),
    ("service", "Service & professional", "#6d28d9", "service"),
    ("thermal", "Thermal receipt (80 mm)", "#111827", "thermal"),
]
DESCRIPTIONS = {
    "gst_classic": "Boxed Indian GST format with CGST/SGST/IGST for every line and an HSN tax summary.",
    "modern": "Coloured header band, clean striped lines. Good for most businesses.",
    "minimal": "Black-and-white, lots of space. Prints well on any printer.",
    "retail": "Detailed retail grid with MRP-style columns, bank and UPI block.",
    "service": "For services: description first, SAC, service period, no stock columns.",
    "thermal": "Narrow 80 mm roll for counter billing printers.",
}
# Formats from earlier versions keep working and map to the nearest new design.
LEGACY = {"classic": "gst_classic", "compact": "gst_classic", "contractor": "gst_classic", "executive": "modern", "emerald": "modern", "bold": "modern",
          "elegant": "minimal", "retail_blue": "retail", "retail_emerald": "retail"}
IDS = {t[0] for t in TEMPLATES}


def resolve(template_id):
    t = LEGACY.get(template_id or "", template_id or "gst_classic")
    return t if t in IDS else "gst_classic"


def accepted_ids():
    return IDS | set(LEGACY)


def d(value):
    try:
        return Decimal(str(value if value not in (None, "") else 0))
    except Exception:
        return D0


def q(value):
    return d(value).quantize(CENT, rounding=ROUND_HALF_UP)


def num(value):
    """Quantities without trailing zeros: 2, 2.5, 0.125."""
    text = f"{d(value).normalize():f}"
    return text if "." not in text else text.rstrip("0").rstrip(".")


# --------------------------------------------------------------------------------------------
# Shared building blocks
# --------------------------------------------------------------------------------------------

def registration(org):
    from .models import BusinessRecord
    r = BusinessRecord.objects(organization=org, kind="gst_settings", key="registration").first()
    return (r.data if r else {}) or {}


def seller_block(org, reg, gstin=None):
    gst = gstin if gstin is not None else reg.get("gstin", "")
    return {"name": reg.get("legal_name") or org.name, "trade": org.name if reg.get("legal_name") and reg.get("legal_name") != org.name else "",
            "address": org.address or "", "phone": org.phone or "", "email": org.email or "", "gstin": gst,
            "pan": gst[2:12] if len(gst) == 15 else "", "state_code": reg.get("state_code", "") or (gst[:2] if gst else "")}


def make_line(name, hsn, qty, unit, rate, discount, tax_rate, line_tax=None, desc="", inter=False, mrp=None):
    qty, rate, discount, tax_rate = d(qty), d(rate), d(discount), d(tax_rate)
    taxable = q(qty * rate - discount)
    tax = q(line_tax) if line_tax is not None else q(taxable * tax_rate / 100)
    cgst = D0 if inter else q(tax / 2)
    return {"name": name or "Item", "desc": desc or "", "hsn": hsn or "", "qty": qty, "unit": unit or "", "rate": rate, "discount": discount,
            "taxable": taxable, "tax_rate": tax_rate, "igst": tax if inter else D0, "cgst": cgst, "sgst": D0 if inter else tax - cgst, "tax": tax,
            "total": taxable + tax, "mrp": mrp}


def finish(doc):
    """Totals, round-off, amount in words and the HSN tax summary from the lines."""
    lines = doc["lines"]
    gross = sum((q(l["qty"] * l["rate"]) for l in lines), D0)
    discount = sum((l["discount"] for l in lines), D0)
    taxable = sum((l["taxable"] for l in lines), D0)
    heads = {k: sum((l[k] for l in lines), D0) for k in ("cgst", "sgst", "igst")}
    exact = taxable + sum(heads.values())
    total = d(doc.get("total")) if doc.get("total") not in (None, "") else exact.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    summary = {}
    for l in lines:
        key = (l["hsn"] or "—", l["tax_rate"])
        row = summary.setdefault(key, {"taxable": D0, "cgst": D0, "sgst": D0, "igst": D0})
        for k in row:
            row[k] += l[k]
    doc.update(gross=gross, discount=discount, taxable=taxable, **heads, round_off=q(total - exact), total=q(total),
               words=amount_words(total), tax_summary=[{"hsn": k[0], "rate": k[1], **v} for k, v in sorted(summary.items(), key=lambda i: (i[0][0], i[0][1]))])
    doc.setdefault("paid", None)
    doc.setdefault("balance", None)
    return doc


def branding(org):
    from .billing import settings
    return settings(org) or {}


# --------------------------------------------------------------------------------------------
# Adapters: each document type → one dictionary
# --------------------------------------------------------------------------------------------

def from_invoice(invoice):
    org = invoice.organization
    bd = dict(invoice.billing_details or {})
    reg = registration(org)
    supply = bd.get("supply_type", "")
    seller = seller_block(org, reg, bd.get("supplier_gstin") if "supplier_gstin" in bd else None)
    seller_state = bd.get("supplier_state") or seller["state_code"]
    pos = bd.get("place_of_supply") or (invoice.customer_gstin or "")[:2] or seller_state
    inter = bool(pos and seller_state and pos != seller_state) and supply in ("", "taxable")
    title = "Tax Invoice" if supply == "taxable" or (not supply and d(invoice.tax_amount) > 0) else "Bill of Supply" if supply in ("exempt", "nil_rated", "non_gst") else "Invoice"
    lines = []
    for i in invoice.items:
        product = i.product
        lines.append(make_line(i.item_name or getattr(product, "name", ""), i.hsn_code or getattr(product, "hsn_code", ""), i.quantity, i.unit or getattr(product, "unit", ""),
                               i.unit_price, i.discount, i.tax_rate, i.line_tax, i.description if i.show_description else "", inter))
    address = ", ".join(x for x in (invoice.billing_address, getattr(invoice, "billing_city", ""), getattr(invoice, "billing_state", ""), getattr(invoice, "billing_pincode", "")) if x)
    meta = [("Invoice no.", invoice.invoice_number), ("Invoice date", invoice.invoice_date.date().strftime("%d-%m-%Y") if invoice.invoice_date else ""),
            ("Due date", invoice.due_date.date().strftime("%d-%m-%Y") if invoice.due_date else ""), ("Place of supply", state_label(pos)),
            ("Reverse charge", "No"), ("PO no.", bd.get("po_number", "")), ("PO date", bd.get("po_date", "")),
            ("Service period", f"{bd.get('service_from', '')} to {bd.get('service_to', '')}" if bd.get("service_from") else ""), ("Site / project", bd.get("site_name", ""))]
    irp = getattr(invoice, "einvoice", None) or {}
    doc = {"kind": "invoice", "title": title, "number": invoice.invoice_number, "status": invoice.status, "seller": seller,
           "buyer": {"name": invoice.billing_name, "address": address, "gstin": invoice.customer_gstin or "", "state": state_label((invoice.customer_gstin or "")[:2] or pos)},
           "ship_to": {"name": invoice.billing_name, "address": bd.get("shipping_address") or bd.get("site_name") or ""} if bd.get("shipping_address") or bd.get("site_name") else None,
           "meta": [m for m in meta if m[1]], "lines": lines, "inter": inter, "total": invoice.total_amount, "notes": invoice.notes or "",
           "terms": bd.get("terms", ""), "payment_terms": bd.get("payment_terms", ""), "bank": bd.get("bank_details", ""), "signatory": bd.get("signatory", ""),
           "irn": irp if irp.get("status") == "registered" and irp.get("environment") == "live" else None,
           "draft": invoice.status == "DRAFT", "cancelled": invoice.status == "CANCELLED", "copies": ["Original for recipient"],
           "unreviewed": not bd.get("tax_reviewed")}
    finish(doc)
    doc["paid"], doc["balance"] = q(invoice.amount_paid), q(invoice.balance_due)
    return doc


def from_quotation(org, record):
    data = record.data or {}
    reg = registration(org)
    seller = seller_block(org, reg)
    customer = data.get("customer_details") or {}
    pos = (customer.get("gstin") or "")[:2] or seller["state_code"]
    inter = bool(pos and seller["state_code"] and pos != seller["state_code"])
    lines = [make_line(i.get("name"), i.get("hsn_code", ""), i.get("quantity"), i.get("unit", ""), i.get("unit_price"), i.get("discount"), i.get("tax_rate"),
                       desc=i.get("description", ""), inter=inter) for i in data.get("items", [])]
    meta = [("Estimate no.", record.key), ("Date", fmt_date(data.get("date"))), ("Valid until", fmt_date(data.get("valid_until"))), ("Place of supply", state_label(pos))]
    doc = {"kind": "quotation", "title": "Estimate / Quotation", "number": record.key, "status": "", "seller": seller,
           "buyer": {"name": customer.get("name") or data.get("customer", ""), "address": customer.get("address", ""), "gstin": customer.get("gstin", ""), "state": state_label(pos)},
           "ship_to": None, "meta": [m for m in meta if m[1]], "lines": lines, "inter": inter, "total": data.get("total"), "notes": data.get("notes", ""),
           "copies": [""], "draft": False, "cancelled": False}
    return finish(doc)


def from_sales_order(order):
    org = order.organization
    reg = registration(org)
    seller = seller_block(org, reg)
    customer = order.customer
    gstin = getattr(customer, "gstin", "") or ""
    pos = gstin[:2] or seller["state_code"]
    inter = bool(pos and seller["state_code"] and pos != seller["state_code"])
    lines = [make_line(getattr(i.product, "name", ""), getattr(i.product, "hsn_code", ""), i.quantity, getattr(i.product, "unit", ""), i.unit_price, i.discount, i.tax_rate, i.line_tax, inter=inter)
             for i in order.items]
    meta = [("Order no.", order.so_number), ("Order date", order.order_date.date().strftime("%d-%m-%Y") if order.order_date else ""),
            ("Expected delivery", order.expected_delivery_date.date().strftime("%d-%m-%Y") if order.expected_delivery_date else ""), ("Place of supply", state_label(pos))]
    address = ", ".join(x for x in (getattr(customer, "billing_address", ""), getattr(customer, "city", ""), getattr(customer, "state", ""), getattr(customer, "pincode", "")) if x)
    doc = {"kind": "sales_order", "title": "Proforma Invoice / Sales Order", "number": order.so_number, "status": order.status, "seller": seller,
           "buyer": {"name": getattr(customer, "name", ""), "address": address, "gstin": gstin, "state": state_label(pos)},
           "ship_to": {"name": getattr(customer, "name", ""), "address": getattr(customer, "shipping_address", "")} if getattr(customer, "shipping_address", "") else None,
           "meta": [m for m in meta if m[1]], "lines": lines, "inter": inter, "total": order.total_amount, "notes": order.notes or "",
           "copies": [""], "draft": order.status == "DRAFT", "cancelled": order.status == "CANCELLED"}
    return finish(doc)


def from_credit_note(note):
    org = note.organization
    reg = registration(org)
    seller = seller_block(org, reg)
    invoice = note.invoice
    customer = note.customer
    bd = dict(getattr(invoice, "billing_details", None) or {})
    seller_state = bd.get("supplier_state") or seller["state_code"]
    gstin = getattr(invoice, "customer_gstin", "") or getattr(customer, "gstin", "") or ""
    pos = bd.get("place_of_supply") or gstin[:2] or seller_state
    inter = bool(pos and seller_state and pos != seller_state)
    lines = [make_line(getattr(i.product, "name", ""), getattr(i.product, "hsn_code", ""), i.quantity, getattr(i.product, "unit", ""), i.unit_price, i.discount, i.tax_rate, i.line_tax, inter=inter)
             for i in note.items]
    meta = [("Credit note no.", note.credit_note_number), ("Date", note.credit_note_date.date().strftime("%d-%m-%Y") if note.credit_note_date else ""),
            ("Against invoice", getattr(invoice, "invoice_number", "")), ("Invoice date", invoice.invoice_date.date().strftime("%d-%m-%Y") if invoice and invoice.invoice_date else ""),
            ("Place of supply", state_label(pos)), ("Reason", getattr(note, "reason", "") or "")]
    doc = {"kind": "credit_note", "title": "Credit Note", "number": note.credit_note_number, "status": note.status, "seller": seller,
           "buyer": {"name": getattr(invoice, "billing_name", "") or getattr(customer, "name", ""), "address": getattr(invoice, "billing_address", "") or getattr(customer, "billing_address", ""),
                     "gstin": gstin, "state": state_label(pos)},
           "ship_to": None, "meta": [m for m in meta if m[1]], "lines": lines, "inter": inter, "total": note.total_amount, "notes": getattr(note, "notes", "") or "",
           "copies": ["Original for recipient"], "draft": note.status == "DRAFT", "cancelled": note.status == "CANCELLED"}
    return finish(doc)


CHALLAN_REASONS = {"job_work": "Job work", "non_supply": "Movement other than supply", "liquid_gas": "Liquid gas — quantity not known at dispatch", "notified": "Other notified movement"}


def from_challan(org, challan):
    reg = registration(org)
    seller = seller_block(org, reg, challan.get("seller_gstin", reg.get("gstin", "")))
    seller.update(name=challan.get("seller_name") or seller["name"], address=challan.get("seller_address") or seller["address"])
    lines = []
    for l in challan.get("items", []):
        line = make_line(l.get("name"), l.get("hsn"), l.get("qty"), l.get("unit"), D0, D0, l.get("rate"), sum(d(l.get(k)) for k in ("cgst", "sgst", "igst")), inter=d(l.get("igst")) > 0)
        line.update(taxable=q(l.get("value")), rate=(q(l.get("value")) / d(l.get("qty")) if d(l.get("qty")) else D0), cgst=q(l.get("cgst")), sgst=q(l.get("sgst")), igst=q(l.get("igst")))
        line["total"] = line["taxable"] + line["cgst"] + line["sgst"] + line["igst"]
        line["provisional"] = d(l.get("qty")) == 0
        lines.append(line)
    meta = [("Challan no.", challan.get("number", "")), ("Date", fmt_date(challan.get("date"))), ("Reason", CHALLAN_REASONS.get(challan.get("reason"), challan.get("reason", ""))),
            ("Place of supply", state_label(challan.get("pos", ""))), ("Transport", challan.get("transport", "")), ("Vehicle no.", challan.get("vehicle_number", "")),
            ("Linked invoice", challan.get("invoice_number", ""))]
    doc = {"kind": "delivery_challan", "title": "Delivery Challan", "number": challan.get("number", ""), "status": challan.get("status", ""), "seller": seller,
           "buyer": {"name": challan.get("customer_name", ""), "address": challan.get("address", ""), "gstin": challan.get("customer_gstin", ""), "state": state_label(challan.get("pos", ""))},
           "ship_to": None, "meta": [m for m in meta if m[1]], "lines": lines, "inter": any(l["igst"] for l in lines), "notes": challan.get("notes", ""),
           "copies": ["Original for consignee", "Duplicate for transporter", "Triplicate for consignor"], "draft": False, "cancelled": challan.get("status") == "cancelled",
           "no_payment": True}
    return finish(doc)


def sample_document(org, kind="invoice"):
    """Realistic sample used for template previews in Settings."""
    reg = registration(org)
    seller = seller_block(org, reg)
    if not seller["gstin"]:
        seller.update(gstin="27AAACN1234F1Z5", pan="AAACN1234F", state_code="27")
    seller.setdefault("address", "")
    seller["address"] = seller["address"] or "Shop 4, Market Yard, Pune 411037"
    inter = False
    lines = [make_line("OPC 53 Grade Cement (50 kg bag)", "2523", 50, "BAG", 380, 500, 28, inter=inter),
             make_line("TMT Steel Bar 12 mm Fe-500D", "7214", 120, "KG", 68.5, 0, 18, inter=inter),
             make_line("Site delivery and unloading", "996511", 1, "TRIP", 1500, 0, 18, desc="Within 15 km of the store", inter=inter)]
    titles = {"invoice": ("Tax Invoice", "INV/26-27/0149", [("Invoice no.", "INV/26-27/0149"), ("Invoice date", "26-11-2026"), ("Due date", "11-12-2026")]),
              "quotation": ("Estimate / Quotation", "QT-0031", [("Estimate no.", "QT-0031"), ("Date", "26-11-2026"), ("Valid until", "10-12-2026")]),
              "sales_order": ("Proforma Invoice / Sales Order", "SO-0091", [("Order no.", "SO-0091"), ("Order date", "26-11-2026")]),
              "credit_note": ("Credit Note", "CN-0012", [("Credit note no.", "CN-0012"), ("Date", "26-11-2026"), ("Against invoice", "INV/26-27/0131")]),
              "delivery_challan": ("Delivery Challan", "DC-0007", [("Challan no.", "DC-0007"), ("Date", "26-11-2026"), ("Reason", "Job work")])}
    title, number, meta = titles.get(kind, titles["invoice"])
    doc = {"kind": kind, "title": title, "number": number, "status": "ISSUED", "seller": seller,
           "buyer": {"name": "Sharma Traders", "address": "12 MG Road, Camp, Pune 411001", "gstin": "27AAPFS1234K1Z5", "state": state_label("27")},
           "ship_to": {"name": "Sharma Traders — Site", "address": "Plot 22, Hinjewadi Phase 2, Pune 411057"},
           "meta": meta + [("Place of supply", state_label("27")), ("Reverse charge", "No"), ("PO no.", "PO-4471")], "lines": lines, "inter": inter,
           "notes": "Thank you for your business.", "copies": ["Original for recipient"] if kind in ("invoice", "credit_note") else ["Original for consignee", "Duplicate for transporter", "Triplicate for consignor"] if kind == "delivery_challan" else [""], "draft": False, "cancelled": False,
           "no_payment": kind == "delivery_challan"}
    finish(doc)
    if kind == "invoice":
        doc["paid"], doc["balance"] = D0, doc["total"]
    return doc


STATES = {"01": "Jammu and Kashmir", "02": "Himachal Pradesh", "03": "Punjab", "04": "Chandigarh", "05": "Uttarakhand", "06": "Haryana", "07": "Delhi", "08": "Rajasthan",
          "09": "Uttar Pradesh", "10": "Bihar", "11": "Sikkim", "12": "Arunachal Pradesh", "13": "Nagaland", "14": "Manipur", "15": "Mizoram", "16": "Tripura", "17": "Meghalaya",
          "18": "Assam", "19": "West Bengal", "20": "Jharkhand", "21": "Odisha", "22": "Chhattisgarh", "23": "Madhya Pradesh", "24": "Gujarat",
          "26": "Dadra and Nagar Haveli and Daman and Diu", "27": "Maharashtra", "29": "Karnataka", "30": "Goa", "31": "Lakshadweep", "32": "Kerala", "33": "Tamil Nadu",
          "34": "Puducherry", "35": "Andaman and Nicobar Islands", "36": "Telangana", "37": "Andhra Pradesh", "38": "Ladakh", "97": "Other Territory"}


def state_label(code):
    code = (code or "").strip()
    return f"{STATES[code]} ({code})" if code in STATES else code


def fmt_date(value):
    value = str(value or "")
    if len(value) == 10 and value[4] == "-":
        return f"{value[8:10]}-{value[5:7]}-{value[:4]}"
    return value


# --------------------------------------------------------------------------------------------
# Rendering
# --------------------------------------------------------------------------------------------

class Kit:
    """Styles and small helpers for one render."""

    def __init__(self, accent, layout, width):
        self.accent = colors.HexColor(accent)
        self.layout = layout
        self.width = width
        small = layout == "thermal"
        base = 7 if small else 8
        self.styles = {
            "cell": ParagraphStyle("cell", fontName="NX", fontSize=base, leading=base + 2.6, wordWrap="CJK"),
            "cellr": ParagraphStyle("cellr", fontName="NX", fontSize=base, leading=base + 2.6, alignment=2),
            "cellc": ParagraphStyle("cellc", fontName="NX", fontSize=base, leading=base + 2.6, alignment=1),
            "bold": ParagraphStyle("bold", fontName="NX-Bold", fontSize=base, leading=base + 2.6, wordWrap="CJK"),
            "boldr": ParagraphStyle("boldr", fontName="NX-Bold", fontSize=base, leading=base + 2.6, alignment=2),
            "head": ParagraphStyle("head", fontName="NX-Bold", fontSize=base - 0.5, leading=base + 2, textColor=colors.white if layout in ("modern", "retail", "gst_classic") else colors.HexColor("#111827")),
            "headr": ParagraphStyle("headr", fontName="NX-Bold", fontSize=base - 0.5, leading=base + 2, alignment=2, textColor=colors.white if layout in ("modern", "retail", "gst_classic") else colors.HexColor("#111827")),
            "brand": ParagraphStyle("brand", fontName="NX-Bold", fontSize=11 if small else 17, leading=14 if small else 21, alignment=1 if small else 0, textColor=colors.white if layout == "modern" else self.accent),
            "title": ParagraphStyle("title", fontName="NX-Bold", fontSize=10 if small else 15, leading=13 if small else 19, alignment=1 if small else 2,
                                    textColor=colors.white if layout == "modern" else colors.HexColor("#111827")),
            "label": ParagraphStyle("label", fontName="NX-Bold", fontSize=base - 1, leading=base + 1, textColor=colors.HexColor("#6b7280")),
            "muted": ParagraphStyle("muted", fontName="NX", fontSize=base - 0.5, leading=base + 2, alignment=1 if small else 0, textColor=colors.white if layout == "modern" else colors.HexColor("#4b5563")),
            "labelr": ParagraphStyle("labelr", fontName="NX-Bold", fontSize=base - 1, leading=base + 1, alignment=2, textColor=colors.HexColor("#6b7280")),
            "big": ParagraphStyle("big", fontName="NX-Bold", fontSize=10 if small else 12, leading=13 if small else 15, alignment=2),
            "center": ParagraphStyle("center", fontName="NX", fontSize=base, leading=base + 2.6, alignment=1),
        }

    def p(self, value, style="cell"):
        text = escape(str("" if value is None else value)).replace("\n", "<br/>")
        return Paragraph(text or "&nbsp;", self.styles[style])

    def money(self, value):
        return indian_money(value)


def qr_drawing(payload, side):
    widget = QrCodeWidget(payload)
    x, y, w, h = widget.getBounds()
    scale = side / (w - x)
    drawing = Drawing(side, side, transform=[scale, 0, 0, scale, -x * scale, -y * scale])
    drawing.add(widget)
    return drawing


def logo_image(value, max_w, max_h):
    try:
        prefix, data = (value or "").split(",", 1)
        if prefix not in ("data:image/png;base64", "data:image/jpeg;base64"):
            return None
        img = Image(BytesIO(base64.b64decode(data, validate=True)))
        scale = min(max_w / img.imageWidth, max_h / img.imageHeight)
        img.drawWidth, img.drawHeight = img.imageWidth * scale, img.imageHeight * scale
        return img
    except (ValueError, OSError):
        return None


def upi_payload(upi_id, name, amount, number):
    from urllib.parse import quote
    return f"upi://pay?pa={quote(upi_id)}&pn={quote(name[:40])}&am={q(amount):.2f}&cu=INR&tn={quote('Payment for ' + number)}"


def _header(doc, kit, brand):
    s = doc["seller"]
    lines = [kit.p(s["name"], "brand")]
    if s.get("trade"):
        lines.append(kit.p(s["trade"], "muted"))
    contact = "\n".join(x for x in (s["address"], " · ".join(x for x in (("Ph: " + s["phone"]) if s["phone"] else "", s["email"]) if x),
                                     " · ".join(x for x in (("GSTIN: " + s["gstin"]) if s["gstin"] else "", ("PAN: " + s["pan"]) if s.get("pan") else "", state_label(s.get("state_code", ""))) if x)) if x)
    lines.append(kit.p(contact, "muted"))
    logo = logo_image(brand.get("logo"), 90 if kit.layout != "thermal" else 70, 48 if kit.layout != "thermal" else 36)
    right = [kit.p(doc["title"].upper(), "title")]
    copy = doc.get("copy")
    if copy:
        right.append(kit.p(copy, "muted" if kit.layout != "modern" else "muted"))
    if kit.layout == "thermal":
        rows = ([[logo]] if logo else []) + [[l] for l in lines] + [[r] for r in right]
        t = Table(rows, colWidths=[kit.width])
        t.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER"), ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0)]))
        return [t, Spacer(1, 4)]
    left = Table(([[logo, lines]] if logo else [[lines]]), colWidths=([100, kit.width * 0.62 - 100] if logo else [kit.width * 0.62]))
    left.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0)]))
    t = Table([[left, right]], colWidths=[kit.width * 0.62, kit.width * 0.38])
    style = [("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6)]
    if kit.layout == "modern":
        style += [("BACKGROUND", (0, 0), (-1, -1), kit.accent), ("TOPPADDING", (0, 0), (-1, -1), 12), ("BOTTOMPADDING", (0, 0), (-1, -1), 12)]
    elif kit.layout == "gst_classic":
        style += [("BOX", (0, 0), (-1, -1), 0.8, colors.black), ("LINEAFTER", (0, 0), (0, 0), 0.5, colors.black), ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]
    elif kit.layout == "retail":
        style += [("LINEBELOW", (0, 0), (-1, -1), 3, kit.accent), ("BOTTOMPADDING", (0, 0), (-1, -1), 8)]
    else:
        style += [("LINEBELOW", (0, 0), (-1, -1), 1.2 if kit.layout != "minimal" else 0.6, kit.accent if kit.layout != "minimal" else colors.HexColor("#111827")), ("BOTTOMPADDING", (0, 0), (-1, -1), 8)]
    t.setStyle(TableStyle(style))
    return [t]


def _parties(doc, kit):
    b = doc["buyer"]
    party = "\n".join(x for x in (b["address"], ("GSTIN: " + b["gstin"]) if b["gstin"] else "GSTIN: Unregistered", ("State: " + b["state"]) if b.get("state") else "") if x)
    buyer = [kit.p("BILL TO" if doc["kind"] != "delivery_challan" else "CONSIGNEE", "label"), kit.p(b["name"], "bold"), kit.p(party)]
    meta_rows = [[kit.p(k, "label"), kit.p(v)] for k, v in doc["meta"]]
    if kit.layout == "thermal":
        rows = [[kit.p(f"{k}: {v}")] for k, v in doc["meta"]] + [[kit.p(f"Bill to: {b['name']}" + (f" · {b['gstin']}" if b["gstin"] else ""))]]
        t = Table(rows, colWidths=[kit.width])
        t.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0), ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 1)]))
        return [t, Spacer(1, 4)]
    meta = Table(meta_rows or [[kit.p(""), kit.p("")]], colWidths=[kit.width * 0.16, kit.width * 0.22])
    meta.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), 1.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5), ("LEFTPADDING", (0, 0), (-1, -1), 0)]))
    cols = [buyer]
    widths = [kit.width * 0.62]
    if doc.get("ship_to"):
        st = doc["ship_to"]
        cols = [buyer, [kit.p("SHIP TO", "label"), kit.p(st["name"], "bold"), kit.p(st["address"])]]
        widths = [kit.width * 0.31, kit.width * 0.31]
    t = Table([cols + [meta]], colWidths=widths + [kit.width * 0.38])
    style = [("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 6), ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]
    if kit.layout == "gst_classic":
        style += [("BOX", (0, 0), (-1, -1), 0.8, colors.black), ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.black)]
    elif kit.layout in ("modern", "retail", "service"):
        style += [("BACKGROUND", (0, 0), (-2, -1), colors.HexColor("#f8fafc"))]
    t.setStyle(TableStyle(style))
    return [Spacer(1, 0 if kit.layout == "gst_classic" else 8), t, Spacer(1, 0 if kit.layout == "gst_classic" else 8)]


def _lines(doc, kit):
    inter = doc["inter"]
    lines = doc["lines"]
    if kit.layout == "thermal":
        rows = [[kit.p("Item", "head"), kit.p("Qty", "headr"), kit.p("Rate", "headr"), kit.p("Amount", "headr")]]
        for l in lines:
            rows.append([kit.p(l["name"] + (f"\nHSN {l['hsn']} · GST {num(l['tax_rate'])}%" if l["hsn"] else f"\nGST {num(l['tax_rate'])}%")), kit.p(num(l["qty"]), "cellr"), kit.p(kit.money(l["rate"]), "cellr"), kit.p(kit.money(l["total"]), "cellr")])
        t = Table(rows, colWidths=[kit.width * 0.44, kit.width * 0.14, kit.width * 0.2, kit.width * 0.22], repeatRows=1)
        t.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, 0), 0.6, colors.black), ("LINEBELOW", (0, -1), (-1, -1), 0.6, colors.black), ("LEFTPADDING", (0, 0), (-1, -1), 1), ("RIGHTPADDING", (0, 0), (-1, -1), 1), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
        return [t]
    service = kit.layout == "service"
    detailed = kit.layout in ("gst_classic", "retail")
    head = ["#", "Description", "HSN/SAC" if service else "HSN"]
    widths = [0.035, 0.0, 0.07]
    if not service:
        head += ["Qty", "Unit"]
        widths += [0.05, 0.05]
    head += ["Rate", "Disc."] if not service else ["Amount"]
    widths += [0.08, 0.07] if not service else [0.11]
    head += ["Taxable"]
    widths += [0.095]
    if detailed:
        if inter:
            head += ["GST", "IGST"]
            widths += [0.045, 0.095]
        else:
            head += ["GST", "CGST", "SGST"]
            widths += [0.045, 0.085, 0.085]
    else:
        head += ["GST"]
        widths += [0.05]
    head += ["Total"]
    widths += [0.1]
    widths[1] = 1 - sum(widths)
    rows = [[kit.p(h, "head" if i < 2 else "headr") for i, h in enumerate(head)]]
    for n, l in enumerate(lines, 1):
        desc = kit.p(l["name"] + ("\n" + l["desc"] if l["desc"] else ""))
        row = [kit.p(str(n), "cellc"), desc, kit.p(l["hsn"], "cellr")]
        if not service:
            row += [kit.p("Provisional" if l.get("provisional") else num(l["qty"]), "cellr"), kit.p(l["unit"], "cellr")]
            row += [kit.p(kit.money(l["rate"]), "cellr"), kit.p(kit.money(l["discount"]) if l["discount"] else "—", "cellr")]
        else:
            row += [kit.p(kit.money(q(l["qty"] * l["rate"])), "cellr")]
        row += [kit.p(kit.money(l["taxable"]), "cellr")]
        if detailed:
            row += [kit.p(num(l["tax_rate"]) + "%", "cellr")] + ([kit.p(kit.money(l["igst"]), "cellr")] if inter else [kit.p(kit.money(l["cgst"]), "cellr"), kit.p(kit.money(l["sgst"]), "cellr")])
        else:
            row += [kit.p(num(l["tax_rate"]) + "%", "cellr")]
        row += [kit.p(kit.money(l["total"]), "boldr")]
        rows.append(row)
    t = Table(rows, colWidths=[w * kit.width for w in widths], repeatRows=1)
    style = [("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4), ("LEFTPADDING", (0, 0), (-1, -1), 3), ("RIGHTPADDING", (0, 0), (-1, -1), 3)]
    if kit.layout == "gst_classic":
        style += [("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#111827")), ("BOX", (0, 0), (-1, -1), 0.8, colors.black), ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#6b7280"))]
    elif kit.layout == "retail":
        style += [("BACKGROUND", (0, 0), (-1, 0), kit.accent), ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#cbd5e1"))]
    elif kit.layout == "modern":
        style += [("BACKGROUND", (0, 0), (-1, 0), kit.accent), ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f1f5f9")])]
    else:
        style += [("LINEBELOW", (0, 0), (-1, 0), 1, colors.HexColor("#111827") if kit.layout == "minimal" else kit.accent), ("LINEBELOW", (0, 1), (-1, -1), 0.3, colors.HexColor("#e5e7eb"))]
    t.setStyle(TableStyle(style))
    return [t]


def _summary_and_totals(doc, kit, brand):
    inter = doc["inter"]
    money = kit.money
    totals = [("Gross amount", doc["gross"])]
    if doc["discount"]:
        totals.append(("Less: discount", -doc["discount"]))
    totals.append(("Taxable value", doc["taxable"]))
    if inter:
        totals.append(("IGST", doc["igst"]))
    else:
        totals += [("CGST", doc["cgst"]), ("SGST / UTGST", doc["sgst"])]
    if doc["round_off"]:
        totals.append(("Round off", doc["round_off"]))
    rows = [[kit.p(k), kit.p(money(v), "cellr")] for k, v in totals]
    rows.append([kit.p("TOTAL (INR)", "bold"), kit.p(money(doc["total"]), "big")])
    if doc.get("paid") is not None and doc["kind"] == "invoice":
        rows += [[kit.p("Received"), kit.p(money(doc["paid"]), "cellr")], [kit.p("Balance due", "bold"), kit.p(money(doc["balance"]), "boldr")]]
    if kit.layout == "thermal":
        t = Table(rows, colWidths=[kit.width * 0.55, kit.width * 0.45])
        t.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 1), ("RIGHTPADDING", (0, 0), (-1, -1), 1), ("TOPPADDING", (0, 0), (-1, -1), 1), ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
                               ("LINEABOVE", (0, len(totals)), (-1, len(totals)), 0.6, colors.black)]))
        return [Spacer(1, 3), t, kit.p(doc["words"], "center")]
    tot = Table(rows, colWidths=[kit.width * 0.2, kit.width * 0.18])
    tstyle = [("TOPPADDING", (0, 0), (-1, -1), 2.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5), ("LINEABOVE", (0, len(totals)), (-1, len(totals)), 1, kit.accent if kit.layout != "minimal" else colors.black),
              ("BACKGROUND", (0, len(totals)), (-1, len(totals)), colors.HexColor("#f1f5f9"))]
    if kit.layout == "gst_classic":
        tstyle += [("BOX", (0, 0), (-1, -1), 0.8, colors.black)]
    tot.setStyle(TableStyle(tstyle))
    # HSN-wise tax summary (left) + totals (right)
    if inter:
        head = ["HSN/SAC", "Rate", "Taxable", "IGST", "Total tax"]
        srows = [[kit.p(r["hsn"]), kit.p(num(r["rate"]) + "%", "cellr"), kit.p(money(r["taxable"]), "cellr"), kit.p(money(r["igst"]), "cellr"), kit.p(money(r["igst"]), "cellr")] for r in doc["tax_summary"]]
        sw = [0.1, 0.06, 0.12, 0.1, 0.12]
    else:
        head = ["HSN/SAC", "Rate", "Taxable", "CGST", "SGST", "Total tax"]
        srows = [[kit.p(r["hsn"]), kit.p(num(r["rate"]) + "%", "cellr"), kit.p(money(r["taxable"]), "cellr"), kit.p(money(r["cgst"]), "cellr"), kit.p(money(r["sgst"]), "cellr"), kit.p(money(r["cgst"] + r["sgst"]), "cellr")] for r in doc["tax_summary"]]
        sw = [0.1, 0.05, 0.11, 0.09, 0.09, 0.1]
    summary = Table([[kit.p(h, "label" if i == 0 else "labelr") for i, h in enumerate(head)]] + srows, colWidths=[w * kit.width * 0.58 / sum(sw) for w in sw])
    summary.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, 0), 0.6, colors.HexColor("#9ca3af")), ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2), ("LEFTPADDING", (0, 0), (-1, -1), 2), ("RIGHTPADDING", (0, 0), (-1, -1), 2)]
                                + ([("BOX", (0, 0), (-1, -1), 0.8, colors.black)] if kit.layout == "gst_classic" else [])))
    left = [kit.p("Tax summary", "label"), summary, Spacer(1, 6), kit.p("Amount in words", "label"), kit.p(doc["words"], "bold")]
    wrap = Table([[left, tot]], colWidths=[kit.width * 0.6, kit.width * 0.4])
    wrap.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0), ("ALIGN", (1, 0), (1, 0), "RIGHT")]))
    return [Spacer(1, 8), wrap]


def _footer_blocks(doc, kit, brand):
    s = doc["seller"]
    bank = doc.get("bank") or brand.get("bank_details", "")
    terms = doc.get("terms") or brand.get("terms", "")
    payment_terms = doc.get("payment_terms") or brand.get("payment_terms", "")
    signatory = doc.get("signatory") or brand.get("signatory", "") or s["name"]
    upi = (brand.get("upi_id") or "").strip()
    show_qr = upi and not doc.get("no_payment") and doc["kind"] in ("invoice", "quotation", "sales_order") and doc["total"] > 0
    pay_amount = doc["balance"] if doc.get("balance") not in (None, D0) else doc["total"]
    out = []
    if kit.layout == "thermal":
        if show_qr:
            out += [Spacer(1, 4), qr_drawing(upi_payload(upi, s["name"], pay_amount, doc["number"]), 90), kit.p("Scan to pay with any UPI app · " + upi, "center")]
        if doc.get("notes"):
            out.append(kit.p(doc["notes"], "center"))
        out.append(kit.p("Thank you! Visit again.", "center"))
        return out
    left = []
    if bank:
        left += [kit.p("Bank details", "label"), kit.p(bank), Spacer(1, 4)]
    if payment_terms:
        left += [kit.p("Payment terms", "label"), kit.p(payment_terms), Spacer(1, 4)]
    if terms:
        left += [kit.p("Terms & conditions", "label"), kit.p(terms), Spacer(1, 4)]
    if doc.get("notes"):
        left += [kit.p("Notes", "label"), kit.p(doc["notes"])]
    middle = [qr_drawing(upi_payload(upi, s["name"], pay_amount, doc["number"]), 78), kit.p("Scan & pay via UPI\n" + upi, "center")] if show_qr else [kit.p("")]
    right = [kit.p("For " + s["name"], "boldr"), Spacer(1, 30), kit.p("Authorised signatory" + (f"\n{signatory}" if signatory != s["name"] else ""), "cellr")]
    t = Table([[left or [kit.p("")], middle, right]], colWidths=[kit.width * 0.52, kit.width * 0.18, kit.width * 0.3])
    style = [("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 4), ("TOPPADDING", (0, 0), (-1, -1), 6)]
    if kit.layout == "gst_classic":
        style += [("BOX", (0, 0), (-1, -1), 0.8, colors.black), ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.black)]
    else:
        style += [("LINEABOVE", (0, 0), (-1, 0), 0.6, colors.HexColor("#d1d5db"))]
    t.setStyle(TableStyle(style))
    return [Spacer(1, 8), KeepTogether([t])]


def _irn_block(doc, kit):
    irp = doc.get("irn")
    if not irp or not irp.get("qr"):
        return []
    side = 70 if kit.layout == "thermal" else 96
    info = kit.p(f"e-Invoice IRN: {irp.get('irn', '')}\nAck no.: {irp.get('ack_no', '')}  Ack date: {irp.get('ack_date', '')}")
    if kit.layout == "thermal":
        return [qr_drawing(irp["qr"], side), info]
    t = Table([[info, qr_drawing(irp["qr"], side)]], colWidths=[kit.width - side - 10, side + 10])
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LEFTPADDING", (0, 0), (-1, -1), 0)]))
    return [Spacer(1, 6), t]


def render(doc, template_id=None, brand=None):
    """PDF bytes for a document dictionary in the chosen template."""
    brand = brand or {}
    tid = resolve(template_id or brand.get("template"))
    _, name, default_color, layout = next(t for t in TEMPLATES if t[0] == tid)
    accent = brand.get("accent_color") or default_color
    if layout == "thermal":
        width_pt = 80 * 2.8346
        height = 470 + 50 * len(doc["lines"]) + (170 if brand.get("upi_id") else 0) + (120 if doc.get("irn") else 0) + 12 * len(doc["meta"])
        pagesize, margins = (width_pt, height), (8, 8, 10, 10)
    else:
        pagesize, margins = A4, (28, 28, 26, 34)
    width = pagesize[0] - margins[0] - margins[1]
    kit = Kit(accent, layout, width)
    story = []
    copies = doc.get("copies") or [""]
    for i, copy in enumerate(copies):
        if i:
            story.append(PageBreak())
        doc["copy"] = copy
        story += _header(doc, kit, brand)
        flags = []
        if doc.get("cancelled"):
            flags.append("CANCELLED")
        if doc.get("draft"):
            flags.append("DRAFT — not a valid tax document until issued")
        if doc.get("unreviewed"):
            flags.append("GST classification pending review")
        if flags:
            story.append(kit.p(" · ".join(flags), "bold"))
        story += _irn_block(doc, kit)
        story += _parties(doc, kit)
        story += _lines(doc, kit)
        story += _summary_and_totals(doc, kit, brand)
        story += _footer_blocks(doc, kit, brand)

    def page(canvas, document):
        canvas.saveState()
        canvas.setFont("NX", 6.5 if layout == "thermal" else 7.5)
        canvas.setFillColor(colors.HexColor("#6b7280"))
        if layout != "thermal":
            canvas.drawString(margins[0], 18, "This is a computer-generated document.")
            canvas.drawRightString(pagesize[0] - margins[1], 18, f"{doc['title']} {doc['number']} · Page {document.page}")
        canvas.restoreState()

    buf = BytesIO()
    SimpleDocTemplate(buf, pagesize=pagesize, leftMargin=margins[0], rightMargin=margins[1], topMargin=margins[2], bottomMargin=margins[3],
                      title=f"{doc['title']} {doc['number']}", author=doc["seller"]["name"]).build(story, onFirstPage=page, onLaterPages=page)
    return buf.getvalue()


def render_for(org, doc, template_id=None):
    brand = branding(org)
    return render(doc, template_id or brand.get("template"), brand)
