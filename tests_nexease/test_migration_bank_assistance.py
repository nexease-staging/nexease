import bootstrap
import unittest
from datetime import datetime
from types import SimpleNamespace
from apps.migration.services.import_dates import calendar_date
from apps.migration.services.migration_file_parser import MigrationFileParser
from apps.finance.services.statement_suggestions import suggest


class ImportTests(unittest.TestCase):
    def test_dates(self):
        for text in ("2026-11-03T00:00:00", "03/11/2026 00:00:00", "3 Nov 2026", "03.11.2026"):
            self.assertEqual(calendar_date(text).isoformat(), "2026-11-03")
        with self.assertRaises(ValueError):
            calendar_date("31/02/2026")

    def test_csv_separator(self):
        for sep in (";", ",", "\t", "|"):
            rows = MigrationFileParser.read_rows(filename="units.csv", content=f"sku{sep}unit\n001{sep}Box\n".encode())
            self.assertIn("001", str(rows))

    def test_narration_and_duplicate_reference(self):
        def entry(description, reference=""):
            return SimpleNamespace(description=description, external_reference=reference, transaction_date=datetime(2026,11,3))
        line = entry("UPI Alpha Tools")
        a, b = entry("Alpha Tools UPI"), entry("Beta Foods UPI")
        self.assertIs(suggest(line, [a,b])[0], a)
        self.assertIsNone(suggest(line, [a,a]))
        line.external_reference = a.external_reference = b.external_reference = "UTR12"
        self.assertIsNone(suggest(line, [a,b]))

    def test_confirm_once_updates_correct_embedded_line(self):
        from bson import ObjectId
        from apps.organizations.models import Organization
        from apps.accounts.models import User
        from apps.finance.models import BankTransaction, BankStatement, BankAccount, BankStatementLine
        from apps.finance.services.bank_statement_service import BankStatementService
        from unittest.mock import patch
        from decimal import Decimal
        org = Organization(id=ObjectId(), name="Import test").save(validate=False)
        user = User(id=ObjectId(), organization=org, is_active=True).save(validate=False)
        account = BankAccount(id=ObjectId(), organization=org).save(validate=False)
        now = datetime(2026,11,3)
        tx = BankTransaction(organization=org, bank_account=account, transaction_number="BT-1",
                             transaction_type="MONEY_IN", amount=Decimal("8"),transaction_date=now).save(validate=False)
        lines = [BankStatementLine(line_number=str(i), transaction_date=now, credit_amount=Decimal("8")) for i in (1,2)]
        statement = BankStatement(organization=org, statement_number="BS-1", bank_account=account,
                                  lines=lines, created_by=user, opening_balance=0,closing_balance=16,
                                  statement_start_date=now,statement_end_date=now,source_type="CSV").save(validate=False)
        with patch.object(User,"has_permission",return_value=True):
            BankStatementService.apply_match(user=user,organization=org,statement=statement,line=statement.lines[1],transaction=tx)
            statement.reload()
            self.assertEqual([l.match_status for l in statement.lines],["UNMATCHED","MATCHED"])
            self.assertEqual(tx.reload().reconciliation_status,"RECONCILED")
            with self.assertRaises(ValueError):
                BankStatementService.apply_match(user=user,organization=org,statement=statement,line=statement.lines[0],transaction=tx)
