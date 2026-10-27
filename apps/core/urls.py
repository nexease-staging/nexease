from django.conf import settings
from django.urls import path

from apps.core import views


# ==========================================================
# PRODUCTION-SAFE CORE URLS
# ==========================================================

urlpatterns = [
    # ------------------------------------------------------
    # Health
    # ------------------------------------------------------
    path(
        "health/",
        views.health_check,
        name="health_check",
    ),
    path(
        "health/live/",
        views.liveness_check,
        name="liveness_check",
    ),
    path(
        "health/ready/",
        views.readiness_check,
        name="readiness_check",
    ),
]


# ==========================================================
# INTERNAL TEST ENDPOINTS
#
# These endpoints are useful during development/testing,
# but must not be exposed in production.
#
# settings.py controls whether they are enabled.
# Production configuration must keep
# ENABLE_INTERNAL_API_TEST_ENDPOINTS disabled.
# ==========================================================

if settings.ENABLE_INTERNAL_API_TEST_ENDPOINTS:
    urlpatterns += [
        path(
            "test-api-success/",
            views.test_api_success,
            name="test_api_success",
        ),
        path(
            "test-api-validation/",
            views.test_api_validation_error,
            name="test_api_validation_error",
        ),
        path(
            "test-api-unauthorized/",
            views.test_api_unauthorized,
            name="test_api_unauthorized",
        ),
        path(
            "test-api-forbidden/",
            views.test_api_forbidden,
            name="test_api_forbidden",
        ),
        path(
            "test-api-not-found/",
            views.test_api_not_found,
            name="test_api_not_found",
        ),
        path(
            "test-api-rate-limited/",
            views.test_api_rate_limited,
            name="test_api_rate_limited",
        ),
        path(
            "test-permission-denied/",
            views.test_permission_denied,
            name="test_permission_denied",
        ),
    ]