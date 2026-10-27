class APIException(
    Exception
):

    code = "API_ERROR"
    message = "API request failed."
    status = 500

    def __init__(
        self,
        message=None,
        *,
        details=None,
    ):
        self.message = (
            str(
                message
            )
            if message
            else self.message
        )

        self.details = details

        super().__init__(
            self.message
        )


class APIBadRequestError(
    APIException
):

    code = "BAD_REQUEST"
    message = "Invalid request."
    status = 400


class APIValidationError(
    APIException
):

    code = "VALIDATION_ERROR"
    message = "Validation failed."
    status = 400


class APIAuthenticationError(
    APIException
):

    code = "UNAUTHORIZED"
    message = "Not authenticated."
    status = 401


class APIAuthorizationError(
    APIException
):

    code = "FORBIDDEN"
    message = "Permission denied."
    status = 403


class APIResourceNotFoundError(
    APIException
):

    code = "NOT_FOUND"
    message = "Resource not found."
    status = 404


class APIMethodNotAllowedError(
    APIException
):

    code = "METHOD_NOT_ALLOWED"
    message = "Method not allowed."
    status = 405


class APIConflictError(
    APIException
):

    code = "CONFLICT"
    message = "Resource conflict."
    status = 409


class APIBusinessRuleError(
    APIException
):

    code = "UNPROCESSABLE_ENTITY"
    message = "Request could not be processed."
    status = 422


class APIRateLimitError(
    APIException
):

    code = "RATE_LIMITED"
    message = "Too many requests."
    status = 429


class APIServiceUnavailableError(
    APIException
):

    code = "SERVICE_UNAVAILABLE"
    message = "Service unavailable."
    status = 503