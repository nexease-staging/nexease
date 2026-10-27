from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

from bson import ObjectId
from django.test import SimpleTestCase

from apps.accounts.models import User
from apps.core.background_job_models import (
    BackgroundJob,
)
from apps.core.services.background_job_service import (
    BackgroundJobService,
)
from apps.finance.background_jobs import (
    execute_document_email,
)
from apps.finance.services.document_api_service import (
    DocumentAPIService,
)
from apps.organizations.models import Organization

from apps.finance.models import (
    DocumentDeliveryLog,
)
from apps.finance.services.document_attachment_service import (
    DocumentAttachmentService,
)
from apps.finance.services.document_email_delivery_service import (
    DocumentEmailDeliveryService,
)

class Day53DocumentEmailIsolationTests(
    SimpleTestCase,
):

    def setUp(self):
        self.test_key = uuid4().hex

        self.organization = Organization(
            name=(
                "Day 53 Document Email "
                f"{self.test_key}"
            ),
            email=(
                f"day53-document-"
                f"{self.test_key}"
                "@example.com"
            ),
        )
        self.organization.save()

        self.user = User(
            organization=self.organization,
            email=(
                f"day53-document-user-"
                f"{self.test_key}"
                "@example.com"
            ),
            password="day53-test-password",
            first_name="Day",
            last_name="FiftyThree",
            is_active=True,
        )
        self.user.save()

    def tearDown(self):
        DocumentDeliveryLog.objects(
            organization=self.organization,
        ).delete()

        BackgroundJob.objects(
            organization=self.organization,
        ).delete()

        User.objects(
            organization=self.organization,
        ).delete()

        self.organization.delete()

    def _create_job(
        self,
        *,
        suffix,
        payload=None,
    ):
        if payload is None:
            payload = {
                "document_type":
                    "INVOICE",
                "document_id":
                    str(ObjectId()),
                "recipient_email":
                    "customer@example.com",
                "subject":
                    "Day 53 Invoice",
                "message":
                    "Please find your invoice.",
            }

        return (
            BackgroundJobService
            .create_job(
                organization=
                    self.organization,
                created_by=
                    self.user,
                job_type=
                    "DOCUMENT_EMAIL",
                payload=payload,
                idempotency_key=(
                    "DOCUMENT_EMAIL:"
                    f"{self.test_key}:"
                    f"{suffix}"
                ),
            )
        )

    # ==========================================
    # TRUSTED JOB CONTEXT
    # ==========================================

    def test_handler_passes_job_context_and_idempotency_key_to_service(
        self,
    ):
        job = self._create_job(
            suffix="context",
        )

        delivery = SimpleNamespace(
            id=ObjectId(),
            recipient=
                "customer@example.com",
            status="SENT",
        )

        with patch.object(
            DocumentAPIService,
            "send_email",
            return_value={
                "delivery":
                    delivery,
                "recipient":
                    delivery.recipient,
                "sent_count":
                    1,
            },
        ) as send_mock:

            result = (
                execute_document_email(
                    job=job,
                )
            )

        send_mock.assert_called_once_with(
            user=self.user,
            organization=
                self.organization,
            document_type=
                job.payload[
                    "document_type"
                ],
            document_id=
                job.payload[
                    "document_id"
                ],
            recipient_email=
                job.payload[
                    "recipient_email"
                ],
            subject=
                job.payload[
                    "subject"
                ],
            message=
                job.payload[
                    "message"
                ],
            background_job_key=
                job.idempotency_key,
        )

        self.assertEqual(
            result[
                "delivery_id"
            ],
            str(delivery.id),
        )

        self.assertEqual(
            result[
                "delivery_status"
            ],
            "SENT",
        )

        self.assertEqual(
            result[
                "sent_count"
            ],
            1,
        )

    # ==========================================
    # REPLAY KEY STABILITY
    # ==========================================

    def test_handler_replay_uses_same_background_job_key(
        self,
    ):
        job = self._create_job(
            suffix="replay",
        )

        delivery = SimpleNamespace(
            id=ObjectId(),
            recipient=
                "customer@example.com",
            status="SENT",
        )

        with patch.object(
            DocumentAPIService,
            "send_email",
            return_value={
                "delivery":
                    delivery,
                "recipient":
                    delivery.recipient,
                "sent_count":
                    1,
            },
        ) as send_mock:

            first_result = (
                execute_document_email(
                    job=job,
                )
            )

            second_result = (
                execute_document_email(
                    job=job,
                )
            )

        self.assertEqual(
            send_mock.call_count,
            2,
        )

        first_call = (
            send_mock.call_args_list[
                0
            ].kwargs
        )

        second_call = (
            send_mock.call_args_list[
                1
            ].kwargs
        )

        self.assertEqual(
            first_call[
                "background_job_key"
            ],
            job.idempotency_key,
        )

        self.assertEqual(
            second_call[
                "background_job_key"
            ],
            job.idempotency_key,
        )

        self.assertEqual(
            first_result,
            second_result,
        )

    # ==========================================
    # MISSING DOCUMENT
    # ==========================================

    def test_handler_rejects_missing_document(
        self,
    ):
        job = self._create_job(
            suffix="missing",
        )

        with patch.object(
            DocumentAPIService,
            "send_email",
            return_value=None,
        ):
            with self.assertRaises(
                LookupError
            ):
                execute_document_email(
                    job=job,
                )

    # ==========================================
    # PAYLOAD VALIDATION
    # ==========================================

    def test_handler_rejects_missing_document_type_before_service_call(
        self,
    ):
        job = self._create_job(
            suffix="no-type",
            payload={
                "document_id":
                    str(ObjectId()),
            },
        )

        with patch.object(
            DocumentAPIService,
            "send_email",
        ) as send_mock:

            with self.assertRaisesRegex(
                ValueError,
                "Document type is required",
            ):
                execute_document_email(
                    job=job,
                )

        send_mock.assert_not_called()

    def test_handler_rejects_missing_document_id_before_service_call(
        self,
    ):
        job = self._create_job(
            suffix="no-id",
            payload={
                "document_type":
                    "INVOICE",
            },
        )

        with patch.object(
            DocumentAPIService,
            "send_email",
        ) as send_mock:

            with self.assertRaisesRegex(
                ValueError,
                "Document ID is required",
            ):
                execute_document_email(
                    job=job,
                )

        send_mock.assert_not_called()

    # ==========================================
    # REAL DELIVERY REPLAY IDEMPOTENCY
    # ==========================================

    def test_successful_delivery_replay_does_not_send_email_twice(
        self,
    ):
        background_job_key = (
            "DOCUMENT_EMAIL:"
            f"{self.test_key}:"
            "real-replay"
        )

        document = SimpleNamespace(
            id=ObjectId(),
        )

        message_data = {
            "subject":
                "Day 53 Replay Test",
            "body":
                "Replay-safe email body.",
        }

        attachment = {
            "filename":
                "invoice.pdf",
            "content":
                b"%PDF-day53-test",
            "content_type":
                "application/pdf",
        }

        with (
            patch.object(
                DocumentAttachmentService,
                "generate",
                return_value=attachment,
            ) as attachment_mock,

            patch(
                "apps.finance.services."
                "document_email_delivery_service."
                "EmailMessage.send",
                return_value=1,
            ) as send_mock,
        ):
            first_result = (
                DocumentEmailDeliveryService
                .send(
                    user=self.user,
                    organization=
                        self.organization,
                    document_type=
                        "INVOICE",
                    document=document,
                    document_id=
                        str(document.id),
                    document_number=
                        "INV-DAY53-001",
                    recipient_email=
                        "customer@example.com",
                    recipient_name=
                        "Day 53 Customer",
                    message_data=
                        message_data,
                    background_job_key=(
                        background_job_key
                    ),
                )
            )

            second_result = (
                DocumentEmailDeliveryService
                .send(
                    user=self.user,
                    organization=
                        self.organization,
                    document_type=
                        "INVOICE",
                    document=document,
                    document_id=
                        str(document.id),
                    document_number=
                        "INV-DAY53-001",
                    recipient_email=
                        "customer@example.com",
                    recipient_name=
                        "Day 53 Customer",
                    message_data=
                        message_data,
                    background_job_key=(
                        background_job_key
                    ),
                )
            )

        first_delivery = (
            first_result[
                "delivery"
            ]
        )

        second_delivery = (
            second_result[
                "delivery"
            ]
        )

        self.assertEqual(
            str(first_delivery.id),
            str(second_delivery.id),
        )

        self.assertEqual(
            first_delivery.status,
            "SENT",
        )

        second_delivery.reload()

        self.assertEqual(
            second_delivery.status,
            "SENT",
        )

        self.assertIsNotNone(
            second_delivery.sent_at
        )

        self.assertEqual(
            DocumentDeliveryLog.objects(
                organization=
                    self.organization,
                background_job_key=(
                    background_job_key
                ),
                channel="EMAIL",
            ).count(),
            1,
        )

        self.assertEqual(
            send_mock.call_count,
            1,
        )

        self.assertEqual(
            attachment_mock.call_count,
            1,
        )

        self.assertEqual(
            first_result[
                "sent_count"
            ],
            1,
        )

        self.assertEqual(
            second_result[
                "sent_count"
            ],
            1,
        )

        self.assertIsNotNone(
            first_result[
                "email"
            ]
        )

        self.assertIsNone(
            second_result[
                "email"
            ]
        )

        self.assertIsNotNone(
            first_result[
                "attachment"
            ]
        )

        self.assertIsNone(
            second_result[
                "attachment"
            ]
        )