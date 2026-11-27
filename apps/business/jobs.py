"""Production jobs: job cards a manufacturer uses to make, track and cost each order.

A job is one thing being made for a customer (a custom almirah, 20 steel racks, a shop counter). It moves
through stages (design → cutting → assembly → finishing → quality check → ready), uses raw materials from
a warehouse, collects labour and other costs, and ends either in finished stock or, for made-to-order
items, straight in the cost of the sale. The job card shows the running cost against the quoted price.

Stock and books
* Issuing material takes it out of the warehouse at its cost price (Dr production WIP, Cr inventory);
  returning puts it back at the average value issued.
* Labour and expenses are added to WIP (Dr WIP, Cr production expenses absorbed).
* Completing a stocked item adds the finished quantity to stock at the job's unit cost and updates the
  item's average cost (Dr inventory, Cr WIP). A made-to-order item or a job without an item goes
  straight to cost of goods sold (Dr COGS, Cr WIP).
* An invoice raised from the job (direct invoice with job_id) uses no raw materials; the job already did.

Concurrency: each change sends the job's revision. Stock moves are undone if the job changed meanwhile.
"""

import logging
import re
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

from bson import ObjectId
from django.views.decorators.http import require_http_methods
from mongoengine.connection import get_db

from apps.core.api.decorators import api_login_required
from apps.core.services.api_response_service import APIResponseService as R
from apps.inventory.models import Inventory, StockMovement, Warehouse
from apps.products.models import Product
from apps.sales.models import Customer
from .manufacturing_books import journal
from .recipes import made_to_order_ids, quantity, recipe
from .views import payload, permitted

log = logging.getLogger(__name__)

DEFAULT_STAGES = [
    ("design", "Design & measurement"),
    ("material", "Material ready"),
    ("cutting", "Cutting"),
    ("assembly", "Assembly / fabrication"),
    ("finishing", "Finishing"),
    ("qc", "Quality check"),
    ("ready", "Ready for delivery"),
]
PRIORITIES = ("low", "normal", "high", "urgent")
EXPENSE_KINDS = {"machine": "Machine / power", "transport": "Transport", "outsourced": "Outsourced work", "consumables": "Consumables", "other": "Other"}
OPEN = ("open", "on_hold")
PAGE = 50
EVENT_LIMIT = 300


def D(v):
    return Decimal(str(v if v not in (None, "") else 0))


def money(v):
    return f"{D(v).quantize(Decimal('.01')):f}"


def rs(v):
    """Rupees with Indian digit grouping, for activity text: ₹1,23,456.50 (paise dropped when zero)."""
    n = D(v).quantize(Decimal(".01"))
    sign = "-" if n < 0 else ""
    whole, frac = f"{abs(n):.2f}".split(".")
    head, tail = whole[:-3], whole[-3:]
    groups = []
    while len(head) > 2:
        groups.insert(0, head[-2:])
        head = head[:-2]
    if head:
        groups.insert(0, head)
    text = ",".join(groups + [tail]) if groups else tail
    return f"{sign}₹{text}" + ("" if frac == "00" else f".{frac}")


def qty_text(v):
    n = D(v).normalize()
    return f"{n:f}" if n != 0 else "0"


def _oid(value, what="record"):
    if isinstance(value, ObjectId):
        return value
    if not isinstance(value, str) or not ObjectId.is_valid(value):
        raise ValueError(f"Select a valid {what}.")
    return ObjectId(value)


def _text(data, key, limit, required=False, label=None):
    v = data.get(key, "")
    if v is None:
        v = ""
    if not isinstance(v, str):
        raise ValueError(f"{label or key.replace('_', ' ').capitalize()} must be text.")
    v = v.strip()
    if len(v) > limit:
        raise ValueError(f"{label or key.replace('_', ' ').capitalize()} is too long (up to {limit} characters).")
    if required and not v:
        raise ValueError(f"Enter {label or key.replace('_', ' ')}.")
    return v


def _amount(v, label):
    return quantity(v if v not in (None, "") else "0", label, positive=False, places=2)


def _now():
    return datetime.now(timezone.utc)


def stages(org_id):
    row = get_db().production_settings.find_one({"organization": org_id})
    if row and row.get("stages"):
        return row["stages"]
    return [dict(key=k, label=l) for k, l in DEFAULT_STAGES]


def _next_number(org_id):
    row = get_db().production_job_counters.find_one_and_update(
        {"_id": str(org_id)}, {"$inc": {"seq": 1}}, upsert=True, return_document=True
    )
    seq = (row or {}).get("seq", 1)
    while get_db().production_jobs.find_one({"organization": org_id, "number": f"JOB-{seq:04d}"}, {"_id": 1}):
        row = get_db().production_job_counters.find_one_and_update({"_id": str(org_id)}, {"$inc": {"seq": 1}}, return_document=True)
        seq = row["seq"]
    return f"JOB-{seq:04d}"


# ---------------------------------------------------------------------------------------------
# Costing and output
# ---------------------------------------------------------------------------------------------

def costs(job):
    material = sum((D(m["value"]) for m in job.get("materials", [])), Decimal(0))
    labour = sum((D(x["amount"]) for x in job.get("labour", [])), Decimal(0))
    other = sum((D(x["amount"]) for x in job.get("expenses", [])), Decimal(0))
    planned = sum((D(m["planned"]) * D(m.get("rate")) for m in job.get("materials", [])), Decimal(0))
    total = material + labour + other
    quoted = D(job.get("quoted"))
    margin = quoted - total
    return dict(
        material=money(material), labour=money(labour), expenses=money(other), total=money(total),
        planned_material=money(planned), quoted=money(quoted), margin=money(margin),
        margin_pct=f"{(margin * 100 / quoted).quantize(Decimal('.1')):f}" if quoted else None,
        unit_cost=money(total / D(job["quantity"])) if D(job.get("quantity")) else None,
    )


def _stage_info(job, stage_list):
    keys = [s["key"] for s in stage_list]
    idx = keys.index(job["stage"]) if job.get("stage") in keys else 0
    done = job["status"] in ("completed", "delivered")
    progress = 100 if done else round(100 * idx / max(1, len(keys)))
    label = next((s["label"] for s in stage_list if s["key"] == job.get("stage")), job.get("stage", ""))
    return idx, progress, label


def summary_row(job, stage_list, today=None):
    today = today or date.today()
    idx, progress, label = _stage_info(job, stage_list)
    due = job.get("due")
    days_left = (date.fromisoformat(due) - today).days if due else None
    c = costs(job)
    return dict(
        id=str(job["_id"]), number=job["number"], title=job["title"],
        customer=job.get("customer"), product=job.get("product"), quantity=qty_text(job.get("quantity", 0)),
        unit=(job.get("product") or {}).get("unit", ""), made_to_order=bool(job.get("made_to_order")),
        status=job["status"], stage=job.get("stage"), stage_label=label, stage_index=idx, progress=progress,
        priority=job.get("priority", "normal"), assignees=job.get("assignees", []), due=due, days_left=days_left,
        overdue=bool(due and job["status"] in OPEN and days_left is not None and days_left < 0),
        quoted=c["quoted"], cost=c["total"], margin=c["margin"], margin_pct=c["margin_pct"],
        invoice=job.get("invoice"), sales_order=job.get("sales_order"), revision=job.get("revision", 1),
        updated_at=job["updated_at"].isoformat() if job.get("updated_at") else None,
    )


def detail(org_id, job):
    stage_list = stages(org_id)
    out = summary_row(job, stage_list)
    ids = [m["product"] for m in job.get("materials", [])]
    held = {}
    if ids and job.get("warehouse"):
        for inv in get_db().inventory.find({"organization": org_id, "warehouse": _oid(job["warehouse"]["id"]), "product": {"$in": [_oid(i) for i in ids]}}):
            held[str(inv["product"])] = D(inv.get("quantity")) - D(inv.get("reserved_quantity"))
    materials = []
    for m in job.get("materials", []):
        issued = D(m["issued"])
        materials.append(dict(
            product=m["product"], name=m["name"], unit=m.get("unit", ""), planned=qty_text(m["planned"]), issued=qty_text(issued),
            pending=qty_text(max(Decimal(0), D(m["planned"]) - issued)), value=money(m["value"]), rate=money(m.get("rate")),
            available=qty_text(held.get(m["product"], Decimal(0))),
        ))
    out.update(
        stages=stage_list, warehouse=job.get("warehouse"), specification=job.get("specification", ""),
        materials=materials, labour=job.get("labour", []), expenses=job.get("expenses", []),
        costs=costs(job), completed_quantity=qty_text(job.get("completed_quantity", 0)),
        finished_to_stock=bool(job.get("finished_to_stock")),
        events=list(reversed(job.get("events", [])))[:100],
        created_at=job["created_at"].isoformat() if job.get("created_at") else None,
        completed_at=job["completed_at"].isoformat() if job.get("completed_at") else None,
        expense_kinds=EXPENSE_KINDS,
    )
    return out


def _event(job, user, kind, text):
    job.setdefault("events", []).append(dict(
        at=_now().isoformat(), kind=kind, text=text[:300],
        by=(f"{getattr(user, 'first_name', '')} {getattr(user, 'last_name', '')}".strip() or getattr(user, "email", "")) if user else "",
    ))
    if len(job["events"]) > EVENT_LIMIT:
        job["events"] = job["events"][-EVENT_LIMIT:]


# ---------------------------------------------------------------------------------------------
# Stock and books
# ---------------------------------------------------------------------------------------------

def _stock(org, job, product, delta, note, user):
    """Move stock in the job's warehouse. Returns an undo callable."""
    warehouse = Warehouse.objects(organization=org, id=_oid(job["warehouse"]["id"])).first()
    if not warehouse:
        raise ValueError("The job's warehouse is no longer available. Pick another warehouse for this job.")
    row = Inventory.objects(organization=org, product=product, warehouse=warehouse).first()
    if delta < 0:
        available = (D(row.quantity) - D(row.reserved_quantity)) if row else Decimal(0)
        if available + delta < 0:
            raise ValueError(
                f"Only {qty_text(max(available, Decimal(0)))} {product.unit} of {product.name} is available in {warehouse.name}. "
                "Record the purchase or stock adjustment first, or issue less."
            )
    if not row:
        row = Inventory(organization=org, product=product, warehouse=warehouse).save()
    after = Inventory.objects(id=row.id).modify(new=True, inc__quantity=delta, set__updated_at=datetime.utcnow())
    movement = StockMovement(
        organization=org, inventory=after, product=product, warehouse=warehouse,
        movement_type="STOCK_IN" if delta > 0 else "STOCK_OUT", quantity=abs(delta),
        quantity_before=after.quantity - delta, quantity_after=after.quantity,
        reserved_before=after.reserved_quantity, reserved_after=after.reserved_quantity,
        reference_type="PRODUCTION_JOB", reference_id=str(job["_id"]), notes=f"{job['number']} · {note}"[:500], created_by=user,
    ).save()

    def undo():
        Inventory.objects(id=row.id).update_one(inc__quantity=-delta)
        movement.delete()

    return undo


def _book(org, job, user, text, debit, credit, value):
    """Best-effort journal; production keeps working if an account needs attention, and says so."""
    if not value:
        return
    try:
        journal(get_db(), None, org.id, user.id, {"number": job["number"], "_id": job["_id"]}, text, _now(), debit, credit, Decimal(value))
    except Exception as exc:  # noqa: BLE001 - surfaced on the job card instead
        log.warning("Production journal skipped for %s: %s", job["number"], exc)
        _event(job, None, "warning", f"Not posted to the books: {exc}")


# ---------------------------------------------------------------------------------------------
# Building a job
# ---------------------------------------------------------------------------------------------

def _goods(org, value, what="item"):
    p = Product.objects(organization=org, id=_oid(value, what), is_active=True).first()
    if not p:
        raise ValueError(f"Select an active {what}.")
    return p


def _plan_from_recipe(org, product, qty):
    row = recipe(org.id, product.id)
    plan = []
    for m in (row or {}).get("materials", []):
        raw = Product.objects(organization=org, id=_oid(m["product"])).first()
        if raw and raw.is_active:
            plan.append(dict(product=str(raw.id), name=raw.name, unit=raw.unit, planned=qty_text(D(m["per_unit"]) * qty),
                             issued="0", value="0.00", rate=money(raw.cost_price)))
    return plan


def _plan_lines(org, rows, existing=None):
    if not isinstance(rows, list) or len(rows) > 80:
        raise ValueError("Add up to 80 material lines.")
    existing = {m["product"]: m for m in (existing or [])}
    out, seen = [], set()
    for r in rows:
        if not isinstance(r, dict):
            raise ValueError("Invalid material line.")
        raw = _goods(org, r.get("product"), "raw material")
        if raw.item_type == "service":
            raise ValueError("Materials must be stock items.")
        if str(raw.id) in seen:
            raise ValueError(f"{raw.name} is listed twice.")
        seen.add(str(raw.id))
        planned = quantity(r.get("planned") or "0", f"planned {raw.name}", positive=False)
        base = existing.get(str(raw.id))
        out.append(dict(base or dict(product=str(raw.id), name=raw.name, unit=raw.unit, issued="0", value="0.00", rate=money(raw.cost_price)),
                        planned=qty_text(planned)))
    for pid, m in existing.items():
        if pid not in seen and D(m["issued"]):
            raise ValueError(f"{m['name']} has been issued to this job. Return it before removing the line.")
    return out


def _common(org, data, job, creating):
    if "title" in data or creating:
        job["title"] = _text(data, "title", 120)
    if "specification" in data:
        job["specification"] = _text(data, "specification", 4000)
    if "priority" in data or creating:
        p = data.get("priority") or "normal"
        if p not in PRIORITIES:
            raise ValueError("Choose a priority: low, normal, high or urgent.")
        job["priority"] = p
    if "due" in data or creating:
        due = data.get("due") or ""
        job["due"] = date.fromisoformat(due).isoformat() if due else None
    if "assignees" in data or creating:
        people = data.get("assignees") or []
        if isinstance(people, str):
            people = [x for x in re.split(r"[,\n]", people)]
        if not isinstance(people, list) or len(people) > 12:
            raise ValueError("Assign up to 12 people.")
        job["assignees"] = [str(x).strip()[:60] for x in people if str(x).strip()]
    if "customer_id" in data or creating:
        cid = data.get("customer_id")
        if cid:
            c = Customer.objects(organization=org, id=_oid(cid, "customer")).first()
            if not c:
                raise ValueError("Select a customer from your list.")
            job["customer"] = dict(id=str(c.id), name=c.name, phone=getattr(c, "phone", "") or "")
        else:
            job["customer"] = None
    if "quoted" in data:
        job["quoted"] = money(_amount(data.get("quoted"), "quoted price"))


def create(org, user, data):
    job = dict(_id=ObjectId(), organization=org.id, status="open", revision=1, labour=[], expenses=[], events=[],
               completed_quantity="0", created_at=_now(), updated_at=_now(), created_by=user.id)
    _common(org, data, job, True)
    product = _goods(org, data["product_id"]) if data.get("product_id") else None
    if product and product.item_type == "service":
        raise ValueError("Pick a goods item to make. Services can't be produced.")
    qty = quantity(data.get("quantity") or "1", "quantity")
    job["quantity"] = qty_text(qty)
    if product:
        job["product"] = dict(id=str(product.id), name=product.name, sku=product.sku, unit=product.unit)
        job["made_to_order"] = bool(made_to_order_ids(org.id, [product.id]))
        if not job["title"]:
            job["title"] = product.name
    else:
        job["product"] = None
        job["made_to_order"] = True
    if not job["title"]:
        raise ValueError("Give the job a name, or pick the item you're making.")
    if data.get("warehouse_id"):
        wh = Warehouse.objects(organization=org, id=_oid(data["warehouse_id"], "warehouse"), is_active=True).first()
        if not wh:
            raise ValueError("Select an active warehouse.")
    else:
        from .quick_stock import warehouse_for
        wh = warehouse_for(org)
    job["warehouse"] = dict(id=str(wh.id), name=wh.name)
    if data.get("sales_order_id"):
        from apps.sales.models import SalesOrder
        so = SalesOrder.objects(organization=org, id=_oid(data["sales_order_id"], "sales order")).first()
        if not so:
            raise ValueError("Select a sales order from your list.")
        job["sales_order"] = dict(id=str(so.id), number=so.so_number)
        if not job.get("customer") and so.customer:
            job["customer"] = dict(id=str(so.customer.id), name=so.customer.name, phone=getattr(so.customer, "phone", "") or "")
    else:
        job["sales_order"] = None
    if "quoted" not in data:
        job["quoted"] = money(D(product.selling_price) * qty) if product else "0.00"
    if isinstance(data.get("materials"), list) and data["materials"]:
        job["materials"] = _plan_lines(org, data["materials"])
    else:
        job["materials"] = _plan_from_recipe(org, product, qty) if product else []
    stage_list = stages(org.id)
    job["stage"] = stage_list[0]["key"]
    job["number"] = _next_number(org.id)
    _event(job, user, "created", f"Job created{' for ' + job['customer']['name'] if job.get('customer') else ''}")
    get_db().production_jobs.insert_one(job)
    return job


# ---------------------------------------------------------------------------------------------
# Changing a job
# ---------------------------------------------------------------------------------------------

def _require_open(job, what="change this job"):
    if job["status"] == "cancelled":
        raise ValueError(f"This job is cancelled, so you can't {what}.")
    if job["status"] in ("completed", "delivered"):
        raise ValueError(f"This job is complete, so you can't {what}.")


def _material(job, pid):
    return next((m for m in job["materials"] if m["product"] == pid), None)


def apply(org, user, job, data, request, undo):
    action = data.get("action")
    stage_list = stages(org.id)
    if action == "update":
        if job["status"] == "cancelled":
            raise ValueError("This job is cancelled.")
        _common(org, data, job, False)
        if not job["title"]:
            raise ValueError("Give the job a name.")
        if "quantity" in data:
            if job["status"] not in OPEN:
                raise ValueError("The quantity can't change after the job is complete.")
            job["quantity"] = qty_text(quantity(data["quantity"], "quantity"))
        if "materials" in data:
            _require_open(job, "change the material plan")
            job["materials"] = _plan_lines(org, data["materials"], job["materials"])
        if "warehouse_id" in data and data["warehouse_id"] != job["warehouse"]["id"]:
            if any(D(m["issued"]) for m in job["materials"]):
                raise ValueError("Material has been issued from the current warehouse. Return it before changing warehouses.")
            wh = Warehouse.objects(organization=org, id=_oid(data["warehouse_id"], "warehouse"), is_active=True).first()
            if not wh:
                raise ValueError("Select an active warehouse.")
            job["warehouse"] = dict(id=str(wh.id), name=wh.name)
        _event(job, user, "updated", "Job details updated")
    elif action == "stage":
        _require_open(job, "move it to another stage")
        key = data.get("stage")
        found = next((s for s in stage_list if s["key"] == key), None)
        if not found:
            raise ValueError("Choose one of your production stages.")
        if key != job.get("stage"):
            job["stage"] = key
            if job["status"] == "on_hold":
                job["status"] = "open"
            _event(job, user, "stage", f"Moved to {found['label']}")
    elif action in ("hold", "resume"):
        _require_open(job)
        job["status"] = "on_hold" if action == "hold" else "open"
        reason = _text(data, "reason", 200)
        _event(job, user, action, ("On hold" + (f": {reason}" if reason else "")) if action == "hold" else "Work resumed")
    elif action in ("issue", "return"):
        _require_open(job, "issue or return material")
        if not permitted(request, "inventory.adjust"):
            raise PermissionError("Stock permission (inventory.adjust) is needed to issue or return material.")
        raw = _goods(org, data.get("product"), "raw material")
        if raw.item_type == "service":
            raise ValueError("Only stock items can be issued.")
        if job.get("product") and str(raw.id) == job["product"]["id"]:
            raise ValueError("You can't issue the item being made as its own material.")
        qty = quantity(data.get("quantity"), "quantity")
        line = _material(job, str(raw.id))
        if action == "issue":
            if not line:
                line = dict(product=str(raw.id), name=raw.name, unit=raw.unit, planned="0", issued="0", value="0.00", rate=money(raw.cost_price))
                job["materials"].append(line)
            rate = D(raw.cost_price)
            value = D(money(qty * rate))
            undo.append(_stock(org, job, raw, -qty, f"Issued {qty_text(qty)} {raw.unit} {raw.name}", user))
            line.update(issued=qty_text(D(line["issued"]) + qty), value=money(D(line["value"]) + value), rate=money(rate))
            _book(org, job, user, f"Material issued: {raw.name}", "PRODUCTION_WIP", "INVENTORY", value)
            _event(job, user, "issue", f"Issued {qty_text(qty)} {raw.unit} {raw.name} ({rs(value)})")
        else:
            if not line or qty > D(line["issued"]):
                raise ValueError(f"You can return up to {qty_text(D(line['issued']) if line else 0)} {raw.unit} of {raw.name}.")
            value = D(money(D(line["value"]) * qty / D(line["issued"])))
            undo.append(_stock(org, job, raw, qty, f"Returned {qty_text(qty)} {raw.unit} {raw.name}", user))
            line.update(issued=qty_text(D(line["issued"]) - qty), value=money(D(line["value"]) - value))
            _book(org, job, user, f"Material returned: {raw.name}", "INVENTORY", "PRODUCTION_WIP", value)
            _event(job, user, "return", f"Returned {qty_text(qty)} {raw.unit} {raw.name} ({rs(value)})")
    elif action == "labour":
        _require_open(job, "add labour")
        worker = _text(data, "worker", 60, True, "the worker's name")
        hours = _amount(data.get("hours"), "hours")
        rate = _amount(data.get("rate"), "rate")
        amt = _amount(data.get("amount"), "amount") if data.get("amount") not in (None, "") else D(money(hours * rate))
        if not amt:
            raise ValueError("Enter the labour amount, or hours and rate.")
        when = date.fromisoformat(data.get("date") or date.today().isoformat()).isoformat()
        job["labour"].append(dict(id=uuid4().hex[:12], date=when, worker=worker, hours=qty_text(hours), rate=money(rate), amount=money(amt),
                                  note=_text(data, "note", 200)))
        _book(org, job, user, f"Labour: {worker}", "PRODUCTION_WIP", "PRODUCTION_ABSORPTION", amt)
        _event(job, user, "labour", f"Labour {worker}: {rs(amt)}")
    elif action == "expense":
        _require_open(job, "add expenses")
        kind = data.get("kind") or "other"
        if kind not in EXPENSE_KINDS:
            raise ValueError("Choose an expense type.")
        amt = quantity(data.get("amount"), "amount", places=2)
        when = date.fromisoformat(data.get("date") or date.today().isoformat()).isoformat()
        job["expenses"].append(dict(id=uuid4().hex[:12], date=when, kind=kind, label=EXPENSE_KINDS[kind], amount=money(amt), note=_text(data, "note", 200)))
        _book(org, job, user, f"{EXPENSE_KINDS[kind]} expense", "PRODUCTION_WIP", "PRODUCTION_ABSORPTION", amt)
        _event(job, user, "expense", f"{EXPENSE_KINDS[kind]}: {rs(amt)}")
    elif action == "remove_entry":
        _require_open(job, "remove costs")
        kind = data.get("kind")
        if kind not in ("labour", "expenses"):
            raise ValueError("Choose a labour or expense entry.")
        entry = next((x for x in job[kind] if x["id"] == data.get("id")), None)
        if not entry:
            raise ValueError("That entry is already removed.")
        job[kind].remove(entry)
        _book(org, job, user, f"Reversed {kind} entry", "PRODUCTION_ABSORPTION", "PRODUCTION_WIP", D(entry["amount"]))
        _event(job, user, "removed", f"Removed {'labour ' + entry.get('worker', '') if kind == 'labour' else entry.get('label', 'expense')}: {rs(entry['amount'])}")
    elif action == "note":
        text = _text(data, "text", 300, True, "a note")
        _event(job, user, "note", text)
    elif action == "complete":
        _require_open(job, "complete it again")
        good = quantity(data.get("quantity") or job["quantity"], "finished quantity")
        c = costs(job)
        total = D(c["total"])
        product = Product.objects(organization=org, id=_oid(job["product"]["id"])).first() if job.get("product") else None
        stocked = bool(product and not made_to_order_ids(org.id, [product.id]) and product.is_active)
        if stocked:
            if not permitted(request, "inventory.adjust"):
                raise PermissionError("Stock permission (inventory.adjust) is needed to add finished goods to stock.")
            on_hand = sum((D(i.quantity) for i in Inventory.objects(organization=org, product=product)), Decimal(0))
            on_hand = max(on_hand, Decimal(0))
            unit = total / good
            average = (on_hand * D(product.cost_price) + total) / (on_hand + good)
            undo.append(_stock(org, job, product, good, f"Finished {qty_text(good)} {product.unit}", user))
            old_cost = product.cost_price
            Product.objects(id=product.id).update_one(set__cost_price=D(money(average)), set__updated_at=datetime.utcnow())
            undo.append(lambda: Product.objects(id=product.id).update_one(set__cost_price=old_cost))
            _book(org, job, user, "Finished goods to stock", "INVENTORY", "PRODUCTION_WIP", total)
            _event(job, user, "complete", f"Completed {qty_text(good)} {product.unit} into {job['warehouse']['name']} at {rs(unit)} each")
        else:
            _book(org, job, user, "Made-to-order job cost", "COST_OF_GOODS_SOLD", "PRODUCTION_WIP", total)
            _event(job, user, "complete", f"Completed {qty_text(good)}{' ' + job['product']['unit'] if job.get('product') else ''}. Cost {rs(total)} charged to the sale (made to order)")
        job.update(status="completed", completed_quantity=qty_text(good), finished_to_stock=stocked, completed_at=_now(), stage=stage_list[-1]["key"])
    elif action == "deliver":
        if job["status"] != "completed":
            raise ValueError("Complete the job before marking it delivered.")
        job["status"] = "delivered"
        job["delivered_at"] = _now()
        _event(job, user, "deliver", "Delivered to the customer")
    elif action == "cancel":
        _require_open(job, "cancel it")
        if any(D(m["issued"]) for m in job["materials"]):
            raise ValueError("Return the issued material to stock before cancelling, or complete the job.")
        if job.get("invoice"):
            raise ValueError("This job has an invoice. Cancel the invoice first.")
        if job["labour"] or job["expenses"]:
            for kind in ("labour", "expenses"):
                for entry in job[kind]:
                    _book(org, job, user, "Cancelled job cost", "PRODUCTION_ABSORPTION", "PRODUCTION_WIP", D(entry["amount"]))
        job["status"] = "cancelled"
        _event(job, user, "cancel", "Job cancelled" + (f": {_text(data, 'reason', 200)}" if data.get("reason") else ""))
    else:
        raise ValueError("Unknown job action.")


def _save(job, revision):
    job["revision"] = revision + 1
    job["updated_at"] = _now()
    res = get_db().production_jobs.replace_one({"_id": job["_id"], "organization": job["organization"], "revision": revision}, job)
    if not res.matched_count:
        raise ValueError("Someone else changed this job just now. Reload it and try again.")


# ---------------------------------------------------------------------------------------------
# Invoice link (called by direct invoices)
# ---------------------------------------------------------------------------------------------

def job_for_invoice(org, job_id):
    job = get_db().production_jobs.find_one({"organization": org.id, "_id": _oid(job_id, "job")})
    if not job:
        raise ValueError("Production job not found.")
    if job["status"] == "cancelled":
        raise ValueError("This job is cancelled.")
    if job.get("invoice"):
        raise ValueError(f"{job['number']} already has invoice {job['invoice']['number']}.")
    if not job.get("product"):
        raise ValueError("Pick the item you're making on the job before invoicing it.")
    if not job.get("made_to_order") and not made_to_order_ids(org.id, [job["product"]["id"]]) and job["status"] in OPEN:
        raise ValueError("Complete the job first so the finished item is in stock, or mark the item as made to order.")
    return job


def link_invoice(org, job, invoice, user):
    db = get_db().production_jobs
    current = db.find_one({"_id": job["_id"]})
    current["invoice"] = dict(id=str(invoice.id), number=invoice.invoice_number, total=money(invoice.total_amount))
    _event(current, user, "invoice", f"Invoice {invoice.invoice_number} raised for {rs(invoice.total_amount)}")
    current["revision"] = current.get("revision", 1) + 1
    current["updated_at"] = _now()
    db.replace_one({"_id": job["_id"]}, current)


# ---------------------------------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------------------------------

def board(org_id, params):
    stage_list = stages(org_id)
    scope = {"organization": org_id}
    status = params.get("status") or "active"
    if status == "active":
        scope["status"] = {"$in": list(OPEN)}
    elif status == "done":
        scope["status"] = {"$in": ["completed", "delivered"]}
    elif status in ("open", "on_hold", "completed", "delivered", "cancelled"):
        scope["status"] = status
    elif status != "all":
        raise ValueError("Unknown status filter.")
    if params.get("stage"):
        scope["stage"] = params["stage"]
    if params.get("customer"):
        scope["customer.id"] = params["customer"]
    if params.get("priority") in PRIORITIES:
        scope["priority"] = params["priority"]
    search = (params.get("search") or "").strip()[:60]
    if search:
        rx = {"$regex": re.escape(search), "$options": "i"}
        scope["$or"] = [{"number": rx}, {"title": rx}, {"customer.name": rx}, {"product.name": rx}, {"assignees": rx}]
    today = date.today()
    rows = list(get_db().production_jobs.find(scope).sort([("due", 1), ("_id", -1)]).limit(500))
    out = [summary_row(j, stage_list, today) for j in rows]
    if params.get("overdue") == "1":
        out = [r for r in out if r["overdue"]]
    rank = {"urgent": 0, "high": 1, "normal": 2, "low": 3}
    out.sort(key=lambda r: (not r["overdue"], r["due"] or "9999-12-31", rank.get(r["priority"], 2)))

    active = list(get_db().production_jobs.find({"organization": org_id, "status": {"$in": list(OPEN)}}))
    week = (today + timedelta(days=7)).isoformat()
    month_ago = _now() - timedelta(days=30)
    done_month = list(get_db().production_jobs.find({"organization": org_id, "status": {"$in": ["completed", "delivered"]}, "completed_at": {"$gte": month_ago}}))
    by_stage = {s["key"]: 0 for s in stage_list}
    for j in active:
        by_stage[j.get("stage")] = by_stage.get(j.get("stage"), 0) + 1
    margin_base = [costs(j) for j in done_month]
    quoted = sum((D(c["quoted"]) for c in margin_base), Decimal(0))
    margin = sum((D(c["margin"]) for c in margin_base), Decimal(0))
    summary = dict(
        active=len(active),
        on_hold=sum(1 for j in active if j["status"] == "on_hold"),
        overdue=sum(1 for j in active if j.get("due") and j["due"] < today.isoformat()),
        due_week=sum(1 for j in active if j.get("due") and today.isoformat() <= j["due"] <= week),
        wip_value=money(sum((D(costs(j)["total"]) for j in active), Decimal(0))),
        completed_30d=len(done_month),
        margin_30d=money(margin),
        margin_pct_30d=f"{(margin * 100 / quoted).quantize(Decimal('.1')):f}" if quoted else None,
        to_invoice=get_db().production_jobs.count_documents({"organization": org_id, "status": {"$in": ["completed", "delivered"]}, "invoice": None}),
        by_stage=[dict(key=s["key"], label=s["label"], count=by_stage.get(s["key"], 0)) for s in stage_list],
    )
    return dict(rows=out[:PAGE * 4], count=len(out), summary=summary, stages=stage_list, priorities=list(PRIORITIES))


@api_login_required
@require_http_methods(["GET", "POST"])
def jobs(request, job_id=None):
    org = request.api_organization
    if not permitted(request, "manufacturing.read"):
        return R.forbidden(message="Manufacturing access required.", request=request)
    try:
        if request.method == "GET":
            if job_id:
                job = get_db().production_jobs.find_one({"organization": org.id, "_id": _oid(job_id, "job")})
                if not job:
                    return R.not_found(message="Production job not found.", request=request)
                return R.success(data=detail(org.id, job), request=request)
            return R.success(data=board(org.id, request.GET), request=request)
        if not permitted(request, "manufacturing.manage"):
            return R.forbidden(message="Manufacturing permission (manage) is needed to change jobs.", request=request)
        data = payload(request)
        if not job_id:
            job = create(org, request.api_user, data)
            return R.success(data=detail(org.id, job), request=request)
        job = get_db().production_jobs.find_one({"organization": org.id, "_id": _oid(job_id, "job")})
        if not job:
            return R.not_found(message="Production job not found.", request=request)
        revision = data.get("revision")
        if revision != job.get("revision", 1):
            raise ValueError("This job changed since you opened it. Reload it and try again.")
        undo = []
        try:
            apply(org, request.api_user, job, data, request, undo)
            _save(job, revision)
        except Exception:
            for fn in reversed(undo):
                fn()
            raise
        return R.success(data=detail(org.id, job), request=request)
    except PermissionError as exc:
        return R.forbidden(message=str(exc), request=request)
    except (ValueError, TypeError, KeyError) as exc:
        return R.validation_error(message=str(exc) or "Check the job details.", request=request)


@api_login_required
@require_http_methods(["GET", "POST"])
def job_settings(request):
    org = request.api_organization
    if not permitted(request, "manufacturing.read"):
        return R.forbidden(message="Manufacturing access required.", request=request)
    try:
        if request.method == "POST":
            if not permitted(request, "manufacturing.manage"):
                return R.forbidden(message="Manufacturing permission (manage) is needed.", request=request)
            data = payload(request)
            rows = data.get("stages")
            if not isinstance(rows, list) or not 2 <= len(rows) <= 15:
                raise ValueError("Use between 2 and 15 stages.")
            clean, keys = [], set()
            for r in rows:
                label = _text(r if isinstance(r, dict) else {}, "label", 40, True, "a stage name")
                key = (r.get("key") or re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-"))[:30] or uuid4().hex[:6]
                if key in keys:
                    key = f"{key}-{len(keys)}"
                keys.add(key)
                clean.append(dict(key=key, label=label))
            active_stages = get_db().production_jobs.distinct("stage", {"organization": org.id, "status": {"$in": list(OPEN)}})
            missing = [s for s in active_stages if s not in keys]
            if missing:
                raise ValueError("Some open jobs are in a stage you removed. Move them first, or keep that stage.")
            get_db().production_settings.update_one({"organization": org.id}, {"$set": {"stages": clean, "updated_at": _now()}}, upsert=True)
        return R.success(data={"stages": stages(org.id), "expense_kinds": EXPENSE_KINDS, "priorities": list(PRIORITIES)}, request=request)
    except ValueError as exc:
        return R.validation_error(message=str(exc), request=request)
