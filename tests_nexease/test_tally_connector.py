"""End to end: the real connector app ↔ NexEase (full Django stack over HTTP) ↔ a fake Tally over HTTP."""
import bootstrap
import os
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch
from wsgiref.simple_server import WSGIRequestHandler, WSGIServer, make_server
from socketserver import ThreadingMixIn

from django.core.handlers.wsgi import WSGIHandler
from mongoengine.connection import get_db

from apps.business import tally_sync as ts
from apps.organizations.models import Organization
from apps.accounts.models import User
from apps.sales.models import Customer

from fake_tally import FakeTally

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "connector" / "tally"))
import nexease_tally  # noqa: E402


class Quiet(WSGIRequestHandler):
    def log_message(self, *args):
        pass


class ThreadingWSGI(ThreadingMixIn, WSGIServer):
    daemon_threads = True


class ConnectorEndToEnd(unittest.TestCase):
    def setUp(self):
        for name in get_db().list_collection_names():
            get_db().drop_collection(name)
        self.org = Organization(name="Sharma Traders", email="s@example.com").save()
        self.user = User(organization=self.org, email="e2e@example.com", password="x", first_name="A", last_name="B").save()
        self.tally = FakeTally()
        self.tally.add("ledger", "Acme Retail", parent="Sundry Debtors", phone="9876500001")
        self.tally_server = self.tally.serve()
        self.web = make_server("127.0.0.1", 0, WSGIHandler(), server_class=ThreadingWSGI, handler_class=Quiet)
        threading.Thread(target=self.web.serve_forever, daemon=True).start()
        self.home = tempfile.mkdtemp()
        os.environ["NEXEASE_TALLY_HOME"] = self.home
        self.addCleanup(self.web.shutdown)
        self.addCleanup(self.tally_server.shutdown)

    def test_pair_and_sync_both_ways_over_http(self):
        code = ts.new_pairing_code(str(self.org.id), self.user)
        server = f"http://127.0.0.1:{self.web.server_port}/api/v1"
        tally = f"http://127.0.0.1:{self.tally_server.server_port}"
        with patch.object(ts, "PROBE_SECONDS", -1), patch("django.conf.settings.ALLOWED_HOSTS", ["*"]):
            self.assertEqual(nexease_tally.main(["--pair", code, "--server", server, "--tally", tally, "--once"]), 0)
            self.assertEqual(nexease_tally.main(["--once"]), 0)
            self.assertTrue(Customer.objects(organization=self.org, name="Acme Retail").first())
            ts.save_settings(str(self.org.id), {"push_from": __import__("datetime").datetime(2020, 1, 1)})
            Customer(organization=self.org, name="Walk-in Buyer", code="C-1").save()
            for _ in range(3):
                self.assertEqual(nexease_tally.main(["--once"]), 0)
        self.assertEqual(self.tally.by_name("ledger", "Walk-in Buyer")["fields"]["parent"], "Sundry Debtors")
        device = get_db().tally_devices.find_one()
        self.assertEqual(device["info"]["tally_ok"], "True")
        self.assertTrue(any("gzip" not in r for r in self.tally.requests))


if __name__ == "__main__":
    unittest.main()
