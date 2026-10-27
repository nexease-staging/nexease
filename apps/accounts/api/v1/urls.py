from django.urls import path

from apps.accounts.api.v1 import views


app_name = "accounts_api_v1"


urlpatterns = [
    path(
        "",
        views.auth_root,
        name="root",
    ),

    path(
        "login/",
        views.login_api,
        name="login",
    ),
    path(
        "signup/",
        views.signup_api,
        name="signup",
    ),
    path(
        "logout/",
        views.logout_api,
        name="logout",
    ),
    path(
        "forgot-password/",
        views.forgot_password_api,
        name="forgot-password",
    ),
    path(
        "reset-password/",
        views.reset_password_api,
        name="reset-password",
    ),
    path(
        "me/",
        views.me_api,
        name="me",
    ),
    path(
        "authentication-audit-logs/",
        views.authentication_audit_logs_api,
        name="authentication_audit_logs",
    ),
    path(
        "csrf/",
        views.csrf_api,
        name="csrf",
    ),
    path(
        "logout-all/",
        views.logout_all_api,
        name="logout_all",
    ),
]