"""Share documents and live statements with customers and suppliers.

One place for every shareable thing: invoices, bills, orders, notes, receipts, payments, goods
receipts, quotations, a customer's or supplier's statement (from NexEase or from Tally) and a
Tally voucher. For each, NexEase prepares the PDF, a ready message for WhatsApp and email, and a
private link that always opens the *current* version of the document (so a ledger link shows
today's balance whenever the customer opens it).

Sending:
- Email goes from NexEase with the PDF attached (the user's connected mailbox when set up).
- WhatsApp is sent from the user's own phone or WhatsApp Web: the app shares the PDF and message
  through the share sheet, and on a computer WhatsApp opens with the message and the link.
Every share is logged per document.

Endpoints (business/share/…):
  GET  prepare/?kind=&id=&from=&to=    recipient, message, subject, file name, private link
  GET  pdf/?kind=&id=&from=&to=         the PDF
  POST email/                           {kind, id, from, to, recipients, cc, subject, message, link}
  POST log/                             {kind, id, channel, recipient}  (WhatsApp / copied link)
  GET  history/?kind=&id=               who it was sent to
  POST links/<token>/revoke/            stop a private link
  GET  l/<token>/                       public: opens the live PDF (no sign-in)
"""
import re
import secrets
from datetime import date, datetime, timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.mail import EmailMessage
from django.core.validators import validate_email
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from mongoengine.connection import get_db

from apps.core.api.decorators import api_login_required
from apps.core.services.api_response_service import APIResponseService as R

from .statement_pdf import party_statement, statement_pdf, voucher_pdf
from .views import payload, permitted

IST = timedelta(hours=5, minutes=30)
LINK_DAYS = 30
MAX_RECIPIENTS = 10


def db():
    return get_db()


def now():
    return datetime.utcnow()


def today_ist():
    return (now() + IST).date()


def inr(v):
    from .reference_invoice import indian_money
    return "₹" + indian_money(Decimal(str(v or 0)).copy_abs())


def _oid(value):
    from bson import ObjectId
    if not ObjectId.is_valid(str(value or "")):
        raise LookupError("Not found.")
    return ObjectId(str(value))


def _dates(params):
    end = today_ist()
    try:
        end = date.fromisoformat(str(params.get("to") or ""))
    except ValueError:
        pass
    fy = date(end.year if end.month >= 4 else end.year - 1, 4, 1)
    try:
        start = date.fromisoformat(str(params.get("from") or ""))
    except ValueError:
        start = fy
    if start > end:
        start, end = end, start
    return start, end


def safe_name(text):
    return re.sub(r"[^A-Za-z0-9._-]+", "-", str(text or "document")).strip("-")[:80] or "document"


# --------------------------------------------------------------------------------------------
# What can be shared
# --------------------------------------------------------------------------------------------

class Shareable:
    """A resolved document: everything needed to send it."""

    def __init__(self, kind, label, number, pdf, party_name="", phone="", email="", amount=None, due=None, extra=None, filename=None):
        self.kind, self.label, self.number, self._pdf = kind, label, number, pdf
        self.party_name, self.phone, self.email = party_name or "", phone or "", email or ""
        self.amount, self.due, self.extra = amount, due, extra or {}
        self.filename = filename or f"{safe_name(label)}-{safe_name(number)}.pdf"

    def pdf(self):
        return self._pdf()


DOCS = {
    # kind: (DocumentAttachmentService type, permission, label, loader)
    "invoice": ("INVOICE", "invoices.read", "Invoice"),
    "sales_order": ("SALES_ORDER", "sales_orders.read", "Sales order"),
    "credit_note": ("CREDIT_NOTE", "credit_notes.read", "Credit note"),
    "receipt": ("CUSTOMER_PAYMENT", "customer_payments.read", "Payment receipt"),
    "purchase_order": ("PURCHASE_ORDER", "purchase_orders.read", "Purchase order"),
    "bill": ("VENDOR_BILL", "bills.read", "Purchase bill"),
    "debit_note": ("VENDOR_DEBIT_NOTE", "vendor_debit_notes.read", "Debit note"),
    "payment": ("SUPPLIER_PAYMENT", "bills.read", "Payment advice"),
    "goods_receipt": ("GOODS_RECEIPT", "goods_receipts.read", "Goods receipt"),
}
KINDS = list(DOCS) + ["quotation", "statement", "tally_ledger", "tally_voucher"]
PERMISSION = {**{k: v[1] for k, v in DOCS.items()}, "quotation": "invoices.read", "tally_ledger": "accounting_reports.read", "tally_voucher": "accounting_reports.read"}


def _model(kind):
    from apps.purchasing.models import GoodsReceipt, PurchaseOrder, SupplierPayment, VendorBill, VendorDebitNote
    from apps.sales.models import CreditNote, CustomerPayment, Invoice, SalesOrder
    return {"invoice": (Invoice, "invoice_number", "customer"), "sales_order": (SalesOrder, "so_number", "customer"), "credit_note": (CreditNote, "credit_note_number", "customer"),
            "receipt": (CustomerPayment, "payment_number", "customer"), "purchase_order": (PurchaseOrder, "po_number", "supplier"), "bill": (VendorBill, "bill_number", "supplier"),
            "debit_note": (VendorDebitNote, "debit_note_number", "supplier"), "payment": (SupplierPayment, "payment_number", "supplier"),
            "goods_receipt": (GoodsReceipt, "grn_number", "supplier")}[kind]


def _party_contact(party):
    return (getattr(party, "name", "") or "", getattr(party, "phone", "") or "", getattr(party, "email", "") or "")


def resolve(org, kind, ident, params=None):
    """kind + id (+ statement params) → Shareable. LookupError if it does not exist in this business."""
    params = params or {}
    if kind in DOCS:
        Model, number_field, party_field = _model(kind)
        doc = Model.objects(organization=org, id=_oid(ident)).first()
        if not doc:
            raise LookupError("Document not found.")
        dtype, _, label = DOCS[kind]
        number = getattr(doc, number_field)
        name, phone, email = _party_contact(getattr(doc, party_field, None))
        amount = getattr(doc, "total_amount", None) if hasattr(doc, "total_amount") else getattr(doc, "amount", None)
        due = getattr(doc, "balance_due", None)

        def pdf():
            from apps.finance.services.document_attachment_service import DocumentAttachmentService
            return DocumentAttachmentService.generate(document_type=dtype, document=doc, document_number=number)["content"]
        extra = {}
        if kind == "invoice":
            extra["due_date"] = doc.due_date.isoformat()[:10] if getattr(doc, "due_date", None) else ""
            name = doc.billing_name or name
        return Shareable(kind, label, number, pdf, name, phone, email, amount, due, extra)
    if kind == "quotation":
        from .models import BusinessRecord
        rec = BusinessRecord.objects(organization=org, kind="quotation", key=str(ident)).first()
        if not rec:
            raise LookupError("Quotation not found.")
        data = rec.data or {}
        cd = data.get("customer_details") or {}
        name, phone, email = cd.get("name") or data.get("customer") or "", cd.get("phone") or "", cd.get("email") or ""
        cust_id = cd.get("id") or data.get("customer_id")
        if cust_id and re.fullmatch(r"[0-9a-f]{24}", str(cust_id)):
            from apps.sales.models import Customer
            c = Customer.objects(organization=org, id=_oid(cust_id)).first()
            if c:
                name, phone, email = name or c.name, phone or c.phone, email or c.email
        elif name and not (phone and email):
            from apps.sales.models import Customer
            c = Customer.objects(organization=org, name__iexact=name).first()
            if c:
                phone, email = phone or c.phone, email or c.email

        def pdf():
            from .doc_templates import from_quotation, render_for
            return render_for(org, from_quotation(org, rec))
        return Shareable("quotation", "Quotation", rec.key, pdf, name, phone, email, data.get("total") or data.get("total_amount"))
    if kind == "statement":
        from apps.purchasing.models import Supplier
        from apps.sales.models import Customer
        side = "supplier" if params.get("side") == "supplier" else "customer"
        party = (Supplier if side == "supplier" else Customer).objects(organization=org, id=_oid(ident)).first()
        if not party:
            raise LookupError("Party not found.")
        start, end = _dates(params)
        data = party_statement(org, side, party, start, end)
        owed = data["closing"] if side == "customer" else -data["closing"]
        return Shareable("statement", "Statement", f"{party.name} {start:%d%b%y}-{end:%d%b%y}", lambda: statement_pdf(org, data), party.name, party.phone, party.email,
                         amount=owed, extra={"from": start.isoformat(), "to": end.isoformat(), "side": side, "balance": owed, "open_bills": len(data["bills"])},
                         filename=f"Statement-{safe_name(party.name)}-{start:%d%b%Y}-to-{end:%d%b%Y}.pdf")
    if kind == "tally_ledger":
        from . import tally_api, tally_sync
        company = tally_sync.active_company(str(org.id))
        if not company:
            raise LookupError("Tally is not connected.")
        start, end = _dates(params)
        data = tally_api.ledger_statement(str(org.id), company["name"], str(ident), start.isoformat(), end.isoformat())
        if not data:
            raise LookupError("Ledger not found in Tally.")
        debit = sum((Decimal(str(r["debit"])) for r in data["rows"]), Decimal(0))
        credit = sum((Decimal(str(r["credit"])) for r in data["rows"]), Decimal(0))
        doc = {"title": "Statement of account", "party": {"name": data["name"], "gstin": data["gstin"], "address": data["address"].replace("\n", ", "), "phone": data["phone"], "email": data["email"]},
               "from": data["from"], "to": data["to"], "opening": data["opening"], "closing": data["period_closing"], "debit": float(debit), "credit": float(credit),
               "rows": data["rows"], "bills": data["bills"], "source": f"Tally · {company['name']}"}
        creditor = data["group"] == "creditors"
        owed = -data["closing"] if creditor else data["closing"]
        name, phone, email = data["name"], data["phone"], data["email"]
        row = db().tally_links.find_one({"org_id": str(org.id), "tally_guid": str(ident)})
        if row and (not phone or not email):
            from apps.purchasing.models import Supplier
            from apps.sales.models import Customer
            p = (Supplier if row["model"] == "supplier" else Customer).objects(id=row["nexease_id"]).first() if row["model"] in ("customer", "supplier") else None
            if p:
                phone, email = phone or p.phone, email or p.email
        return Shareable("tally_ledger", "Statement", f"{data['name']} {start:%d%b%y}-{end:%d%b%y}", lambda: statement_pdf(org, doc), name, phone, email, amount=owed,
                         extra={"from": data["from"], "to": data["to"], "side": "supplier" if creditor else "customer", "balance": owed, "open_bills": len(data["bills"])},
                         filename=f"Statement-{safe_name(name)}-{start:%d%b%Y}-to-{end:%d%b%Y}.pdf")
    if kind == "tally_voucher":
        from . import tally_api, tally_sync
        company = tally_sync.active_company(str(org.id))
        o = db().tally_objects.find_one({"org_id": str(org.id), "company": company["name"] if company else "", "kind": "voucher", "guid": str(ident)}) if company else None
        if not o:
            raise LookupError("Voucher not found in Tally.")
        tmap, _ = tally_api._type_map(str(org.id), company["name"])
        d = o["data"]
        v = {**tally_api._vrow(o, tmap), "narration": d.get("narration", ""), "party_gstin": d.get("party_gstin", ""), "inventory": d.get("inventory", []),
             "entries": [{"ledger": e["ledger"], "debit": float(Decimal(e["amount"])) if Decimal(e["amount"]) > 0 else 0, "credit": float(-Decimal(e["amount"])) if Decimal(e["amount"]) < 0 else 0}
                         for e in d.get("entries", [])]}
        led = db().tally_objects.find_one({"org_id": str(org.id), "company": company["name"], "kind": "ledger", "name": d.get("party", "")}) if d.get("party") else None
        ld = (led or {}).get("data") or {}
        return Shareable("tally_voucher", d.get("voucher_type") or "Voucher", d.get("number") or o["guid"][:8], lambda: voucher_pdf(org, v, company["name"]),
                         d.get("party", ""), ld.get("phone", ""), ld.get("email", ""), amount=v["amount"])
    raise LookupError("This cannot be shared.")


def allowed(request, kind, params):
    if kind == "statement":
        return permitted(request, "bills.read" if params.get("side") == "supplier" else "invoices.read")
    return kind in PERMISSION and permitted(request, PERMISSION[kind])


# --------------------------------------------------------------------------------------------
# Messages
# --------------------------------------------------------------------------------------------

def compose(org, s, user=None):
    """Default WhatsApp text, email subject and email body; the user can edit all three."""
    business = org.name
    hello = f"Dear {s.party_name}," if s.party_name else "Hello,"
    person = " ".join(x for x in [getattr(user, "first_name", ""), getattr(user, "last_name", "")] if x).strip() if user else ""
    signature = "Regards,\n" + (person + "\n" if person else "") + business
    if s.kind in ("statement", "tally_ledger"):
        bal = Decimal(str(s.extra.get("balance") or 0))
        period = f"{date.fromisoformat(s.extra['from']):%d %b %Y} to {date.fromisoformat(s.extra['to']):%d %b %Y}"
        if s.extra.get("side") == "supplier":
            line = f"Our account with you shows {inr(bal)} payable by us." if bal > 0 else f"Our account with you shows {inr(bal)} receivable from you." if bal < 0 else "Our account with you is fully settled."
        else:
            line = f"The balance due is {inr(bal)}." if bal > 0 else f"You have a credit balance of {inr(bal)}." if bal < 0 else "Your account is fully settled. Thank you!"
        whatsapp = f"{hello}\nPlease find your statement of account with {business} for {period}. {line}"
        subject = f"Statement of account – {s.party_name} – {business}"
        body = f"{hello}\n\nPlease find attached your statement of account with {business} for {period}.\n{line}\n"
        if s.extra.get("open_bills") and bal > 0 and s.extra.get("side") != "supplier":
            body += f"Pending bills are listed at the end of the statement ({s.extra['open_bills']}).\n"
        body += "\nKindly let us know of any difference.\n\n" + signature
        return whatsapp, subject, body
    amount = f" for {inr(s.amount)}" if s.amount not in (None, "") else ""
    due = ""
    if s.kind == "invoice" and s.due not in (None, "") and Decimal(str(s.due)) > 0:
        due = f" Balance due {inr(s.due)}" + (f" by {date.fromisoformat(s.extra['due_date']):%d %b %Y}" if s.extra.get("due_date") else "") + "."
    label = s.label.lower() if not s.kind.startswith("tally") else s.label
    whatsapp = f"{hello}\nPlease find {label} {s.number}{amount} from {business}.{due}"
    if s.kind == "invoice":
        whatsapp += " Thank you for your business."
    subject = f"{s.label} {s.number} from {business}"
    body = f"{hello}\n\nPlease find attached {label} {s.number}{amount}.{due}\n\nFor any questions, simply reply to this email.\n\n{signature}"
    return whatsapp, subject, body


# --------------------------------------------------------------------------------------------
# Private links (always open the live document)
# --------------------------------------------------------------------------------------------

def link_for(request, org, kind, ident, params, create=True):
    clean = {k: params[k] for k in ("from", "to", "side") if params.get(k)}
    q = {"org_id": str(org.id), "kind": kind, "ident": str(ident), "params": clean, "revoked": False, "expires": {"$gt": now()}}
    row = db().share_links.find_one(q)
    if not row and create:
        row = {"_id": secrets.token_urlsafe(18), "org_id": str(org.id), "kind": kind, "ident": str(ident), "params": clean, "revoked": False, "views": 0,
               "created_by": str(request.api_user.id), "created_at": now(), "expires": now() + timedelta(days=LINK_DAYS)}
        db().share_links.insert_one(row)
    if not row:
        return None
    return {"token": row["_id"], "url": public_url(request, row["_id"]), "expires": (row["expires"] + IST).date().isoformat(), "views": row.get("views", 0)}


def public_url(request, token):
    url = request.build_absolute_uri(f"/api/v1/business/share/l/{token}/")
    host = request.get_host().split(":")[0]
    if host not in ("localhost", "127.0.0.1", "testserver") and url.startswith("http://"):
        url = "https://" + url[len("http://"):]
    return url


@csrf_exempt
@require_http_methods(["GET"])
def public_link(request, token):
    row = db().share_links.find_one({"_id": token})
    if not row or row.get("revoked") or row["expires"] < now():
        return HttpResponse("This link has expired or was withdrawn. Please ask the sender for a new one.", status=410, content_type="text/plain; charset=utf-8")
    from apps.organizations.models import Organization
    org = Organization.objects(id=row["org_id"]).first()
    try:
        s = resolve(org, row["kind"], row["ident"], row.get("params") or {})
        content = s.pdf()
    except (LookupError, ValueError):
        return HttpResponse("This document is no longer available.", status=404, content_type="text/plain; charset=utf-8")
    db().share_links.update_one({"_id": token}, {"$inc": {"views": 1}, "$set": {"last_viewed": now()}})
    response = HttpResponse(content, content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="{s.filename}"'
    response["Cache-Control"] = "no-store"
    response["X-Robots-Tag"] = "noindex"
    return response


# --------------------------------------------------------------------------------------------
# App endpoints
# --------------------------------------------------------------------------------------------

def _target(request, source):
    kind = str(source.get("kind") or "")
    ident = str(source.get("id") or "")
    params = {k: str(source.get(k) or "") for k in ("from", "to", "side")}
    if kind not in KINDS or not ident:
        raise LookupError("Choose what to share.")
    return kind, ident, params


def log_share(request, kind, ident, number, channel, recipients, subject="", status="sent", error=""):
    db().share_log.insert_one({"org_id": str(request.api_organization.id), "kind": kind, "ident": str(ident), "number": number, "channel": channel,
                               "recipients": recipients, "subject": subject, "status": status, "error": error[:300], "by": str(request.api_user.id),
                               "by_name": " ".join(x for x in [request.api_user.first_name, getattr(request.api_user, "last_name", "")] if x) or request.api_user.email, "at": now()})


@api_login_required
@require_http_methods(["GET"])
def prepare(request):
    try:
        kind, ident, params = _target(request, request.GET)
        if not allowed(request, kind, params):
            return R.forbidden(request=request)
        org = request.api_organization
        s = resolve(org, kind, ident, params)
    except LookupError as e:
        return R.not_found(message=str(e), request=request)
    whatsapp, subject, body = compose(org, s, request.api_user)
    link = link_for(request, org, kind, ident, params)
    last = list(db().share_log.find({"org_id": str(org.id), "kind": kind, "ident": str(ident)}, {"_id": 0, "channel": 1, "recipients": 1, "at": 1, "by_name": 1}).sort("at", -1).limit(5))
    return R.success(data={"kind": kind, "id": ident, "label": s.label, "number": s.number, "filename": s.filename, "recipient": {"name": s.party_name, "phone": s.phone, "email": s.email},
                           "amount": float(s.amount) if s.amount not in (None, "") else None, "whatsapp": whatsapp, "subject": subject, "body": body, "link": link,
                           "extra": s.extra, "history": [{**h, "at": (h["at"] + IST).isoformat(timespec="minutes")} for h in last]}, request=request)


@api_login_required
@require_http_methods(["GET"])
def pdf(request):
    try:
        kind, ident, params = _target(request, request.GET)
        if not allowed(request, kind, params):
            return R.forbidden(request=request)
        s = resolve(request.api_organization, kind, ident, params)
        content = s.pdf()
    except LookupError as e:
        return R.not_found(message=str(e), request=request)
    response = HttpResponse(content, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{s.filename}"'
    response["Cache-Control"] = "private, no-store"
    return response


def _emails(value):
    items = value if isinstance(value, list) else re.split(r"[,;\s]+", str(value or ""))
    out = []
    for raw in items:
        e = str(raw or "").strip()
        if not e:
            continue
        try:
            validate_email(e)
        except ValidationError:
            raise ValueError(f"“{e}” is not a valid email address.")
        if e.lower() not in [o.lower() for o in out]:
            out.append(e)
    return out


@api_login_required
@require_http_methods(["POST"])
def email(request):
    body = payload(request)
    try:
        kind, ident, params = _target(request, body)
        if not allowed(request, kind, params):
            return R.forbidden(request=request)
        org = request.api_organization
        s = resolve(org, kind, ident, params)
    except LookupError as e:
        return R.not_found(message=str(e), request=request)
    try:
        to, cc = _emails(body.get("recipients") or body.get("to_emails")), _emails(body.get("cc"))
        if not to:
            raise ValueError("Enter the customer's email address.")
        if len(to) + len(cc) > MAX_RECIPIENTS:
            raise ValueError(f"Send to at most {MAX_RECIPIENTS} addresses at a time.")
        default_whatsapp, default_subject, default_body = compose(org, s, request.api_user)
        subject = (str(body.get("subject") or "").strip() or default_subject)[:200]
        message = (str(body.get("message") or "").strip() or default_body)[:10000]
        if body.get("link"):
            link = link_for(request, org, kind, ident, params)
            message += f"\n\nView the latest version online: {link['url']}"
        from apps.core.services.user_mailbox_service import delivery_options
        sender = delivery_options(request.api_user, org)
        mail = EmailMessage(subject=subject, body=message, to=to, cc=cc, **sender)
        if body.get("attach", True):
            mail.attach(s.filename, s.pdf(), "application/pdf")
        if mail.send(fail_silently=False) != 1:
            raise RuntimeError("The email server did not confirm delivery.")
    except ValueError as e:
        return R.validation_error(message=str(e), request=request)
    except Exception as e:  # SMTP and similar
        log_share(request, kind, ident, s.number, "email", to if "to" in locals() else [], status="failed", error=str(e))
        return R.validation_error(message=f"Could not send the email: {e}", request=request)
    log_share(request, kind, ident, s.number, "email", to + cc, subject)
    from .views import audit
    audit(request, "share", f"{kind}:{ident}", "email")
    return R.success(data={"sent_to": to + cc}, message=f"Sent to {', '.join(to)}.", request=request)


@api_login_required
@require_http_methods(["POST"])
def log(request):
    body = payload(request)
    try:
        kind, ident, params = _target(request, body)
    except LookupError as e:
        return R.not_found(message=str(e), request=request)
    if not allowed(request, kind, params):
        return R.forbidden(request=request)
    channel = body.get("channel") if body.get("channel") in ("whatsapp", "link", "download", "share") else "share"
    recipient = re.sub(r"[^\d+]", "", str(body.get("recipient") or ""))[:20]
    log_share(request, kind, ident, str(body.get("number") or "")[:80], channel, [recipient] if recipient else [])
    return R.success(data={"logged": True}, request=request)


@api_login_required
@require_http_methods(["GET"])
def history(request):
    q = {"org_id": str(request.api_organization.id)}
    if request.GET.get("kind"):
        q["kind"] = request.GET["kind"]
    if request.GET.get("id"):
        q["ident"] = request.GET["id"]
    if not (permitted(request, "invoices.read") or permitted(request, "bills.read") or permitted(request, "accounting_reports.read")):
        return R.forbidden(request=request)
    rows = [{"kind": r["kind"], "id": r["ident"], "number": r.get("number", ""), "channel": r["channel"], "recipients": r.get("recipients", []), "status": r.get("status", "sent"),
             "error": r.get("error", ""), "by": r.get("by_name", ""), "at": (r["at"] + IST).isoformat(timespec="minutes")}
            for r in db().share_log.find(q).sort("at", -1).limit(100)]
    return R.success(data={"history": rows}, request=request)


@api_login_required
@require_http_methods(["POST"])
def revoke(request, token):
    row = db().share_links.find_one({"_id": token, "org_id": str(request.api_organization.id)})
    if not row:
        return R.not_found(message="Link not found.", request=request)
    if not allowed(request, row["kind"], row.get("params") or {}):
        return R.forbidden(request=request)
    db().share_links.update_one({"_id": token}, {"$set": {"revoked": True, "revoked_at": now()}})
    return R.success(message="Link withdrawn. It no longer opens.", request=request)
