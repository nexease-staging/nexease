from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

from bson import ObjectId
from django.core.files.uploadedfile import (
    SimpleUploadedFile,
)
from django.test import SimpleTestCase

from apps.accounts.models import User
from apps.core.background_job_models import (
    BackgroundJob,
)
from apps.core.background_upload_models import (
    BackgroundUpload,
)
from apps.core.services.background_job_service import (
    BackgroundJobService,
)
from apps.core.services.background_upload_service import (
    BackgroundUploadService,
)
from apps.finance.background_jobs import (
    execute_bank_statement_import,
)
from apps.finance.services.bank_statement_api_service import (
    BankStatementAPIService,
)
from apps.organizations.models import Organization


class Day53BankImportIsolationTests(
    SimpleTestCase,
):

    def setUp(self):
        self.test_key = uuid4().hex

        self.organization_a = Organization(
            name=(
                "Day 53 Bank Import A "
                f"{self.test_key}"
            ),
            email=(
                f"day53-bank-a-{self.test_key}"
                "@example.com"
            ),
        )
        self.organization_a.save()

        self.organization_b = Organization(
            name=(
                "Day 53 Bank Import B "
                f"{self.test_key}"
            ),
            email=(
                f"day53-bank-b-{self.test_key}"
                "@example.com"
            ),
        )
        self.organization_b.save()

        self.user_a = self._create_user(
            organization=self.organization_a,
            email=(
                f"day53-bank-user-a-"
                f"{self.test_key}"
                "@example.com"
            ),
        )

        self.user_b = self._create_user(
            organization=self.organization_b,
            email=(
                f"day53-bank-user-b-"
                f"{self.test_key}"
                "@example.com"
            ),
        )

    def tearDown(self):
        BackgroundJob.objects(
            organization__in=[
                self.organization_a,
                self.organization_b,
            ]
        ).delete()

        BackgroundUpload.objects(
            organization__in=[
                self.organization_a,
                self.organization_b,
            ]
        ).delete()

        User.objects(
            organization__in=[
                self.organization_a,
                self.organization_b,
            ]
        ).delete()

        self.organization_a.delete()
        self.organization_b.delete()

    def _create_user(
        self,
        *,
        organization,
        email,
    ):
        user = User(
            organization=organization,
            email=email,
            password="day53-test-password",
            first_name="Day",
            last_name="FiftyThree",
            is_active=True,
        )
        user.save()

        return user

    def _store_upload(
        self,
        *,
        organization,
        user,
    ):
        uploaded_file = SimpleUploadedFile(
            "statement.csv",
            (
                b"date,description,debit,credit\n"
                b"2026-08-10,"
                b"Customer payment,"
                b"0,250\n"
            ),
            content_type="text/csv",
        )

        return (
            BackgroundUploadService
            .store_bank_statement(
                organization=organization,
                uploaded_by=user,
                uploaded_file=uploaded_file,
            )
        )

    def _create_job(
        self,
        *,
        organization,
        user,
        upload_id,
        suffix,
        bank_account_id=None,
    ):
        return (
            BackgroundJobService
            .create_job(
                organization=organization,
                created_by=user,
                job_type=(
                    "BANK_STATEMENT_IMPORT"
                ),
                payload={
                    "upload_id":
                        str(upload_id),

                    "bank_account_id": (
                        str(
                            bank_account_id
                            or ObjectId()
                        )
                    ),

                    "statement_start_date":
                        "2026-08-01",

                    "statement_end_date":
                        "2026-08-31",

                    "opening_balance":
                        "1000.00",

                    "closing_balance":
                        "1250.00",
                },
                idempotency_key=(
                    "day53-bank-import:"
                    f"{self.test_key}:"
                    f"{suffix}"
                ),
            )
        )

    # ==========================================
    # SUCCESS + CONSUMPTION
    # ==========================================

    def test_successful_execution_consumes_upload_and_stores_statement_result(
        self,
    ):
        upload = self._store_upload(
            organization=
                self.organization_a,
            user=self.user_a,
        )

        job = self._create_job(
            organization=
                self.organization_a,
            user=self.user_a,
            upload_id=upload.id,
            suffix="success",
        )

        statement_id = ObjectId()

        statement = SimpleNamespace(
            id=statement_id,
        )

        with patch.object(
            BankStatementAPIService,
            "create_statement",
            return_value=statement,
        ) as create_mock:
            result = (
                execute_bank_statement_import(
                    job=job,
                )
            )

        self.assertEqual(
            result,
            {
                "bank_statement_id":
                    str(statement_id),
            },
        )

        create_mock.assert_called_once()

        upload.reload()

        self.assertEqual(
            upload.status,
            "CONSUMED",
        )

        self.assertEqual(
            upload.result,
            {
                "bank_statement_id":
                    str(statement_id),
            },
        )

        self.assertIsNotNone(
            upload.consumed_at
        )

    # ==========================================
    # REPLAY IDEMPOTENCY
    # ==========================================

    def test_replay_of_consumed_upload_returns_same_result_without_importing_again(
        self,
    ):
        upload = self._store_upload(
            organization=
                self.organization_a,
            user=self.user_a,
        )

        job = self._create_job(
            organization=
                self.organization_a,
            user=self.user_a,
            upload_id=upload.id,
            suffix="replay",
        )

        statement_id = ObjectId()

        statement = SimpleNamespace(
            id=statement_id,
        )

        with patch.object(
            BankStatementAPIService,
            "create_statement",
            return_value=statement,
        ) as create_mock:

            first_result = (
                execute_bank_statement_import(
                    job=job,
                )
            )

            second_result = (
                execute_bank_statement_import(
                    job=job,
                )
            )

        self.assertEqual(
            first_result,
            second_result,
        )

        self.assertEqual(
            second_result[
                "bank_statement_id"
            ],
            str(statement_id),
        )

        self.assertEqual(
            create_mock.call_count,
            1,
        )

        upload.reload()

        self.assertEqual(
            upload.status,
            "CONSUMED",
        )

    # ==========================================
    # CROSS-TENANT UPLOAD
    # ==========================================

    def test_job_cannot_process_upload_from_another_organization(
        self,
    ):
        foreign_upload = (
            self._store_upload(
                organization=
                    self.organization_b,
                user=self.user_b,
            )
        )

        job = self._create_job(
            organization=
                self.organization_a,
            user=self.user_a,
            upload_id=
                foreign_upload.id,
            suffix=
                "foreign-upload",
        )

        with patch.object(
            BankStatementAPIService,
            "create_statement",
        ) as create_mock:

            with self.assertRaises(
                LookupError
            ):
                (
                    execute_bank_statement_import(
                        job=job,
                    )
                )

        create_mock.assert_not_called()

        foreign_upload.reload()

        self.assertEqual(
            foreign_upload.status,
            "AVAILABLE",
        )

        self.assertEqual(
            foreign_upload.result,
            {},
        )

    # ==========================================
    # CONSUMED WITHOUT RESULT
    # ==========================================

    def test_consumed_upload_without_statement_result_is_not_reprocessed(
        self,
    ):
        upload = self._store_upload(
            organization=
                self.organization_a,
            user=self.user_a,
        )

        upload.status = "CONSUMED"
        upload.result = {}
        upload.save()

        job = self._create_job(
            organization=
                self.organization_a,
            user=self.user_a,
            upload_id=upload.id,
            suffix=(
                "consumed-no-result"
            ),
        )

        with patch.object(
            BankStatementAPIService,
            "create_statement",
        ) as create_mock:

            with self.assertRaises(
                ValueError
            ):
                (
                    execute_bank_statement_import(
                        job=job,
                    )
                )

        create_mock.assert_not_called()

    # ==========================================
    # FAILED IMPORT DOES NOT CONSUME UPLOAD
    # ==========================================

    def test_failed_statement_creation_leaves_upload_available_for_retry(
        self,
    ):
        upload = self._store_upload(
            organization=
                self.organization_a,
            user=self.user_a,
        )

        job = self._create_job(
            organization=
                self.organization_a,
            user=self.user_a,
            upload_id=upload.id,
            suffix="failed-import",
        )

        with patch.object(
            BankStatementAPIService,
            "create_statement",
            side_effect=ValueError(
                "Simulated import failure."
            ),
        ):
            with self.assertRaisesRegex(
                ValueError,
                "Simulated import failure",
            ):
                (
                    execute_bank_statement_import(
                        job=job,
                    )
                )

        upload.reload()

        self.assertEqual(
            upload.status,
            "AVAILABLE",
        )

        self.assertEqual(
            upload.result,
            {},
        )