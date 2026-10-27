import json

from django.test import (
    Client,
    SimpleTestCase,
)


class Day53HTTPSecurityTests(
    SimpleTestCase,
):

    def setUp(self):
        self.client = Client(
            raise_request_exception=False,
        )

        self.csrf_client = Client(
            enforce_csrf_checks=True,
            raise_request_exception=False,
        )

    # ==========================================
    # SAFE REQUESTS / CSRF BOOTSTRAP
    # ==========================================

    def test_safe_csrf_bootstrap_get_succeeds_without_existing_token(
        self,
    ):
        response = self.csrf_client.get(
            "/api/v1/auth/csrf/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertIn(
            "csrftoken",
            self.csrf_client.cookies,
        )

        body = response.json()

        self.assertEqual(
            body["data"]["csrf"][
                "header_name"
            ],
            "X-CSRFToken",
        )

    # ==========================================
    # UNSAFE REQUEST WITHOUT CSRF
    # ==========================================

    def test_login_post_without_csrf_is_blocked_before_authentication(
        self,
    ):
        response = self.csrf_client.post(
            "/api/v1/auth/login/",
            data=json.dumps(
                {
                    "email":
                        "does-not-matter@example.com",
                    "password":
                        "does-not-reach-view",
                }
            ),
            content_type=
                "application/json",
        )

        self.assertEqual(
            response.status_code,
            403,
        )

        body = response.json()

        self.assertEqual(
            body["error"]["code"],
            "CSRF_FAILED",
        )

    # ==========================================
    # VALID CSRF REACHES APPLICATION LAYER
    # ==========================================

    def test_login_post_with_valid_csrf_reaches_authentication_layer(
        self,
    ):
        bootstrap = (
            self.csrf_client.get(
                "/api/v1/auth/csrf/"
            )
        )

        self.assertEqual(
            bootstrap.status_code,
            200,
        )

        csrf_token = (
            bootstrap.json()[
                "data"
            ][
                "csrf"
            ][
                "token"
            ]
        )

        response = self.csrf_client.post(
            "/api/v1/auth/login/",
            data=json.dumps(
                {
                    "email":
                        "day53-missing@example.com",
                    "password":
                        "invalid-password",
                }
            ),
            content_type=
                "application/json",
            HTTP_X_CSRFTOKEN=
                csrf_token,
        )

        # The important assertion here is that
        # CSRF middleware did NOT reject it.
        self.assertNotEqual(
            response.status_code,
            403,
        )

        body = response.json()

        if "error" in body:
            self.assertNotEqual(
                body["error"].get("code"),
                "CSRF_FAILED",
            )

    # ==========================================
    # ANONYMOUS PROTECTED RESOURCE
    # ==========================================

    def test_anonymous_me_request_is_unauthorized(
        self,
    ):
        response = self.client.get(
            "/api/v1/auth/me/"
        )

        self.assertEqual(
            response.status_code,
            401,
        )

        self.assertEqual(
            response.json()[
                "error"
            ][
                "code"
            ],
            "UNAUTHORIZED",
        )

    # ==========================================
    # METHOD SECURITY
    # ==========================================

    def test_csrf_endpoint_rejects_post(
        self,
    ):
        # Normal client is intentional here.
        # We are testing endpoint method
        # enforcement rather than middleware
        # CSRF enforcement.
        response = self.client.post(
            "/api/v1/auth/csrf/",
            data=json.dumps({}),
            content_type=
                "application/json",
        )

        self.assertEqual(
            response.status_code,
            405,
        )

        self.assertEqual(
            response.json()[
                "error"
            ][
                "code"
            ],
            "METHOD_NOT_ALLOWED",
        )

    def test_auth_root_rejects_post(
        self,
    ):
        response = self.client.post(
            "/api/v1/auth/",
            data=json.dumps({}),
            content_type=
                "application/json",
        )

        self.assertEqual(
            response.status_code,
            405,
        )

        self.assertEqual(
            response.json()[
                "error"
            ][
                "code"
            ],
            "METHOD_NOT_ALLOWED",
        )