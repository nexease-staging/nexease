import logging


class ApplicationLoggingService:

    LOGGER_NAME = "ims"

    SENSITIVE_KEYS = {
        "password",
        "passwd",
        "secret",
        "secret_key",
        "token",
        "access_token",
        "refresh_token",
        "api_key",
        "apikey",
        "authorization",
        "cookie",
        "cookies",
        "set_cookie",
        "sessionid",
        "session_id",
        "ims_sessionid",
        "smtp_password",
        "mongodb_uri",
        "database_url",
        "client_secret",
    }

    REDACTED_VALUE = "<REDACTED>"

    @staticmethod
    def _normalize_key(
        key,
    ):
        return (
            str(
                key
            )
            .strip()
            .lower()
            .replace(
                "-",
                "_",
            )
        )

    @staticmethod
    def _is_sensitive_key(
        key,
    ):
        normalized_key = (
            ApplicationLoggingService
            ._normalize_key(
                key
            )
        )

        if (
            normalized_key
            in
            ApplicationLoggingService
            .SENSITIVE_KEYS
        ):
            return True

        sensitive_fragments = {
            "password",
            "passwd",
            "secret",
            "token",
            "api_key",
            "apikey",
            "authorization",
            "cookie",
            "session",
        }

        return any(
            fragment
            in
            normalized_key

            for fragment
            in sensitive_fragments
        )

    @staticmethod
    def _sanitize_data(
        value,
        key=None,
    ):
        # ==================================================
        # SENSITIVE KEY
        # ==================================================

        if (
            key is not None
            and
            ApplicationLoggingService
            ._is_sensitive_key(
                key
            )
        ):
            return (
                ApplicationLoggingService
                .REDACTED_VALUE
            )

        # ==================================================
        # DICTIONARY
        # ==================================================

        if isinstance(
            value,
            dict,
        ):

            return {
                str(
                    child_key
                ):
                    ApplicationLoggingService
                    ._sanitize_data(
                        child_value,
                        key=child_key,
                    )

                for (
                    child_key,
                    child_value,
                )
                in value.items()
            }

        # ==================================================
        # LIST / TUPLE / SET
        # ==================================================

        if isinstance(
            value,
            (
                list,
                tuple,
                set,
            ),
        ):

            return [
                ApplicationLoggingService
                ._sanitize_data(
                    item
                )

                for item
                in value
            ]

        # ==================================================
        # NONE
        # ==================================================

        if value is None:
            return None

        # ==================================================
        # STRING
        # ==================================================

        value = str(
            value
        )

        # Avoid obvious connection-string leakage.
        lowered_value = (
            value.lower()
        )

        if (
            "mongodb+srv://"
            in lowered_value
            or
            "mongodb://"
            in lowered_value
        ):
            return (
                ApplicationLoggingService
                .REDACTED_VALUE
            )

        return value

    @staticmethod
    def _build_context(
        *,
        module=None,
        action=None,
        status=None,
        user=None,
        organization=None,
        request_id=None,
        **extra,
    ):
        context = {}

        if module is not None:

            context[
                "module"
            ] = (
                ApplicationLoggingService
                ._sanitize_data(
                    module,
                    key="module",
                )
            )

        if action is not None:

            context[
                "action"
            ] = (
                ApplicationLoggingService
                ._sanitize_data(
                    action,
                    key="action",
                )
            )

        if status is not None:

            context[
                "status"
            ] = (
                ApplicationLoggingService
                ._sanitize_data(
                    status,
                    key="status",
                )
            )

        if user is not None:

            context[
                "user_id"
            ] = str(
                getattr(
                    user,
                    "id",
                    "",
                )
            )

        if organization is not None:

            context[
                "organization_id"
            ] = str(
                getattr(
                    organization,
                    "id",
                    "",
                )
            )

        if request_id is not None:

            context[
                "request_id"
            ] = str(
                request_id
            )

        for (
            key,
            value,
        ) in extra.items():

            context[
                key
            ] = (
                ApplicationLoggingService
                ._sanitize_data(
                    value,
                    key=key,
                )
            )

        return context

    @staticmethod
    def _format_message(
        *,
        message,
        context,
    ):
        parts = [
            str(
                message
            )
        ]

        for key in sorted(
            context.keys()
        ):

            value = (
                context[
                    key
                ]
            )

            if value is None:
                continue

            parts.append(
                f"{key}={value}"
            )

        return " | ".join(
            parts
        )

    @staticmethod
    def log(
        *,
        level,
        message,
        module=None,
        action=None,
        status=None,
        user=None,
        organization=None,
        request_id=None,
        **extra,
    ):
        logger = logging.getLogger(
            ApplicationLoggingService
            .LOGGER_NAME
        )

        context = (
            ApplicationLoggingService
            ._build_context(
                module=module,
                action=action,
                status=status,
                user=user,
                organization=organization,
                request_id=request_id,
                **extra,
            )
        )

        formatted_message = (
            ApplicationLoggingService
            ._format_message(
                message=message,
                context=context,
            )
        )

        normalized_level = (
            str(
                level
            )
            .strip()
            .upper()
        )

        if normalized_level == "DEBUG":

            logger.debug(
                formatted_message
            )

        elif normalized_level == "INFO":

            logger.info(
                formatted_message
            )

        elif normalized_level == "WARNING":

            logger.warning(
                formatted_message
            )

        elif normalized_level == "ERROR":

            logger.error(
                formatted_message
            )

        elif normalized_level == "CRITICAL":

            logger.critical(
                formatted_message
            )

        else:

            raise ValueError(
                "Invalid log level."
            )

        return formatted_message