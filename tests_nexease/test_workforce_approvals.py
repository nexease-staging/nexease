import bootstrap
import json
import unittest
from datetime import date, timedelta
from unittest.mock import patch
from uuid import uuid4

from django.test import RequestFactory
from mongoengine.connection import get_db

from apps.accounts.models import User
from apps.business import workforce_approvals as wa
from apps.business.models import BusinessAudit, BusinessRecord as Record
from apps.business.views import key_for, validate
from apps.organizations.models import Organization


def unwrap(view):
    while hasattr(view, "__wrapped__"):
        view = view.__wrapped__
    return view


class ApprovalTests(unittest.TestCase):
    def setUp(self):
        for name in get_db().list_collection_names():
            get_db().drop_collection(name)
        self.org = Organization(name="Crew org", email="c@example.com").save()
        self.other = Organization(name="Other", email="o@example.com").save()
        self.user = User(organization=self.org, email=uuid4().hex + "@example.com", password="x", first_name="A", last_name="B").save()
        self.allowed = None
        patcher = patch("apps.authorization.services.AuthorizationService.has_permission",
                        side_effect=lambda user, code: self.allowed is None or code in self.allowed)
        patcher.start(); self.addCleanup(patcher.stop)
        self.today = wa.today_ist()
        self.ravi = self.record("employees", {"name": "Ravi Kumar", "code": "E1", "joining_date": "2025-01-01", "basis": "daily", "rate": "800", "active": True, "employment_type": "site"})
        self.asha = self.record("employees", {"name": "Asha Patil", "code": "E2", "joining_date": "2025-01-01", "basis": "monthly", "rate": "24000", "active": True, "employment_type": "inhouse"})
        self.site = self.record("sites", {"name": "Hinjewadi tower", "code": "S1", "start_date": "2025-01-01", "active": True, "billing_rate": "1200"})
        day = self.today.isoformat()
        self.record("assignments", {"employee_id": str(self.ravi.id), "site_id": str(self.site.id), "start_date": "2025-01-01", "end_date": (self.today + timedelta(days=30)).isoformat(), "shift": "Day", "status": "active", "billing_rate": "1200"})
        self.leave = self.record("leave_requests", {"employee_id": str(self.asha.id), "start_date": day, "end_date": day, "leave_type": "casual", "days": "1", "status": "requested"})
        self.sheet = self.record("timesheets", {"employee_id": str(self.ravi.id), "site_id": str(self.site.id), "date": day, "shift": "Day", "hours": "8", "billable_units": "1", "billing_rate": "1200", "status": "draft"})
        # Another organisation's pending leave must never show.
        stranger = Record(organization=self.other, kind="employees", key="X", data={"name": "X"}, created_by=self.user).save()
        Record(organization=self.other, kind="leave_requests", key="L", created_by=self.user,
               data={"employee_id": str(stranger.id), "start_date": day, "end_date": day, "leave_type": "paid", "days": "1", "status": "requested"}).save()

    def record(self, kind, data):
        clean = validate(kind, data, self.org)
        return Record(organization=self.org, kind=kind, key=key_for(kind, clean), data=clean, created_by=self.user).save()

    def call(self, method="get", body=None):
        factory = RequestFactory()
        request = factory.get("/") if method == "get" else factory.post("/", data=json.dumps(body), content_type="application/json")
        request.api_user, request.api_organization = self.user, self.org
        response = unwrap(wa.approvals)(request)
        return response.status_code, json.loads(response.content)

    def test_inbox_lists_pending_items_with_names(self):
        status, body = self.call()
        self.assertEqual(status, 200)
        data = body["data"]
        self.assertEqual([x["employee"]["name"] for x in data["leave"]], ["Asha Patil"])
        self.assertEqual(data["timesheets"][0]["site"]["name"], "Hinjewadi tower")
        self.assertEqual(data["on_leave_today"], [])
        self.assertTrue(data["can_manage"]["timesheets"])

    def test_approve_leave_and_timesheet_with_audit(self):
        status, body = self.call("post", {"kind": "leave_requests", "ids": [str(self.leave.id)], "status": "approved"})
        self.assertEqual(status, 200, body)
        self.assertEqual(self.leave.reload().data["status"], "approved")
        self.assertEqual(self.leave.revision, 2)
        self.assertEqual(body["message"], "Approved 1.")
        _, inbox = self.call()
        self.assertEqual([x["employee"] for x in inbox["data"]["on_leave_today"]], ["Asha Patil"])
        status, body = self.call("post", {"kind": "timesheets", "ids": [str(self.sheet.id)], "status": "approved"})
        self.assertEqual(self.sheet.reload().data["status"], "approved")
        self.assertEqual(BusinessAudit.objects(organization=self.org).count(), 2)

    def test_partial_failures_are_reported_per_item(self):
        self.call("post", {"kind": "leave_requests", "ids": [str(self.leave.id)], "status": "rejected"})
        status, body = self.call("post", {"kind": "leave_requests", "ids": [str(self.leave.id), "bad-id", str(self.sheet.id)], "status": "approved"})
        self.assertEqual(status, 200)
        self.assertEqual(body["data"]["updated"], [])
        self.assertEqual([f["message"] for f in body["data"]["failed"]], ["Already rejected.", "Not found.", "Not found."])
        self.assertEqual(self.leave.reload().data["status"], "rejected")

    def test_validation_and_permissions(self):
        self.assertEqual(self.call("post", {"kind": "employees", "ids": ["x"], "status": "approved"})[0], 400)
        self.assertEqual(self.call("post", {"kind": "timesheets", "ids": [str(self.sheet.id)], "status": "rejected"})[0], 400)
        self.assertEqual(self.call("post", {"kind": "timesheets", "ids": [], "status": "approved"})[0], 400)
        self.allowed = {"payroll.read", "labour.read"}
        self.assertEqual(self.call("post", {"kind": "leave_requests", "ids": [str(self.leave.id)], "status": "approved"})[0], 403)
        self.allowed = {"labour.read"}
        _, body = self.call()
        self.assertEqual(body["data"]["leave"], [])
        self.assertEqual(len(body["data"]["timesheets"]), 1)

    def test_locked_payroll_month_blocks_approval(self):
        Record(organization=self.org, kind="payruns", key=self.today.strftime("%Y-%m"), created_by=self.user,
               data={"status": "approved", "month": self.today.strftime("%Y-%m"),
                     "rows": [{"employee_id": str(self.asha.id), "source": {"mode": "automatic"}}]}).save()
        status, body = self.call("post", {"kind": "leave_requests", "ids": [str(self.leave.id)], "status": "approved"})
        self.assertEqual(status, 200)
        self.assertEqual(len(body["data"]["failed"]), 1)
        self.assertEqual(self.leave.reload().data["status"], "requested")


if __name__ == "__main__":
    unittest.main()
