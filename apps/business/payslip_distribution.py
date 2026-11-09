"""Private per-employee payslip distribution; never attach multiple salaries to one email."""

from django.views.decorators.http import require_http_methods
from django.core.mail import EmailMessage
from django.core.validators import validate_email
from mongoengine.errors import ValidationError
from apps.core.api.decorators import api_login_required
from apps.core.services.api_response_service import APIResponseService as R
from apps.core.services.user_mailbox_service import delivery_options
from apps.core.services.background_job_service import BackgroundJobService
from .models import BusinessRecord as Record
from .views import permitted, payload
from .print_documents import payslip_pdf


@api_login_required
@require_http_methods(["GET", "POST"])
def distribute(request, run_id):
    if not permitted(request, "payroll.read"):
        return R.forbidden(message="Payroll permission required.", request=request)
    try:
        run = Record.objects(
            organization=request.api_organization, kind="payruns", id=run_id
        ).first()
        if not run or run.data.get("status") not in ("approved", "paid"):
            raise ValueError("Select an approved payroll run.")
        rows = {r["employee_id"]: r for r in run.data["rows"]}
        employees = {
            str(e.id): e
            for e in Record.objects(
                organization=request.api_organization,
                kind="employees",
                id__in=list(rows),
            )
        }
        if request.method == "GET":
            return R.success(
                data={
                    "employees": [
                        {
                            "id": eid,
                            "name": row["employee"].get("name", ""),
                            "email": (
                                employees[eid].data.get("email", "")
                                if eid in employees
                                else ""
                            ),
                            "phone": (
                                employees[eid].data.get("phone", "")
                                if eid in employees
                                else ""
                            ),
                        }
                        for eid, row in rows.items()
                    ]
                },
                request=request,
            )
        if not permitted(request, "payroll.manage"):
            return R.forbidden(
                message="Payroll management permission is required to send bulk payslip emails.",
                request=request,
            )
        ids = payload(request).get("employee_ids")
        if (
            not isinstance(ids, list)
            or not 1 <= len(ids) <= 100
            or any(not isinstance(eid, str) or eid not in rows for eid in ids)
        ):
            raise ValueError("Select 1–100 employees in this payroll.")
        delivery_options(
            request.api_user, request.api_organization
        )  # Verify sender before accepting work.
        queued = []
        skipped = []
        for eid in dict.fromkeys(ids):
            email = (
                employees[eid].data.get("email", "").strip() if eid in employees else ""
            )
            try:
                validate_email(email)
            except Exception:
                skipped.append(
                    {"employee_id": eid, "reason": "Save a valid employee email first."}
                )
                continue
            import hashlib

            key = (
                "payslip:"
                + str(run.id)
                + ":"
                + eid
                + ":"
                + hashlib.sha256(email.encode()).hexdigest()[:16]
            )
            job = BackgroundJobService.create_job(
                organization=request.api_organization,
                created_by=request.api_user,
                job_type="PAYSLIP_EMAIL",
                payload={"run_id": str(run.id), "employee_id": eid, "email": email},
                idempotency_key=key,
            )
            queued.append(
                {"employee_id": eid, "job_id": str(job.id), "status": job.status}
            )
        return R.success(data={"queued": queued, "skipped": skipped}, request=request)
    except (ValueError, TypeError, ValidationError) as e:
        return R.validation_error(message=str(e), request=request)


def execute(*, job):
    from apps.authorization.services import AuthorizationService

    if not job.created_by.is_active or not AuthorizationService.has_permission(
        job.created_by, "payroll.manage"
    ):
        raise PermissionError("Sender no longer has payroll access.")
    run = Record.objects(
        organization=job.organization, kind="payruns", id=job.payload["run_id"]
    ).first()
    if not run or run.data.get("status") not in ("approved", "paid"):
        raise ValueError("Payroll is no longer approved.")
    row = next(
        (r for r in run.data["rows"] if r["employee_id"] == job.payload["employee_id"]),
        None,
    )
    employee = Record.objects(
        organization=job.organization, kind="employees", id=job.payload["employee_id"]
    ).first()
    if (
        not row
        or not employee
        or employee.data.get("email", "").strip() != job.payload["email"]
    ):
        raise ValueError("Employee email changed. Review and queue the payslip again.")
    # A separate receipt prevents ordinary retries re-sending an already delivered payslip.
    from mongoengine.connection import get_db

    receipts = get_db().payslip_delivery_receipts
    if receipts.find_one({"_id": job.idempotency_key, "sent": True}):
        return {"sent_count": 1, "already_sent": True}
    message = EmailMessage(
        subject=f"Payslip {run.key} - {job.organization.name}",
        body=f'Hello {row["employee"].get("name", "")},\n\nYour payslip for {run.key} is attached.\n\n{job.organization.name}',
        to=[job.payload["email"]],
        **delivery_options(job.created_by, job.organization),
    )
    message.attach(
        "Payslip-" + run.key + ".pdf",
        payslip_pdf(job.organization, run, row),
        "application/pdf",
    )
    if message.send(fail_silently=False) != 1:
        raise ValueError("Payslip email was not accepted by the email provider.")
    receipts.update_one(
        {"_id": job.idempotency_key},
        {
            "$set": {
                "sent": True,
                "run_id": str(run.id),
                "employee_id": job.payload["employee_id"],
            }
        },
        upsert=True,
    )
    return {"sent_count": 1, "employee_id": job.payload["employee_id"]}
