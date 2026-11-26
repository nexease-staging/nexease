"""Two-way sync between NexEase and TallyPrime.

How it runs
- A desktop connector on the Tally computer polls NexEase (`agent/poll`). NexEase hands it jobs: XML
  requests to post to Tally (exports to pull data, imports to push entries). The connector posts each
  to Tally on localhost and returns Tally's reply (`agent/jobs/<id>`). All Tally knowledge lives
  here, so the connector rarely needs updating.
- Tally → NexEase: each poll asks Tally for its companies and their latest master / voucher alter ids
  (cheap). When they move, only objects with a higher ALTERID are fetched; vouchers in windows so a
  first sync of years of data stays in small pieces. Every half hour a GUID index finds deletions.
  Everything is mirrored in `tally_objects`; parties and stock items also become NexEase customers,
  suppliers and products.
- NexEase → Tally: new or changed customers, suppliers, products, invoices, bills, receipts,
  payments, credit/debit notes, orders, expenses and manual journals are turned into Tally imports.
  Vouchers carry a REMOTEID, so an edit or cancellation updates the same Tally voucher, and the
  copy that comes back from Tally is recognised as NexEase's own (no duplicates, no loops).
Tally stays the main books: Tally vouchers are mirrored and shown in NexEase's Tally section, and are
not posted again into NexEase's own accounts.
"""
import gzip
import base64
import hashlib
import json
import secrets
from datetime import datetime, timedelta
from decimal import Decimal

from mongoengine.connection import get_db
from pymongo import ReturnDocument

from . import tally_xml as tx

D0 = Decimal(0)
VOUCHER_WINDOW = 3000
PROBE_SECONDS = 25
INDEX_MINUTES = 30
STALE_MINUTES = 5
MAX_ATTEMPTS = 5
DEFAULT_TYPES = {"sales": "Sales", "purchase": "Purchase", "receipt": "Receipt", "payment": "Payment", "journal": "Journal", "credit_note": "Credit Note",
                 "debit_note": "Debit Note", "sales_order": "Sales Order", "purchase_order": "Purchase Order"}
WRITE_KINDS = ["customers", "suppliers", "products", "invoices", "bills", "receipts", "payments", "credit_notes", "debit_notes", "sales_orders",
               "purchase_orders", "expenses", "journals"]
MAPPING_KEYS = ["sales", "purchase", "service_income", "cgst_out", "sgst_out", "igst_out", "cgst_in", "sgst_in", "igst_in", "round_off", "cash", "bank", "expense_default"]


def db():
    return get_db()


def now():
    return datetime.utcnow()


def oid(org):
    return str(org.id) if hasattr(org, "id") else str(org)


# --------------------------------------------------------------------------------------------
# Pairing and devices
# --------------------------------------------------------------------------------------------

def token_hash(token):
    return hashlib.sha256(token.encode()).hexdigest()


def new_pairing_code(org, user):
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    code = "".join(secrets.choice(alphabet) for _ in range(8))
    db().tally_pairing.delete_many({"org_id": oid(org)})
    db().tally_pairing.insert_one({"_id": code, "org_id": oid(org), "created_by": str(user.id), "expires": now() + timedelta(minutes=15)})
    return code


def pair(code, device_name, info):
    code = (code or "").strip().upper().replace("-", "").replace(" ", "")
    row = db().tally_pairing.find_one_and_delete({"_id": code, "expires": {"$gt": now()}})
    if not row:
        raise ValueError("This pairing code is wrong or has expired. Create a new one in NexEase → Tally.")
    token = "nxt_" + secrets.token_urlsafe(32)
    device_id = secrets.token_hex(8)
    db().tally_devices.insert_one({"_id": device_id, "org_id": row["org_id"], "name": (device_name or "Tally computer")[:80], "token_hash": token_hash(token),
                                   "created_at": now(), "last_seen": now(), "revoked": False, "info": _info(info)})
    return token, device_id, row["org_id"]


def _info(info):
    info = info or {}
    return {k: str(info.get(k, ""))[:200] for k in ("version", "tally_url", "tally_ok", "tally_version", "os", "interval", "error")}


def device_for(token):
    if not token or not token.startswith("nxt_"):
        return None
    return db().tally_devices.find_one({"token_hash": token_hash(token), "revoked": False})


def settings(org_id):
    s = db().tally_settings.find_one({"_id": org_id}) or {}
    s.setdefault("write_back", {k: True for k in WRITE_KINDS})
    s.setdefault("mapping", {})
    s.setdefault("expense_ledgers", {})
    s.setdefault("bank_ledgers", {})
    s.setdefault("voucher_types", dict(DEFAULT_TYPES))
    s.setdefault("import_masters", True)
    s.setdefault("debtors_group", "Sundry Debtors")
    s.setdefault("creditors_group", "Sundry Creditors")
    s.setdefault("out_cursor", {})
    return s


def save_settings(org_id, patch):
    db().tally_settings.update_one({"_id": org_id}, {"$set": patch}, upsert=True)


def active_company(org_id):
    return db().tally_companies.find_one({"org_id": org_id, "enabled": True}, sort=[("enabled_at", 1)])


# --------------------------------------------------------------------------------------------
# Jobs
# --------------------------------------------------------------------------------------------

def enqueue(org_id, jtype, xml, company="", kind="", params=None, source=None, priority=5, unique=None):
    if unique and db().tally_jobs.find_one({"org_id": org_id, "unique": unique, "status": {"$in": ["queued", "sent"]}}):
        return None
    doc = {"org_id": org_id, "type": jtype, "company": company, "kind": kind, "params": params or {}, "xml": xml, "status": "queued", "attempts": 0,
           "priority": priority, "created_at": now(), "source": source or {}, "unique": unique}
    return db().tally_jobs.insert_one(doc).inserted_id


def plan(org_id):
    """Decide what to ask Tally for next. Called on every connector poll."""
    jobs = db().tally_jobs
    # Jobs handed out but never answered (connector closed) go back to the queue.
    stale = now() - timedelta(minutes=STALE_MINUTES)
    for j in jobs.find({"org_id": org_id, "status": "sent", "sent_at": {"$lt": stale}}):
        jobs.update_one({"_id": j["_id"]}, {"$set": {"status": "failed" if j["attempts"] >= MAX_ATTEMPTS else "queued", "error": "No reply from the connector."}})
    state = db().tally_state.find_one({"_id": org_id}) or {}
    if not state.get("probed_at") or state["probed_at"] < now() - timedelta(seconds=PROBE_SECONDS):
        enqueue(org_id, "companies", tx.companies_request(), priority=0, unique="companies")
        db().tally_state.update_one({"_id": org_id}, {"$set": {"probed_at": now()}}, upsert=True)
    company = active_company(org_id)
    if not company:
        return
    name = company["name"]
    cursors = company.get("cursors", {})
    masters_pending = jobs.find_one({"org_id": org_id, "type": "pull", "company": name, "kind": {"$ne": "voucher"}, "status": {"$in": ["queued", "sent"]}})
    if company.get("alt_mst", 0) > company.get("mst_synced", 0) and not masters_pending:
        for i, kind in enumerate(tx.SYNC_ORDER):
            enqueue(org_id, "pull", tx.master_request(kind, name, cursors.get(kind, 0)), name, kind, {"after": cursors.get(kind, 0), "alt_mst": company["alt_mst"]},
                    priority=1 + i * 0.01, unique=f"pull:{name}:{kind}")
    vch = cursors.get("voucher", 0)
    target = company.get("alt_vch", 0)
    if target > vch and not jobs.find_one({"org_id": org_id, "type": "pull", "kind": "voucher", "status": {"$in": ["queued", "sent"]}}):
        upto = min(target, vch + VOUCHER_WINDOW)
        enqueue(org_id, "pull", tx.voucher_request(name, vch, upto), name, "voucher", {"after": vch, "upto": upto}, priority=2)
    if not company.get("index_at") or company["index_at"] < now() - timedelta(minutes=INDEX_MINUTES):
        if company.get("mst_synced") and vch >= target:
            for kind in ("ledger", "stockitem", "voucher"):
                enqueue(org_id, "index", tx.index_request(kind, name), name, kind, priority=3, unique=f"index:{name}:{kind}")
            db().tally_companies.update_one({"_id": company["_id"]}, {"$set": {"index_at": now()}})
    if vch >= target and company.get("mst_synced", 0) >= company.get("alt_mst", 0):
        from .tally_outbox import produce
        produce(org_id, company)


def next_jobs(org_id, limit=8):
    plan(org_id)
    out = []
    for j in db().tally_jobs.find({"org_id": org_id, "status": "queued"}).sort([("priority", 1), ("created_at", 1)]).limit(limit):
        db().tally_jobs.update_one({"_id": j["_id"]}, {"$set": {"status": "sent", "sent_at": now()}, "$inc": {"attempts": 1}})
        out.append({"id": str(j["_id"]), "type": j["type"], "company": j.get("company", ""), "xml": j["xml"]})
    return out


def decode_body(payload):
    body = payload.get("body", "")
    if payload.get("encoding") == "gzip+base64":
        return gzip.decompress(base64.b64decode(body)).decode("utf-8", errors="replace")
    return body


def complete(org_id, job_id, payload):
    from bson import ObjectId
    if not ObjectId.is_valid(job_id):
        raise ValueError("Unknown job.")
    job = db().tally_jobs.find_one({"_id": ObjectId(job_id), "org_id": org_id})
    if not job:
        raise ValueError("Unknown job.")
    if not payload.get("ok"):
        status = "failed" if job["attempts"] >= MAX_ATTEMPTS else "queued"
        db().tally_jobs.update_one({"_id": job["_id"]}, {"$set": {"status": status, "error": str(payload.get("error") or "Tally did not answer.")[:500]}})
        return {"status": status}
    body = decode_body(payload)
    try:
        result = HANDLERS[job["type"]](org_id, job, body)
        db().tally_jobs.update_one({"_id": job["_id"]}, {"$set": {"status": "done", "done_at": now(), "result": result, "error": "", "xml": job["xml"] if job["type"] == "push" else ""}})
        log(org_id, job, "done", result)
        return {"status": "done", **(result or {})}
    except ValueError as e:
        db().tally_jobs.update_one({"_id": job["_id"]}, {"$set": {"status": "failed", "done_at": now(), "error": str(e)[:1000]}})
        log(org_id, job, "failed", {"error": str(e)})
        if job["type"] == "push" and job.get("source"):
            mark_link(org_id, job["source"], state="error", error=str(e)[:500])
        return {"status": "failed", "error": str(e)}


def log(org_id, job, status, result):
    db().tally_log.insert_one({"org_id": org_id, "at": now(), "type": job["type"], "kind": job.get("kind", ""), "company": job.get("company", ""), "status": status,
                               "summary": {k: v for k, v in (result or {}).items() if k in ("received", "deleted", "created", "altered", "error", "label")}})


# --------------------------------------------------------------------------------------------
# Handlers for Tally replies
# --------------------------------------------------------------------------------------------

def handle_companies(org_id, job, body):
    companies = tx.parse_objects(body, "COMPANY")
    seen = []
    first_enabled = db().tally_companies.count_documents({"org_id": org_id, "enabled": True}) > 0
    for c in companies:
        name = tx._name(c)
        if not name:
            continue
        key = f"{org_id}:{tx.text(c.get('GUID')) or name}"
        update = {"org_id": org_id, "name": name, "guid": tx.text(c.get("GUID")), "alt_mst": int(tx.text(c.get("ALTMSTID")) or 0), "alt_vch": int(tx.text(c.get("ALTVCHID")) or 0),
                  "books_from": tx.tdate(c.get("BOOKSFROM")), "starting_from": tx.tdate(c.get("STARTINGFROM")), "state": tx.text(c.get("STATENAME")),
                  "gstin": tx.text(c.get("GSTREGISTRATIONNUMBER")), "seen_at": now(), "open": True}
        row = db().tally_companies.find_one_and_update({"_id": key}, {"$set": update, "$setOnInsert": {"enabled": False, "cursors": {}, "mst_synced": 0, "created_at": now()}},
                                                       upsert=True, return_document=ReturnDocument.AFTER)
        if not first_enabled:
            db().tally_companies.update_one({"_id": row["_id"]}, {"$set": {"enabled": True, "enabled_at": now()}})
            first_enabled = True
        seen.append(key)
    db().tally_companies.update_many({"org_id": org_id, "_id": {"$nin": seen}}, {"$set": {"open": False}})
    db().tally_state.update_one({"_id": org_id}, {"$set": {"tally_seen_at": now(), "companies_open": len(seen)}}, upsert=True)
    return {"received": len(seen), "label": "companies"}


TAGS = {"group": "GROUP", "ledger": "LEDGER", "stockgroup": "STOCKGROUP", "stockitem": "STOCKITEM", "unit": "UNIT", "godown": "GODOWN", "costcentre": "COSTCENTRE",
        "vouchertype": "VOUCHERTYPE", "voucher": "VOUCHER"}


def upsert_objects(org_id, company, kind, records):
    coll = db().tally_objects
    for r in records:
        if not r.get("guid"):
            continue
        coll.update_one({"org_id": org_id, "company": company, "kind": kind, "guid": r["guid"]},
                        {"$set": {"alter_id": r["alter_id"], "name": r.get("name", ""), "data": r, "deleted": r.get("deleted", False), "updated_at": now()},
                         "$setOnInsert": {"created_at": now()}}, upsert=True)
    coll.create_index([("org_id", 1), ("company", 1), ("kind", 1), ("guid", 1)], unique=True)
    coll.create_index([("org_id", 1), ("company", 1), ("kind", 1), ("data.date", -1)])


def handle_pull(org_id, job, body):
    kind = job["kind"]
    company = job["company"]
    records = [tx.normalise(kind, d) for d in tx.parse_objects(body, TAGS[kind])]
    upsert_objects(org_id, company, kind, records)
    params = job.get("params", {})
    top = max([r["alter_id"] for r in records] + [params.get("after", 0)])
    field = f"cursors.{kind}"
    if kind == "voucher":
        top = max(top, params.get("upto", 0))
    db().tally_companies.update_one({"org_id": org_id, "name": company}, {"$max": {field: top}})
    if kind != "voucher":
        # When every master kind has caught up to the company's master alter id, masters are in sync.
        pending = db().tally_jobs.count_documents({"org_id": org_id, "type": "pull", "kind": {"$ne": "voucher"}, "company": company, "status": {"$in": ["queued", "sent"]}, "_id": {"$ne": job["_id"]}})
        if not pending:
            db().tally_companies.update_one({"org_id": org_id, "name": company}, {"$max": {"mst_synced": params.get("alt_mst", 0)}})
        if kind in ("ledger", "stockitem"):
            from .tally_masters import import_masters
            import_masters(org_id, company, kind, records)
    else:
        link_returned_vouchers(org_id, company, records)
    return {"received": len(records), "label": kind}


def handle_index(org_id, job, body):
    kind, company = job["kind"], job["company"]
    guids = {tx.text(d.get("GUID")) for d in tx.parse_objects(body, TAGS[kind])}
    guids.discard("")
    coll = db().tally_objects
    existing = coll.count_documents({"org_id": org_id, "company": company, "kind": kind, "deleted": False})
    if not guids and existing > 5:
        raise ValueError(f"Tally returned no {kind}s; skipped deletion check to be safe.")
    gone = [o["guid"] for o in coll.find({"org_id": org_id, "company": company, "kind": kind, "deleted": False, "guid": {"$nin": list(guids)}}, {"guid": 1})]
    res = coll.update_many({"org_id": org_id, "company": company, "kind": kind, "guid": {"$in": gone}}, {"$set": {"deleted": True, "data.deleted": True, "updated_at": now()}})
    if gone and kind in ("ledger", "stockitem"):
        from .tally_masters import deactivate
        deactivate(org_id, gone)
    return {"received": len(guids), "deleted": res.modified_count, "label": f"{kind} index"}


def handle_push(org_id, job, body):
    result = tx.parse_response(body)
    if result["errors"] or result["exceptions"]:
        raise ValueError("Tally rejected it: " + ("; ".join(result["messages"]) or f"{result['errors']} errors"))
    if job.get("source"):
        mark_link(org_id, job["source"], state="synced", tally_id=result["last_id"])
    return {"created": result["created"], "altered": result["altered"], "label": job.get("source", {}).get("label", "")}


HANDLERS = {"companies": handle_companies, "pull": handle_pull, "index": handle_index, "push": handle_push}


# --------------------------------------------------------------------------------------------
# Links between NexEase records and Tally objects
# --------------------------------------------------------------------------------------------

def link(org_id, model, nexease_id):
    return db().tally_links.find_one({"org_id": org_id, "model": model, "nexease_id": str(nexease_id)})


def set_link(org_id, model, nexease_id, **fields):
    db().tally_links.update_one({"org_id": org_id, "model": model, "nexease_id": str(nexease_id)}, {"$set": {**fields, "updated_at": now()}}, upsert=True)
    db().tally_links.create_index([("org_id", 1), ("model", 1), ("nexease_id", 1)], unique=True)


def mark_link(org_id, source, **fields):
    if source.get("model") and source.get("id"):
        update = {**fields}
        if fields.get("state") == "synced":
            update.update(synced_at=now(), hash=source.get("hash", ""), error="", **(source.get("extra") or {}))
            if source.get("tally_name"):
                update["tally_name"] = source["tally_name"]
        set_link(org_id, source["model"], source["id"], **update)


def fingerprint(data):
    return hashlib.sha256(json.dumps(data, sort_keys=True, default=str).encode()).hexdigest()[:20]


def link_returned_vouchers(org_id, company, records):
    """Vouchers NexEase created carry REMOTEID 'NX-…'; Tally echoes it as the GUID. Tag them."""
    for r in records:
        rid = r.get("remote_id") or (r["guid"] if r["guid"].startswith("NX-") else "")
        if rid:
            db().tally_objects.update_one({"org_id": org_id, "company": company, "kind": "voucher", "guid": r["guid"]}, {"$set": {"from_nexease": rid}})
