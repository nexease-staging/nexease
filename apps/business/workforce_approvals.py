"""Workforce approvals inbox: pending leave and draft timesheets, approved in one tap or in bulk.

GET  /api/v1/business/workforce/approvals/    pending items with employee and site names, plus today's snapshot
POST /api/v1/business/workforce/approvals/    {kind: leave_requests|timesheets, ids:[...], status}

Each change goes through the same validate(), payroll-lock guard, revision check and audit as a
normal record save, under the same workforce write lock. Items that fail are reported one by one;
the others are still saved.
"""

from datetime import date, datetime, timedelta

from django.views.decorators.http import require_http_methods
from mongoengine.errors import ValidationError

from apps.core.api.decorators import api_login_required
from apps.core.services.api_response_service import APIResponseService as R

from .automation import write_lock
from .models import BusinessRecord as Record
from .views import audit, key_for, payload, permitted, serialize, validate

MAX_IDS = 100
FLOWS = {
    # kind: (permission, pending status, allowed new statuses)
    "leave_requests": ("payroll", "requested", ("approved", "rejected")),
    "timesheets": ("labour", "draft", ("approved",)),
}
IST = timedelta(hours=5, minutes=30)


def today_ist():
    return (datetime.utcnow() + IST).date()


def names(org, kind, ids):
    ids = [i for i in ids if i]
    if not ids:
        return {}
    return {str(r.id): {"name": r.data.get("name", ""), "code": r.data.get("code", "")}
            for r in Record.objects(organization=org, kind=kind, id__in=ids).only("id", "data")}


@api_login_required
@require_http_methods(["GET", "POST"])
@write_lock
def approvals(request):
    org = request.api_organization
    if not getattr(org, "workforce_enabled", True):
        return R.forbidden(message="Workforce is disabled by your organisation administrator.", request=request)
    if request.method == "GET":
        return inbox(request, org)
    try:
        p = payload(request)
        kind = p.get("kind")
        if kind not in FLOWS:
            raise ValueError("Choose leave or timesheets.")
        permission, pending, allowed = FLOWS[kind]
        if not permitted(request, permission + ".manage"):
            return R.forbidden(message="Permission denied.", request=request)
        status = p.get("status")
        if status not in allowed:
            raise ValueError("Choose " + " or ".join(allowed) + ".")
        ids = p.get("ids")
        if not isinstance(ids, list) or not ids or len(ids) > MAX_IDS:
            raise ValueError(f"Choose between 1 and {MAX_IDS} items.")
        ids = list(dict.fromkeys(str(i) for i in ids))
    except ValueError as exc:
        return R.validation_error(message=str(exc), request=request)

    done, failed = [], []
    for record_id in ids:
        try:
            record = Record.objects(id=record_id, organization=org, kind=kind).first()
        except ValidationError:
            record = None
        if not record:
            failed.append({"id": record_id, "message": "Not found."})
            continue
        if record.data.get("status") != pending:
            failed.append({"id": record_id, "message": f"Already {record.data.get('status', 'changed')}."})
            continue
        try:
            data = validate(kind, {**record.data, "status": status}, org, record_id)
            saved = Record.objects(id=record.id, organization=org, revision=record.revision).modify(
                new=True, set__data=data, set__key=key_for(kind, data), inc__revision=1, set__updated_at=datetime.utcnow())
            if not saved:
                failed.append({"id": record_id, "message": "Changed by someone else. Reload and try again."})
                continue
            audit(request, kind, saved.id, "PATCH")
            done.append(serialize(saved))
        except (ValueError, ValidationError) as exc:
            failed.append({"id": record_id, "message": str(exc)})
    word = {"approved": "Approved", "rejected": "Rejected"}[status]
    message = f"{word} {len(done)} of {len(ids)}." if failed else f"{word} {len(done)}."
    return R.success(data={"updated": done, "failed": failed}, message=message, request=request)


def inbox(request, org):
    can_payroll, can_labour = permitted(request, "payroll.read"), permitted(request, "labour.read")
    if not (can_payroll or can_labour):
        return R.forbidden(message="Workforce permission required.", request=request)
    today = today_ist().isoformat()
    leave = list(Record.objects(organization=org, kind="leave_requests", data__status="requested").order_by("data.start_date").limit(200)) if can_payroll else []
    sheets = list(Record.objects(organization=org, kind="timesheets", data__status="draft").order_by("data.date").limit(200)) if can_labour else []
    people = names(org, "employees", {r.data.get("employee_id") for r in leave + sheets})
    sites = names(org, "sites", {r.data.get("site_id") for r in sheets})
    on_leave = []
    if can_payroll:
        approved = Record.objects(organization=org, kind="leave_requests", data__status="approved", data__start_date__lte=today, data__end_date__gte=today).limit(200)
        on_leave_people = names(org, "employees", {r.data.get("employee_id") for r in approved})
        on_leave = [{"id": str(r.id), "employee": on_leave_people.get(r.data.get("employee_id"), {}).get("name", ""),
                     "until": r.data.get("end_date"), "leave_type": r.data.get("leave_type")} for r in approved]
    person = lambda r: people.get(r.data.get("employee_id"), {"name": "", "code": ""})
    return R.success(data={
        "today": today,
        "can_manage": {"leave_requests": permitted(request, "payroll.manage"), "timesheets": permitted(request, "labour.manage")},
        "leave": [{**serialize(r), "employee": person(r)} for r in leave],
        "timesheets": [{**serialize(r), "employee": person(r), "site": sites.get(r.data.get("site_id"), {"name": "In-house", "code": ""})} for r in sheets],
        "on_leave_today": on_leave,
    }, request=request)
