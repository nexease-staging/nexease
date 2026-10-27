from datetime import (
    datetime,
    timezone,
)


class APIMetadataService:

    API_VERSION = "v1"

    @staticmethod
    def _utc_timestamp():
        return (
            datetime.now(
                timezone.utc
            )
            .isoformat()
            .replace(
                "+00:00",
                "Z",
            )
        )

    @staticmethod
    def build(
        request=None,
    ):
        metadata = {
            "api_version":
                (
                    APIMetadataService
                    .API_VERSION
                ),

            "response_timestamp":
                (
                    APIMetadataService
                    ._utc_timestamp()
                ),
        }

        if request is None:

            return metadata

        client_correlation_id = getattr(
            request,
            "client_correlation_id",
            None,
        )

        if client_correlation_id:

            metadata[
                "client_correlation_id"
            ] = str(
                client_correlation_id
            )

        return metadata

    @staticmethod
    def attach(
        payload,
        *,
        request=None,
    ):
        payload = dict(
            payload
        )

        request_id = getattr(
            request,
            "request_id",
            None,
        )

        if request_id:

            payload[
                "request_id"
            ] = str(
                request_id
            )

        payload[
            "meta"
        ] = (
            APIMetadataService
            .build(
                request
            )
        )

        return payload