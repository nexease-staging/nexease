from uuid import uuid4

from django.test import SimpleTestCase

from apps.accounts.models import User
from apps.core.notification_models import Notification
from apps.core.repositories.notification_repository import (
    NotificationRepository,
)
from apps.organizations.models import Organization


class NotificationRepositoryTests(
    SimpleTestCase
):

    def setUp(self):
        self.test_key = (
            f"notification-test-{uuid4().hex}"
        )

        self.organization = Organization(
            name="Notification Repository Test",
            email=(
                f"{self.test_key}"
                "@example.com"
            ),
        )
        self.organization.save()

        self.user = User(
            organization=
                self.organization,

            email=(
                f"user-{self.test_key}"
                "@example.com"
            ),

            password="test-password",

            first_name="Notification",
            last_name="Tester",
        )
        self.user.save()

    def tearDown(self):
        Notification.objects(
            organization=
                self.organization,
        ).delete()

        User.objects(
            organization=
                self.organization,
        ).delete()

        self.organization.delete()

    def create_notification(
        self,
        *,
        background_job_key=None,
    ):
        return (
            NotificationRepository
            .create(
                organization=
                    self.organization,

                recipient=
                    self.user,

                notification_type=
                    "SYSTEM",

                title=
                    "Repository notification",

                message=
                    "Repository test notification.",

                severity=
                    "INFO",

                background_job_key=
                    background_job_key,
            )
        )

    # ==================================================
    # BACKGROUND JOB IDEMPOTENCY
    # ==================================================

    def test_duplicate_background_job_key_returns_same_notification(
        self,
    ):
        key = (
            f"{self.test_key}-job"
        )

        first = self.create_notification(
            background_job_key=key,
        )

        second = self.create_notification(
            background_job_key=key,
        )

        self.assertEqual(
            str(first.id),
            str(second.id),
        )

        count = (
            Notification.objects(
                organization=
                    self.organization,

                background_job_key=
                    key,
            )
            .count()
        )

        self.assertEqual(
            count,
            1,
        )

    def test_same_background_job_key_allowed_in_other_organization(
        self,
    ):
        second_organization = Organization(
            name="Second Notification Organization",
            email=(
                f"second-{self.test_key}"
                "@example.com"
            ),
        )
        second_organization.save()

        second_user = User(
            organization=
                second_organization,

            email=(
                f"second-user-{self.test_key}"
                "@example.com"
            ),

            password="test-password",

            first_name="Second",
            last_name="Tester",
        )
        second_user.save()

        try:
            key = (
                f"{self.test_key}-shared"
            )

            first = (
                NotificationRepository
                .create(
                    organization=
                        self.organization,

                    recipient=
                        self.user,

                    notification_type=
                        "SYSTEM",

                    title="First",
                    message="First message",

                    background_job_key=
                        key,
                )
            )

            second = (
                NotificationRepository
                .create(
                    organization=
                        second_organization,

                    recipient=
                        second_user,

                    notification_type=
                        "SYSTEM",

                    title="Second",
                    message="Second message",

                    background_job_key=
                        key,
                )
            )

            self.assertNotEqual(
                str(first.id),
                str(second.id),
            )

        finally:
            Notification.objects(
                organization=
                    second_organization,
            ).delete()

            User.objects(
                organization=
                    second_organization,
            ).delete()

            second_organization.delete()

    # ==================================================
    # ORDINARY NOTIFICATIONS
    # ==================================================

    def test_multiple_notifications_without_background_job_key_allowed(
        self,
    ):
        first = (
            self.create_notification()
        )

        second = (
            self.create_notification()
        )

        self.assertNotEqual(
            str(first.id),
            str(second.id),
        )

        count = (
            Notification.objects(
                organization=
                    self.organization,

                background_job_key=
                    None,
            )
            .count()
        )

        self.assertGreaterEqual(
            count,
            2,
        )