from django.urls import path

from apps.authorization.api.v1 import (
    views,
)


app_name = "authorization_api_v1"


urlpatterns = [
    path(
        "permissions/",
        views.permission_list_api,
        name="permission_list",
    ),

    path(
        "roles/",
        views.role_list_api,
        name="role_list",
    ),

    path(
        "roles/<str:role_id>/permissions/",
        views.role_permissions_api,
        name="role_permissions",
    ),

    path(
        "roles/<str:role_id>/activate/",
        views.role_activate_api,
        name="role_activate",
    ),

    path(
        "roles/<str:role_id>/deactivate/",
        views.role_deactivate_api,
        name="role_deactivate",
    ),

    path(
        "roles/<str:role_id>/",
        views.role_detail_api,
        name="role_detail",
    ),
]