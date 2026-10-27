from django.urls import path

from apps.accounts.api.v1 import (
    user_views,
)


app_name = "users_api_v1"


urlpatterns = [
    path(
        "",
        user_views.user_list_api,
        name="list",
    ),

    path(
        "<str:user_id>/activate/",
        user_views.user_activate_api,
        name="activate",
    ),

    path(
        "<str:user_id>/deactivate/",
        user_views.user_deactivate_api,
        name="deactivate",
    ),

    path(
        "<str:user_id>/",
        user_views.user_detail_api,
        name="detail",
    ),
]