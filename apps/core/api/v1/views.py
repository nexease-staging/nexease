from apps.core.services.api_response_service import (
    APIResponseService,
)
from apps.core.services.api_discovery_service import (
    APIDiscoveryService,
)

def api_root(
    request,
):
    # ==================================================
    # METHOD
    # ==================================================

    if request.method != "GET":

        return (
            APIResponseService
            .method_not_allowed(
                message=(
                    "Use GET to retrieve "
                    "API discovery metadata."
                ),
                request=request,
            )
        )

    # ==================================================
    # DISCOVERY MANIFEST
    # ==================================================

    manifest = (
        APIDiscoveryService
        .get_manifest()
    )

    # ==================================================
    # RESPONSE
    # ==================================================

    return (
        APIResponseService
        .success(
            data=manifest,
            message=(
                "API discovery metadata "
                "retrieved successfully."
            ),
            request=request,
        )
    )

