import bootstrap
import json
import time
import unittest
from datetime import datetime, timedelta
from unittest.mock import patch

from django.contrib.auth.hashers import make_password
from django.test import RequestFactory
from mongoengine.connection import get_db

from apps.organizations.models import Organization
from apps.saas import partners
from apps.saas.models import Membership, PlatformOwner


class Session(dict):
    def cycle_key(self):
        pass


class PartnerProgramTests(unittest.TestCase):
    def setUp(self):
        for name in get_db().list_collection_names():
            get_db().drop_collection(name)
        self.factory = RequestFactory()
        patcher = patch("apps.saas.partners.rate")
        patcher.start(); self.addCleanup(patcher.stop)
        get_db().saas_partners.insert_one({"_id": "p1", "name": "CA Meera Joshi", "email": "meera@ca.in", "password": make_password("Partner#1234"),
                                           "generation": 0, "status": "pending", "email_verified": True, "created_at": datetime.utcnow()})

    def approve(self):
        owner = PlatformOwner(email="owner@example.com", password=make_password("Owner#1234"), totp_secret="unused").save()
        session = Session(nexease_owner={"email": owner.email, "generation": 0, "at": time.time()})
        request = self.factory.post("/", json.dumps({"id": "p1", "action": "approve", "reason": "Identity verified", "password": "Owner#1234", "code": "123456"}), content_type="application/json")
        request.session = session
        with patch("apps.saas.partners.verify_totp", return_value=True):
            response = partners.owner_partners(request)
        self.assertEqual(response.status_code, 200, response.content)
        return get_db().saas_partners.find_one({"_id": "p1"})

    def test_approval_creates_short_readable_code(self):
        row = self.approve()
        code = row["short_code"]
        self.assertRegex(code, r"^NX[A-HJ-KM-NP-Z2-9]{6}$")
        self.assertTrue(row["referral_code"])  # long code kept for existing links
        # Approving again never changes a code partners have already shared.
        self.assertEqual(partners.ensure_short_code(row)["short_code"], code)

    def test_signup_accepts_short_code_any_case_and_long_code(self):
        row = self.approve()
        short = row["short_code"]
        for typed in (short, short.lower(), f"{short[:2]}-{short[2:]}", f" {short} "):
            self.assertEqual(partners.resolve_referral(typed, "owner@shop.in"), "p1", typed)
        self.assertEqual(partners.resolve_referral(row["referral_code"], "owner@shop.in"), "p1")
        with self.assertRaises(ValueError):
            partners.resolve_referral("NXAAAAAA", "owner@shop.in")
        with self.assertRaises(ValueError):
            partners.resolve_referral(short, "MEERA@ca.in")

    def test_pending_partner_gets_no_code(self):
        row = get_db().saas_partners.find_one({"_id": "p1"})
        self.assertNotIn("short_code", partners.ensure_short_code(row))

    def test_dashboard_shows_business_plan_and_status_but_no_amounts(self):
        self.approve()
        now = datetime.utcnow()
        shop = Organization(name="Sharma Traders", email="s@x.in").save()
        trial = Organization(name="Patil Hardware", email="p@x.in").save()
        for org, at in ((shop, now - timedelta(days=3)), (trial, now - timedelta(days=1))):
            get_db().saas_referrals.insert_one({"_id": str(org.id), "partner_id": "p1", "assigned_by": "signup", "assigned_at": at})
        Membership(organization_id=str(shop.id), plan="plus", status="active", start=now - timedelta(days=3), end=now + timedelta(days=27)).save()
        Membership(organization_id=str(trial.id), plan="basic", status="trial", start=now - timedelta(days=1), end=now + timedelta(days=13)).save()
        get_db().saas_payments.insert_one({"_id": "pay1", "organization_id": str(shop.id), "mode": "live", "amount_paise": 34900, "paid_at": 1, "subscription_id": "s"})
        request = self.factory.get("/")
        request.session = Session(nexease_partner={"id": "p1", "generation": 1, "at": time.time()})
        body = json.loads(partners.dashboard(request).content)["data"]
        self.assertTrue(body["partner"]["short_code"].startswith("NX"))
        self.assertEqual(body["referral_total"], 2)
        self.assertEqual(body["paid_total"], 1)
        self.assertEqual([(r["business"], r["plan"], r["status"]) for r in body["referrals"]],
                         [("Patil Hardware", "NexEase", "Trial"), ("Sharma Traders", "NexEase Plus", "Paid")])
        self.assertTrue(all(set(r) == {"reference", "business", "date", "plan", "status"} for r in body["referrals"]))


if __name__ == "__main__":
    unittest.main()
