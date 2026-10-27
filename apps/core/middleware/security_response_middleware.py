class SecurityResponseMiddleware:

    def __init__(
        self,
        get_response,
    ):
        self.get_response = (
            get_response
        )

    def __call__(
        self,
        request,
    ):
        response = (
            self.get_response(
                request
            )
        )

        # ==================================================
        # PERMISSIONS POLICY
        # ==================================================

        response[
            "Permissions-Policy"
        ] = (
            "camera=(), "
            "microphone=(), "
            "geolocation=()"
        )

        # ==================================================
        # API CACHE SAFETY
        # ==================================================

        if (
            request.path.startswith(
                "/api/"
            )
            or
            request.path.startswith(
                "/accounts/"
            )
            or
            request.path.startswith(
                "/finance/"
            )
            or
            request.path.startswith(
                "/sales/"
            )
            or
            request.path.startswith(
                "/purchases/"
            )
        ):

            response[
                "Cache-Control"
            ] = (
                "no-store"
            )

        return response