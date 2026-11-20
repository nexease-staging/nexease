"""Production orders and batch postings in the same Mongo transaction as inventory."""

import hashlib
import json
import re
from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import UUID

from bson import ObjectId
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
from mongoengine.connection import get_db
from pymongo.errors import PyMongoError

from apps.core.api.decorators import api_login_required
from apps.core.services.api_response_service import APIResponseService as R
from apps.inventory.models import Inventory, StockMovement, Warehouse
from apps.products.models import Product
from apps.sales.models import SalesOrder
from .pro_api import csv_bytes
from .manufacturing_reports import production_rows
from .manufacturing_books import journal
from .payroll import amount, money
from .views import payload, permitted

EXPENSES = ("labour", "machine", "consumables", "other")


def number(value, label, positive=False):
    n = amount(value, label)
    if n != n.quantize(Decimal(".01")) or (positive and not n):
        raise ValueError(
            f"Check {label}: use up to two decimals and a positive quantity."
        )
    return n


def oid(value):
    if not isinstance(value, str) or not ObjectId.is_valid(value):
        raise ValueError("Select a valid record.")
    return ObjectId(value)


def goods(org, value):
    p = Product.objects(organization=org, id=oid(value), is_active=True).first()
    if not p or p.item_type == "service":
        raise ValueError("Select an active inventory item.")
    return p


def plan(org, data):
    warehouse = Warehouse.objects(
        organization=org, id=oid(data.get("warehouse")), is_active=True
    ).first()
    if not warehouse:
        raise ValueError("Select an active warehouse.")
    so = None
    if data.get("sales_order"):
        so = SalesOrder.objects(
            organization=org, id=oid(data["sales_order"]), warehouse=warehouse
        ).first()
        if not so or so.status in ("FULFILLED", "CANCELLED"):
            raise ValueError("Choose an open sales order for this warehouse.")
    outputs = data.get("outputs")
    if not isinstance(outputs, list) or not 1 <= len(outputs) <= 100:
        raise ValueError("Add between one and 100 finished product lines.")
    rows = []
    for line in outputs:
        if not isinstance(line, dict):
            raise ValueError("Invalid finished product line.")
        product = goods(org, line.get("product"))
        if so and product.id not in {i.product.id for i in so.items}:
            raise ValueError(
                "The finished product is absent from the selected sales order."
            )
        qty = number(line.get("quantity"), "planned quantity", True)
        materials = []
        estimate = number(line.get("estimated_expenses", 0), "estimated expenses")
        requirements = line.get("materials")
        if not isinstance(requirements, list) or not 1 <= len(requirements) <= 100:
            raise ValueError("Add the material required per finished unit.")
        for material in requirements:
            raw = goods(
                org, material.get("product") if isinstance(material, dict) else None
            )
            if raw == product or any(m["product"] == str(raw.id) for m in materials):
                raise ValueError(
                    "Choose distinct raw materials for each finished product."
                )
            per = number(material.get("per_unit"), "material per unit", True)
            required = Decimal(money(per * qty))
            estimate += required * raw.cost_price
            materials.append(
                dict(
                    product=str(raw.id),
                    name=raw.name,
                    unit=raw.unit,
                    per_unit=str(per),
                    required=str(required),
                    rate=money(raw.cost_price),
                    issued="0.00",
                    value="0.00",
                )
            )
        rows.append(
            dict(
                product=str(product.id),
                name=product.name,
                unit=product.unit,
                quantity=str(qty),
                specification=str(line.get("specification", ""))[:2000],
                materials=materials,
                estimated_expenses=money(
                    number(line.get("estimated_expenses", 0), "expenses")
                ),
                estimate=money(estimate),
                accepted="0.00",
                rejected="0.00",
                expenses="0.00",
            )
        )
    return dict(
        warehouse=str(warehouse.id),
        warehouse_name=warehouse.name,
        sales_order=str(so.id) if so else "",
        sales_number=so.so_number if so else "",
        due=date.fromisoformat(data["due"]).isoformat(),
        outputs=rows,
    )


def stock(db, session, org, actor, order, product, delta, operation, now):
    key = dict(
        organization=org, warehouse=oid(order["warehouse"]), product=oid(product)
    )
    row = db.inventory.find_one(key, session=session)
    before = Decimal(str(row["quantity"])) if row else Decimal(0)
    reserved = Decimal(str(row.get("reserved_quantity", 0))) if row else Decimal(0)
    after = before + delta
    if delta < 0 and after < reserved:
        raise ValueError("Insufficient unreserved stock in this warehouse.")
    inv = row["_id"] if row else ObjectId()
    db.inventory.update_one(
        {"_id": inv},
        {
            "$set": dict(quantity=float(after), updated_at=now),
            "$setOnInsert": dict(**key, created_at=now, reserved_quantity=0.0),
        },
        upsert=True,
        session=session,
    )
    db.stock_movements.insert_one(
        dict(
            **key,
            inventory=inv,
            quantity=float(delta),
            quantity_before=float(before),
            quantity_after=float(after),
            reserved_before=float(reserved),
            reserved_after=float(reserved),
            movement_type="STOCK_IN" if delta > 0 else "STOCK_OUT",
            reference_type="MANUFACTURING",
            reference_id=str(order["_id"]),
            notes=operation,
            created_by=actor,
            created_at=now,
        ),
        session=session,
    )


def post(db, session, org, actor, order, data, now):
    action = data.get("action")
    if order["status"] == "completed":
        raise ValueError("This order is complete.")
    if action == "close":
        if not all(
            Decimal(line["accepted"]) + Decimal(line["rejected"]) > 0
            for line in order["outputs"]
        ):
            raise ValueError("Record production for each output before closing.")
        if any(
            not b["posted"]
            for line in order["outputs"]
            for b in line.get("batches", [])
        ):
            raise ValueError("Finish all open batches before closing.")
        order["status"] = "completed"
        return
    batch = data.get("batch", "")
    if not isinstance(batch, str) or not re.fullmatch(r"[\w./-]{1,60}", batch):
        raise ValueError(
            "Enter a batch reference (1–60 letters, digits, dots, dashes or slashes)."
        )
    idx = data.get("line")
    if type(idx) is not int or not 0 <= idx < len(order["outputs"]):
        raise ValueError("Select a finished product line.")
    line = order["outputs"][idx]
    reference = f"{batch} · {data['request_key']}"
    batches = line.setdefault("batches", [])
    current = next((b for b in batches if b["name"] == batch), None)
    if current is None:
        current = dict(name=batch, posted=False, materials={})
        batches.append(current)
    if current["posted"]:
        raise ValueError("This batch is posted. Enter a new batch reference.")
    if action in ("allocate", "release", "issue", "return"):
        mat = next(
            (m for m in line["materials"] if m["product"] == data.get("material")), None
        )
        if not mat:
            raise ValueError("Select a planned material.")
        qty = number(data.get("quantity"), "quantity", True)
        issued, value = Decimal(mat["issued"]), Decimal(mat["value"])
        balance = current["materials"].setdefault(
            mat["product"], {"qty": "0", "value": "0"}
        )
        bqty, bvalue = Decimal(balance["qty"]), Decimal(balance["value"])
        allocated = Decimal(balance.get("allocated", "0"))
        if action in ("allocate", "release") or (action == "issue" and allocated):
            change = (
                qty
                if action == "allocate"
                else -qty if action == "release" else -min(qty, allocated)
            )
            if allocated + change < 0:
                raise ValueError("Release exceeds this batch allocation.")
            key = dict(
                organization=org,
                warehouse=oid(order["warehouse"]),
                product=oid(mat["product"]),
            )
            inv = db.inventory.find_one(key, session=session)
            if not inv:
                raise ValueError("Material has no stock in this warehouse.")
            held = Decimal(str(inv.get("reserved_quantity", 0)))
            total = Decimal(str(inv["quantity"]))
            if held + change < 0 or (change > 0 and held + change > total):
                raise ValueError("Insufficient available stock for this allocation.")
            db.inventory.update_one(
                {"_id": inv["_id"]},
                {
                    "$set": {
                        "reserved_quantity": float(held + change),
                        "updated_at": now,
                    }
                },
                session=session,
            )
            db.stock_movements.insert_one(
                dict(
                    **key,
                    inventory=inv["_id"],
                    movement_type=(
                        "RESERVATION" if change > 0 else "RESERVATION_RELEASE"
                    ),
                    quantity=float(abs(change)),
                    quantity_before=float(total),
                    quantity_after=float(total),
                    reserved_before=float(held),
                    reserved_after=float(held + change),
                    reference_type="MANUFACTURING",
                    reference_id=str(order["_id"]),
                    notes=reference,
                    created_by=actor,
                    created_at=now,
                ),
                session=session,
            )
            balance["allocated"] = money(allocated + change)
            if action != "issue":
                if not any(
                    Decimal(x["qty"]) or Decimal(x.get("allocated", 0))
                    for x in current["materials"].values()
                ):
                    batches.remove(current)
                order["status"] = "in progress"
                return
        if action == "return" and qty > bqty:
            raise ValueError("Return exceeds net issued material.")
        if action == "issue":
            raw = db.products.find_one(
                {"_id": oid(mat["product"]), "organization": org}, session=session
            )
            if not raw or not raw.get("is_active", True):
                raise ValueError("Material is unavailable.")
            change = Decimal(money(qty * Decimal(str(raw["cost_price"]))))
        else:
            change = -Decimal(money(bvalue * qty / bqty))
            qty = -qty
        stock(
            db,
            session,
            org,
            actor,
            order,
            mat["product"],
            -qty,
            f"{action} {reference}",
            now,
        )
        mat.update(issued=money(issued + qty), value=money(value + change))
        balance.update(qty=money(bqty + qty), value=money(bvalue + change))
        dr, cr = (
            ("PRODUCTION_WIP", "INVENTORY")
            if action == "issue"
            else ("INVENTORY", "PRODUCTION_WIP")
        )
        journal(db, session, org, actor, order, reference, now, dr, cr, abs(change))
        if not any(
            Decimal(x["qty"]) or Decimal(x.get("allocated", 0))
            for x in current["materials"].values()
        ):
            batches.remove(current)
    elif action == "produce":
        good = number(data.get("accepted", 0), "accepted")
        bad = number(data.get("rejected", 0), "rejected")
        if not good + bad or not any(
            Decimal(m["qty"]) > 0 for m in current["materials"].values()
        ):
            raise ValueError("Issue material and enter the produced quantity.")
        cost = sum(number(data.get(k, 0), k) for k in EXPENSES)
        if any(Decimal(m.get("allocated", 0)) for m in current["materials"].values()):
            raise ValueError("Issue or release outstanding batch allocations.")
        batch_cost = cost + sum(
            Decimal(m["value"]) for m in current["materials"].values()
        )
        journal(
            db,
            session,
            org,
            actor,
            order,
            reference,
            now,
            "PRODUCTION_WIP",
            "PRODUCTION_ABSORPTION",
            cost,
        )
        journal(
            db,
            session,
            org,
            actor,
            order,
            reference,
            now,
            "INVENTORY" if good else "COST_OF_GOODS_SOLD",
            "PRODUCTION_WIP",
            batch_cost,
        )
        current.update(
            posted=True,
            accepted=money(good),
            rejected=money(bad),
            cost=money(batch_cost),
            expenses={k: money(number(data.get(k, 0), k)) for k in EXPENSES},
        )
        if good:
            product_key = {
                "_id": oid(line["product"]),
                "organization": org,
                "is_active": True,
            }
            product = db.products.find_one(product_key, session=session)
            if not product:
                raise ValueError("Finished product is inactive or missing.")
            balances = db.inventory.find(
                dict(organization=org, product=product["_id"]),
                {"quantity": 1},
                session=session,
            )
            on_hand = max(
                Decimal(0),
                sum((Decimal(str(x["quantity"])) for x in balances), Decimal(0)),
            )
            average = (on_hand * Decimal(str(product["cost_price"])) + batch_cost) / (
                on_hand + good
            )
            db.products.update_one(
                product_key,
                {"$set": {"cost_price": float(money(average)), "updated_at": now}},
                session=session,
            )
            stock(
                db,
                session,
                org,
                actor,
                order,
                line["product"],
                good,
                f"Production {reference}",
                now,
            )
        line.update(
            accepted=money(Decimal(line["accepted"]) + good),
            rejected=money(Decimal(line["rejected"]) + bad),
            expenses=money(Decimal(line["expenses"]) + cost),
        )
    else:
        raise ValueError("Unknown production action.")
    order["status"] = "in progress"


def totals(order):
    for line in order["outputs"]:
        actual = sum(
            (Decimal(m["value"]) for m in line["materials"]), Decimal(line["expenses"])
        )
        good = Decimal(line["accepted"])
        posted = sum(
            (Decimal(b["cost"]) for b in line.get("batches", []) if b["posted"]),
            Decimal(0),
        )
        line.update(
            posted_cost=money(posted),
            work_in_progress=money(actual - posted),
            actual=money(actual),
            variance=money(actual - Decimal(line["estimate"])),
            pending=money(max(Decimal(0), Decimal(line["quantity"]) - good)),
            unit_cost=money(posted / good) if good else None,
        )
    return order


def public(row):
    return {
        **{k: v for k, v in totals(row).items() if k not in ("_id", "organization")},
        "id": str(row["_id"]),
    }


@api_login_required
@require_http_methods(["GET", "POST"])
def orders(request, order_id=None):
    write = request.method == "POST"
    if not permitted(request, "manufacturing.read") or (
        write
        and not all(
            permitted(request, p) for p in ("manufacturing.manage", "inventory.adjust")
        )
    ):
        return R.forbidden(message="Inventory permission required.", request=request)
    db = get_db()
    org = request.api_organization.id
    scope = {"organization": org}
    try:
        if order_id:
            scope["_id"] = oid(order_id)
        if not write:
            if order_id:
                row = db.manufacturing_orders.find_one(scope)
                if not row:
                    return R.not_found(
                        message="Manufacturing order not found.", request=request
                    )
                product_ids = {
                    oid(v["product"])
                    for line in row["outputs"]
                    for v in [line, *line["materials"]]
                }
                stocks = {
                    str(b["product"]): b
                    for b in db.inventory.find(
                        {
                            "organization": org,
                            "warehouse": oid(row["warehouse"]),
                            "product": {"$in": list(product_ids)},
                        }
                    )
                }
                for line in row["outputs"]:
                    line["on_hand"] = str(
                        stocks.get(line["product"], {}).get("quantity", 0)
                    )
                    for m in line["materials"]:
                        balance = stocks.get(m["product"], {})
                        m["available"] = money(
                            Decimal(str(balance.get("quantity", 0)))
                            - Decimal(str(balance.get("reserved_quantity", 0)))
                        )
                events = db.manufacturing_events.find(
                    {"organization": org, "order": row["_id"]}
                ).sort("revision", 1)
                result = dict(
                    order=public(row),
                    history=[
                        dict(
                            action=e["action"],
                            revision=e["revision"],
                            at=e["at"],
                            actor=str(e["actor"]),
                            entry=e["entry"],
                        )
                        for e in events
                    ],
                )
                if row["sales_order"] and permitted(request, "invoices.read"):
                    invoices = list(
                        db.invoices.find(
                            dict(
                                organization=org,
                                sales_order=oid(row["sales_order"]),
                                status={"$in": ["ISSUED", "PARTIALLY_PAID", "PAID"]},
                            )
                        )
                    )
                    result["sales"] = [
                        dict(
                            number=x["invoice_number"],
                            total=str(x["total_amount"]),
                            paid=str(x.get("amount_paid", 0)),
                            due=str(x.get("balance_due", 0)),
                        )
                        for x in invoices
                    ]
                    items = {line["product"] for line in row["outputs"]}
                    shared = db.manufacturing_orders.find_one(
                        {
                            "organization": org,
                            "sales_order": row["sales_order"],
                            "_id": {"$ne": row["_id"]},
                            "outputs.product": {"$in": list(items)},
                        }
                    )
                    if not shared:
                        billed = invoices
                        credits = db.credit_notes.find(
                            {
                                "organization": org,
                                "invoice": {"$in": [i["_id"] for i in billed]},
                                "status": "ISSUED",
                            }
                        )

                        def net(doc):
                            return sum(
                                (
                                    Decimal(str(i["line_subtotal"]))
                                    - Decimal(str(i.get("discount", 0)))
                                    for i in doc["items"]
                                    if str(i["product"]) in items
                                ),
                                Decimal(0),
                            )

                        revenue = sum(map(net, billed), Decimal(0)) - sum(
                            map(net, credits), Decimal(0)
                        )
                        result["net_revenue"] = money(revenue)
                        result["revenue_less_job_cost"] = money(
                            revenue - sum(Decimal(l["actual"]) for l in row["outputs"])
                        )
            else:
                if "sales_ids" in request.GET:
                    ids = request.GET["sales_ids"].split(",")
                    if len(ids) > 100 or not all(ObjectId.is_valid(key) for key in ids):
                        raise ValueError("Select up to 100 sales orders.")
                    jobs = db.manufacturing_orders.find(
                        dict(organization=org, sales_order={"$in": ids}),
                        {"sales_order": 1, "status": 1},
                    )
                    statuses = {}
                    for job in jobs:
                        statuses.setdefault(job["sales_order"], set()).add(
                            job["status"]
                        )
                    return R.success(
                        data={"statuses": {k: sorted(v) for k, v in statuses.items()}},
                        request=request,
                    )
                for field in ("status", "sales_order"):
                    if request.GET.get(field):
                        scope[field] = request.GET[field]
                if request.GET.get("product"):
                    scope["outputs.product"] = request.GET["product"]
                if request.GET.get("search"):
                    scope["number"] = {
                        "$regex": re.escape(request.GET["search"][:60]),
                        "$options": "i",
                    }
                for key, operator in [("from", "$gte"), ("to", "$lte")]:
                    if request.GET.get(key):
                        scope.setdefault("due", {})[operator] = date.fromisoformat(
                            request.GET[key]
                        ).isoformat()
                if request.GET.get("export") == "csv":
                    report = production_rows(
                        (
                            totals(job)
                            for job in db.manufacturing_orders.find(scope).sort(
                                "_id", 1
                            )
                        ),
                        request.GET.get("report"),
                        request.GET.get("product"),
                    )
                    response = HttpResponse(
                        csv_bytes(report), content_type="text/csv; charset=utf-8"
                    )
                    response["Content-Disposition"] = (
                        'attachment; filename="manufacturing.csv"'
                    )
                    return response
                page = max(1, int(request.GET.get("page", "1")))
                rows = (
                    db.manufacturing_orders.find(scope)
                    .sort("_id", 1 if request.GET.get("sort") == "oldest" else -1)
                    .skip((page - 1) * 25)
                    .limit(25)
                )
                result = dict(
                    rows=[public(x) for x in rows],
                    count=db.manufacturing_orders.count_documents(scope),
                )
                result["completed"] = db.manufacturing_orders.count_documents(
                    {"$and": [scope, {"status": "completed"}]}
                )
                result["pending"] = result["count"] - result["completed"]
            return R.success(data=result, request=request)
        data = payload(request)
        if data.get("sales_order") and not permitted(request, "sales_orders.read"):
            return R.forbidden(message="Sales order access required.", request=request)
        token = str(UUID(str(data.get("request_key", ""))))
        digest = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
        action = data.get("action", "create")
        now = datetime.now(timezone.utc)
        target = scope.get("_id") or ObjectId()

        def execute(session):
            key = f"{org}:{token}"
            previous = db.manufacturing_events.find_one({"_id": key}, session=session)
            if previous:
                if previous["digest"] != digest or (
                    order_id and previous["order"] != target
                ):
                    raise ValueError("Request key already used for another entry.")
                return str(previous["order"])
            if not order_id:
                if action != "create":
                    raise ValueError("Create an order first.")
                row = dict(
                    _id=target,
                    organization=org,
                    number="MO-" + str(target).upper(),
                    status="planned",
                    revision=1,
                    created_at=now,
                    **plan(request.api_organization, data),
                )
                db.manufacturing_orders.insert_one(row, session=session)
            else:
                row = db.manufacturing_orders.find_one(scope, session=session)
                if not row or row["revision"] != data.get("revision"):
                    raise ValueError("Reload the order before making this change.")
                if action == "edit":
                    if row["status"] != "planned":
                        raise ValueError("Only unstarted plans can be edited.")
                    row.update(plan(request.api_organization, data))
                else:
                    post(db, session, org, request.api_user.id, row, data, now)
                row["revision"] += 1
                db.manufacturing_orders.replace_one(scope, row, session=session)
            db.manufacturing_events.insert_one(
                dict(
                    _id=key,
                    organization=org,
                    order=target,
                    revision=row["revision"],
                    actor=request.api_user.id,
                    at=now,
                    action=action,
                    digest=digest,
                    entry={k: v for k, v in data.items() if k != "request_key"},
                ),
                session=session,
            )
            return str(target)

        with db.client.start_session() as session:
            result = session.with_transaction(execute)
        return R.success(data={"id": result}, request=request)
    except (ValueError, KeyError, TypeError) as exc:
        return R.error(
            code="MANUFACTURING_INPUT", message=str(exc), status=400, request=request
        )
    except (PyMongoError, NotImplementedError):
        return R.error(
            code="MANUFACTURING_DATABASE",
            message="Database transaction unavailable. Refresh the order and retry the same request.",
            status=503,
            request=request,
        )
