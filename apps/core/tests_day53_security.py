from datetime import datetime
from unittest.mock import patch
from uuid import uuid4

from django.test import Client, SimpleTestCase

from apps.accounts.models import User
from apps.core.background_job_models import BackgroundJob
from apps.core.notification_models import Notification
from apps.core.services.background_job_service import (
    BackgroundJobService,
)
from apps.core.services.notification_service import (
    NotificationService,
)
from apps.organizations.api_context_service import (
    APIOrganizationContextService,
)
from apps.organizations.models import Organization


class Day53AsyncAPISecurityTests(
    SimpleTestCase,
):
    BACKGROUND_JOBS_URL = (
        "/api/v1/background-jobs/"
    )

    NOTIFICATIONS_URL = (
        "/api/v1/notifications/"
    )

    def setUp(self):
        self.client = Client()

        self.test_key = (
            uuid4().hex
        )

        self.organization_a = (
            Organization(
                name=(
                    "Day 53 Organization A "
                    f"{self.test_key}"
                ),
                email=(
                    f"day53-a-{self.test_key}"
                    "@example.com"
                ),
            )
        )
        self.organization_a.save()

        self.organization_b = (
            Organization(
                name=(
                    "Day 53 Organization B "
                    f"{self.test_key}"
                ),
                email=(
                    f"day53-b-{self.test_key}"
                    "@example.com"
                ),
            )
        )
        self.organization_b.save()

        self.user_a = self._create_user(
            organization=
                self.organization_a,
            email=(
                f"day53-user-a-"
                f"{self.test_key}"
                "@example.com"
            ),
        )

        self.user_a_other = (
            self._create_user(
                organization=
                    self.organization_a,
                email=(
                    f"day53-user-a-other-"
                    f"{self.test_key}"
                    "@example.com"
                ),
            )
        )

        self.user_b = self._create_user(
            organization=
                self.organization_b,
            email=(
                f"day53-user-b-"
                f"{self.test_key}"
                "@example.com"
            ),
        )

        self.own_job = (
            BackgroundJobService
            .create_job(
                organization=
                    self.organization_a,
                created_by=
                    self.user_a,
                job_type="NOTIFICATION",
                payload={
                    "test": "own",
                },
                idempotency_key=(
                    f"day53-own-"
                    f"{self.test_key}"
                ),
            )
        )

        self.same_org_other_job = (
            BackgroundJobService
            .create_job(
                organization=
                    self.organization_a,
                created_by=
                    self.user_a_other,
                job_type="NOTIFICATION",
                payload={
                    "test":
                        "same-org-other-user",
                },
                idempotency_key=(
                    f"day53-same-org-other-"
                    f"{self.test_key}"
                ),
            )
        )

        self.cross_org_job = (
            BackgroundJobService
            .create_job(
                organization=
                    self.organization_b,
                created_by=
                    self.user_b,
                job_type="NOTIFICATION",
                payload={
                    "test": "cross-org",
                },
                idempotency_key=(
                    f"day53-cross-org-"
                    f"{self.test_key}"
                ),
            )
        )

        self.retryable_own_job = (
            BackgroundJobService
            .create_job(
                organization=
                    self.organization_a,
                created_by=
                    self.user_a,
                job_type="NOTIFICATION",
                payload={
                    "test": "retry-own",
                },
                idempotency_key=(
                    f"day53-retry-own-"
                    f"{self.test_key}"
                ),
            )
        )

        self.retryable_own_job.status = (
            "FAILED"
        )
        self.retryable_own_job.last_error = (
            "Day 53 test failure."
        )
        self.retryable_own_job.completed_at = (
            datetime.utcnow()
        )
        self.retryable_own_job.save()

        self.retryable_other_job = (
            BackgroundJobService
            .create_job(
                organization=
                    self.organization_a,
                created_by=
                    self.user_a_other,
                job_type="NOTIFICATION",
                payload={
                    "test":
                        "retry-other-user",
                },
                idempotency_key=(
                    f"day53-retry-other-"
                    f"{self.test_key}"
                ),
            )
        )

        self.retryable_other_job.status = (
            "FAILED"
        )
        self.retryable_other_job.last_error = (
            "Day 53 other-user failure."
        )
        self.retryable_other_job.completed_at = (
            datetime.utcnow()
        )
        self.retryable_other_job.save()

        self.own_notification = (
            NotificationService
            .create_notification(
                organization=
                    self.organization_a,
                recipient=
                    self.user_a,
                notification_type="SYSTEM",
                title="Own notification",
                message=(
                    "Visible to user A."
                ),
                severity="INFO",
            )
        )

        self.other_notification = (
            NotificationService
            .create_notification(
                organization=
                    self.organization_a,
                recipient=
                    self.user_a_other,
                notification_type="SYSTEM",
                title=(
                    "Other user notification"
                ),
                message=(
                    "Must not be visible "
                    "to user A."
                ),
                severity="INFO",
            )
        )

        self.cross_org_notification = (
            NotificationService
            .create_notification(
                organization=
                    self.organization_b,
                recipient=
                    self.user_b,
                notification_type="SYSTEM",
                title=(
                    "Cross organization "
                    "notification"
                ),
                message=(
                    "Must not be visible "
                    "to organization A."
                ),
                severity="INFO",
            )
        )

    def tearDown(self):
        BackgroundJob.objects(
            idempotency_key__startswith=(
                "day53-"
            )
        ).delete()

        Notification.objects(
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

    def _organization_context(
        self,
        user,
    ):
        return {
            "user": user,
            "organization":
                user.organization,
            "organization_id":
                str(
                    user.organization.id
                ),
        }

    def _get_as(
        self,
        user,
        url,
    ):
        with patch.object(
            APIOrganizationContextService,
            "resolve",
            return_value=(
                self._organization_context(
                    user
                )
            ),
        ):
            return self.client.get(
                url
            )

    def _post_as(
        self,
        user,
        url,
    ):
        with patch.object(
            APIOrganizationContextService,
            "resolve",
            return_value=(
                self._organization_context(
                    user
                )
            ),
        ):
            return self.client.post(
                url,
                data={},
            )

    # ==========================================
    # BACKGROUND JOB LIST ISOLATION
    # ==========================================

    def test_background_job_list_only_returns_jobs_created_by_user(
        self,
    ):
        response = self._get_as(
            self.user_a,
            self.BACKGROUND_JOBS_URL,
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        body = response.json()

        job_ids = {
            item["id"]
            for item
            in body["data"]["results"]
        }

        self.assertIn(
            str(self.own_job.id),
            job_ids,
        )

        self.assertIn(
            str(
                self.retryable_own_job.id
            ),
            job_ids,
        )

        self.assertNotIn(
            str(
                self.same_org_other_job.id
            ),
            job_ids,
        )

        self.assertNotIn(
            str(
                self.retryable_other_job.id
            ),
            job_ids,
        )

        self.assertNotIn(
            str(self.cross_org_job.id),
            job_ids,
        )

    # ==========================================
    # BACKGROUND JOB DETAIL ISOLATION
    # ==========================================

    def test_same_org_other_user_job_detail_is_hidden(
        self,
    ):
        response = self._get_as(
            self.user_a,
            (
                "/api/v1/background-jobs/"
                f"{self.same_org_other_job.id}/"
            ),
        )

        self.assertEqual(
            response.status_code,
            404,
        )

    def test_cross_org_job_detail_is_hidden(
        self,
    ):
        response = self._get_as(
            self.user_a,
            (
                "/api/v1/background-jobs/"
                f"{self.cross_org_job.id}/"
            ),
        )

        self.assertEqual(
            response.status_code,
            404,
        )

    # ==========================================
    # BACKGROUND JOB RETRY ISOLATION
    # ==========================================

    def test_user_can_retry_own_failed_job(
        self,
    ):
        response = self._post_as(
            self.user_a,
            (
                "/api/v1/background-jobs/"
                f"{self.retryable_own_job.id}/"
                "retry/"
            ),
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.retryable_own_job.reload()

        self.assertEqual(
            self.retryable_own_job.status,
            "PENDING",
        )

        self.assertEqual(
            self.retryable_own_job.attempts,
            0,
        )

        self.assertIsNone(
            self.retryable_own_job.last_error
        )

    def test_same_org_other_user_failed_job_cannot_be_retried(
        self,
    ):
        response = self._post_as(
            self.user_a,
            (
                "/api/v1/background-jobs/"
                f"{self.retryable_other_job.id}/"
                "retry/"
            ),
        )

        self.assertEqual(
            response.status_code,
            404,
        )

        self.retryable_other_job.reload()

        self.assertEqual(
            self.retryable_other_job.status,
            "FAILED",
        )

    def test_cross_org_failed_job_cannot_be_retried(
        self,
    ):
        self.cross_org_job.status = (
            "FAILED"
        )
        self.cross_org_job.last_error = (
            "Cross-org failure."
        )
        self.cross_org_job.completed_at = (
            datetime.utcnow()
        )
        self.cross_org_job.save()

        response = self._post_as(
            self.user_a,
            (
                "/api/v1/background-jobs/"
                f"{self.cross_org_job.id}/"
                "retry/"
            ),
        )

        self.assertEqual(
            response.status_code,
            404,
        )

        self.cross_org_job.reload()

        self.assertEqual(
            self.cross_org_job.status,
            "FAILED",
        )

    # ==========================================
    # NOTIFICATION LIST ISOLATION
    # ==========================================

    def test_notification_list_only_returns_current_user_notifications(
        self,
    ):
        response = self._get_as(
            self.user_a,
            self.NOTIFICATIONS_URL,
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        body = response.json()

        notification_ids = {
            item["id"]
            for item
            in body["data"]["results"]
        }

        self.assertIn(
            str(
                self.own_notification.id
            ),
            notification_ids,
        )

        self.assertNotIn(
            str(
                self.other_notification.id
            ),
            notification_ids,
        )

        self.assertNotIn(
            str(
                self.cross_org_notification.id
            ),
            notification_ids,
        )

    # ==========================================
    # NOTIFICATION READ ISOLATION
    # ==========================================

    def test_user_can_mark_own_notification_read(
        self,
    ):
        response = self._post_as(
            self.user_a,
            (
                "/api/v1/notifications/"
                f"{self.own_notification.id}/"
                "read/"
            ),
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.own_notification.reload()

        self.assertTrue(
            self.own_notification.is_read
        )

        self.assertIsNotNone(
            self.own_notification.read_at
        )

    def test_same_org_other_user_notification_cannot_be_marked_read(
        self,
    ):
        response = self._post_as(
            self.user_a,
            (
                "/api/v1/notifications/"
                f"{self.other_notification.id}/"
                "read/"
            ),
        )

        self.assertEqual(
            response.status_code,
            403,
        )

        self.other_notification.reload()

        self.assertFalse(
            self.other_notification.is_read
        )

    def test_cross_org_notification_is_hidden(
        self,
    ):
        response = self._post_as(
            self.user_a,
            (
                "/api/v1/notifications/"
                f"{self.cross_org_notification.id}/"
                "read/"
            ),
        )

        self.assertEqual(
            response.status_code,
            404,
        )

        self.cross_org_notification.reload()

        self.assertFalse(
            self.cross_org_notification.is_read
        )