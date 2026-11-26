"""GST compliance: IMS inbox, GSTR-2B ↔ purchase reconciliation, GSTR-1 and GSTR-3B preparation.

How it follows the GST rules (as advised by GSTN, Oct 2024 – Oct 2025):
- Supplier documents reach the recipient's IMS from GSTR-1 / IFF / GSTR-1A. The recipient may Accept,
  Reject or keep Pending. No action is treated as accepted when GSTR-2B is generated (14th of the
  following month). Actions can still change until GSTR-3B for that period is filed.
- Accepted / deemed-accepted records form "ITC available" in GSTR-2B, which auto-fills Table 4 of
  GSTR-3B. Rule 36(4): ITC is claimable only to the extent it appears in GSTR-2B.
- Pending records stay out of GSTR-2B. Credit notes may be kept pending for one following period.
  When accepting a credit note the recipient may declare the ITC to be reduced.
- Reverse-charge records do not appear in IMS.
- GSTR-3B Table 3 (outward liability) is auto-filled from GSTR-1 and is not editable on the portal.

NexEase cannot connect to the GST portal (that needs a GSP licence). The user downloads the GSTR-2B
JSON from the portal and uploads it here (or fills the CSV template), takes IMS decisions here, and
mirrors them on the portal. Nothing in this module files a return.
"""
import csv
import hashlib
import io
import json
import re
from datetime import date, datetime, time, timedelta
from decimal import Decimal, InvalidOperation

from bson import ObjectId
from django.views.decorators.http import require_http_methods
from mongoengine.connection import get_db

from apps.core.api.decorators import api_login_required
from apps.core.services.api_response_service import APIResponseService as R
from apps.purchasing.models import Supplier, VendorBill, VendorDebitNote
from apps.sales.models import CreditNote, Invoice

from .models import BusinessRecord
from .views import audit, payload, permitted, workbook_response

D0 = Decimal(0)
CENT = Decimal("0.01")
IST = timedelta(hours=5, minutes=30)
ACTIONS = ("accept", "reject", "pending", "none")
TAX_KEYS = ("taxable", "igst", "cgst", "sgst", "cess")
SALE_STATUSES = ("ISSUED", "PARTIALLY_PAID", "PAID")
BILL_STATUSES = ("POSTED", "PARTIALLY_PAID", "PAID")
# Quarterly (QRMP) GSTR-3B is due on the 22nd in these states and the 24th elsewhere.
STATES_22 = {"22", "23", "24", "26", "27", "29", "30", "31", "32", "33", "34", "35", "36", "37"}
B2CL_LIMIT = Decimal("100000")  # inter-state B2C invoices above ₹1 lakh are reported invoice-wise (Table 5)
GSTIN_RE = re.compile(r"^\d{2}[A-Z0-9]{10}[A-Z0-9]Z[A-Z0-9]$")
STATE_NAMES = {"01": "Jammu and Kashmir", "02": "Himachal Pradesh", "03": "Punjab", "04": "Chandigarh", "05": "Uttarakhand", "06": "Haryana",
               "07": "Delhi", "08": "Rajasthan", "09": "Uttar Pradesh", "10": "Bihar", "11": "Sikkim", "12": "Arunachal Pradesh", "13": "Nagaland",
               "14": "Manipur", "15": "Mizoram", "16": "Tripura", "17": "Meghalaya", "18": "Assam", "19": "West Bengal", "20": "Jharkhand",
               "21": "Odisha", "22": "Chhattisgarh", "23": "Madhya Pradesh", "24": "Gujarat", "26": "Dadra and Nagar Haveli and Daman and Diu",
               "27": "Maharashtra", "29": "Karnataka", "30": "Goa", "31": "Lakshadweep", "32": "Kerala", "33": "Tamil Nadu", "34": "Puducherry",
               "35": "Andaman and Nicobar Islands", "36": "Telangana", "37": "Andhra Pradesh", "38": "Ladakh", "97": "Other Territory"}


def col():
    return get_db().nexease_gst_inward


def dec(value):
    try:
        return Decimal(str(value or 0)).quantize(CENT)
    except (InvalidOperation, ValueError):
        raise ValueError("Amounts must be numbers.")


def money(value):
    return f"{Decimal(value).quantize(CENT):.2f}"


def parse_period(value):
    if not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", value or ""):
        raise ValueError("Choose a period like 2026-10.")
    return int(value[:4]), int(value[5:])


def month_bounds(period):
    """First and last calendar day of a YYYY-MM period."""
    y, m = parse_period(period)
    start = date(y, m, 1)
    end = (date(y + (m == 12), m % 12 + 1, 1) - timedelta(days=1))
    return start, end


def utc_range(start, end):
    return datetime.combine(start, time.min) - IST, datetime.combine(end + timedelta(days=1), time.min) - IST


def ist_day(value):
    return (value + IST).date() if value else None


def norm_number(value):
    """Supplier invoice numbers are compared without spaces, symbols, case or leading zeros."""
    text = re.sub(r"[^A-Z0-9]", "", str(value or "").upper())
    return re.sub(r"(?<![0-9])0+(?=[0-9])", "", text)


def parse_doc_date(value):
    value = str(value or "").strip()
    for fmt in ("%d-%m-%Y", "%Y-%m-%d", "%d/%m/%Y", "%d-%b-%Y"):
        try:
            return datetime.strptime(value, fmt).date().isoformat()
        except ValueError:
            continue
    raise ValueError("Unrecognised document date: " + value)


def registration(org):
    r = BusinessRecord.objects(organization=org, kind="gst_settings", key="registration").first()
    data = (r.data if r else {}) or {}
    return {"gstin": data.get("gstin", ""), "state_code": data.get("state_code", ""), "legal_name": data.get("legal_name", ""),
            "registration": data.get("registration", "regular"), "frequency": data.get("frequency", "monthly"), "configured": bool(r)}


# --------------------------------------------------------------------------------------------
# Due dates
# --------------------------------------------------------------------------------------------

def deadlines(period, reg):
    """Statutory due dates that apply to a tax period (CGST Act / notified dates, before any extension)."""
    y, m = parse_period(period)
    ny, nm = (y + (m == 12), m % 12 + 1)
    quarterly = reg.get("frequency") == "quarterly"
    quarter_end = m % 3 == 0
    items = [{"key": "ims", "label": "IMS: act on supplier documents", "date": date(ny, nm, 13).isoformat(),
              "note": "Act before GSTR-2B is generated on the 14th; no action counts as accepted. You can still change actions until GSTR-3B is filed."},
             {"key": "gstr2b", "label": "GSTR-2B generated", "date": date(ny, nm, 14).isoformat(), "note": "Recompute GSTR-2B on the portal if you change IMS actions afterwards."}]
    if not quarterly:
        items.append({"key": "gstr1", "label": "GSTR-1", "date": date(ny, nm, 11).isoformat(), "note": "Outward supplies. Auto-fills Table 3 of GSTR-3B, which cannot be edited."})
        items.append({"key": "gstr3b", "label": "GSTR-3B and tax payment", "date": date(ny, nm, 20).isoformat(), "note": "Monthly return and payment."})
    elif quarter_end:
        items.append({"key": "gstr1", "label": "GSTR-1 (quarterly)", "date": date(ny, nm, 13).isoformat(), "note": "Outward supplies for the quarter."})
        day = 22 if reg.get("state_code") in STATES_22 else 24
        items.append({"key": "gstr3b", "label": "GSTR-3B (quarterly)", "date": date(ny, nm, day).isoformat(), "note": "Quarterly return; due date depends on your state."})
    else:
        items.append({"key": "iff", "label": "IFF (optional B2B invoices)", "date": date(ny, nm, 13).isoformat(), "note": "Lets your B2B buyers claim ITC monthly."})
        items.append({"key": "pmt06", "label": "PMT-06 monthly tax payment", "date": date(ny, nm, 25).isoformat(), "note": "Fixed-sum or self-assessment payment for QRMP."})
    fy_start = y if m >= 4 else y - 1
    items.append({"key": "sec16_4", "label": "Last date to claim this year's ITC (Section 16(4))", "date": date(fy_start + 1, 11, 30).isoformat(),
                  "note": "ITC for invoices of FY " + f"{fy_start}-{str(fy_start + 1)[2:]}" + " must be claimed by 30 November or the annual return date, whichever is earlier."})
    return sorted(items, key=lambda i: i["date"])


# --------------------------------------------------------------------------------------------
# Import: GSTR-2B JSON from the portal, or the NexEase CSV template
# --------------------------------------------------------------------------------------------

def _record(org, period, src, ctin, name, doc_type, number, doc_date, values, pos="", rcm=False, portal="", itc_available=True, reason=""):
    ctin = (ctin or "").strip().upper()
    if not GSTIN_RE.match(ctin):
        raise ValueError("Supplier GSTIN is not valid: " + ctin)
    if doc_type not in ("INV", "CN", "DN"):
        raise ValueError("Document type must be INV, CN or DN.")
    if not str(number or "").strip():
        raise ValueError("Document number is missing for " + ctin)
    rec = {"organization_id": str(org.id), "period": period, "source": src, "supplier_gstin": ctin, "supplier_name": (name or "").strip()[:200],
           "doc_type": doc_type, "doc_number": str(number).strip()[:40], "doc_key": norm_number(number), "doc_date": parse_doc_date(doc_date),
           "pos": str(pos or ctin[:2]).zfill(2)[:2], "rcm": bool(rcm), "portal_action": portal, "itc_available": bool(itc_available), "portal_reason": reason}
    for k in TAX_KEYS:
        rec[k] = money(dec(values.get(k)))
    rec["total_tax"] = money(sum(dec(rec[k]) for k in ("igst", "cgst", "sgst", "cess")))
    rec["value"] = money(dec(values.get("value")) or dec(rec["taxable"]) + dec(rec["total_tax"]))
    return rec


def parse_gstr2b(raw, org):
    data = raw.get("data", raw)
    period_raw = str(data.get("rtnprd", ""))
    if not re.fullmatch(r"\d{6}", period_raw):
        raise ValueError("This does not look like a GSTR-2B JSON (return period missing).")
    period = f"{period_raw[2:]}-{period_raw[:2]}"
    own = (data.get("gstin") or "").upper()
    reg = registration(org)
    if reg["gstin"] and own and own != reg["gstin"].upper():
        raise ValueError(f"This GSTR-2B belongs to {own}, but your GST registration is {reg['gstin']}.")
    rows = []
    sections = [("docdata", True), ("docRejdata", False), ("docrejdata", False)]
    for section, available in sections:
        doc = data.get(section) or {}
        for supplier in doc.get("b2b", []) + doc.get("b2ba", []):
            for inv in supplier.get("inv", []):
                rows.append(_record(org, period, "gstr2b", supplier.get("ctin"), supplier.get("trdnm"), "INV", inv.get("inum"), inv.get("dt"),
                                    {"value": inv.get("val"), **{k: inv.get("txval" if k == "taxable" else k) for k in TAX_KEYS}},
                                    inv.get("pos"), inv.get("rev") == "Y", "" if available else "rejected", available and inv.get("itcavl", "Y") != "N", inv.get("rsn", "")))
        for supplier in doc.get("cdnr", []) + doc.get("cdnra", []):
            for note in supplier.get("nt", []):
                kind = "CN" if note.get("typ") == "C" else "DN"
                rows.append(_record(org, period, "gstr2b", supplier.get("ctin"), supplier.get("trdnm"), kind, note.get("ntnum"), note.get("dt"),
                                    {"value": note.get("val"), **{k: note.get("txval" if k == "taxable" else k) for k in TAX_KEYS}},
                                    note.get("pos"), note.get("rev") == "Y", "" if available else "rejected", available and note.get("itcavl", "Y") != "N", note.get("rsn", "")))
    if not rows:
        raise ValueError("No B2B invoices or credit/debit notes were found in this GSTR-2B.")
    return period, rows


TEMPLATE_HEADERS = ["supplier_gstin", "supplier_name", "doc_type", "doc_number", "doc_date", "taxable", "igst", "cgst", "sgst", "cess", "pos", "reverse_charge"]


def parse_csv(text, org, period):
    reader = csv.DictReader(io.StringIO(text))
    missing = [h for h in TEMPLATE_HEADERS[:6] if h not in (reader.fieldnames or [])]
    if missing:
        raise ValueError("CSV is missing columns: " + ", ".join(missing))
    rows = []
    for n, line in enumerate(reader, start=2):
        if not any((v or "").strip() for v in line.values()):
            continue
        try:
            rows.append(_record(org, period, "csv", line.get("supplier_gstin"), line.get("supplier_name"), (line.get("doc_type") or "INV").strip().upper(),
                                line.get("doc_number"), line.get("doc_date"), {k: line.get(k) for k in TAX_KEYS}, line.get("pos"),
                                (line.get("reverse_charge") or "").strip().upper() in ("Y", "YES", "TRUE", "1")))
        except ValueError as e:
            raise ValueError(f"Row {n}: {e}")
    if not rows:
        raise ValueError("The CSV has no rows.")
    return rows


def store(org, period, rows, user):
    """Insert new documents; refresh amounts on ones already imported but keep the user's IMS decision."""
    added = updated = 0
    for rec in rows:
        key = {"organization_id": rec["organization_id"], "supplier_gstin": rec["supplier_gstin"], "doc_type": rec["doc_type"], "doc_key": rec["doc_key"], "doc_date": rec["doc_date"]}
        existing = col().find_one(key)
        if existing:
            col().update_one({"_id": existing["_id"]}, {"$set": {k: v for k, v in rec.items() if k not in ("organization_id",)}})
            updated += 1
        else:
            col().insert_one({**rec, "action": "none", "reason": "", "itc_reduce": "", "action_by": "", "action_at": None,
                              "linked_bill": "", "imported_at": datetime.utcnow(), "imported_by": str(user.id)})
            added += 1
    col().create_index([("organization_id", 1), ("period", 1)])
    return added, updated


# --------------------------------------------------------------------------------------------
# Reconciliation against purchase bills
# --------------------------------------------------------------------------------------------

def bill_tax_split(bill, own_state):
    """CGST+SGST when the supplier is in your state, IGST otherwise."""
    tax = dec(bill.tax_amount)
    supplier_state = (bill.supplier_gstin or "")[:2] or ""
    if supplier_state and own_state and supplier_state != own_state:
        return {"igst": tax, "cgst": D0, "sgst": D0}
    half = (tax / 2).quantize(CENT)
    return {"igst": D0, "cgst": half, "sgst": tax - half}


def books(org, start, end, own_state):
    lo, hi = utc_range(start, end)
    rows = []
    bills = VendorBill.objects(organization=org, status__in=BILL_STATUSES, bill_date__gte=lo, bill_date__lt=hi)
    for b in bills.only("id", "bill_number", "supplier_invoice_number", "supplier", "supplier_name", "supplier_gstin", "bill_date", "subtotal", "tax_amount", "total_amount", "discount_amount"):
        split = bill_tax_split(b, own_state)
        number = b.supplier_invoice_number or b.bill_number
        rows.append({"id": str(b.id), "kind": "bill", "doc_type": "INV", "number": number, "bill_number": b.bill_number, "doc_key": norm_number(number),
                     "supplier_gstin": (b.supplier_gstin or "").upper(), "supplier_name": b.supplier_name or "", "date": ist_day(b.bill_date).isoformat(),
                     "taxable": dec(b.total_amount) - dec(b.tax_amount), **split, "total_tax": dec(b.tax_amount)})
    return rows


def match_period(org, period):
    """Pairs each 2B/IMS record with a purchase bill: same supplier GSTIN and invoice number."""
    reg = registration(org)
    start, end = month_bounds(period)
    # Supplier invoices can be dated in earlier months but reported late; look back six months in books.
    book_rows = books(org, start - timedelta(days=183), end, reg["state_code"])
    by_key = {}
    for b in book_rows:
        by_key.setdefault((b["supplier_gstin"], b["doc_key"]), []).append(b)
    linked = {}
    records = list(col().find({"organization_id": str(org.id), "period": period}))
    used = set()
    out = []
    for r in records:
        bill = None
        if r.get("linked_bill"):
            bill = next((b for b in book_rows if b["id"] == r["linked_bill"]), None)
        if bill is None and r["doc_type"] == "INV":
            candidates = [b for b in by_key.get((r["supplier_gstin"], r["doc_key"]), []) if b["id"] not in used]
            bill = candidates[0] if candidates else None
        status, diffs = "only_in_2b", []
        if bill:
            used.add(bill["id"])
            for k in ("taxable", "igst", "cgst", "sgst"):
                d = dec(r[k]) - bill[k]
                if abs(d) > Decimal("1.00"):
                    diffs.append({"field": k, "portal": r[k], "books": money(bill[k]), "difference": money(d)})
            status = "mismatch" if diffs else "matched"
            if not diffs and r["doc_date"] != bill["date"]:
                status, diffs = "date_mismatch", [{"field": "date", "portal": r["doc_date"], "books": bill["date"], "difference": ""}]
        elif r["doc_type"] != "INV":
            status = "note"
        linked[str(r["_id"])] = bill["id"] if bill else ""
        out.append((r, bill, status, diffs))
    in_period = [b for b in book_rows if start.isoformat() <= b["date"] <= end.isoformat()]
    missing = [b for b in in_period if b["id"] not in used]
    return out, missing, reg


def suggestion(status, record):
    if record.get("rcm"):
        return "none", "Reverse-charge documents do not appear in IMS; pay the tax yourself in GSTR-3B Table 3.1(d)."
    if status == "matched":
        return "accept", "Matches your purchase bill."
    if status == "date_mismatch":
        return "accept", "Matches on amount; only the date differs. Check the bill date."
    if status == "mismatch":
        return "pending", "Amounts differ from your bill. Ask the supplier to amend, or correct your bill."
    if status == "note":
        return "accept", "Credit/debit note: accept if you agreed it; declare the ITC to reduce if you had not claimed the full credit."
    return "pending", "Not in your books. Record the bill if the purchase is yours, or reject it if it is not."


def serialise_record(r, bill, status, diffs):
    action_hint, why = suggestion(status, r)
    return {"id": str(r["_id"]), "period": r["period"], "source": r["source"], "supplier_gstin": r["supplier_gstin"], "supplier_name": r.get("supplier_name", ""),
            "doc_type": r["doc_type"], "doc_number": r["doc_number"], "doc_date": r["doc_date"], "pos": r.get("pos", ""), "rcm": r.get("rcm", False),
            **{k: r[k] for k in TAX_KEYS}, "total_tax": r["total_tax"], "value": r["value"], "itc_available": r.get("itc_available", True),
            "portal_action": r.get("portal_action", ""), "action": r.get("action", "none"), "reason": r.get("reason", ""), "itc_reduce": r.get("itc_reduce", ""),
            "action_at": r["action_at"].isoformat() if r.get("action_at") else None,
            "match": {"status": status, "differences": diffs, "bill": {"id": bill["id"], "number": bill["bill_number"], "supplier_invoice": bill["number"], "date": bill["date"],
                                                                         "taxable": money(bill["taxable"]), "total_tax": money(bill["total_tax"])} if bill else None},
            "suggested": action_hint, "suggestion": why}


# --------------------------------------------------------------------------------------------
# Outward: GSTR-1 tables and GSTR-3B Table 3
# --------------------------------------------------------------------------------------------

def invoice_heads(inv, own_state):
    """(category, place of supply, taxable, igst, cgst, sgst, needs_review) for one sales invoice."""
    d = inv.billing_details or {}
    taxable = dec(inv.total_amount) - dec(inv.tax_amount)
    tax = dec(inv.tax_amount)
    supply = d.get("supply_type") or ""
    review = not d.get("tax_reviewed") or not supply
    pos = d.get("place_of_supply") or (inv.customer_gstin or "")[:2] or own_state
    supplier_state = d.get("supplier_state") or own_state
    if supply in ("exempt", "nil_rated", "non_gst"):
        return supply, pos, taxable, D0, D0, D0, False
    if pos and supplier_state and pos != supplier_state:
        return "taxable", pos, taxable, tax, D0, D0, review
    cgst = sum((dec(Decimal(str(i.line_tax)) / 2) for i in inv.items), D0)
    return "taxable", pos, taxable, D0, cgst, tax - cgst, review


def outward(org, start, end, own_state):
    lo, hi = utc_range(start, end)
    invoices = list(Invoice.objects(organization=org, status__in=SALE_STATUSES, invoice_date__gte=lo, invoice_date__lt=hi))
    cancelled = Invoice.objects(organization=org, status="CANCELLED", invoice_date__gte=lo, invoice_date__lt=hi).count()
    notes = list(CreditNote.objects(organization=org, status="ISSUED", credit_note_date__gte=lo, credit_note_date__lt=hi))
    return invoices, cancelled, notes


def zero():
    return {k: D0 for k in TAX_KEYS} | {"count": 0}


def add(bucket, taxable, igst, cgst, sgst, count=1):
    bucket["taxable"] += taxable
    bucket["igst"] += igst
    bucket["cgst"] += cgst
    bucket["sgst"] += sgst
    bucket["count"] += count


def out(bucket):
    return {k: (money(v) if isinstance(v, Decimal) else v) for k, v in bucket.items()}


def gstr1_data(org, start, end, reg):
    own = reg["state_code"]
    invoices, cancelled, notes = outward(org, start, end, own)
    t = {"b2b": zero(), "b2cl": zero(), "b2cs": zero(), "nil": zero(), "cdnr": zero(), "cdnur": zero()}
    b2cs_rows, hsn, review, numbers = {}, {}, [], []
    for inv in invoices:
        cat, pos, taxable, igst, cgst, sgst, needs = invoice_heads(inv, own)
        numbers.append(inv.invoice_number)
        if needs:
            review.append({"id": str(inv.id), "number": inv.invoice_number, "reason": "GST classification not reviewed; counted from the tax on the invoice."})
        registered = bool(inv.customer_gstin)
        if cat != "taxable":
            add(t["nil"], taxable, D0, D0, D0)
        elif registered:
            add(t["b2b"], taxable, igst, cgst, sgst)
        elif igst and dec(inv.total_amount) > B2CL_LIMIT:
            add(t["b2cl"], taxable, igst, cgst, sgst)
        else:
            add(t["b2cs"], taxable, igst, cgst, sgst)
            rate = max((Decimal(str(i.tax_rate)) for i in inv.items), default=D0)
            key = (pos, f"{rate.normalize():f}")
            add(b2cs_rows.setdefault(key, zero()), taxable, igst, cgst, sgst)
        for line in inv.items:
            code = (line.hsn_code or "").strip() or "—"
            k = ("B2B" if registered else "B2C", code, f"{Decimal(str(line.tax_rate)).normalize():f}")
            row = hsn.setdefault(k, {"quantity": D0, "taxable": D0, "tax": D0})
            row["quantity"] += Decimal(str(line.quantity))
            row["taxable"] += Decimal(str(line.line_subtotal)) - Decimal(str(line.discount or 0))
            row["tax"] += Decimal(str(line.line_tax))
    for note in notes:
        inv = note.invoice
        registered = bool(getattr(inv, "customer_gstin", "")) if inv else False
        tax = dec(note.tax_amount)
        taxable = dec(note.total_amount) - tax if hasattr(note, "total_amount") else dec(note.subtotal)
        if inv:
            _, _, _, igst, _, _, _ = invoice_heads(inv, own)
            inter = bool(igst)
        else:
            inter = False
        half = (tax / 2).quantize(CENT)
        add(t["cdnr" if registered else "cdnur"], taxable, tax if inter else D0, D0 if inter else half, D0 if inter else tax - half)
    docs = {"from": min(numbers) if numbers else "", "to": max(numbers) if numbers else "", "issued": len(numbers) + cancelled, "cancelled": cancelled}
    return t, b2cs_rows, hsn, review, docs


def gstr1(org, period, reg):
    start, end = month_bounds(period)
    if reg["frequency"] == "quarterly":
        y, m = parse_period(period)
        qm = ((m - 1) // 3) * 3 + 1
        start = date(y, qm, 1)
    t, b2cs_rows, hsn, review, docs = gstr1_data(org, start, end, reg)
    tables = [
        {"table": "4A", "label": "B2B invoices (registered buyers)", **out(t["b2b"])},
        {"table": "5", "label": "B2C large (inter-state, invoice above ₹1 lakh)", **out(t["b2cl"])},
        {"table": "7", "label": "B2C others", **out(t["b2cs"])},
        {"table": "8", "label": "Nil-rated, exempt and non-GST", **out(t["nil"])},
        {"table": "9B", "label": "Credit notes to registered buyers", **out(t["cdnr"])},
        {"table": "9B", "label": "Credit notes to unregistered buyers", **out(t["cdnur"])},
    ]
    return {"period": period, "from": start.isoformat(), "to": end.isoformat(), "tables": tables,
            "b2cs": [{"pos": k[0], "state": STATE_NAMES.get(k[0], k[0]), "rate": k[1], **out(v)} for k, v in sorted(b2cs_rows.items())],
            "hsn": [{"section": k[0], "hsn": k[1], "rate": k[2], "quantity": f"{v['quantity'].normalize():f}", "taxable": money(v["taxable"]), "tax": money(v["tax"])} for k, v in sorted(hsn.items())],
            "documents": docs, "review": review[:100], "review_count": len(review)}


# --------------------------------------------------------------------------------------------
# GSTR-3B
# --------------------------------------------------------------------------------------------

def itc_from_2b(org, periods):
    """Table 4(A)(5): accepted + no-action records; pending and rejected stay out (credit notes reduce)."""
    avail = {k: D0 for k in ("igst", "cgst", "sgst", "cess")}
    counts = {a: 0 for a in ACTIONS}
    rcm = {k: D0 for k in ("taxable", "igst", "cgst", "sgst", "cess")}
    for r in col().find({"organization_id": str(org.id), "period": {"$in": periods}}):
        counts[r.get("action", "none")] += 1
        if r.get("rcm"):
            for k in rcm:
                rcm[k] += dec(r[k])
            continue
        if r.get("action") in ("reject", "pending") or r.get("portal_action") == "rejected" or not r.get("itc_available", True):
            continue
        sign = -1 if r["doc_type"] == "CN" else 1
        if r["doc_type"] == "CN" and r.get("itc_reduce"):
            reduce = dec(r["itc_reduce"])
            total = dec(r["total_tax"]) or Decimal(1)
            for k in avail:
                avail[k] -= (dec(r[k]) * reduce / total).quantize(CENT)
            continue
        for k in avail:
            avail[k] += sign * dec(r[k])
    return avail, counts, rcm


def rule37_reversal(org, as_of, own_state):
    """Unpaid supplier bills older than 180 days: ITC to reverse under Rule 37 until paid."""
    cutoff = datetime.combine(as_of - timedelta(days=180), time.min) - IST
    rows = []
    total = {k: D0 for k in ("igst", "cgst", "sgst")}
    for b in VendorBill.objects(organization=org, status__in=("POSTED", "PARTIALLY_PAID"), balance_due__gt=0, bill_date__lt=cutoff).limit(500):
        unpaid_share = dec(b.balance_due) / (dec(b.total_amount) or Decimal(1))
        split = bill_tax_split(b, own_state)
        part = {k: (v * unpaid_share).quantize(CENT) for k, v in split.items()}
        for k in total:
            total[k] += part[k]
        rows.append({"id": str(b.id), "number": b.bill_number, "supplier": b.supplier_name or "", "date": ist_day(b.bill_date).isoformat(),
                     "balance": money(b.balance_due), "itc": money(sum(part.values()))})
    return total, rows


def set_off(liability, itc):
    """Utilise ITC as Section 49 / Rule 88A requires: IGST credit first against IGST, then CGST, then SGST;
    CGST credit against CGST then IGST; SGST credit against SGST then IGST. CGST and SGST never cross."""
    L = {k: max(liability[k], D0) for k in ("igst", "cgst", "sgst", "cess")}
    C = {k: max(itc[k], D0) for k in ("igst", "cgst", "sgst", "cess")}
    used = {(a, b): D0 for a in C for b in L}

    def use(credit, head):
        amount = min(C[credit], L[head])
        C[credit] -= amount
        L[head] -= amount
        used[(credit, head)] += amount

    use("igst", "igst")
    use("igst", "cgst")
    use("igst", "sgst")
    use("cgst", "cgst")
    use("cgst", "igst")
    use("sgst", "sgst")
    use("sgst", "igst")
    use("cess", "cess")
    return {"cash": {k: money(v) for k, v in L.items()}, "carry_forward": {k: money(v) for k, v in C.items()},
            "utilised": [{"credit": a, "against": b, "amount": money(v)} for (a, b), v in used.items() if v]}


def gstr3b(org, period, reg):
    start, end = month_bounds(period)
    periods = [period]
    if reg["frequency"] == "quarterly":
        y, m = parse_period(period)
        qm = ((m - 1) // 3) * 3 + 1
        start = date(y, qm, 1)
        periods = [f"{y}-{qm + i:02d}" for i in range(3) if qm + i <= m]
    t, _, _, review, _ = gstr1_data(org, start, end, reg)
    a = {k: t["b2b"][k] + t["b2cl"][k] + t["b2cs"][k] - t["cdnr"][k] - t["cdnur"][k] for k in ("taxable", "igst", "cgst", "sgst")}
    a["cess"] = D0
    avail, counts, rcm = itc_from_2b(org, periods)
    rule37, rule37_rows = rule37_reversal(org, end, reg["state_code"])
    rule37["cess"] = D0
    inter_unreg = {}
    lo, hi = utc_range(start, end)
    for inv in Invoice.objects(organization=org, status__in=SALE_STATUSES, invoice_date__gte=lo, invoice_date__lt=hi):
        if inv.customer_gstin:
            continue
        cat, pos, taxable, igst, _, _, _ = invoice_heads(inv, reg["state_code"])
        if cat == "taxable" and igst:
            row = inter_unreg.setdefault(pos, {"taxable": D0, "igst": D0})
            row["taxable"] += taxable
            row["igst"] += igst
    liability = {k: a[k] + rcm.get(k, D0) for k in ("igst", "cgst", "sgst", "cess")}
    net_itc = {k: avail[k] - rule37.get(k, D0) for k in ("igst", "cgst", "sgst", "cess")}
    # Purchases in your books for comparison (ITC you expect vs ITC in GSTR-2B).
    book = {k: D0 for k in ("igst", "cgst", "sgst")}
    for b in books(org, start, end, reg["state_code"]):
        for k in book:
            book[k] += b[k]
    return {"period": period, "periods": periods, "from": start.isoformat(), "to": end.isoformat(),
            "table_3_1": [
                {"row": "3.1(a)", "label": "Outward taxable supplies (other than zero-rated, nil-rated and exempted)", **{k: money(v) for k, v in a.items()}},
                {"row": "3.1(b)", "label": "Outward taxable supplies (zero-rated)", **{k: "0.00" for k in TAX_KEYS}},
                {"row": "3.1(c)", "label": "Other outward supplies (nil-rated, exempted)", "taxable": money(t["nil"]["taxable"]), **{k: "0.00" for k in ("igst", "cgst", "sgst", "cess")}},
                {"row": "3.1(d)", "label": "Inward supplies liable to reverse charge", **{k: money(v) for k, v in rcm.items()}},
                {"row": "3.1(e)", "label": "Non-GST outward supplies", **{k: "0.00" for k in TAX_KEYS}},
            ],
            "table_3_2": [{"pos": pos, "state": STATE_NAMES.get(pos, pos), "taxable": money(v["taxable"]), "igst": money(v["igst"])} for pos, v in sorted(inter_unreg.items())],
            "table_4": {
                "a5_all_other_itc": {k: money(v) for k, v in avail.items()},
                "a3_reverse_charge": {k: money(rcm[k]) for k in ("igst", "cgst", "sgst", "cess")},
                "b2_rule37_reversal": {k: money(v) for k, v in rule37.items()},
                "net": {k: money(v) for k, v in net_itc.items()},
                "books": {k: money(v) for k, v in book.items()},
            },
            "rule37_bills": rule37_rows[:50],
            "ims_counts": counts,
            "payment": set_off(liability, {k: net_itc[k] + rcm.get(k, D0) for k in net_itc}),
            "liability": {k: money(v) for k, v in liability.items()},
            "review_count": len(review),
            "notes": ["Table 3 is auto-filled from your GSTR-1 on the portal and cannot be edited there; correct mistakes through GSTR-1A.",
                      "Table 4(A)(5) comes from GSTR-2B: documents you accepted or did not act on. Pending and rejected documents are left out.",
                      "Reverse-charge tax must be paid in cash; its ITC is available after payment.",
                      "Blocked credits under Section 17(5) and Rule 42/43 reversals are not calculated here. Add them on the portal if they apply."]}


# --------------------------------------------------------------------------------------------
# Views
# --------------------------------------------------------------------------------------------

def guard(request, manage=False):
    if not permitted(request, "taxation.manage" if manage else "taxation.read"):
        return R.forbidden(message="You need the Taxation " + ("manage" if manage else "read") + " permission.", request=request)
    return None


@api_login_required
@require_http_methods(["GET"])
def overview(request):
    denied = guard(request)
    if denied:
        return denied
    try:
        org = request.api_organization
        period = request.GET.get("period") or (date.today().replace(day=1) - timedelta(days=1)).strftime("%Y-%m")
        reg = registration(org)
        matched, missing, _ = match_period(org, period)
        statuses = {}
        for _, _, status, _ in matched:
            statuses[status] = statuses.get(status, 0) + 1
        actions = {a: 0 for a in ACTIONS}
        for r, _, _, _ in matched:
            actions[r.get("action", "none")] += 1
        g1 = gstr1(org, period, reg)
        g3 = gstr3b(org, period, reg)
        alerts = []
        if not reg["configured"]:
            alerts.append({"tone": "danger", "text": "Add your GSTIN, state and return frequency under GST settings.", "href": "/taxation?tab=settings"})
        if not matched:
            alerts.append({"tone": "warn", "text": "Upload this period's GSTR-2B from the GST portal to start IMS and reconciliation.", "href": "/taxation?tab=ims"})
        if actions["none"]:
            alerts.append({"tone": "warn", "text": f"{actions['none']} supplier documents have no IMS action. They will count as accepted.", "href": "/taxation?tab=ims"})
        if missing:
            alerts.append({"tone": "warn", "text": f"{len(missing)} purchase bills are not in GSTR-2B yet. Their ITC cannot be claimed until the supplier reports them.", "href": "/taxation?tab=reconcile"})
        if g1["review_count"]:
            alerts.append({"tone": "info", "text": f"{g1['review_count']} sales invoices have no reviewed GST classification.", "href": "/taxation?tab=gstr1"})
        if g3["rule37_bills"]:
            alerts.append({"tone": "danger", "text": f"{len(g3['rule37_bills'])} supplier bills are unpaid for over 180 days. Reverse their ITC (Rule 37) until you pay.", "href": "/taxation?tab=gstr3b"})
        return R.success(data={"period": period, "registration": reg, "deadlines": deadlines(period, reg), "ims": actions, "reconciliation": statuses,
                               "missing_in_2b": len(missing), "gstr1": {"tables": g1["tables"], "documents": g1["documents"]},
                               "gstr3b": {"liability": g3["liability"], "itc": g3["table_4"]["net"], "cash": g3["payment"]["cash"]}, "alerts": alerts}, request=request)
    except ValueError as e:
        return R.validation_error(message=str(e), request=request)


@api_login_required
@require_http_methods(["GET", "POST"])
def ims(request):
    if request.method == "GET":
        denied = guard(request)
        if denied:
            return denied
        try:
            org = request.api_organization
            period = request.GET.get("period", "")
            parse_period(period)
            matched, missing, _ = match_period(org, period)
            rows = [serialise_record(*m) for m in matched]
            action = request.GET.get("action")
            status = request.GET.get("match")
            term = (request.GET.get("search") or "").strip().lower()
            if action:
                rows = [r for r in rows if r["action"] == action]
            if status:
                rows = [r for r in rows if r["match"]["status"] == status]
            if term:
                rows = [r for r in rows if term in (r["supplier_name"] + " " + r["supplier_gstin"] + " " + r["doc_number"]).lower()]
            rows.sort(key=lambda r: (r["rcm"], r["action"] != "none", r["supplier_name"], r["doc_date"]))
            return R.success(data={"period": period, "records": rows, "count": len(rows),
                                   "missing_in_2b": [{"id": b["id"], "number": b["number"], "bill_number": b["bill_number"], "supplier_gstin": b["supplier_gstin"],
                                                      "supplier_name": b["supplier_name"], "date": b["date"], "taxable": money(b["taxable"]), "total_tax": money(b["total_tax"])} for b in missing]}, request=request)
        except ValueError as e:
            return R.validation_error(message=str(e), request=request)
    denied = guard(request, manage=True)
    if denied:
        return denied
    try:
        org = request.api_organization
        upload = request.FILES.get("file")
        if not upload:
            raise ValueError("Choose the GSTR-2B JSON or the CSV template to upload.")
        if upload.size > 15 * 1024 * 1024:
            raise ValueError("The file is larger than 15 MB.")
        blob = upload.read()
        text = blob.decode("utf-8-sig", errors="strict")
        if upload.name.lower().endswith(".json") or text.lstrip().startswith("{"):
            period, rows = parse_gstr2b(json.loads(text), org)
        else:
            period = request.POST.get("period", "")
            parse_period(period)
            rows = parse_csv(text, org, period)
        added, updated = store(org, period, rows, request.api_user)
        audit(request, "gst_inward", hashlib.sha256(blob).hexdigest()[:24], f"import {period}: {added} new, {updated} updated")
        return R.success(data={"period": period, "added": added, "updated": updated}, message=f"Imported {added} new and refreshed {updated} documents for {period}.", request=request)
    except UnicodeDecodeError:
        return R.validation_error(message="The file must be UTF-8 text (JSON or CSV).", request=request)
    except json.JSONDecodeError:
        return R.validation_error(message="The JSON file could not be read. Download it again from the GST portal.", request=request)
    except ValueError as e:
        return R.validation_error(message=str(e), request=request)


@api_login_required
@require_http_methods(["POST"])
def ims_action(request):
    denied = guard(request, manage=True)
    if denied:
        return denied
    try:
        org = request.api_organization
        p = payload(request)
        action = p.get("action")
        ids = p.get("ids") or []
        reason = str(p.get("reason") or "").strip()[:300]
        if action not in ACTIONS:
            raise ValueError("Choose accept, reject, pending or clear.")
        if not isinstance(ids, list) or not ids or len(ids) > 1000:
            raise ValueError("Select 1–1,000 documents.")
        if action == "reject" and not reason:
            raise ValueError("Give a reason for rejecting, so the supplier and your auditor know why.")
        oids = [ObjectId(i) for i in ids if ObjectId.is_valid(i)]
        docs = list(col().find({"_id": {"$in": oids}, "organization_id": str(org.id)}))
        if len(docs) != len(ids):
            raise ValueError("Some documents were not found. Reload and try again.")
        skipped = []
        for d in docs:
            if d.get("rcm") and action != "none":
                skipped.append(d["doc_number"])
                continue
            update = {"action": action, "reason": reason if action in ("reject", "pending") else "", "action_by": str(request.api_user.id), "action_at": datetime.utcnow()}
            if action == "accept" and d["doc_type"] == "CN" and p.get("itc_reduce") not in (None, ""):
                reduce = dec(p.get("itc_reduce"))
                if reduce < 0 or reduce > dec(d["total_tax"]):
                    raise ValueError(f"ITC to reduce on {d['doc_number']} must be between 0 and the note's tax ({d['total_tax']}).")
                update["itc_reduce"] = money(reduce)
            col().update_one({"_id": d["_id"]}, {"$set": update})
        audit(request, "gst_inward", ",".join(ids[:5]), f"ims {action} x{len(docs) - len(skipped)}")
        msg = f"{len(docs) - len(skipped)} documents marked {action if action != 'none' else 'no action'}."
        if skipped:
            msg += f" {len(skipped)} reverse-charge documents were skipped: they are not actioned in IMS."
        return R.success(data={"updated": len(docs) - len(skipped), "skipped": skipped}, message=msg, request=request)
    except ValueError as e:
        return R.validation_error(message=str(e), request=request)


@api_login_required
@require_http_methods(["POST"])
def link_bill(request):
    denied = guard(request, manage=True)
    if denied:
        return denied
    p = payload(request)
    org = request.api_organization
    rid, bill = p.get("record_id", ""), p.get("bill_id", "")
    if not ObjectId.is_valid(rid) or (bill and not VendorBill.objects(organization=org, id=bill).first()):
        return R.validation_error(message="Choose a valid document and purchase bill.", request=request)
    res = col().update_one({"_id": ObjectId(rid), "organization_id": str(org.id)}, {"$set": {"linked_bill": bill}})
    if not res.matched_count:
        return R.not_found(message="Document not found.", request=request)
    return R.success(data={"linked": bool(bill)}, message="Linked to the purchase bill." if bill else "Link removed.", request=request)


@api_login_required
@require_http_methods(["GET"])
def returns(request, form):
    denied = guard(request)
    if denied:
        return denied
    try:
        org = request.api_organization
        period = request.GET.get("period", "")
        parse_period(period)
        reg = registration(org)
        if form == "gstr1":
            data = gstr1(org, period, reg)
            if request.GET.get("format") == "xlsx":
                sheets = {"Summary": [["Table", "Section", "Documents", "Taxable value", "IGST", "CGST", "SGST", "Cess"]] +
                          [[t["table"], t["label"], t["count"], float(t["taxable"]), float(t["igst"]), float(t["cgst"]), float(t["sgst"]), float(t["cess"])] for t in data["tables"]],
                          "B2CS (Table 7)": [["Place of supply", "State", "Rate %", "Taxable value", "IGST", "CGST", "SGST"]] + [[r["pos"], r["state"], r["rate"], float(r["taxable"]), float(r["igst"]), float(r["cgst"]), float(r["sgst"])] for r in data["b2cs"]],
                          "HSN (Table 12)": [["B2B / B2C", "HSN / SAC", "Rate %", "Quantity", "Taxable value", "Tax"]] + [[r["section"], r["hsn"], r["rate"], float(r["quantity"]), float(r["taxable"]), float(r["tax"])] for r in data["hsn"]],
                          "Documents (Table 13)": [["From", "To", "Total issued", "Cancelled"], [data["documents"]["from"], data["documents"]["to"], data["documents"]["issued"], data["documents"]["cancelled"]]],
                          "Read me": [["NexEase GSTR-1 preparation summary for " + period], ["Check against your records, then file on the GST portal. This is not a filed return."]]}
                return workbook_response(sheets, f"NexEase-GSTR1-{period}")
            return R.success(data=data, request=request)
        if form == "gstr3b":
            data = gstr3b(org, period, reg)
            if request.GET.get("format") == "xlsx":
                rows = [["Row", "Description", "Taxable value", "IGST", "CGST", "SGST", "Cess"]] + [[r["row"], r["label"], float(r["taxable"]), float(r["igst"]), float(r["cgst"]), float(r["sgst"]), float(r["cess"])] for r in data["table_3_1"]]
                t4 = data["table_4"]
                itc = [["Row", "IGST", "CGST", "SGST", "Cess"]] + [[label, *[float(t4[key].get(k, 0)) for k in ("igst", "cgst", "sgst", "cess")]] for label, key in
                                                                 (("4(A)(3) Reverse charge", "a3_reverse_charge"), ("4(A)(5) All other ITC (GSTR-2B)", "a5_all_other_itc"), ("4(B)(2) Rule 37 reversal", "b2_rule37_reversal"), ("Net ITC", "net"), ("ITC in your books", "books"))]
                pay = [["Head", "Cash payable", "ITC carried forward"]] + [[k.upper(), float(data["payment"]["cash"][k]), float(data["payment"]["carry_forward"][k])] for k in ("igst", "cgst", "sgst", "cess")]
                return workbook_response({"3.1 Outward": rows, "4 ITC": itc, "6 Payment": pay, "Read me": [[n] for n in data["notes"]]}, f"NexEase-GSTR3B-{period}")
            return R.success(data=data, request=request)
        return R.not_found(message="Unknown return.", request=request)
    except ValueError as e:
        return R.validation_error(message=str(e), request=request)


@api_login_required
@require_http_methods(["GET"])
def template(request):
    denied = guard(request)
    if denied:
        return denied
    from django.http import HttpResponse
    sample = ",".join(TEMPLATE_HEADERS) + "\n27AAPFU0939F1ZV,Om Steel,INV,OMS/221,25-10-2026,13000,0,1170,1170,0,27,N\n"
    response = HttpResponse(sample, content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="NexEase-IMS-template.csv"'
    return response
