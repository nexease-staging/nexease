"""Tally parties and stock items ↔ NexEase customers, suppliers and products.

Tally → NexEase: ledgers under Sundry Debtors become customers, under Sundry Creditors suppliers, and
stock items become products (category "Tally" or the item's stock group). A record is found again by
the Tally GUID stored in `tally_links`, else by name, so existing NexEase parties are matched, not
duplicated.

Loop prevention: after a Tally change is applied, the NexEase record's outbound fingerprint is stored
on its link. The outbox only pushes a record whose fingerprint differs, so a change that came from
Tally is never sent straight back.
"""
import hashlib
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation

from mongoengine.errors import NotUniqueError, ValidationError

from . import tally_xml as tx
from .tally_sync import db, fingerprint, link, set_link, settings

EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
HSN = re.compile(r"^(\d{4}|\d{6}|\d{8})$")


def _org(org_id):
    from apps.organizations.models import Organization
    return Organization.objects(id=org_id).first()


def _models():
    from apps.products.models import Category, Product
    from apps.purchasing.models import Supplier
    from apps.sales.models import Customer
    return {"customer": Customer, "supplier": Supplier, "product": Product, "category": Category}


def _dec(value):
    try:
        return Decimal(str(value or 0)).quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError):
        return Decimal("0.00")


# --------------------------------------------------------------------------------------------
# Outbound payloads (what NexEase would send to Tally) — also the loop-prevention fingerprint
# --------------------------------------------------------------------------------------------

def party_payload(doc, model):
    address = doc.billing_address if model == "customer" else doc.address
    return {"name": (doc.name or "").strip(), "gstin": (doc.gstin or "").strip().upper(), "state": (doc.state or "").strip(), "address": (address or "").strip(),
            "phone": (doc.phone or "").strip(), "email": (doc.email or "").strip(), "pincode": (doc.pincode or "").strip()}


def product_payload(doc):
    return {"name": (doc.name or "").strip(), "unit": (doc.unit or "Nos").strip(), "hsn": (doc.hsn_code or "").strip(), "price": str(_dec(doc.selling_price)),
            "description": (doc.description or "").strip()[:200]}


def gst_rate_of(doc):
    for field in ("tax_rate", "gst_rate"):
        value = getattr(doc, field, None)
        if value not in (None, ""):
            return str(value)
    return ""


# --------------------------------------------------------------------------------------------
# Inbound
# --------------------------------------------------------------------------------------------

def import_masters(org_id, company, kind, records):
    if not settings(org_id).get("import_masters", True):
        return {"created": 0, "updated": 0}
    org = _org(org_id)
    if not org:
        return {"created": 0, "updated": 0}
    stats = {"created": 0, "updated": 0, "skipped": 0}
    if kind == "ledger":
        groups = group_map(org_id, company)
        for r in records:
            code = tx.primary_group(r.get("parent", ""), groups)
            if code in ("debtors", "creditors"):
                _apply_party(org, org_id, "customer" if code == "debtors" else "supplier", r, stats)
    elif kind == "stockitem":
        for r in records:
            _apply_product(org, org_id, r, stats)
    return stats


def group_map(org_id, company):
    return {o["name"]: (o.get("data") or {}).get("parent", "") for o in db().tally_objects.find({"org_id": org_id, "company": company, "kind": "group"}, {"name": 1, "data.parent": 1})}


def _find(org, org_id, model, guid, name):
    Model = _models()[model]
    row = db().tally_links.find_one({"org_id": org_id, "model": model, "tally_guid": guid})
    if row:
        doc = Model.objects(id=row["nexease_id"], organization=org).first()
        if doc:
            return doc, row
    doc = Model.objects(organization=org, name__iexact=name.strip()).first() if name else None
    return doc, (link(org_id, model, doc.id) if doc else None)


def _code(prefix, guid):
    return f"{prefix}-{hashlib.sha1(guid.encode()).hexdigest()[:8].upper()}"


def _apply_party(org, org_id, model, r, stats):
    Model = _models()[model]
    name = (r.get("name") or "").strip()[:200]
    if not name or not r.get("guid"):
        return
    incoming = fingerprint({k: r.get(k, "") for k in ("name", "gstin", "phone", "email", "state", "pincode", "address", "deleted")})
    doc, row = _find(org, org_id, model, r["guid"], name)
    if row and row.get("in_hash") == incoming and doc:
        return
    if r.get("deleted"):
        if doc and row:
            doc.is_active = False
            doc.save()
        return
    created = doc is None
    if created:
        doc = Model(organization=org, name=name, code=_code("TL", r["guid"]))
    doc.name = name
    if r.get("gstin") and len(r["gstin"]) == 15:
        doc.gstin = r["gstin"]
    if r.get("phone"):
        doc.phone = r["phone"][:30]
    if r.get("email") and EMAIL.match(r["email"]):
        doc.email = r["email"]
    if r.get("state"):
        doc.state = r["state"][:100]
    if r.get("pincode"):
        doc.pincode = r["pincode"][:20]
    if r.get("address"):
        if model == "customer":
            doc.billing_address = r["address"][:500]
        else:
            doc.address = r["address"][:500]
    doc.updated_at = datetime.utcnow()
    try:
        doc.save()
    except (ValidationError, NotUniqueError) as e:
        stats["skipped"] += 1
        set_link(org_id, f"{model}_skipped", r["guid"], tally_guid=r["guid"], tally_name=name, error=str(e)[:300])
        return
    stats["created" if created else "updated"] += 1
    set_link(org_id, model, doc.id, tally_guid=r["guid"], tally_name=name, in_hash=incoming, hash=fingerprint(party_payload(doc, model)), state="synced",
             synced_at=datetime.utcnow(), origin="tally" if created else (row or {}).get("origin", "nexease"))


def _category(org, name):
    Category = _models()["category"]
    name = (name or "Tally").strip()[:100] or "Tally"
    cat = Category.objects(organization=org, name=name).first()
    if not cat:
        cat = Category(organization=org, name=name, description="Imported from Tally")
        cat.save()
    return cat


def _apply_product(org, org_id, r, stats):
    Product = _models()["product"]
    name = (r.get("name") or "").strip()[:200]
    if not name or not r.get("guid"):
        return
    incoming = fingerprint({k: r.get(k, "") for k in ("name", "unit", "hsn", "gst_rate", "selling_price", "cost_price", "description", "parent", "deleted")})
    doc, row = _find(org, org_id, "product", r["guid"], name)
    if row and row.get("in_hash") == incoming and doc:
        return
    if r.get("deleted"):
        if doc and row:
            doc.is_active = False
            doc.save()
        return
    created = doc is None
    if created:
        doc = Product(organization=org, name=name, sku=_code("TL", r["guid"]), category=_category(org, r.get("parent") if r.get("parent") not in ("", "Primary") else "Tally"),
                      unit=(r.get("unit") or "Nos")[:30])
    doc.name = name
    if r.get("unit"):
        doc.unit = r["unit"][:30]
    hsn = re.sub(r"\D", "", r.get("hsn") or "")
    if HSN.match(hsn) and not (doc.item_type == "service" and len(hsn) != 6):
        doc.hsn_code = hsn
    if _dec(r.get("selling_price")):
        doc.selling_price = _dec(r["selling_price"])
    if _dec(r.get("cost_price")):
        doc.cost_price = _dec(r["cost_price"])
    if r.get("description"):
        doc.description = r["description"][:1000]
    if r.get("gst_rate") and hasattr(Product, "tax_rate"):
        doc.tax_rate = _dec(r["gst_rate"])
    doc.updated_at = datetime.utcnow()
    try:
        doc.save()
    except (ValidationError, NotUniqueError) as e:
        stats["skipped"] += 1
        set_link(org_id, "product_skipped", r["guid"], tally_guid=r["guid"], tally_name=name, error=str(e)[:300])
        return
    stats["created" if created else "updated"] += 1
    set_link(org_id, "product", doc.id, tally_guid=r["guid"], tally_name=name, in_hash=incoming, hash=fingerprint(product_payload(doc)), state="synced",
             synced_at=datetime.utcnow(), origin="tally" if created else (row or {}).get("origin", "nexease"))


def deactivate(org_id, guids):
    """Parties and items deleted in Tally are made inactive in NexEase (never deleted: entries may use them)."""
    org = _org(org_id)
    models = _models()
    for row in db().tally_links.find({"org_id": org_id, "tally_guid": {"$in": list(guids)}, "model": {"$in": ["customer", "supplier", "product"]}}):
        doc = models[row["model"]].objects(id=row["nexease_id"], organization=org).first()
        if doc and doc.is_active:
            doc.is_active = False
            doc.save()
            db().tally_links.update_one({"_id": row["_id"]}, {"$set": {"hash": fingerprint(party_payload(doc, row["model"]) if row["model"] != "product" else product_payload(doc)),
                                                                   "tally_deleted": True}})
