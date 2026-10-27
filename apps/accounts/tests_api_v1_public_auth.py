import json
from datetime import (
    timedelta,
)
from apps.accounts.password_reset_timing_service import (
    PasswordResetTimingService,
)
from threading import (
    Barrier,
    Thread,
)
from types import SimpleNamespace
from apps.core.services.api_rate_limit_service import (
    APIRateLimitService,
)
from django.core import mail
from django.test import override_settings

from apps.accounts.password_reset_email_service import (
    PasswordResetEmailError,
    PasswordResetEmailService,
)
from unittest.mock import patch

from apps.accounts.password_reset_models import (
    PasswordResetToken,
)
from apps.accounts.password_reset_service import (
    PasswordResetError,
    PasswordResetService,
)
from django.test import (
    Client,
    SimpleTestCase,
)
from uuid import uuid4

from apps.accounts.models import User
from apps.authorization.models import (
    Role,
)
from apps.authorization.roles import (
    ROLE_CATALOG,
)
from apps.organizations.models import (
    Organization,
)

class PublicSignupAPIV1TestCase(
    SimpleTestCase
):

    URL = "/api/v1/auth/signup/"

    def setUp(self):
        self.client = Client(
            raise_request_exception=False
        )
        self.rate_limit_patcher = patch.object(
            APIRateLimitService,
            "check",
            return_value={
                "allowed": True,
                "scope": "test",
                "limit": 1000,
                "remaining": 999,
                "request_count": 1,
                "window_seconds": 3600,
                "window_started_at": None,
                "window_ends_at": None,
                "reset_timestamp": 0,
                "retry_after": 0,
            },
        )

        self.rate_limit_patcher.start()

    def assert_error_contract(
        self,
        response,
        expected_status=400,
    ):
        body = response.json()

        self.assertEqual(
            response.status_code,
            expected_status,
        )

        self.assertFalse(
            body["success"]
        )

        self.assertIn(
            "error",
            body,
        )

        self.assertTrue(
            body.get("request_id")
        )

        self.assertEqual(
            response.headers.get(
                "X-Request-ID"
            ),
            body["request_id"],
        )

        return body

    def test_get_returns_405_contract(
        self,
    ):
        response = self.client.get(
            self.URL
        )

        self.assert_error_contract(
            response,
            expected_status=405,
        )

    def test_non_json_request_returns_400_contract(
        self,
    ):
        response = self.client.post(
            self.URL,
            data={
                "organization_name":
                    "Test Organization",
            },
        )

        body = self.assert_error_contract(
            response
        )

        self.assertEqual(
            body["error"]["message"],
            (
                "Content-Type must be "
                "application/json."
            ),
        )

    def test_invalid_json_returns_400_contract(
        self,
    ):
        response = self.client.post(
            self.URL,
            data="{invalid-json",
            content_type="application/json",
        )

        body = self.assert_error_contract(
            response
        )

        self.assertEqual(
            body["error"]["message"],
            "Invalid JSON body.",
        )

    def test_non_object_json_returns_validation_error(
        self,
    ):
        response = self.client.post(
            self.URL,
            data=json.dumps(
                [
                    "not",
                    "an",
                    "object",
                ]
            ),
            content_type="application/json",
        )

        body = self.assert_error_contract(
            response
        )

        self.assertEqual(
            body["error"]["message"],
            "Validation failed.",
        )

        self.assertIn(
            "body",
            body["error"]["details"],
        )

    def test_missing_required_fields_returns_validation_error(
        self,
    ):
        response = self.client.post(
            self.URL,
            data=json.dumps({}),
            content_type="application/json",
        )

        body = self.assert_error_contract(
            response
        )

        self.assertEqual(
            body["error"]["message"],
            "Validation failed.",
        )

        details = body["error"]["details"]

        expected_fields = {
            "organization_name",
            "organization_email",
            "first_name",
            "last_name",
            "email",
            "password",
        }

        self.assertEqual(
            set(details.keys()),
            expected_fields,
        )

        for field_name in expected_fields:
            self.assertTrue(
                details[field_name],
                msg=(
                    f"Expected validation error "
                    f"for {field_name}."
                ),
            )

        self.assertNotIn(
            "phone",
            details,
        )

    def test_invalid_emails_and_weak_password_return_validation_errors(
        self,
    ):
        payload = {
            "organization_name":
                "Validation Test Organization",

            "organization_email":
                "invalid-organization-email",

            "first_name":
                "Validation",

            "last_name":
                "Tester",

            "email":
                "invalid-user-email",

            "password":
                "123",
        }

        response = self.client.post(
            self.URL,
            data=json.dumps(
                payload
            ),
            content_type="application/json",
        )

        body = self.assert_error_contract(
            response
        )

        self.assertEqual(
            body["error"]["message"],
            "Validation failed.",
        )

        details = body["error"]["details"]

        self.assertIn(
            "organization_email",
            details,
        )

        self.assertIn(
            "email",
            details,
        )

        self.assertIn(
            "password",
            details,
        )

        self.assertTrue(
            details["organization_email"]
        )

        self.assertTrue(
            details["email"]
        )

        self.assertTrue(
            details["password"]
        )

    def test_successful_signup_creates_admin_account(
        self,
    ):
        test_key = uuid4().hex

        organization_email = (
            f"organization-{test_key}"
            "@example.com"
        )

        user_email = (
            f"admin-{test_key}"
            "@example.com"
        )

        password = "SignupTest#9274"

        organization = None

        try:
            response = self.client.post(
                self.URL,
                data=json.dumps(
                    {
                        "organization_name":
                            "Public Signup Test",
                        "organization_email":
                            organization_email,
                        "phone":
                            "9876543210",
                        "first_name":
                            "Signup",
                        "last_name":
                            "Administrator",
                        "email":
                            user_email,
                        "password":
                            password,
                    }
                ),
                content_type="application/json",
            )

            body = response.json()

            self.assertEqual(
                response.status_code,
                201,
            )

            self.assertTrue(
                body["success"]
            )

            self.assertIn(
                "data",
                body,
            )

            self.assertTrue(
                body.get("request_id")
            )

            organization = (
                Organization.objects(
                    email=organization_email
                )
                .first()
            )

            self.assertIsNotNone(
                organization
            )

            user = (
                User.objects(
                    email=user_email
                )
                .first()
            )

            self.assertIsNotNone(
                user
            )

            self.assertEqual(
                user.organization.id,
                organization.id,
            )

            self.assertTrue(
                user.is_active
            )

            self.assertNotEqual(
                user.password,
                password,
            )

            self.assertTrue(
                user.check_password(
                    password
                )
            )

            role = (
                Role.objects(
                    organization=organization,
                    name="Admin",
                )
                .first()
            )

            self.assertIsNotNone(
                role
            )

            self.assertEqual(
                user.role.id,
                role.id,
            )

            self.assertTrue(
                role.is_system
            )

            self.assertTrue(
                role.is_active
            )

            expected_permissions = set(
                ROLE_CATALOG[
                    "admin"
                ][
                    "permissions"
                ]
            )

            actual_permissions = {
                permission.code
                for permission
                in role.permissions
            }

            self.assertEqual(
                actual_permissions,
                expected_permissions,
            )

        finally:
            if organization is not None:
                User.objects(
                    organization=organization
                ).delete()

                Role.objects(
                    organization=organization
                ).delete()

                organization.delete()

    def tearDown(self):
        self.rate_limit_patcher.stop()

class PasswordResetServiceTestCase(
    SimpleTestCase
):

    def test_concurrent_token_requests_leave_only_one_usable_token(
        self,
    ):
        original_save = (
            PasswordResetToken.save
        )

        save_barrier = Barrier(2)

        results = []
        errors = []

        def synchronized_save(
            token_record,
            *args,
            **kwargs,
        ):
            # Both requests must finish invalidating
            # older tokens before either new token is
            # inserted. This deterministically exposes
            # the create-token race.
            save_barrier.wait(
                timeout=10
            )

            return original_save(
                token_record,
                *args,
                **kwargs,
            )

        def create_token():
            try:
                result = (
                    PasswordResetService
                    .create_reset_token(
                        email=self.user.email,
                    )
                )

                results.append(
                    result
                )

            except Exception as error:
                errors.append(
                    error
                )

        with patch.object(
            PasswordResetToken,
            "save",
            new=synchronized_save,
        ):
            threads = [
                Thread(
                    target=create_token
                ),
                Thread(
                    target=create_token
                ),
            ]

            for thread in threads:
                thread.start()

            for thread in threads:
                thread.join(
                    timeout=15
                )

        self.assertFalse(
            errors,
            msg=f"Concurrent errors: {errors}",
        )

        self.assertEqual(
            len(results),
            2,
        )

        usable_tokens = []

        for result in results:
            try:
                (
                    PasswordResetService
                    .get_valid_token_record(
                        token=result["token"],
                    )
                )

                usable_tokens.append(
                    result["token"]
                )

            except PasswordResetError:
                pass

        self.assertEqual(
            len(usable_tokens),
            1,
            msg=(
                "Concurrent password-reset requests "
                "must leave exactly one usable token."
            ),
        )

        unused_records = (
            PasswordResetToken.objects(
                user=self.user,
                used_at=None,
            )
            .count()
        )

        self.assertEqual(
            unused_records,
            1,
        )
    def setUp(self):
        self.test_key = uuid4().hex

        self.organization = Organization(
            name="Password Reset Test",
            email=(
                f"organization-{self.test_key}"
                "@example.com"
            ),
        )

        self.organization.save()

        self.user = User(
            organization=self.organization,
            email=(
                f"user-{self.test_key}"
                "@example.com"
            ),
            first_name="Password",
            last_name="Tester",
            is_active=True,
        )

        self.original_password = (
            "OriginalPassword#9274"
        )

        self.user.set_password(
            self.original_password
        )

        self.user.save()

    def tearDown(self):
        PasswordResetToken.objects(
            user=self.user
        ).delete()

        User.objects(
            organization=self.organization
        ).delete()

        Role.objects(
            organization=self.organization
        ).delete()

        self.organization.delete()

    def test_unknown_email_returns_none(
        self,
    ):
        result = (
            PasswordResetService
            .create_reset_token(
                email=(
                    f"missing-{self.test_key}"
                    "@example.com"
                ),
            )
        )

        self.assertIsNone(
            result
        )

    def test_reset_token_is_hashed_in_database(
        self,
    ):
        result = (
            PasswordResetService
            .create_reset_token(
                email=self.user.email,
            )
        )

        self.assertIsNotNone(
            result
        )

        raw_token = result["token"]

        self.assertEqual(
            len(raw_token),
            43,
        )

        record = (
            PasswordResetToken.objects(
                user=self.user
            )
            .first()
        )

        self.assertIsNotNone(
            record
        )

        self.assertNotEqual(
            record.token_hash,
            raw_token,
        )

        self.assertEqual(
            len(record.token_hash),
            64,
        )

        self.assertEqual(
            record.token_hash,
            PasswordResetService.hash_token(
                raw_token
            ),
        )

        self.assertIsNone(
            PasswordResetToken.objects(
                token_hash=raw_token
            ).first()
        )

    def test_new_token_invalidates_previous_token(
        self,
    ):
        first = (
            PasswordResetService
            .create_reset_token(
                email=self.user.email,
            )
        )

        second = (
            PasswordResetService
            .create_reset_token(
                email=self.user.email,
            )
        )

        first_record = (
            PasswordResetToken.objects(
                token_hash=(
                    PasswordResetService
                    .hash_token(
                        first["token"]
                    )
                )
            )
            .first()
        )

        second_record = (
            PasswordResetToken.objects(
                token_hash=(
                    PasswordResetService
                    .hash_token(
                        second["token"]
                    )
                )
            )
            .first()
        )

        self.assertIsNotNone(
            first_record.used_at
        )

        self.assertIsNone(
            second_record.used_at
        )

        with self.assertRaises(
            PasswordResetError
        ):
            (
                PasswordResetService
                .get_valid_token_record(
                    token=first["token"],
                )
            )

        valid_record = (
            PasswordResetService
            .get_valid_token_record(
                token=second["token"],
            )
        )

        self.assertEqual(
            valid_record.id,
            second_record.id,
        )

    def test_expired_token_is_rejected(
        self,
    ):
        result = (
            PasswordResetService
            .create_reset_token(
                email=self.user.email,
            )
        )

        record = (
            PasswordResetToken.objects(
                token_hash=(
                    PasswordResetService
                    .hash_token(
                        result["token"]
                    )
                )
            )
            .first()
        )

        record.expires_at = (
            PasswordResetService.now()
            -
            timedelta(
                minutes=1
            )
        )

        record.save()

        with self.assertRaisesRegex(
            PasswordResetError,
            (
                "This password reset link "
                "is invalid or has expired."
            ),
        ):
            (
                PasswordResetService
                .get_valid_token_record(
                    token=result["token"],
                )
            )

    def test_invalid_token_is_rejected(
        self,
    ):
        with self.assertRaisesRegex(
            PasswordResetError,
            (
                "This password reset link "
                "is invalid or has expired."
            ),
        ):
            (
                PasswordResetService
                .get_valid_token_record(
                    token="invalid-reset-token",
                )
            )

    def test_weak_password_is_rejected(
        self,
    ):
        result = (
            PasswordResetService
            .create_reset_token(
                email=self.user.email,
            )
        )

        with self.assertRaises(
            PasswordResetError
        ):
            (
                PasswordResetService
                .reset_password(
                    token=result["token"],
                    new_password="123",
                )
            )

        self.user.reload()

        self.assertTrue(
            self.user.check_password(
                self.original_password
            )
        )

        record = (
            PasswordResetToken.objects(
                token_hash=(
                    PasswordResetService
                    .hash_token(
                        result["token"]
                    )
                )
            )
            .first()
        )

        self.assertIsNone(
            record.used_at
        )

    def test_successful_reset_changes_password_and_consumes_token(
        self,
    ):
        result = (
            PasswordResetService
            .create_reset_token(
                email=self.user.email,
            )
        )

        new_password = (
            "NewPassword#8642"
        )

        with patch(
            "apps.accounts."
            "password_reset_service."
            "AuthenticationService."
            "revoke_user_sessions",
            return_value=2,
        ) as revoke_sessions:

            reset_result = (
                PasswordResetService
                .reset_password(
                    token=result["token"],
                    new_password=new_password,
                )
            )

        self.user.reload()

        self.assertFalse(
            self.user.check_password(
                self.original_password
            )
        )

        self.assertTrue(
            self.user.check_password(
                new_password
            )
        )

        self.assertEqual(
            reset_result[
                "sessions_revoked"
            ],
            2,
        )

        revoke_sessions.assert_called_once()

        record = (
            PasswordResetToken.objects(
                token_hash=(
                    PasswordResetService
                    .hash_token(
                        result["token"]
                    )
                )
            )
            .first()
        )

        self.assertIsNotNone(
            record.used_at
        )

    def test_consumed_token_cannot_be_reused(
        self,
    ):
        result = (
            PasswordResetService
            .create_reset_token(
                email=self.user.email,
            )
        )

        with patch(
            "apps.accounts."
            "password_reset_service."
            "AuthenticationService."
            "revoke_user_sessions",
            return_value=0,
        ):
            (
                PasswordResetService
                .reset_password(
                    token=result["token"],
                    new_password=(
                        "FirstReset#8642"
                    ),
                )
            )

        with self.assertRaisesRegex(
            PasswordResetError,
            (
                "This password reset link "
                "is invalid or has expired."
            ),
        ):
            (
                PasswordResetService
                .reset_password(
                    token=result["token"],
                    new_password=(
                        "SecondReset#9753"
                    ),
                )
            )

        self.user.reload()

        self.assertTrue(
            self.user.check_password(
                "FirstReset#8642"
            )
        )

        self.assertFalse(
            self.user.check_password(
                "SecondReset#9753"
            )
        )


class PasswordResetEmailServiceTestCase(
    SimpleTestCase
):

    @override_settings(
        FRONTEND_BASE_URL=(
            "http://localhost:3000/"
        ),
        DEFAULT_FROM_EMAIL=(
            "no-reply@demoinventory.local"
        ),
        MAILERS={
            "default": {
                "BACKEND": (
                    "django.core.mail.backends."
                    "locmem.EmailBackend"
                ),
            },
        },
    )
    def test_build_reset_url(
        self,
    ):
        reset_url = (
            PasswordResetEmailService
            .build_reset_url(
                token="test-token",
            )
        )

        self.assertEqual(
            reset_url,
            (
                "http://localhost:3000"
                "/reset-password"
                "?token=test-token"
            ),
        )

    @override_settings(
        FRONTEND_BASE_URL=(
            "http://localhost:3000"
        ),
        DEFAULT_FROM_EMAIL=(
            "no-reply@demoinventory.local"
        ),
        MAILERS={
            "default": {
                "BACKEND": (
                    "django.core.mail.backends."
                    "locmem.EmailBackend"
                ),
            },
        },
    )
    def test_send_reset_email(
        self,
    ):
        user = SimpleNamespace(
            email="reset-user@example.com",
            first_name="Reset",
        )

        result = (
            PasswordResetEmailService
            .send_reset_email(
                user=user,
                token="secure-test-token",
            )
        )

        self.assertTrue(
            result["sent"]
        )

        self.assertEqual(
            result["recipient"],
            user.email,
        )

        self.assertEqual(
            len(mail.outbox),
            1,
        )

        message = mail.outbox[0]

        self.assertEqual(
            message.to,
            [
                user.email,
            ],
        )

        self.assertEqual(
            message.subject,
            (
                "Reset your Django IMS "
                "password"
            ),
        )

        self.assertIn(
            (
                "http://localhost:3000"
                "/reset-password"
                "?token=secure-test-token"
            ),
            message.body,
        )

        self.assertIn(
            "30 minutes",
            message.body,
        )

        self.assertIn(
            "can be used only once",
            message.body,
        )

    @override_settings(
        FRONTEND_BASE_URL="",
    )
    def test_missing_frontend_url_is_rejected(
        self,
    ):
        with self.assertRaises(
            PasswordResetEmailError
        ):
            (
                PasswordResetEmailService
                .build_reset_url(
                    token="test-token",
                )
            )

    @override_settings(
        FRONTEND_BASE_URL=(
            "http://localhost:3000"
        ),
        DEFAULT_FROM_EMAIL=(
            "no-reply@demoinventory.local"
        ),
    )
    def test_email_delivery_failure_is_wrapped(
        self,
    ):
        user = SimpleNamespace(
            email="reset-user@example.com",
            first_name="Reset",
        )

        with patch(
            "apps.accounts."
            "password_reset_email_service."
            "EmailMessage.send",
            side_effect=Exception(
                "SMTP failure"
            ),
        ):
            with self.assertRaises(
                PasswordResetEmailError
            ):
                (
                    PasswordResetEmailService
                    .send_reset_email(
                        user=user,
                        token="test-token",
                    )
                )


class PublicPasswordResetAPIV1TestCase(
    SimpleTestCase
):

    FORGOT_URL = (
        "/api/v1/auth/forgot-password/"
    )

    RESET_URL = (
        "/api/v1/auth/reset-password/"
    )

    GENERIC_MESSAGE = (
        "If an account exists for that "
        "email address, password reset "
        "instructions will be sent."
    )

    def setUp(self):
        self.client = Client(
            raise_request_exception=False
        )
        self.rate_limit_patcher = patch.object(
            APIRateLimitService,
            "check",
            return_value={
                "allowed": True,
                "scope": "test",
                "limit": 1000,
                "remaining": 999,
                "request_count": 1,
                "window_seconds": 3600,
                "window_started_at": None,
                "window_ends_at": None,
                "reset_timestamp": 0,
                "retry_after": 0,
            },
        )
        self.timing_start_patcher = patch.object(
            PasswordResetTimingService,
            "start",
            return_value=100.0,
        )

        self.timing_wait_patcher = patch.object(
            PasswordResetTimingService,
            "wait_for_minimum_duration",
            return_value={
                "elapsed_seconds": 0.1,
                "slept_seconds": 0.7,
            },
        )

        self.mock_timing_start = (
            self.timing_start_patcher.start()
        )

        self.mock_timing_wait = (
            self.timing_wait_patcher.start()
        )
        self.rate_limit_patcher.start()

    def tearDown(self):
        self.timing_wait_patcher.stop()
        self.timing_start_patcher.stop()
        self.rate_limit_patcher.stop()
    def assert_error_contract(
        self,
        response,
        expected_status=400,
    ):
        body = response.json()

        self.assertEqual(
            response.status_code,
            expected_status,
        )

        self.assertFalse(
            body["success"]
        )

        self.assertIn(
            "error",
            body,
        )

        self.assertTrue(
            body.get("request_id")
        )

        self.assertEqual(
            response.headers.get(
                "X-Request-ID"
            ),
            body["request_id"],
        )

        return body

    def assert_success_contract(
        self,
        response,
        expected_status=200,
    ):
        body = response.json()

        self.assertEqual(
            response.status_code,
            expected_status,
        )

        self.assertTrue(
            body["success"]
        )

        self.assertIn(
            "data",
            body,
        )

        self.assertTrue(
            body.get("request_id")
        )

        self.assertEqual(
            response.headers.get(
                "X-Request-ID"
            ),
            body["request_id"],
        )

        return body

    def test_forgot_password_missing_email_uses_error_contract(
        self,
    ):
        response = self.client.post(
            self.FORGOT_URL,
            data=json.dumps({}),
            content_type="application/json",
        )

        body = self.assert_error_contract(
            response
        )

        self.assertEqual(
            body["error"]["message"],
            "Validation failed.",
        )

        self.assertIn(
            "email",
            body["error"]["details"],
        )

    def test_forgot_password_invalid_json_uses_error_contract(
        self,
    ):
        response = self.client.post(
            self.FORGOT_URL,
            data="{invalid-json",
            content_type="application/json",
        )

        body = self.assert_error_contract(
            response
        )

        self.assertEqual(
            body["error"]["message"],
            "Invalid JSON body.",
        )

    def test_forgot_existing_account_returns_generic_success(
        self,
    ):
        reset_result = {
            "user": SimpleNamespace(
                email="existing@example.com",
            ),
            "token": "raw-reset-token",
            "expires_at": (
                PasswordResetService.now()
                +
                timedelta(
                    minutes=30
                )
            ),
        }

        with patch(
            "apps.accounts.api.v1.views."
            "PasswordResetService."
            "create_reset_token",
            return_value=reset_result,
        ) as create_token, patch(
            "apps.accounts.api.v1.views."
            "PasswordResetEmailService."
            "send_reset_email",
            return_value={
                "sent": True,
            },
        ) as send_email:

            response = self.client.post(
                self.FORGOT_URL,
                data=json.dumps(
                    {
                        "email":
                            "existing@example.com",
                    }
                ),
                content_type=(
                    "application/json"
                ),
            )

        body = self.assert_success_contract(
            response
        )

        self.assertEqual(
            body["data"]["message"],
            self.GENERIC_MESSAGE,
        )

        create_token.assert_called_once_with(
            email="existing@example.com"
        )

        send_email.assert_called_once()

    def test_forgot_missing_account_returns_same_generic_success(
        self,
    ):
        with patch(
            "apps.accounts.api.v1.views."
            "PasswordResetService."
            "create_reset_token",
            return_value=None,
        ), patch(
            "apps.accounts.api.v1.views."
            "PasswordResetEmailService."
            "send_reset_email",
        ) as send_email:

            response = self.client.post(
                self.FORGOT_URL,
                data=json.dumps(
                    {
                        "email":
                            "missing@example.com",
                    }
                ),
                content_type=(
                    "application/json"
                ),
            )

        body = self.assert_success_contract(
            response
        )

        self.assertEqual(
            body["data"]["message"],
            self.GENERIC_MESSAGE,
        )

        send_email.assert_not_called()

    def test_forgot_email_failure_still_returns_generic_success(
        self,
    ):
        reset_result = {
            "user": SimpleNamespace(
                email="existing@example.com",
            ),
            "token": "raw-reset-token",
            "expires_at": (
                PasswordResetService.now()
                +
                timedelta(
                    minutes=30
                )
            ),
        }

        with patch(
            "apps.accounts.api.v1.views."
            "PasswordResetService."
            "create_reset_token",
            return_value=reset_result,
        ), patch(
            "apps.accounts.api.v1.views."
            "PasswordResetEmailService."
            "send_reset_email",
            side_effect=(
                PasswordResetEmailError(
                    "Email failed."
                )
            ),
        ):

            response = self.client.post(
                self.FORGOT_URL,
                data=json.dumps(
                    {
                        "email":
                            "existing@example.com",
                    }
                ),
                content_type=(
                    "application/json"
                ),
            )

        body = self.assert_success_contract(
            response
        )

        self.assertEqual(
            body["data"]["message"],
            self.GENERIC_MESSAGE,
        )

    def test_reset_password_get_returns_405(
        self,
    ):
        response = self.client.get(
            self.RESET_URL
        )

        self.assertEqual(
            response.status_code,
            405,
        )

    def test_reset_password_invalid_json_uses_error_contract(
        self,
    ):
        response = self.client.post(
            self.RESET_URL,
            data="{invalid-json",
            content_type="application/json",
        )

        body = self.assert_error_contract(
            response
        )

        self.assertEqual(
            body["error"]["message"],
            "Invalid JSON body.",
        )

    def test_reset_password_missing_fields_uses_validation_contract(
        self,
    ):
        response = self.client.post(
            self.RESET_URL,
            data=json.dumps({}),
            content_type="application/json",
        )

        body = self.assert_error_contract(
            response
        )

        self.assertEqual(
            body["error"]["message"],
            "Validation failed.",
        )

        details = (
            body["error"]["details"]
        )

        self.assertIn(
            "token",
            details,
        )

        self.assertIn(
            "new_password",
            details,
        )

    def test_reset_password_invalid_token_returns_generic_error(
        self,
    ):
        with patch(
            "apps.accounts.api.v1.views."
            "PasswordResetService."
            "reset_password",
            side_effect=PasswordResetError(
                (
                    "This password reset link "
                    "is invalid or has expired."
                )
            ),
        ):
            response = self.client.post(
                self.RESET_URL,
                data=json.dumps(
                    {
                        "token":
                            "invalid-token",
                        "new_password":
                            "NewPassword#8642",
                    }
                ),
                content_type=(
                    "application/json"
                ),
            )

        body = self.assert_error_contract(
            response
        )

        self.assertEqual(
            body["error"]["message"],
            (
                "This password reset link "
                "is invalid or has expired."
            ),
        )

    def test_reset_password_weak_password_returns_service_error(
        self,
    ):
        with patch(
            "apps.accounts.api.v1.views."
            "PasswordResetService."
            "reset_password",
            side_effect=PasswordResetError(
                "This password is too short."
            ),
        ):
            response = self.client.post(
                self.RESET_URL,
                data=json.dumps(
                    {
                        "token":
                            "valid-token",
                        "new_password":
                            "123",
                    }
                ),
                content_type=(
                    "application/json"
                ),
            )

        body = self.assert_error_contract(
            response
        )

        self.assertEqual(
            body["error"]["message"],
            "This password is too short.",
        )

    def test_reset_password_success_uses_success_contract(
        self,
    ):
        with patch(
            "apps.accounts.api.v1.views."
            "PasswordResetService."
            "reset_password",
            return_value={
                "user": SimpleNamespace(
                    email="user@example.com"
                ),
                "sessions_revoked": 3,
            },
        ) as reset_password:

            response = self.client.post(
                self.RESET_URL,
                data=json.dumps(
                    {
                        "token":
                            "valid-token",
                        "new_password":
                            "NewPassword#8642",
                    }
                ),
                content_type=(
                    "application/json"
                ),
            )

        body = self.assert_success_contract(
            response
        )

        self.assertEqual(
            body["data"][
                "sessions_revoked"
            ],
            3,
        )

        self.assertEqual(
            body["data"]["message"],
            (
                "Your password has been reset "
                "successfully. Please sign in "
                "with your new password."
            ),
        )

        reset_password.assert_called_once_with(
            token="valid-token",
            new_password=(
                "NewPassword#8642"
            ),
        )

    def test_forgot_existing_account_uses_timing_protection(
        self,
    ):
        reset_result = {
            "user": SimpleNamespace(
                email="existing@example.com",
            ),
            "token": "raw-reset-token",
            "expires_at": (
                PasswordResetService.now()
                +
                timedelta(
                    minutes=30
                )
            ),
        }

        self.mock_timing_start.reset_mock()
        self.mock_timing_wait.reset_mock()

        with patch(
            "apps.accounts.api.v1.views."
            "PasswordResetService."
            "create_reset_token",
            return_value=reset_result,
        ), patch(
            "apps.accounts.api.v1.views."
            "PasswordResetEmailService."
            "send_reset_email",
            return_value={
                "sent": True,
            },
        ):
            response = self.client.post(
                self.FORGOT_URL,
                data=json.dumps(
                    {
                        "email":
                            "existing@example.com",
                    }
                ),
                content_type="application/json",
            )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.mock_timing_start.assert_called_once_with()

        self.mock_timing_wait.assert_called_once_with(
            started_at=100.0,
        )


    def test_forgot_missing_account_uses_timing_protection(
        self,
    ):
        self.mock_timing_start.reset_mock()
        self.mock_timing_wait.reset_mock()

        with patch(
            "apps.accounts.api.v1.views."
            "PasswordResetService."
            "create_reset_token",
            return_value=None,
        ), patch(
            "apps.accounts.api.v1.views."
            "PasswordResetEmailService."
            "send_reset_email",
        ) as send_email:

            response = self.client.post(
                self.FORGOT_URL,
                data=json.dumps(
                    {
                        "email":
                            "missing@example.com",
                    }
                ),
                content_type="application/json",
            )

        self.assertEqual(
            response.status_code,
            200,
        )

        send_email.assert_not_called()

        self.mock_timing_start.assert_called_once_with()

        self.mock_timing_wait.assert_called_once_with(
            started_at=100.0,
        )
class PublicAuthRateLimitAPIV1TestCase(
    SimpleTestCase
):

    SIGNUP_URL = "/api/v1/auth/signup/"
    FORGOT_URL = (
        "/api/v1/auth/forgot-password/"
    )
    RESET_URL = (
        "/api/v1/auth/reset-password/"
    )

    def setUp(self):
        self.client = Client(
            raise_request_exception=False
        )

    @staticmethod
    def denied_result(
        *,
        scope,
        limit,
        window_seconds,
    ):
        return {
            "allowed": False,
            "scope": scope,
            "limit": limit,
            "remaining": 0,
            "request_count": limit + 1,
            "window_seconds": (
                window_seconds
            ),
            "window_started_at": None,
            "window_ends_at": None,
            "reset_timestamp": 1234567890,
            "retry_after": 60,
        }

    def assert_rate_limited(
        self,
        response,
        *,
        expected_limit,
    ):
        body = response.json()

        self.assertEqual(
            response.status_code,
            429,
        )

        self.assertFalse(
            body["success"]
        )

        self.assertEqual(
            body["error"]["message"],
            (
                "API request limit exceeded. "
                "Try again later."
            ),
        )

        self.assertTrue(
            body.get("request_id")
        )

        self.assertEqual(
            response.headers.get(
                "X-Request-ID"
            ),
            body["request_id"],
        )

        self.assertEqual(
            response.headers.get(
                "X-RateLimit-Limit"
            ),
            str(expected_limit),
        )

        self.assertEqual(
            response.headers.get(
                "X-RateLimit-Remaining"
            ),
            "0",
        )

        self.assertEqual(
            response.headers.get(
                "X-RateLimit-Reset"
            ),
            "1234567890",
        )

        self.assertEqual(
            response.headers.get(
                "Retry-After"
            ),
            "60",
        )

    def test_signup_rate_limit_returns_429(
        self,
    ):
        with patch.object(
            APIRateLimitService,
            "check",
            return_value=self.denied_result(
                scope="auth.signup",
                limit=5,
                window_seconds=3600,
            ),
        ) as check_rate_limit:

            response = self.client.post(
                self.SIGNUP_URL,
                data=json.dumps({}),
                content_type="application/json",
            )

        self.assert_rate_limited(
            response,
            expected_limit=5,
        )

        check_rate_limit.assert_called_once()

        call_kwargs = (
            check_rate_limit.call_args.kwargs
        )

        self.assertEqual(
            call_kwargs["scope"],
            "auth.signup",
        )

        self.assertEqual(
            call_kwargs["limit"],
            5,
        )

        self.assertEqual(
            call_kwargs["window_seconds"],
            3600,
        )

    def test_forgot_password_rate_limit_returns_429(
        self,
    ):
        with patch.object(
            APIRateLimitService,
            "check",
            return_value=self.denied_result(
                scope="auth.forgot_password",
                limit=5,
                window_seconds=900,
            ),
        ) as check_rate_limit:

            response = self.client.post(
                self.FORGOT_URL,
                data=json.dumps(
                    {
                        "email":
                            "user@example.com",
                    }
                ),
                content_type="application/json",
            )

        self.assert_rate_limited(
            response,
            expected_limit=5,
        )

        call_kwargs = (
            check_rate_limit.call_args.kwargs
        )

        self.assertEqual(
            call_kwargs["scope"],
            "auth.forgot_password",
        )

        self.assertEqual(
            call_kwargs["limit"],
            5,
        )

        self.assertEqual(
            call_kwargs["window_seconds"],
            900,
        )

    def test_reset_password_rate_limit_returns_429(
        self,
    ):
        with patch.object(
            APIRateLimitService,
            "check",
            return_value=self.denied_result(
                scope="auth.reset_password",
                limit=10,
                window_seconds=900,
            ),
        ) as check_rate_limit:

            response = self.client.post(
                self.RESET_URL,
                data=json.dumps(
                    {
                        "token":
                            "test-token",
                        "new_password":
                            "NewPassword#8642",
                    }
                ),
                content_type="application/json",
            )

        self.assert_rate_limited(
            response,
            expected_limit=10,
        )

        call_kwargs = (
            check_rate_limit.call_args.kwargs
        )

        self.assertEqual(
            call_kwargs["scope"],
            "auth.reset_password",
        )

        self.assertEqual(
            call_kwargs["limit"],
            10,
        )

        self.assertEqual(
            call_kwargs["window_seconds"],
            900,
        )

    def test_rate_limit_storage_failure_returns_503(
        self,
    ):
        from apps.core.services.api_rate_limit_service import (
            APIRateLimitUnavailable,
        )

        with patch.object(
            APIRateLimitService,
            "check",
            side_effect=APIRateLimitUnavailable(
                "Storage unavailable."
            ),
        ):
            response = self.client.post(
                self.FORGOT_URL,
                data=json.dumps(
                    {
                        "email":
                            "user@example.com",
                    }
                ),
                content_type="application/json",
            )

        body = response.json()

        self.assertEqual(
            response.status_code,
            503,
        )

        self.assertFalse(
            body["success"]
        )

        self.assertEqual(
            body["error"]["message"],
            (
                "API rate-limit service "
                "is unavailable."
            ),
        )

        self.assertTrue(
            body.get("request_id")
        )

class PasswordResetTimingServiceTestCase(
    SimpleTestCase
):

    def test_start_returns_perf_counter(
        self,
    ):
        with patch(
            "apps.accounts."
            "password_reset_timing_service."
            "time.perf_counter",
            return_value=100.0,
        ):
            started_at = (
                PasswordResetTimingService
                .start()
            )

        self.assertEqual(
            started_at,
            100.0,
        )

    def test_wait_sleeps_for_remaining_duration(
        self,
    ):
        with patch(
            "apps.accounts."
            "password_reset_timing_service."
            "time.perf_counter",
            return_value=100.2,
        ), patch(
            "apps.accounts."
            "password_reset_timing_service."
            "time.sleep",
        ) as mocked_sleep:

            result = (
                PasswordResetTimingService
                .wait_for_minimum_duration(
                    started_at=100.0,
                )
            )

        mocked_sleep.assert_called_once()

        self.assertAlmostEqual(
            mocked_sleep.call_args.args[0],
            0.6,
        )

        self.assertAlmostEqual(
            result["elapsed_seconds"],
            0.2,
        )

        self.assertAlmostEqual(
            result["slept_seconds"],
            0.6,
        )

    def test_wait_does_not_sleep_when_minimum_already_reached(
        self,
    ):
        with patch(
            "apps.accounts."
            "password_reset_timing_service."
            "time.perf_counter",
            return_value=101.0,
        ), patch(
            "apps.accounts."
            "password_reset_timing_service."
            "time.sleep",
        ) as mocked_sleep:

            result = (
                PasswordResetTimingService
                .wait_for_minimum_duration(
                    started_at=100.0,
                )
            )

        mocked_sleep.assert_not_called()

        self.assertAlmostEqual(
            result["elapsed_seconds"],
            1.0,
        )

        self.assertEqual(
            result["slept_seconds"],
            0,
        )

    def test_wait_does_not_sleep_at_exact_minimum(
        self,
    ):
        with patch(
            "apps.accounts."
            "password_reset_timing_service."
            "time.perf_counter",
            return_value=100.8,
        ), patch(
            "apps.accounts."
            "password_reset_timing_service."
            "time.sleep",
        ) as mocked_sleep:

            result = (
                PasswordResetTimingService
                .wait_for_minimum_duration(
                    started_at=100.0,
                )
            )

        mocked_sleep.assert_not_called()

        self.assertAlmostEqual(
            result["elapsed_seconds"],
            0.8,
        )

        self.assertEqual(
            result["slept_seconds"],
            0,
        )