from .mapping_views import mapping_api
from django.urls import (
    path,
)

from apps.migration.api.v1 import (
    views,
)


app_name = "migration_api_v1"


urlpatterns = [
    path("migrations/<str:batch_id>/mapping/", mapping_api),
    path("migrations/templates/<str:migration_type>/", views.migration_template_api, name="migration_template"),
    path(
        "migrations/",
        views.migration_collection_api,
        name="migration_collection",
    ),
    path(
        "migrations/<str:batch_id>/",
        views.migration_detail_api,
        name="migration_detail",
    ),
    path(
        "migrations/<str:batch_id>/upload/",
        views.migration_upload_api,
        name="migration_upload",
    ),
    path(
        "migrations/<str:batch_id>/validate/",
        views.migration_validate_api,
        name="migration_validate",
    ),
    path(
        "migrations/<str:batch_id>/import/",
        views.migration_import_api,
        name="migration_import",
    ),
]