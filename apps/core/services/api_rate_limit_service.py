from datetime import (
    datetime,
    timedelta,
)
from hashlib import sha256
from math import ceil

from apps.accounts.login_rate_limit_service import (
    LoginRateLimitService,
)
from apps.core.api_models import (
    APIRateLimitBucket,
)


class APIRateLimitUnavailable(
    RuntimeError
):

    pass


class APIRateLimitService:

    @staticmethod
    def _validate_configuration(
        *,
        scope,
        limit,
        window_seconds,
    ):
        scope = str(
            scope
            or
            ""
        ).strip()

        if not scope:

            raise ValueError(
                "Rate-limit scope is required."
            )

        try:

            limit = int(
                limit
            )

            window_seconds = int(
                window_seconds
            )

        except (
            TypeError,
            ValueError,
        ) as exc:

            raise ValueError(
                (
                    "Rate-limit values must "
                    "be integers."
                )
            ) from exc

        if limit < 1:

            raise ValueError(
                (
                    "Rate-limit limit must "
                    "be greater than zero."
                )
            )

        if window_seconds < 1:

            raise ValueError(
                (
                    "Rate-limit window must "
                    "be greater than zero."
                )
            )

        return {
            "scope":
                scope,

            "limit":
                limit,

            "window_seconds":
                window_seconds,
        }

    @staticmethod
    def _get_identity(
        request,
    ):
        user = getattr(
            request,
            "api_user",
            None,
        )

        if user:

            organization = getattr(
                request,
                "api_organization",
                None,
            )

            organization_id = (
                str(
                    organization.id
                )
                if organization
                else "no-organization"
            )

            return (
                "user:"
                f"{user.id}:"
                f"{organization_id}"
            )

        ip_address = (
            LoginRateLimitService
            .get_client_ip(
                request
            )
        )

        return (
            f"ip:{ip_address}"
        )

    @staticmethod
    def _get_window(
        *,
        now,
        window_seconds,
    ):
        timestamp = int(
            now.timestamp()
        )

        window_timestamp = (
            timestamp
            -
            (
                timestamp
                %
                window_seconds
            )
        )

        window_started_at = (
            datetime.utcfromtimestamp(
                window_timestamp
            )
        )

        window_ends_at = (
            window_started_at
            +
            timedelta(
                seconds=window_seconds
            )
        )

        return {
            "started_at":
                window_started_at,

            "ends_at":
                window_ends_at,
        }

    @staticmethod
    def check(
        request,
        *,
        scope,
        limit,
        window_seconds,
    ):
        configuration = (
            APIRateLimitService
            ._validate_configuration(
                scope=scope,
                limit=limit,
                window_seconds=(
                    window_seconds
                ),
            )
        )

        scope = configuration[
            "scope"
        ]

        limit = configuration[
            "limit"
        ]

        window_seconds = (
            configuration[
                "window_seconds"
            ]
        )

        now = datetime.utcnow()

        window = (
            APIRateLimitService
            ._get_window(
                now=now,
                window_seconds=(
                    window_seconds
                ),
            )
        )

        identity = (
            APIRateLimitService
            ._get_identity(
                request
            )
        )

        identity_hash = sha256(
            identity.encode(
                "utf-8"
            )
        ).hexdigest()

        request_method = str(
            request.method
            or
            "UNKNOWN"
        ).upper()

        bucket_source = (
            f"{scope}|"
            f"{identity_hash}|"
            f"{request_method}|"
            f"{window['started_at'].isoformat()}"
        )

        bucket_key = sha256(
            bucket_source.encode(
                "utf-8"
            )
        ).hexdigest()

        try:

            bucket = (
                APIRateLimitBucket.objects(
                    bucket_key=bucket_key
                )
                .modify(
                    upsert=True,
                    new=True,
                    inc__request_count=1,
                    set_on_insert__scope=(
                        scope
                    ),
                    set_on_insert__identity_hash=(
                        identity_hash
                    ),
                    set_on_insert__request_method=(
                        request_method
                    ),
                    set_on_insert__window_started_at=(
                        window[
                            "started_at"
                        ]
                    ),
                    set_on_insert__expires_at=(
                        window[
                            "ends_at"
                        ]
                    ),
                    set__updated_at=now,
                    set_on_insert__created_at=now,
                )
            )

        except Exception as exc:

            raise APIRateLimitUnavailable(
                (
                    "API rate-limit storage "
                    "is unavailable."
                )
            ) from exc

        request_count = int(
            bucket.request_count
        )

        remaining = max(
            limit
            -
            request_count,
            0,
        )

        retry_after = max(
            ceil(
                (
                    window[
                        "ends_at"
                    ]
                    -
                    now
                ).total_seconds()
            ),
            0,
        )

        return {
            "allowed":
                request_count
                <=
                limit,

            "scope":
                scope,

            "limit":
                limit,

            "remaining":
                remaining,

            "request_count":
                request_count,

            "window_seconds":
                window_seconds,

            "window_started_at":
                window[
                    "started_at"
                ],

            "window_ends_at":
                window[
                    "ends_at"
                ],

            "reset_timestamp":
                int(
                    window[
                        "ends_at"
                    ].timestamp()
                ),

            "retry_after":
                retry_after,
        }

    @staticmethod
    def add_headers(
        response,
        rate_limit_result,
    ):
        response[
            "X-RateLimit-Limit"
        ] = str(
            rate_limit_result[
                "limit"
            ]
        )

        response[
            "X-RateLimit-Remaining"
        ] = str(
            rate_limit_result[
                "remaining"
            ]
        )

        response[
            "X-RateLimit-Reset"
        ] = str(
            rate_limit_result[
                "reset_timestamp"
            ]
        )

        if not rate_limit_result[
            "allowed"
        ]:

            response[
                "Retry-After"
            ] = str(
                rate_limit_result[
                    "retry_after"
                ]
            )

        return response