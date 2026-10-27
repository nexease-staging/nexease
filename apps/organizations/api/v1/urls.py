from django.urls import path

from apps.organizations.api.v1 import (
    views,
)


app_name = "organizations_api_v1"


urlpatterns = [
    path(
        "",
        views.current_organization_api,
        name="current",
    ),
]