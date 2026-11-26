"""Payments hub: one place for money in and money out.

GET  /api/v1/business/payments/register/      money in + money out, newest first, with totals
GET  /api/v1/business/payments/outstanding/   open invoices/bills, by party or for one party
POST /api/v1/business/payments/receive/       one customer receipt split across several invoices
POST /api/v1/business/payments/pay/           one supplier payment split across several bills

Receive/pay never write money movements themselves. Each allocation is recorded through the
existing per-document API services, so validation, the bank transaction, the journal entry and
the durable retry receipt (payment_operations) are exactly the same as a single payment.

Retrying: every allocation gets the request key "<request_key>-<n>". Sending the same request
again replays the allocations that already completed and records only the rest, so a payment
that stopped half way can be finished without paying anything twice.
"""

import json
import re
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from hashlib import sha256

from bson import ObjectId
from bson.errors import InvalidId
from django.views.decorators.http import require_http_methods
from mongoengine.connection import get_db

from apps.core.api.decorators import api_login_required
from apps.core.services.api_response_service import APIResponseService as R
from apps.purchasing.models import Supplier, SupplierPayment, VendorBill, VendorDebitNote
from apps.sales.models import CreditNote, Customer, CustomerPayment, Invoice

from .views import permitted

CENT = Decimal("0.01")
IST = timedelta(hours=5, minutes=30)
MAX_ALLOCATIONS = 50
MAX_OPEN_DOCUMENTS = 5000
METHODS = ("CASH", "BANK_TRANSFER", "UPI", "CHEQUE", "CARD", "OTHER")
KEY_RE = re.compile(r"[A-Za-z0-9_-]{16,80}")
BUCKETS = ("current", "d1_30", "d31_60", "d61_90", "d90_plus")


def money(value):
    return str(Decimal(value or 0).quantize(CENT))


def today_ist():
    return (datetime.utcnow() + IST).date()


def as_date(value):
    if not value:
        return None
    return value.date() if isinstance(value, datetime) else value


def bucket(days_overdue):
    if days_overdue <= 0:
        return "current"
    if days_overdue <= 30:
        return "d1_30"
    if days_overdue <= 60:
        return "d31_60"
    if days_overdue <= 90:
        return "d61_90"
    return "d90_plus"


def object_id(value, field):
    try:
        return ObjectId(str(value))
    except (InvalidId, TypeError):
        raise ValueError(f"{field} is not a valid id.")


# ----------------------------------------------------------------------------------------------
# Sides: everything that differs between receivables (customers) and payables (suppliers)
# ----------------------------------------------------------------------------------------------

class Side:
    def __init__(self, name):
        self.name = name
        self.receivable = name == "receivable"
        self.Party = Customer if self.receivable else Supplier
        self.Doc = Invoice if self.receivable else VendorBill
        self.party_field = "customer" if self.receivable else "supplier"
        self.number_field = "invoice_number" if self.receivable else "bill_number"
        self.date_field = "invoice_date" if self.receivable else "bill_date"
        self.open_status = ("ISSUED", "PARTIALLY_PAID") if self.receivable else ("POSTED", "PARTIALLY_PAID")
        self.read_permission = "invoices.read" if self.receivable else "bills.read"
        self.pay_permission = "invoices.record_payment" if self.receivable else "bills.record_payment"
        self.operation_kind = "customer" if self.receivable else "supplier"

    def open_documents(self, org, party_ids=None):
        query = {"organization": org, "status__in": self.open_status, "balance_due__gt": 0}
        if party_ids is not None:
            query[self.party_field + "__in"] = list(party_ids)
        fields = ("id", self.party_field, self.number_field, self.date_field, "due_date",
                  "total_amount", "balance_due", "status")
        return list(self.Doc.objects(**query).only(*fields).order_by("due_date", self.date_field, "id")
                    .limit(MAX_OPEN_DOCUMENTS))

    def applied_credit(self, org, documents):
        """Issued credit notes (sales) or debit notes (purchase) already set off, per document."""
        ids = [d.id for d in documents]
        if not ids:
            return {}
        if self.receivable:
            notes = CreditNote.objects(organization=org, status="ISSUED", invoice__in=ids).only("invoice", "applied_amount")
            pairs = ((n._data.get("invoice"), n.applied_amount) for n in notes)
        else:
            notes = VendorDebitNote.objects(organization=org, status="ISSUED", vendor_bill__in=ids).only("vendor_bill", "applied_amount")
            pairs = ((n._data.get("vendor_bill"), n.applied_amount) for n in notes)
        found = {}
        for ref, amount in pairs:
            key = getattr(ref, "id", ref)
            found[key] = found.get(key, Decimal(0)) + Decimal(amount or 0)
        return found

    def rows(self, org, documents):
        """Open documents with their net outstanding (balance less set-off credit) and age."""
        credits = self.applied_credit(org, documents)
        today = today_ist()
        rows = []
        for d in documents:
            outstanding = Decimal(d.balance_due or 0) - credits.get(d.id, Decimal(0))
            if outstanding <= 0:
                continue
            doc_date = as_date(getattr(d, self.date_field))
            due = as_date(d.due_date) or doc_date
            overdue = (today - due).days if due else 0
            party = d._data.get(self.party_field)
            rows.append({
                "id": str(d.id),
                "party_id": str(getattr(party, "id", party)),
                "number": getattr(d, self.number_field),
                "date": doc_date.isoformat() if doc_date else None,
                "due_date": due.isoformat() if due else None,
                "days_overdue": max(overdue, 0),
                "bucket": bucket(overdue),
                "total": money(d.total_amount),
                "outstanding": outstanding.quantize(CENT),
                "status": d.status,
            })
        return rows


SIDES = {"receivable": Side("receivable"), "payable": Side("payable")}


# ----------------------------------------------------------------------------------------------
# Outstanding
# ----------------------------------------------------------------------------------------------

def party_summaries(side, org, rows, search=""):
    parties = {}
    for row in rows:
        p = parties.setdefault(row["party_id"], {
            "id": row["party_id"], "open_count": 0, "outstanding": Decimal(0), "overdue": Decimal(0),
            "buckets": {b: Decimal(0) for b in BUCKETS}, "oldest_due": None, "max_days_overdue": 0,
        })
        p["open_count"] += 1
        p["outstanding"] += row["outstanding"]
        p["buckets"][row["bucket"]] += row["outstanding"]
        if row["days_overdue"] > 0:
            p["overdue"] += row["outstanding"]
        if row["due_date"] and (not p["oldest_due"] or row["due_date"] < p["oldest_due"]):
            p["oldest_due"] = row["due_date"]
        p["max_days_overdue"] = max(p["max_days_overdue"], row["days_overdue"])
    ids = [ObjectId(i) for i in parties if ObjectId.is_valid(i)]
    for party in side.Party.objects(organization=org, id__in=ids).only("id", "name", "code", "phone", "email"):
        parties[str(party.id)].update(name=party.name, code=party.code, phone=party.phone or "", email=party.email or "")
    term = search.strip().lower()
    result = [p for p in parties.values() if not term or term in (p.get("name", "") + " " + p.get("code", "")).lower()]
    result.sort(key=lambda p: (-p["overdue"], -p["outstanding"], p.get("name", "")))
    return result


def serialise(value):
    if isinstance(value, Decimal):
        return money(value)
    if isinstance(value, dict):
        return {k: serialise(v) for k, v in value.items()}
    if isinstance(value, list):
        return [serialise(v) for v in value]
    return value


@api_login_required
@require_http_methods(["GET"])
def outstanding(request):
    side = SIDES.get(request.GET.get("side", "receivable"))
    if not side:
        return R.validation_error(message="side must be receivable or payable.", request=request)
    if not permitted(request, side.read_permission):
        return R.forbidden(message="Permission denied.", request=request)
    org = request.api_organization
    try:
        party_id = request.GET.get("party_id")
        if party_id:
            party = side.Party.objects(organization=org, id=object_id(party_id, "party_id")).first()
            if not party:
                return R.not_found(message="Party not found.", request=request)
            rows = side.rows(org, side.open_documents(org, [party.id]))
            return R.success(data=serialise({
                "side": side.name,
                "party": {"id": str(party.id), "name": party.name, "code": party.code,
                          "phone": party.phone or "", "email": party.email or ""},
                "documents": rows,
                "total": sum((r["outstanding"] for r in rows), Decimal(0)),
            }), request=request)
        documents = side.open_documents(org)
        rows = side.rows(org, documents)
        parties = party_summaries(side, org, rows, request.GET.get("search", ""))
        totals = {"outstanding": Decimal(0), "overdue": Decimal(0), "buckets": {b: Decimal(0) for b in BUCKETS}}
        for row in rows:
            totals["outstanding"] += row["outstanding"]
            totals["buckets"][row["bucket"]] += row["outstanding"]
            if row["days_overdue"] > 0:
                totals["overdue"] += row["outstanding"]
        return R.success(data=serialise({
            "side": side.name, "as_of": today_ist().isoformat(), "totals": totals,
            "party_count": len(parties), "document_count": len(rows),
            "truncated": len(documents) >= MAX_OPEN_DOCUMENTS, "parties": parties,
        }), request=request)
    except ValueError as exc:
        return R.validation_error(message=str(exc), request=request)


# ----------------------------------------------------------------------------------------------
# Register
# ----------------------------------------------------------------------------------------------

def parse_day(value, field):
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise ValueError(f"{field} must be a date like 2026-04-01.")


def register_query(Model, Party, party_field, org, params):
    query = {"organization": org}
    start, end = parse_day(params.get("from"), "from"), parse_day(params.get("to"), "to")
    # Payment dates are stored in UTC; a business day runs midnight to midnight IST.
    if start:
        query["payment_date__gte"] = datetime.combine(start, datetime.min.time()) - IST
    if end:
        query["payment_date__lt"] = datetime.combine(end + timedelta(days=1), datetime.min.time()) - IST
    method = (params.get("method") or "").upper()
    if method:
        if method not in METHODS:
            raise ValueError("Unknown payment method.")
        query["payment_method"] = method
    if params.get("account_id"):
        query["bank_account"] = object_id(params["account_id"], "account_id")
    if params.get("party_id"):
        query[party_field] = object_id(params["party_id"], "party_id")
    qs = Model.objects(**query)
    term = (params.get("search") or "").strip()
    if term:
        from mongoengine.queryset.visitor import Q
        party_ids = [p.id for p in Party.objects(organization=org).filter(Q(name__icontains=term) | Q(code__icontains=term)).only("id").limit(500)]
        qs = qs.filter(Q(payment_number__icontains=term) | Q(reference_number__icontains=term) | Q(**{party_field + "__in": party_ids}))
    return qs


def payment_row(payment, direction, parties, accounts, numbers):
    party_ref = payment._data.get("customer" if direction == "in" else "supplier")
    party = parties.get(getattr(party_ref, "id", party_ref))
    account_ref = payment._data.get("bank_account")
    account = accounts.get(getattr(account_ref, "id", account_ref))
    docs = []
    for allocation in payment.allocations or []:
        ref = allocation._data.get("invoice" if direction == "in" else "vendor_bill")
        key = getattr(ref, "id", ref)
        docs.append({"id": str(key), "number": numbers.get(key, ""), "amount": money(allocation.amount)})
    when = payment.payment_date
    return {
        "id": str(payment.id), "direction": direction, "number": payment.payment_number,
        "date": (when + IST).date().isoformat() if when else None,
        "party": {"id": str(getattr(party_ref, "id", party_ref)), "name": party.name if party else "",
                  "code": party.code if party else "", "phone": (party.phone or "") if party else "",
                  "email": (party.email or "") if party else ""},
        "amount": money(payment.amount), "method": payment.payment_method,
        "account": {"id": str(getattr(account_ref, "id", "")), "name": account.account_name if account else ""},
        "reference": payment.reference_number or "", "notes": payment.notes or "", "documents": docs,
    }


def total_of(qs):
    return sum((Decimal(str(p.amount or 0)) for p in qs.only("amount")), Decimal(0))


@api_login_required
@require_http_methods(["GET"])
def register(request):
    direction = request.GET.get("direction", "all")
    if direction not in ("all", "in", "out"):
        return R.validation_error(message="direction must be all, in or out.", request=request)
    wants = {"in": direction in ("all", "in"), "out": direction in ("all", "out")}
    if wants["in"] and not (permitted(request, "invoices.read") or permitted(request, "customer_payments.read")):
        if direction == "in":
            return R.forbidden(message="Permission denied.", request=request)
        wants["in"] = False
    if wants["out"] and not permitted(request, "bills.read"):
        if direction == "out":
            return R.forbidden(message="Permission denied.", request=request)
        wants["out"] = False
    if not any(wants.values()):
        return R.forbidden(message="Permission denied.", request=request)
    org = request.api_organization
    try:
        page = max(int(request.GET.get("page") or 1), 1)
        page_size = min(max(int(request.GET.get("page_size") or 25), 1), 100)
        if page * page_size > 5000:
            raise ValueError("Narrow the dates or search to see older payments.")
        sets = {}
        if wants["in"]:
            sets["in"] = register_query(CustomerPayment, Customer, "customer", org, request.GET)
        if wants["out"]:
            sets["out"] = register_query(SupplierPayment, Supplier, "supplier", org, request.GET)
    except ValueError as exc:
        return R.validation_error(message=str(exc), request=request)

    window = page * page_size
    merged = []
    for key, qs in sets.items():
        merged += [(p, key) for p in qs.order_by("-payment_date", "-id").limit(window)]
    merged.sort(key=lambda pair: (pair[0].payment_date or datetime.min, str(pair[0].id)), reverse=True)
    chosen = merged[(page - 1) * page_size: window]

    party_ids = {"in": set(), "out": set()}
    account_ids, doc_ids = set(), {"in": set(), "out": set()}
    for payment, key in chosen:
        ref = payment._data.get("customer" if key == "in" else "supplier")
        party_ids[key].add(getattr(ref, "id", ref))
        account = payment._data.get("bank_account")
        if account is not None:
            account_ids.add(getattr(account, "id", account))
        for allocation in payment.allocations or []:
            r = allocation._data.get("invoice" if key == "in" else "vendor_bill")
            doc_ids[key].add(getattr(r, "id", r))
    parties = {}
    for Party, key in ((Customer, "in"), (Supplier, "out")):
        if party_ids[key]:
            parties.update({p.id: p for p in Party.objects(organization=org, id__in=list(party_ids[key])).only("id", "name", "code", "phone", "email")})
    from apps.finance.models import BankAccount
    accounts = {a.id: a for a in BankAccount.objects(organization=org, id__in=list(account_ids)).only("id", "account_name")} if account_ids else {}
    numbers = {}
    if doc_ids["in"]:
        numbers.update({d.id: d.invoice_number for d in Invoice.objects(organization=org, id__in=list(doc_ids["in"])).only("id", "invoice_number")})
    if doc_ids["out"]:
        numbers.update({d.id: d.bill_number for d in VendorBill.objects(organization=org, id__in=list(doc_ids["out"])).only("id", "bill_number")})

    money_in = total_of(sets["in"]) if "in" in sets else Decimal(0)
    money_out = total_of(sets["out"]) if "out" in sets else Decimal(0)
    count = sum(qs.count() for qs in sets.values())
    by_method = {}
    for key, qs in sets.items():
        for p in qs.only("payment_method", "amount"):
            entry = by_method.setdefault(p.payment_method, {"in": Decimal(0), "out": Decimal(0)})
            entry[key] += Decimal(str(p.amount or 0))
    return R.success(data=serialise({
        "summary": {"money_in": money_in, "money_out": money_out, "net": money_in - money_out,
                    "count": count, "by_method": by_method},
        "payments": [payment_row(p, key, parties, accounts, numbers) for p, key in chosen],
        "pagination": {"page": page, "page_size": page_size, "total": count,
                       "pages": max((count + page_size - 1) // page_size, 1)},
    }), request=request)


# ----------------------------------------------------------------------------------------------
# Receive / pay against several documents
# ----------------------------------------------------------------------------------------------

def decimal_amount(value, field):
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError(f"{field} must be a number.")
    if not amount.is_finite() or amount <= 0:
        raise ValueError(f"{field} must be greater than zero.")
    if amount != amount.quantize(CENT):
        raise ValueError(f"{field} can have at most two decimals.")
    return amount


def completed_keys(org, side, keys):
    """Allocation request keys that already recorded a payment (safe to replay)."""
    ids = {sha256(f"{org.id}:{side.operation_kind}:{k}".encode()).hexdigest(): k for k in keys}
    done = get_db().payment_operations.find({"_id": {"$in": list(ids)}, "status": "completed"}, {"_id": 1})
    return {ids[d["_id"]] for d in done}


def plan_allocations(side, org, party, amount, requested, keys):
    """Return [(document_row, amount)] after checking every line, before anything is written."""
    rows = {r["id"]: r for r in side.rows(org, side.open_documents(org, [party.id]))}
    if requested is None:
        plan, left = [], amount
        for row in rows.values():  # already oldest due first
            if left <= 0:
                break
            take = min(left, row["outstanding"])
            plan.append((row, take))
            left -= take
        if left > 0:
            raise ValueError(f"Amount is more than the total outstanding of {money(amount - left)}. "
                             "Advance payments are not supported yet.")
        return plan
    if not isinstance(requested, list) or not requested:
        raise ValueError("allocations must be a non-empty list.")
    if len(requested) > MAX_ALLOCATIONS:
        raise ValueError(f"Split a payment across at most {MAX_ALLOCATIONS} documents.")
    plan, seen = [], set()
    done = completed_keys(org, side, keys[:len(requested)])
    for index, line in enumerate(requested):
        if not isinstance(line, dict):
            raise ValueError("Each allocation needs document_id and amount.")
        doc_id = str(line.get("document_id") or "")
        if doc_id in seen:
            raise ValueError("A document appears twice in allocations.")
        seen.add(doc_id)
        value = decimal_amount(line.get("amount"), f"Allocation {index + 1} amount")
        row = rows.get(doc_id)
        if keys[index] in done:
            # Recorded on an earlier attempt; the document may now be fully paid.
            row = row or {"id": doc_id, "number": "", "outstanding": value}
        elif not row:
            raise ValueError(f"Allocation {index + 1}: document is not open for this party.")
        elif value > row["outstanding"]:
            raise ValueError(f"{row['number']}: amount is more than its outstanding {money(row['outstanding'])}.")
        plan.append((row, value))
    total = sum((v for _, v in plan), Decimal(0))
    if total != amount:
        raise ValueError(f"Allocations add up to {money(total)}, not the payment amount {money(amount)}.")
    return plan


def record_one(side, request, document_id, payload):
    if side.receivable:
        from apps.sales.services.invoice_api_service import InvoiceAPIService as Service
        result = Service.record_payment(user=request.api_user, organization=request.api_organization,
                                        invoice_id=document_id, payload=payload)
    else:
        from apps.purchasing.services.vendor_bill_api_service import VendorBillAPIService as Service
        result = Service.record_payment(user=request.api_user, organization=request.api_organization,
                                        bill_id=document_id, payload=payload)
    return result["payment"]


def error_text(exc):
    details = getattr(exc, "details", None) or {}
    for messages in details.values():
        if isinstance(messages, list) and messages:
            return str(messages[0])
    return getattr(exc, "message", None) or str(exc) or "Payment could not be recorded."


def settle(request, side):
    if not permitted(request, side.pay_permission):
        return R.forbidden(message="Permission denied.", request=request)
    try:
        body = json.loads(request.body or b"{}")
    except ValueError:
        return R.validation_error(message="Send a JSON body.", request=request)
    if not isinstance(body, dict):
        return R.validation_error(message="Send a JSON object.", request=request)
    org = request.api_organization
    try:
        key = str(body.get("request_key") or "")
        if not KEY_RE.fullmatch(key):
            raise ValueError("request_key is required (16-80 letters, digits, - or _).")
        party = side.Party.objects(organization=org, id=object_id(body.get("party_id"), "party_id")).first()
        if not party:
            return R.not_found(message="Party not found.", request=request)
        amount = decimal_amount(body.get("amount"), "Amount")
        method = str(body.get("payment_method") or "").strip().upper()
        if method not in METHODS:
            raise ValueError("Select a valid payment method.")
        if not body.get("bank_account_id"):
            raise ValueError("Choose the account the money moves through.")
        reference = str(body.get("reference_number") or "").strip()
        if len(reference) > 90:
            raise ValueError("Reference can be at most 90 characters.")
        notes = str(body.get("notes") or "").strip()[:900]
        keys = [f"{key}-{n}" for n in range(1, MAX_ALLOCATIONS + 1)]
        plan = plan_allocations(side, org, party, amount, body.get("allocations"), keys)
    except ValueError as exc:
        return R.validation_error(message=str(exc), request=request)

    many = len(plan) > 1
    recorded = []
    for index, (row, value) in enumerate(plan):
        payload = {
            "amount": money(value), "payment_method": method, "bank_account_id": str(body["bank_account_id"]),
            "reference_number": f"{reference}/{index + 1}" if reference and many else reference,
            "notes": (notes + (" · " if notes else "") + f"Part {index + 1} of {len(plan)}, total {money(amount)}") if many else notes,
            "request_key": keys[index],
        }
        if body.get("payment_date"):
            payload["payment_date"] = body["payment_date"]
        try:
            payment = record_one(side, request, row["id"], payload)
        except PermissionError:
            return R.forbidden(message="Permission denied.", request=request)
        except Exception as exc:  # validation/state/lookup errors from the per-document service
            message = error_text(exc)
            if not recorded:
                return R.validation_error(message=message, details={"document": row.get("number") or row["id"]}, request=request)
            return R.unprocessable_entity(
                message=(f"Recorded {len(recorded)} of {len(plan)} parts. {row.get('number') or 'Next document'}: {message} "
                         "Fix it and send the same payment again; recorded parts will not be paid twice."),
                details={"recorded": recorded, "failed": {"document_id": row["id"], "number": row.get("number", ""), "message": message},
                         "remaining": [r["id"] for r, _ in plan[index:]]},
                request=request)
        recorded.append({"document_id": row["id"], "number": row.get("number", ""), "amount": money(value),
                         "payment_id": str(payment.id), "payment_number": payment.payment_number})
    word = "Receipt" if side.receivable else "Payment"
    return R.success(data={"party": {"id": str(party.id), "name": party.name}, "amount": money(amount),
                           "payments": recorded},
                     message=f"{word} of ₹{money(amount)} recorded against {len(recorded)} "
                             f"{'invoice' if side.receivable else 'bill'}{'s' if len(recorded) != 1 else ''}.",
                     request=request)


@api_login_required
@require_http_methods(["POST"])
def receive(request):
    return settle(request, SIDES["receivable"])


@api_login_required
@require_http_methods(["POST"])
def pay(request):
    return settle(request, SIDES["payable"])
