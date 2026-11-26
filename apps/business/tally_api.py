"""Tally endpoints.

Connector (no user session; authenticated by the device token from pairing):
  POST tally/agent/pair/            pairing code → device token
  POST tally/agent/poll/            heartbeat → jobs to run against Tally
  POST tally/agent/jobs/<id>/       Tally's reply to one job

NexEase app (signed-in users; reading needs accounting_reports.read, changing setup needs an admin):
  tally/status/, tally/pair/, tally/devices/<id>/revoke/, tally/companies/<id>/, tally/settings/,
  tally/resync/, tally/jobs/, tally/jobs/<id>/retry/, tally/issues/, tally/issues/retry/,
  tally/overview/, tally/parties/, tally/parties/<guid>/, tally/stock/, tally/daybook/,
  tally/vouchers/<guid>/, tally/registers/, tally/trial-balance/
"""
import json
import re
from collections import defaultdict
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation

from bson import ObjectId
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from apps.core.api.decorators import api_login_required
from apps.core.services.api_response_service import APIResponseService as R

from . import tally_sync as ts
from . import tally_xml as tx
from .enhancements import is_admin
from .views import payload, permitted, workbook_response

D0 = Decimal(0)
IST = timedelta(hours=5, minutes=30)
CONNECTOR_URL = "https://github.com/nexease-staging/nexease/releases/download/tally-connector/NexEase-Tally-Connector.exe"
POLL_SECONDS = 30
BASE_TYPES = ["Sales", "Purchase", "Receipt", "Payment", "Contra", "Journal", "Credit Note", "Debit Note", "Sales Order", "Purchase Order",
              "Delivery Note", "Receipt Note", "Rejections In", "Rejections Out", "Stock Journal", "Physical Stock", "Material In", "Material Out",
              "Memorandum", "Reversing Journal", "Payroll", "Attendance", "Job Work In Order", "Job Work Out Order"]


def dec(v):
    try:
        return Decimal(str(v or 0))
    except (InvalidOperation, ValueError):
        return D0


def f2(v):
    return float(dec(v).quantize(Decimal("0.01")))


# --------------------------------------------------------------------------------------------
# Connector endpoints
# --------------------------------------------------------------------------------------------

def _agent_json(request):
    try:
        return json.loads(request.body or b"{}")
    except ValueError:
        return {}


def _device(request):
    token = request.headers.get("X-NexEase-Device") or request.headers.get("Authorization", "").replace("Bearer ", "")
    return ts.device_for(token.strip())


def _deny(message, status=401):
    return JsonResponse({"ok": False, "error": message}, status=status)


@csrf_exempt
@require_http_methods(["POST"])
def agent_pair(request):
    body = _agent_json(request)
    try:
        token, device_id, org_id = ts.pair(body.get("code"), body.get("name"), body.get("info"))
    except ValueError as e:
        return _deny(str(e), 400)
    from apps.organizations.models import Organization
    org = Organization.objects(id=org_id).first()
    return JsonResponse({"ok": True, "token": token, "device_id": device_id, "organization": getattr(org, "name", ""), "interval": POLL_SECONDS})


@csrf_exempt
@require_http_methods(["POST"])
def agent_poll(request):
    device = _device(request)
    if not device:
        return _deny("This connector is not paired or was removed. Pair it again from NexEase → Tally.")
    body = _agent_json(request)
    info = ts._info(body.get("info"))
    ts.db().tally_devices.update_one({"_id": device["_id"]}, {"$set": {"last_seen": ts.now(), "info": info}})
    org_id = device["org_id"]
    st = ts.settings(org_id)
    if st.get("paused"):
        return JsonResponse({"ok": True, "jobs": [], "interval": POLL_SECONDS, "paused": True})
    if info.get("tally_ok") not in ("True", "true", "1", "yes"):
        # Tally closed or unreachable: heartbeat only; jobs wait until Tally is back.
        ts.db().tally_state.update_one({"_id": org_id}, {"$set": {"tally_error": info.get("error", "")[:200] or "Tally is not running or its port is closed.", "tally_down_at": ts.now()}}, upsert=True)
        return JsonResponse({"ok": True, "jobs": [], "interval": int(st.get("interval") or POLL_SECONDS), "paused": False})
    jobs = ts.next_jobs(org_id, limit=int(body.get("max_jobs") or 8))
    return JsonResponse({"ok": True, "jobs": jobs, "interval": int(st.get("interval") or POLL_SECONDS), "paused": False})


@csrf_exempt
@require_http_methods(["POST"])
def agent_job(request, job_id):
    device = _device(request)
    if not device:
        return _deny("This connector is not paired or was removed.")
    try:
        result = ts.complete(device["org_id"], job_id, _agent_json(request))
    except ValueError as e:
        return _deny(str(e), 404)
    return JsonResponse({"ok": True, **{k: v for k, v in result.items() if isinstance(v, (str, int, float, bool))}})


# --------------------------------------------------------------------------------------------
# Helpers for app endpoints
# --------------------------------------------------------------------------------------------

def _oid(request):
    return str(request.api_organization.id)


def _read(request):
    return permitted(request, "accounting_reports.read")


def _admin(request):
    return is_admin(request.api_user)


def _company(org_id, request=None):
    name = request.GET.get("company") if request is not None else None
    if name:
        return ts.db().tally_companies.find_one({"org_id": org_id, "name": name})
    return ts.active_company(org_id)


def _iso(dt):
    return (dt + IST).isoformat(timespec="seconds") if isinstance(dt, datetime) else dt


def _group_map(org_id, company):
    return {o["name"]: (o.get("data") or {}).get("parent", "") for o in ts.db().tally_objects.find({"org_id": org_id, "company": company, "kind": "group"}, {"name": 1, "data.parent": 1})}


def _type_map(org_id, company):
    """Voucher type name → its base type (custom "GST Sales" → "Sales")."""
    parents = {o["name"]: (o.get("data") or {}).get("parent", "") for o in ts.db().tally_objects.find({"org_id": org_id, "company": company, "kind": "vouchertype"}, {"name": 1, "data.parent": 1})}

    def base(name):
        seen = set()
        while name and name not in seen:
            if name in BASE_TYPES:
                return name
            seen.add(name)
            name = parents.get(name, "")
        return ""
    return {n: base(n) or n for n in parents}, base


def _ledgers(org_id, company):
    groups = _group_map(org_id, company)
    out = []
    for o in ts.db().tally_objects.find({"org_id": org_id, "company": company, "kind": "ledger", "deleted": False}, {"name": 1, "guid": 1, "data": 1}):
        d = o.get("data") or {}
        code = tx.primary_group(d.get("parent", ""), groups)
        out.append({"guid": o["guid"], "name": o["name"], "parent": d.get("parent", ""), "group": code, "nature": tx.NATURE.get(code, ""),
                    "closing": dec(d.get("closing")), "opening": dec(d.get("opening")), "gstin": d.get("gstin", ""), "phone": d.get("phone", ""),
                    "email": d.get("email", ""), "state": d.get("state", ""), "address": d.get("address", ""), "credit_days": d.get("credit_days", ""),
                    "credit_limit": d.get("credit_limit", "")})
    return out


def _vq(org_id, company, extra=None):
    q = {"org_id": org_id, "company": company, "kind": "voucher", "deleted": False, "data.cancelled": {"$ne": True}, "data.optional": {"$ne": True}}
    q.update(extra or {})
    return q


def _vrow(o, tmap):
    d = o.get("data") or {}
    return {"guid": o["guid"], "date": d.get("date", ""), "type": d.get("voucher_type", ""), "base": tmap.get(d.get("voucher_type", ""), d.get("voucher_type", "")),
            "number": d.get("number", ""), "party": d.get("party", ""), "amount": f2(d.get("amount")), "narration": (d.get("narration") or "")[:160],
            "reference": d.get("reference", ""), "from_nexease": bool(o.get("from_nexease")), "cancelled": bool(d.get("cancelled"))}


def _no_company():
    return R.success(data={"connected": False}, message="Tally is not connected yet.")


def _range(request, default_days=30):
    today = (datetime.utcnow() + IST).date()
    try:
        start = date.fromisoformat(request.GET.get("from") or "")
    except ValueError:
        start = today - timedelta(days=default_days)
    try:
        end = date.fromisoformat(request.GET.get("to") or "")
    except ValueError:
        end = today
    return start.isoformat(), end.isoformat()


# --------------------------------------------------------------------------------------------
# Setup and status
# --------------------------------------------------------------------------------------------

@api_login_required
@require_http_methods(["GET"])
def status(request):
    if not _read(request):
        return R.forbidden(request=request)
    org_id = _oid(request)
    db = ts.db()
    devices = [{"id": d["_id"], "name": d["name"], "last_seen": _iso(d.get("last_seen")), "online": bool(d.get("last_seen") and d["last_seen"] > ts.now() - timedelta(minutes=2)),
                "info": d.get("info", {})} for d in db.tally_devices.find({"org_id": org_id, "revoked": False}).sort("created_at", -1)]
    companies = []
    for c in db.tally_companies.find({"org_id": org_id}).sort("name", 1):
        cur = c.get("cursors", {})
        alt_vch, done = c.get("alt_vch", 0), min(cur.get("voucher", 0), c.get("alt_vch", 0))
        counts = {k: db.tally_objects.count_documents({"org_id": org_id, "company": c["name"], "kind": k, "deleted": False}) for k in ("ledger", "stockitem", "voucher")} if c.get("enabled") else {}
        companies.append({"id": c["_id"], "name": c["name"], "enabled": bool(c.get("enabled")), "open": bool(c.get("open")), "gstin": c.get("gstin", ""), "state": c.get("state", ""),
                          "books_from": c.get("books_from", ""), "progress": round(100 * done / alt_vch) if alt_vch else (100 if c.get("mst_synced") else 0),
                          "masters_synced": c.get("mst_synced", 0) >= c.get("alt_mst", 0) > 0, "counts": counts, "seen_at": _iso(c.get("seen_at"))})
    state = db.tally_state.find_one({"_id": org_id}) or {}
    st = ts.settings(org_id)
    jobs = db.tally_jobs
    pending = jobs.count_documents({"org_id": org_id, "status": {"$in": ["queued", "sent"]}})
    failed = jobs.count_documents({"org_id": org_id, "status": "failed", "created_at": {"$gt": ts.now() - timedelta(days=7)}})
    issues = db.tally_links.count_documents({"org_id": org_id, "state": {"$in": ["blocked", "error"]}})
    synced_out = db.tally_links.count_documents({"org_id": org_id, "state": "synced", "origin": {"$ne": "tally"}})
    last = db.tally_log.find_one({"org_id": org_id, "status": "done"}, sort=[("at", -1)])
    online = any(d["online"] for d in devices)
    tally_ok = online and state.get("tally_seen_at") and state["tally_seen_at"] > ts.now() - timedelta(minutes=2)
    return R.success(data={"connected": bool(devices), "online": online, "tally_ok": bool(tally_ok), "devices": devices, "companies": companies,
                           "pending": pending, "failed": failed, "issues": issues, "pushed": synced_out, "paused": bool(st.get("paused")),
                           "last_sync": _iso(last["at"]) if last else None, "tally_error": state.get("tally_error", "") if not tally_ok else "",
                           "download_url": CONNECTOR_URL, "can_manage": _admin(request), "interval": int(st.get("interval") or POLL_SECONDS)}, request=request)


@api_login_required
@require_http_methods(["POST"])
def pairing(request):
    if not _admin(request):
        return R.forbidden(message="Only an admin can connect Tally.", request=request)
    code = ts.new_pairing_code(_oid(request), request.api_user)
    return R.success(data={"code": f"{code[:4]}-{code[4:]}", "expires_in": 900, "download_url": CONNECTOR_URL}, message="Pairing code created.", request=request)


@api_login_required
@require_http_methods(["POST"])
def revoke_device(request, device_id):
    if not _admin(request):
        return R.forbidden(request=request)
    res = ts.db().tally_devices.update_one({"_id": device_id, "org_id": _oid(request)}, {"$set": {"revoked": True}})
    if not res.matched_count:
        return R.not_found(message="Connector not found.", request=request)
    return R.success(message="Connector removed. It will stop syncing.", request=request)


@api_login_required
@require_http_methods(["POST"])
def company(request, company_id):
    if not _admin(request):
        return R.forbidden(request=request)
    org_id = _oid(request)
    row = ts.db().tally_companies.find_one({"_id": company_id, "org_id": org_id})
    if not row:
        return R.not_found(message="Company not found.", request=request)
    if payload(request).get("enabled", True):
        # One company syncs at a time; its data stays when switching, and sync resumes where it stopped.
        ts.db().tally_companies.update_many({"org_id": org_id}, {"$set": {"enabled": False}})
        ts.db().tally_companies.update_one({"_id": company_id}, {"$set": {"enabled": True, "enabled_at": ts.now()}})
        return R.success(message=f"Syncing {row['name']}.", request=request)
    ts.db().tally_companies.update_one({"_id": company_id}, {"$set": {"enabled": False}})
    return R.success(message=f"Stopped syncing {row['name']}.", request=request)


def _options(org_id):
    from apps.finance.models import BankAccount, ChartOfAccount
    company_row = ts.active_company(org_id)
    ledgers = _ledgers(org_id, company_row["name"]) if company_row else []
    by_group = defaultdict(list)
    for l in ledgers:
        by_group[l["group"] or "other"].append(l["name"])
    names = sorted(l["name"] for l in ledgers)
    from apps.organizations.models import Organization
    org = Organization.objects(id=org_id).first()
    banks = [{"id": str(b.id), "name": b.account_name, "type": b.account_type} for b in BankAccount.objects(organization=org, is_active=True)] if org else []
    accounts = [{"id": str(a.id), "name": a.account_name, "code": a.account_code} for a in ChartOfAccount.objects(organization=org, is_active=True).order_by("account_code")] if org else []
    cats = sorted({(r.get("data") or {}).get("category", "") for r in ts.db().nexease_business_records.find({"organization": org.id if org else None, "kind": "expenses"}, {"data.category": 1}).limit(5000)} - {""})
    types = sorted(o["name"] for o in ts.db().tally_objects.find({"org_id": org_id, "company": company_row["name"] if company_row else "", "kind": "vouchertype", "deleted": False}, {"name": 1}))
    return {"ledgers": names, "by_group": by_group, "bank_accounts": banks, "accounts": accounts, "expense_categories": cats, "voucher_types": types,
            "suggested": suggest_mapping(by_group)}


def suggest_mapping(by_group):
    """A first guess at the ledger mapping from the Tally chart (the user confirms it)."""
    def pick(group, *words, exclude=()):
        names = by_group.get(group, [])
        for w in words:
            for n in names:
                low = n.lower()
                if w in low and not any(e in low for e in exclude):
                    return n
        return names[0] if names and not words else ""
    tax = by_group.get("tax", [])

    def taxl(head, side):
        words_in = ("input", " in", "itc")
        for n in tax:
            low = n.lower()
            if head in low and ((side == "in") == any(w in low for w in words_in)):
                return n
        return next((n for n in tax if head in n.lower()), "")
    return {"sales": pick("sales", "sales", "gst sales") or (by_group.get("sales") or [""])[0], "purchase": pick("purchase", "purchase") or (by_group.get("purchase") or [""])[0],
            "service_income": pick("sales", "service") or pick("direct_income", "service") or pick("indirect_income", "service"),
            "cgst_out": taxl("cgst", "out"), "sgst_out": taxl("sgst", "out"), "igst_out": taxl("igst", "out"),
            "cgst_in": taxl("cgst", "in"), "sgst_in": taxl("sgst", "in"), "igst_in": taxl("igst", "in"),
            "round_off": pick("indirect_expense", "round") or pick("indirect_income", "round"), "cash": (by_group.get("cash") or [""])[0],
            "bank": (by_group.get("bank") or [""])[0], "expense_default": pick("indirect_expense", "misc", "general", "office")}


SETTING_KEYS = {"write_back": dict, "mapping": dict, "bank_ledgers": dict, "expense_ledgers": dict, "journal_accounts": dict, "voucher_types": dict,
                "import_masters": bool, "invoice_mode": str, "debtors_group": str, "creditors_group": str, "paused": bool, "interval": int, "push_from": str}


@api_login_required
@require_http_methods(["GET", "POST"])
def sync_settings(request):
    if not _read(request):
        return R.forbidden(request=request)
    org_id = _oid(request)
    if request.method == "POST":
        if not _admin(request):
            return R.forbidden(message="Only an admin can change Tally settings.", request=request)
        body = payload(request)
        patch = {}
        for key, kind in SETTING_KEYS.items():
            if key not in body:
                continue
            value = body[key]
            if kind is dict:
                if not isinstance(value, dict):
                    return R.validation_error(message=f"{key} must be an object.", request=request)
                value = {str(k)[:120]: (bool(v) if key == "write_back" else str(v or "").strip()[:120]) for k, v in value.items()}
                if key == "write_back":
                    value = {k: v for k, v in value.items() if k in ts.WRITE_KINDS}
                if key == "mapping":
                    value = {k: v for k, v in value.items() if k in ts.MAPPING_KEYS}
            elif kind is bool:
                value = bool(value)
            elif kind is int:
                value = max(10, min(600, int(value or POLL_SECONDS)))
            elif key == "push_from":
                try:
                    value = datetime.combine(date.fromisoformat(str(value)), datetime.min.time()) - IST
                except ValueError:
                    return R.validation_error(message="Push-from must be a date.", request=request)
            elif key == "invoice_mode":
                if value not in ("auto", "item", "accounting"):
                    return R.validation_error(message="Choose auto, item or accounting.", request=request)
            else:
                value = str(value or "").strip()[:120]
            patch[key] = value
        if "push_from" in patch:
            patch["out_cursor"] = {}
        ts.save_settings(org_id, patch)
        # Entries held back for a missing mapping are tried again on the next poll.
        ts.db().tally_links.update_many({"org_id": org_id, "state": "blocked"}, {"$set": {"state": "retry"}})
        from .views import audit
        audit(request, "tally_settings", org_id, "update")
    st = ts.settings(org_id)
    st.pop("_id", None)
    st["push_from"] = ((st.get("push_from") + IST).date().isoformat()) if isinstance(st.get("push_from"), datetime) else ""
    st.pop("out_cursor", None)
    return R.success(data={"settings": st, "options": _options(org_id), "write_kinds": ts.WRITE_KINDS, "mapping_keys": ts.MAPPING_KEYS},
                     message="Tally settings saved." if request.method == "POST" else None, request=request)


@api_login_required
@require_http_methods(["POST"])
def resync(request):
    if not _admin(request):
        return R.forbidden(request=request)
    org_id = _oid(request)
    scope = payload(request).get("scope", "all")
    reset = {"index_at": None}
    if scope in ("all", "masters"):
        reset.update({"mst_synced": 0, **{f"cursors.{k}": 0 for k in tx.SYNC_ORDER}})
    if scope in ("all", "vouchers"):
        reset["cursors.voucher"] = 0
    ts.db().tally_companies.update_many({"org_id": org_id, "enabled": True}, {"$set": reset})
    ts.db().tally_jobs.update_many({"org_id": org_id, "type": {"$in": ["pull", "index"]}, "status": "queued"}, {"$set": {"status": "cancelled"}})
    return R.success(message="Full refresh started. Tally data will be fetched again.", request=request)


@api_login_required
@require_http_methods(["GET"])
def jobs(request):
    if not _read(request):
        return R.forbidden(request=request)
    org_id = _oid(request)
    q = {"org_id": org_id}
    if request.GET.get("status"):
        q["status"] = request.GET["status"]
    if request.GET.get("type"):
        q["type"] = request.GET["type"]
    rows = []
    for j in ts.db().tally_jobs.find(q, {"xml": 0}).sort("created_at", -1).limit(200):
        rows.append({"id": str(j["_id"]), "type": j["type"], "kind": j.get("kind", ""), "label": (j.get("source") or {}).get("label") or j.get("kind", ""),
                     "status": j["status"], "attempts": j.get("attempts", 0), "error": j.get("error", ""), "created_at": _iso(j.get("created_at")),
                     "done_at": _iso(j.get("done_at")), "result": {k: v for k, v in (j.get("result") or {}).items() if isinstance(v, (int, str))}})
    return R.success(data={"jobs": rows}, request=request)


@api_login_required
@require_http_methods(["POST"])
def retry_job(request, job_id):
    if not _admin(request):
        return R.forbidden(request=request)
    if not ObjectId.is_valid(job_id):
        return R.not_found(request=request)
    res = ts.db().tally_jobs.update_one({"_id": ObjectId(job_id), "org_id": _oid(request), "status": "failed"}, {"$set": {"status": "queued", "attempts": 0, "error": ""}})
    if not res.matched_count:
        return R.not_found(message="Only failed jobs can be retried.", request=request)
    return R.success(message="Will retry on the next sync.", request=request)


@api_login_required
@require_http_methods(["GET"])
def issues(request):
    if not _read(request):
        return R.forbidden(request=request)
    rows = [{"model": r["model"], "id": r["nexease_id"], "label": r.get("label") or r.get("tally_name") or r["model"], "state": r["state"], "error": r.get("error", ""),
             "updated_at": _iso(r.get("updated_at"))} for r in ts.db().tally_links.find({"org_id": _oid(request), "state": {"$in": ["blocked", "error"]}}).sort("updated_at", -1).limit(300)]
    return R.success(data={"issues": rows}, request=request)


@api_login_required
@require_http_methods(["POST"])
def retry_issues(request):
    if not _admin(request):
        return R.forbidden(request=request)
    q = {"org_id": _oid(request), "state": {"$in": ["blocked", "error"]}}
    one = payload(request).get("id")
    if one:
        q["nexease_id"] = str(one)
    res = ts.db().tally_links.update_many(q, {"$set": {"state": "retry", "hash": ""}})
    return R.success(data={"count": res.modified_count}, message=f"{res.modified_count} entr{'y' if res.modified_count == 1 else 'ies'} will be sent again.", request=request)


# --------------------------------------------------------------------------------------------
# Tally data views
# --------------------------------------------------------------------------------------------

def _guard(request):
    if not _read(request):
        return None, None, R.forbidden(request=request)
    org_id = _oid(request)
    c = _company(org_id, request)
    if not c:
        return org_id, None, _no_company()
    return org_id, c["name"], None


@api_login_required
@require_http_methods(["GET"])
def overview(request):
    org_id, company_name, err = _guard(request)
    if err:
        return err
    db = ts.db()
    ledgers = _ledgers(org_id, company_name)
    tmap, _ = _type_map(org_id, company_name)
    today = (datetime.utcnow() + IST).date()
    month_start = today.replace(day=1)
    prev_start = (month_start - timedelta(days=1)).replace(day=1)
    totals = defaultdict(lambda: defaultdict(Decimal))
    trend = defaultdict(lambda: defaultdict(Decimal))
    start12 = (month_start - timedelta(days=330)).replace(day=1).isoformat()
    for o in db.tally_objects.find(_vq(org_id, company_name, {"data.date": {"$gte": start12}}), {"data.date": 1, "data.voucher_type": 1, "data.amount": 1}):
        d = o["data"]
        base = tmap.get(d.get("voucher_type", ""), d.get("voucher_type", ""))
        amt = dec(d.get("amount"))
        trend[d["date"][:7]][base] += amt
        if d["date"] >= month_start.isoformat():
            totals["month"][base] += amt
        elif d["date"] >= prev_start.isoformat():
            totals["prev"][base] += amt
    group_sum = defaultdict(Decimal)
    for l in ledgers:
        group_sum[l["group"]] += l["closing"]
    debtors = sorted([l for l in ledgers if l["group"] == "debtors" and l["closing"] > 0], key=lambda l: -l["closing"])[:8]
    creditors = sorted([l for l in ledgers if l["group"] == "creditors" and l["closing"] < 0], key=lambda l: l["closing"])[:8]
    cash_bank = [{"name": l["name"], "balance": f2(l["closing"]), "group": l["group"]} for l in ledgers if l["group"] in ("cash", "bank")]
    months = []
    m = (month_start - timedelta(days=330)).replace(day=1)
    while m <= month_start:
        k = m.isoformat()[:7]
        months.append({"month": k, "sales": f2(trend[k]["Sales"] - trend[k]["Credit Note"]), "purchase": f2(trend[k]["Purchase"] - trend[k]["Debit Note"]),
                       "receipts": f2(trend[k]["Receipt"]), "payments": f2(trend[k]["Payment"])})
        m = (m + timedelta(days=32)).replace(day=1)
    recent = [_vrow(o, tmap) for o in db.tally_objects.find(_vq(org_id, company_name)).sort([("data.date", -1), ("alter_id", -1)]).limit(10)]
    stock_value = sum((dec((o.get("data") or {}).get("closing_value")) for o in db.tally_objects.find({"org_id": org_id, "company": company_name, "kind": "stockitem", "deleted": False}, {"data.closing_value": 1})), D0)

    def kpi(base, minus=None):
        cur = totals["month"][base] - (totals["month"][minus] if minus else D0)
        prev = totals["prev"][base] - (totals["prev"][minus] if minus else D0)
        return {"value": f2(cur), "previous": f2(prev)}
    return R.success(data={"connected": True, "company": company_name, "kpis": {"sales": kpi("Sales", "Credit Note"), "purchase": kpi("Purchase", "Debit Note"),
                           "receipts": kpi("Receipt"), "payments": kpi("Payment")},
                           "receivable": f2(group_sum["debtors"]), "payable": f2(-group_sum["creditors"]), "cash": f2(group_sum["cash"]), "bank": f2(group_sum["bank"]),
                           "stock_value": f2(stock_value), "cash_bank": cash_bank, "trend": months,
                           "top_debtors": [{"guid": l["guid"], "name": l["name"], "balance": f2(l["closing"]), "phone": l["phone"]} for l in debtors],
                           "top_creditors": [{"guid": l["guid"], "name": l["name"], "balance": f2(-l["closing"]), "phone": l["phone"]} for l in creditors],
                           "recent": recent}, request=request)


@api_login_required
@require_http_methods(["GET"])
def parties(request):
    org_id, company_name, err = _guard(request)
    if err:
        return err
    side = request.GET.get("side", "debtors")
    q = (request.GET.get("q") or "").strip().lower()
    groups = ("debtors",) if side == "debtors" else ("creditors",) if side == "creditors" else ("debtors", "creditors")
    links = {r["tally_guid"]: r for r in ts.db().tally_links.find({"org_id": org_id, "model": {"$in": ["customer", "supplier"]}, "tally_guid": {"$exists": True}}, {"tally_guid": 1, "nexease_id": 1, "model": 1})}
    rows = []
    for l in _ledgers(org_id, company_name):
        if l["group"] not in groups or (q and q not in l["name"].lower() and q not in l["gstin"].lower() and q not in l["phone"]):
            continue
        bal = l["closing"] if l["group"] == "debtors" else -l["closing"]
        lk = links.get(l["guid"]) or {}
        rows.append({"guid": l["guid"], "name": l["name"], "group": l["group"], "parent": l["parent"], "gstin": l["gstin"], "phone": l["phone"], "email": l["email"],
                     "state": l["state"], "balance": f2(bal), "credit_days": l["credit_days"], "nexease_id": lk.get("nexease_id"), "nexease_model": lk.get("model")})
    rows.sort(key=lambda r: -r["balance"])
    if request.GET.get("export") == "xlsx":
        return workbook_response({"Parties": [["Name", "Group", "GSTIN", "Phone", "State", "Balance"]] + [[r["name"], r["parent"], r["gstin"], r["phone"], r["state"], r["balance"]] for r in rows]},
                                 "tally-parties.xlsx")
    return R.success(data={"parties": rows[:1000], "total": f2(sum(Decimal(str(r["balance"])) for r in rows)), "count": len(rows)}, request=request)


def _bill_outstanding(vouchers, ledger):
    bills = {}
    for o in vouchers:
        d = o["data"]
        for b in d.get("bills", []):
            if b.get("ledger") != ledger:
                continue
            row = bills.setdefault(b["name"], {"name": b["name"], "date": d["date"], "amount": D0, "credit_days": b.get("credit_days", "")})
            row["amount"] += dec(b.get("amount"))
            if b.get("type") == "New Ref":
                row["date"] = d["date"]
                row["credit_days"] = b.get("credit_days") or row["credit_days"]
    today = (datetime.utcnow() + IST).date()
    out = []
    for b in bills.values():
        if abs(b["amount"]) < Decimal("0.01"):
            continue
        due = date.fromisoformat(b["date"]) + timedelta(days=int(b["credit_days"] or 0)) if b["date"] else today
        out.append({"name": b["name"], "date": b["date"], "due": due.isoformat(), "overdue_days": max(0, (today - due).days), "amount": f2(b["amount"])})
    return sorted(out, key=lambda b: b["date"])


def ledger_statement(org_id, company_name, guid, start, end):
    """One Tally ledger: details, running statement for [start, end] and its open bills. None if unknown."""
    led = ts.db().tally_objects.find_one({"org_id": org_id, "company": company_name, "kind": "ledger", "guid": guid})
    if not led:
        return None
    name = led["name"]
    d = led.get("data") or {}
    tmap, _ = _type_map(org_id, company_name)
    vouchers = list(ts.db().tally_objects.find(_vq(org_id, company_name, {"data.entries.ledger": name})).sort([("data.date", 1), ("alter_id", 1)]))
    balance = dec(d.get("opening"))
    rows = []
    opening_in_range = None
    for o in vouchers:
        v = o["data"]
        amt = sum((dec(e["amount"]) for e in v.get("entries", []) if e["ledger"] == name), D0)
        if v["date"] < start:
            balance += amt
            continue
        if opening_in_range is None:
            opening_in_range = balance
        if v["date"] > end:
            break
        balance += amt
        others = [e for e in v.get("entries", []) if e["ledger"] != name and (dec(e["amount"]) > 0) != (amt > 0)]
        particulars = others[0]["ledger"] if others else ""
        rows.append({**_vrow(o, tmap), "particulars": particulars, "debit": f2(amt if amt > 0 else 0), "credit": f2(-amt if amt < 0 else 0), "balance": f2(balance)})
    opening_in_range = balance if opening_in_range is None else opening_in_range
    code = tx.primary_group(d.get("parent", ""), _group_map(org_id, company_name))
    return {"guid": guid, "name": name, "group": code, "parent": d.get("parent", ""), "gstin": d.get("gstin", ""), "phone": d.get("phone", ""), "email": d.get("email", ""),
            "address": d.get("address", ""), "state": d.get("state", ""), "credit_days": d.get("credit_days", ""), "closing": f2(d.get("closing")),
            "opening": f2(opening_in_range), "period_closing": f2(balance if rows else opening_in_range), "from": start, "to": end, "rows": rows,
            "bills": _bill_outstanding(vouchers, name), "company": company_name}


@api_login_required
@require_http_methods(["GET"])
def party_detail(request, guid):
    org_id, company_name, err = _guard(request)
    if err:
        return err
    start, end = _range(request, default_days=365)
    data = ledger_statement(org_id, company_name, guid, start, end)
    if not data:
        return R.not_found(message="Ledger not found.", request=request)
    rows, name = data["rows"], data["name"]
    if request.GET.get("export") == "xlsx":
        return workbook_response({"Statement": [["Date", "Type", "Number", "Particulars", "Debit", "Credit", "Balance"], ["", "", "", "Opening balance", "", "", data["opening"]]]
                                  + [[r["date"], r["type"], r["number"], r["particulars"] or r["narration"], r["debit"], r["credit"], r["balance"]] for r in rows],
                                  "Outstanding bills": [["Bill", "Date", "Due", "Overdue days", "Amount"]] + [[b["name"], b["date"], b["due"], b["overdue_days"], b["amount"]] for b in data["bills"]]},
                                 f"tally-{re.sub(r'[^A-Za-z0-9]+', '-', name)[:40]}.xlsx")
    return R.success(data=data, request=request)


@api_login_required
@require_http_methods(["GET"])
def stock(request):
    org_id, company_name, err = _guard(request)
    if err:
        return err
    q = (request.GET.get("q") or "").strip().lower()
    rows = []
    for o in ts.db().tally_objects.find({"org_id": org_id, "company": company_name, "kind": "stockitem", "deleted": False}).sort("name", 1):
        d = o.get("data") or {}
        if q and q not in o["name"].lower() and q not in (d.get("hsn") or ""):
            continue
        rows.append({"guid": o["guid"], "name": o["name"], "group": d.get("parent", ""), "unit": d.get("unit", ""), "hsn": d.get("hsn", ""), "gst_rate": d.get("gst_rate", ""),
                     "qty": f2(d.get("closing_qty")), "rate": f2(d.get("closing_rate")), "value": f2(d.get("closing_value")), "price": f2(d.get("selling_price"))})
    if request.GET.get("export") == "xlsx":
        return workbook_response({"Stock": [["Item", "Group", "HSN", "GST %", "Qty", "Unit", "Rate", "Value"]] + [[r["name"], r["group"], r["hsn"], r["gst_rate"], r["qty"], r["unit"], r["rate"], r["value"]] for r in rows]},
                                 "tally-stock.xlsx")
    return R.success(data={"items": rows[:2000], "count": len(rows), "value": f2(sum(Decimal(str(r["value"])) for r in rows)),
                           "negative": sum(1 for r in rows if r["qty"] < 0)}, request=request)


@api_login_required
@require_http_methods(["GET"])
def daybook(request):
    org_id, company_name, err = _guard(request)
    if err:
        return err
    tmap, _ = _type_map(org_id, company_name)
    start, end = _range(request, default_days=0)
    extra = {"data.date": {"$gte": start, "$lte": end}}
    vtype = request.GET.get("type")
    if vtype:
        names = [n for n, b in tmap.items() if b == vtype or n == vtype] or [vtype]
        extra["data.voucher_type"] = {"$in": names}
    q = (request.GET.get("q") or "").strip()
    if q:
        rx = {"$regex": re.escape(q), "$options": "i"}
        extra["$or"] = [{"data.party": rx}, {"data.number": rx}, {"data.narration": rx}]
    rows = [_vrow(o, tmap) for o in ts.db().tally_objects.find(_vq(org_id, company_name, extra)).sort([("data.date", 1), ("alter_id", 1)]).limit(3000)]
    if request.GET.get("export") == "xlsx":
        return workbook_response({"Day book": [["Date", "Type", "Number", "Party", "Narration", "Amount"]] + [[r["date"], r["type"], r["number"], r["party"], r["narration"], r["amount"]] for r in rows]},
                                 "tally-daybook.xlsx")
    by_type = defaultdict(Decimal)
    for r in rows:
        by_type[r["base"]] += Decimal(str(r["amount"]))
    return R.success(data={"from": start, "to": end, "vouchers": rows, "by_type": {k: f2(v) for k, v in by_type.items()}, "types": sorted(set(tmap.values()) | set(by_type))}, request=request)


@api_login_required
@require_http_methods(["GET"])
def voucher(request, guid):
    org_id, company_name, err = _guard(request)
    if err:
        return err
    o = ts.db().tally_objects.find_one({"org_id": org_id, "company": company_name, "kind": "voucher", "guid": guid})
    if not o:
        return R.not_found(message="Voucher not found.", request=request)
    tmap, _ = _type_map(org_id, company_name)
    d = o["data"]
    entries = [{"ledger": e["ledger"], "debit": f2(dec(e["amount"])) if dec(e["amount"]) > 0 else 0, "credit": f2(-dec(e["amount"])) if dec(e["amount"]) < 0 else 0} for e in d.get("entries", [])]
    return R.success(data={**_vrow(o, tmap), "narration": d.get("narration", ""), "party_gstin": d.get("party_gstin", ""), "place_of_supply": d.get("place_of_supply", ""),
                           "entries": entries, "inventory": d.get("inventory", []), "bills": d.get("bills", []), "deleted": bool(o.get("deleted"))}, request=request)


@api_login_required
@require_http_methods(["GET"])
def registers(request):
    org_id, company_name, err = _guard(request)
    if err:
        return err
    tmap, _ = _type_map(org_id, company_name)
    base = request.GET.get("type", "Sales")
    start, end = _range(request, default_days=365)
    names = [n for n, b in tmap.items() if b == base] or [base]
    rows, months, ledger_totals = [], defaultdict(Decimal), defaultdict(Decimal)
    for o in ts.db().tally_objects.find(_vq(org_id, company_name, {"data.voucher_type": {"$in": names}, "data.date": {"$gte": start, "$lte": end}})).sort("data.date", 1):
        r = _vrow(o, tmap)
        rows.append(r)
        months[r["date"][:7]] += Decimal(str(r["amount"]))
        for e in o["data"].get("entries", []):
            if e["ledger"] != o["data"].get("party"):
                ledger_totals[e["ledger"]] += abs(dec(e["amount"]))
    if request.GET.get("export") == "xlsx":
        return workbook_response({f"{base} register": [["Date", "Number", "Party", "Amount"]] + [[r["date"], r["number"], r["party"], r["amount"]] for r in rows]}, f"tally-{base.lower().replace(' ', '-')}.xlsx")
    return R.success(data={"type": base, "from": start, "to": end, "vouchers": rows[-2000:], "count": len(rows), "total": f2(sum(months.values(), D0)),
                           "months": [{"month": k, "amount": f2(v)} for k, v in sorted(months.items())],
                           "ledgers": [{"ledger": k, "amount": f2(v)} for k, v in sorted(ledger_totals.items(), key=lambda kv: -kv[1])[:20]]}, request=request)


GROUP_LABELS = {"capital": "Capital account", "loan": "Loans (liability)", "current_liability": "Current liabilities", "creditors": "Sundry creditors", "tax": "Duties & taxes",
                "fixed_asset": "Fixed assets", "investment": "Investments", "current_asset": "Current assets", "stock": "Stock-in-hand", "debtors": "Sundry debtors",
                "cash": "Cash-in-hand", "bank": "Bank accounts", "sales": "Sales accounts", "purchase": "Purchase accounts", "direct_income": "Direct incomes",
                "indirect_income": "Indirect incomes", "direct_expense": "Direct expenses", "indirect_expense": "Indirect expenses", "suspense": "Suspense", "branch": "Branch / divisions", "": "Other"}


@api_login_required
@require_http_methods(["GET"])
def trial_balance(request):
    org_id, company_name, err = _guard(request)
    if err:
        return err
    groups = defaultdict(lambda: {"debit": D0, "credit": D0, "ledgers": []})
    for l in _ledgers(org_id, company_name):
        c = l["closing"]
        if not c:
            continue
        g = groups[l["group"]]
        g["debit" if c > 0 else "credit"] += abs(c)
        g["ledgers"].append({"guid": l["guid"], "name": l["name"], "debit": f2(c if c > 0 else 0), "credit": f2(-c if c < 0 else 0)})
    order = list(GROUP_LABELS)
    out = [{"code": k, "label": GROUP_LABELS.get(k, k), "debit": f2(v["debit"]), "credit": f2(v["credit"]), "ledgers": sorted(v["ledgers"], key=lambda x: x["name"])}
           for k, v in sorted(groups.items(), key=lambda kv: order.index(kv[0]) if kv[0] in order else 99)]
    debit = sum((g["debit"] for g in groups.values()), D0)
    credit = sum((g["credit"] for g in groups.values()), D0)
    if request.GET.get("export") == "xlsx":
        sheet = [["Group", "Ledger", "Debit", "Credit"]]
        for g in out:
            sheet.append([g["label"], "", g["debit"], g["credit"]])
            sheet += [["", l["name"], l["debit"], l["credit"]] for l in g["ledgers"]]
        sheet.append(["Total", "", f2(debit), f2(credit)])
        return workbook_response({"Trial balance": sheet}, "tally-trial-balance.xlsx")
    return R.success(data={"groups": out, "debit": f2(debit), "credit": f2(credit), "difference": f2(debit - credit)}, request=request)
