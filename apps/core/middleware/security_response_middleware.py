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

        user = getattr(request, 'api_user', None) or getattr(request, 'user', None)
        if user and getattr(user, 'is_authenticated', True) and not getattr(response, 'streaming', False) and 'application/json' in response.get('Content-Type', '') and b'"cost_price"' in response.content:
            from apps.core.services.cost_visibility import can_read_cost, redact_costs
            if not can_read_cost(user):
                import json
                data = json.loads(response.content)
                response.content = json.dumps(redact_costs(data), default=str).encode('utf-8')
                if response.has_header('Content-Length'):
                    response['Content-Length'] = str(len(response.content))
        return response