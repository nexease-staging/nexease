"""Read-only operational dashboard totals scoped to the authenticated organization."""
from datetime import date, datetime, time, timedelta

from decimal import Decimal
from collections import defaultdict
from bson import ObjectId

from django.views.decorators.http import require_GET
from mongoengine.connection import get_db
from apps.core.api.decorators import api_login_required
from apps.core.services.api_response_service import APIResponseService as R
from .views import permitted


@api_login_required
@require_GET
def insights(request, section):
    org = request.api_organization.id
    db = get_db()
    result = {}
    try:
        start = date.fromisoformat(request.GET.get("from", ""))
        end = date.fromisoformat(request.GET.get("to", ""))
        if end < start or (end - start).days > 366:
            raise ValueError
        period = {"$gte": datetime.combine(start, time.min),
                  "$lt": datetime.combine(end + timedelta(days=1), time.min)}
    except (ValueError, OverflowError):
        return R.error(code="INVALID_PERIOD", message="Select a range of 1–367 days.", status=400, request=request)

    if section == "collections" and permitted(request, "customer_payments.read"):
        rows = list(db.customer_payments.aggregate([
            {"$match": {"organization": org, "payment_date": period}},
            {"$group": {"_id": None, "amount": {"$sum": {"$toDecimal": "$amount"}}}},
        ]))
        result["collections"] = str(rows[0]["amount"]) if rows else "0"
    if section == "purchase" and permitted(request, "purchase_orders.read"):
        result["open_orders"] = db.purchase_orders.count_documents({
            "organization": org, "status": {"$in": ["DRAFT", "CONFIRMED", "PARTIALLY_RECEIVED"]}})
    if section == "sales" and permitted(request, "invoices.read") and permitted(request, "credit_notes.read"):
        def net_sales(collection, date_field, statuses):
            group = {"$sum": {"$subtract": [{"$toDecimal": "$total_amount"},
                                             {"$toDecimal": "$tax_amount"}]}}
            rows = list(collection.aggregate([
                {"$match": {"organization": org, date_field: period, "status": {"$in": statuses}}},
                {"$group": {"_id": None, "net": group}},
            ]))
            return rows[0]["net"].to_decimal() if rows else Decimal(0)
        result["net_sales"] = str(net_sales(db.invoices, "invoice_date", ["ISSUED", "PAID", "PARTIALLY_PAID"])
                                  - net_sales(db.credit_notes, "credit_note_date", ["ISSUED"]))
    if section == "production" and permitted(request, "manufacturing.read"):
        today = date.today()
        active = {"organization": org, "status": {"$ne": "completed"}}
        result["late"] = db.manufacturing_orders.count_documents({**active, "due": {"$lt": today.isoformat()}})
        result["soon"] = db.manufacturing_orders.count_documents({**active, "due": {
            "$gte": today.isoformat(), "$lte": (today + timedelta(days=7)).isoformat()}})
        units = defaultdict(lambda: [Decimal(0), Decimal(0)])
        variance = Decimal(0)
        for job in db.manufacturing_orders.find({"organization": org, "due": {
                "$gte": start.isoformat(), "$lte": end.isoformat()}}, {"outputs": 1}):
            for line in job["outputs"]:
                totals = units[line["unit"]]
                totals[0] += Decimal(line["accepted"])
                totals[1] += Decimal(line["rejected"])
                variance += sum((Decimal(m["value"]) for m in line["materials"]),
                                Decimal(line["expenses"])) - Decimal(line["estimate"])
        result["units"] = {unit: [str(a), str(r)] for unit, (a, r) in units.items()}
        result["variance"] = str(variance)
        if permitted(request, "inventory.read"):
            demand = defaultdict(Decimal)
            for job in db.manufacturing_orders.find(active, {"warehouse": 1, "outputs": 1}):
                for line in job["outputs"]:
                    for material in line["materials"]:
                        held = sum((Decimal(b["materials"].get(material["product"], {}).get("allocated", 0))
                                    for b in line.get("batches", []) if not b["posted"]), Decimal(0))
                        demand[job["warehouse"], material["product"]] += max(Decimal(0),
                            Decimal(material["required"]) - Decimal(material["issued"]) - held)
            shortages = 0
            for (warehouse, product), required in demand.items():
                stock = db.inventory.find_one({"organization": org, "warehouse": ObjectId(warehouse),
                                               "product": ObjectId(product)}, {"quantity": 1, "reserved_quantity": 1}) or {}
                available = Decimal(str(stock.get("quantity", 0))) - Decimal(str(stock.get("reserved_quantity", 0)))
                shortages += required > max(available, Decimal(0))
            result["shortages"] = shortages
    if section == "banking":
        if permitted(request, "bank_statements.read"):
            active = {"organization": org, "status": {"$ne": "CANCELLED"}}
            rows = list(db.bank_statements.aggregate([
                {"$match": active}, {"$unwind": "$lines"},
                {"$match": {"lines.match_status": "UNMATCHED"}}, {"$count": "count"},
            ]))
            result["unmatched"] = rows[0]["count"] if rows else 0
            last = db.bank_statements.find_one({**active, "reconciled_at": {"$type": "date"}},
                                              {"reconciled_at": 1}, sort=[("reconciled_at", -1)])
            result["last_reconciliation"] = last["reconciled_at"].date().isoformat() if last else "None recorded"
        if permitted(request, "bank_transactions.read"):
            result["book_unmatched"] = db.bank_transactions.count_documents(
                {"organization": org, "reconciliation_status": "UNRECONCILED"})
    if section == "workforce":
        today = date.today().isoformat()
        records = db.nexease_business_records
        if permitted(request, "labour.read"):
            approved = {"organization": org, "kind": "timesheets", "data.status": "approved"}
            result["present"] = len(records.distinct("data.employee_id", {**approved, "data.date": today}))
            overtime = list(records.aggregate([
                {"$match": {**approved, "data.date": {"$gte": start.isoformat(), "$lte": end.isoformat()}}},
                {"$group": {"_id": None, "hours": {"$sum": {"$toDecimal": {"$ifNull": ["$data.overtime_hours", "0"]}}}}},
            ]))
            result["ot"] = str(overtime[0]["hours"]) if overtime else "0"
        if permitted(request, "payroll.read"):
            result["leave"] = len(records.distinct("data.employee_id", {
                "organization": org, "kind": "leave_requests", "data.status": "approved",
                "data.start_date": {"$lte": today}, "data.end_date": {"$gte": today}}))
    if not result:
        return R.forbidden(message="Permission required to view this section.", request=request)
    return R.success(data=result, request=request)
