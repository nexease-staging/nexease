from bson import (
    ObjectId,
)

from apps.finance.repositories.chart_of_account_repository import (
    ChartOfAccountRepository,
)
from apps.finance.services.chart_of_account_service import (
    ChartOfAccountService,
)


class ChartOfAccountAPIValidationError(
    ValueError
):

    def __init__(
        self,
        *,
        message=(
            "Chart of account "
            "validation failed."
        ),
        details=None,
    ):
        super().__init__(
            message
        )

        self.message = message
        self.details = details or {}


class ChartOfAccountAPIStateError(
    ValueError
):

    def __init__(
        self,
        *,
        message,
        details=None,
    ):
        super().__init__(
            message
        )

        self.message = message
        self.details = details or {}


class ChartOfAccountAPIService:

    ACCOUNT_TYPES = {
        "ASSET",
        "LIABILITY",
        "EQUITY",
        "REVENUE",
        "EXPENSE",
    }

    CREATE_FIELDS = {
        "account_code",
        "account_name",
        "account_type",
        "account_subtype",
        "description",
        "allow_manual_posting",
    }

    UPDATE_FIELDS = {
        "account_name",
        "account_subtype",
        "description",
        "allow_manual_posting",
    }

    @staticmethod
    def _raise_field_error(
        field,
        message,
    ):
        raise (
            ChartOfAccountAPIValidationError(
                details={
                    field: [
                        message,
                    ],
                },
            )
        )

    @staticmethod
    def _validate_payload_object(
        payload,
    ):
        if not isinstance(
            payload,
            dict,
        ):
            raise (
                ChartOfAccountAPIValidationError(
                    details={
                        "body": [
                            (
                                "JSON body must "
                                "be an object."
                            ),
                        ],
                    },
                )
            )

    @staticmethod
    def _validate_allowed_fields(
        payload,
        *,
        allowed_fields,
    ):
        unknown_fields = (
            set(
                payload.keys()
            )
            -
            allowed_fields
        )

        if unknown_fields:
            raise (
                ChartOfAccountAPIValidationError(
                    details={
                        field: [
                            (
                                "This field is "
                                "not supported."
                            ),
                        ]
                        for field
                        in sorted(
                            unknown_fields
                        )
                    },
                )
            )

    @staticmethod
    def _normalize_identifier(
        value,
        *,
        field,
    ):
        if (
            not isinstance(
                value,
                str,
            )
            or
            not ObjectId.is_valid(
                value.strip()
            )
        ):
            (
                ChartOfAccountAPIService
                ._raise_field_error(
                    field,
                    (
                        "This field must contain "
                        "a valid ObjectId."
                    ),
                )
            )

        return value.strip()

    @staticmethod
    def _normalize_required_text(
        value,
        *,
        field,
        maximum_length=None,
    ):
        if not isinstance(
            value,
            str,
        ):
            (
                ChartOfAccountAPIService
                ._raise_field_error(
                    field,
                    (
                        "This field must be "
                        "a string."
                    ),
                )
            )

        normalized = value.strip()

        if not normalized:
            (
                ChartOfAccountAPIService
                ._raise_field_error(
                    field,
                    "This field is required.",
                )
            )

        if (
            maximum_length is not None
            and
            len(
                normalized
            )
            >
            maximum_length
        ):
            (
                ChartOfAccountAPIService
                ._raise_field_error(
                    field,
                    (
                        "This field must not exceed "
                        f"{maximum_length} characters."
                    ),
                )
            )

        return normalized

    @staticmethod
    def _normalize_optional_text(
        value,
        *,
        field,
        maximum_length=None,
    ):
        if value is None:
            return ""

        if not isinstance(
            value,
            str,
        ):
            (
                ChartOfAccountAPIService
                ._raise_field_error(
                    field,
                    (
                        "This field must be "
                        "a string."
                    ),
                )
            )

        normalized = value.strip()

        if (
            maximum_length is not None
            and
            len(
                normalized
            )
            >
            maximum_length
        ):
            (
                ChartOfAccountAPIService
                ._raise_field_error(
                    field,
                    (
                        "This field must not exceed "
                        f"{maximum_length} characters."
                    ),
                )
            )

        return normalized

    @staticmethod
    def _normalize_boolean(
        value,
        *,
        field,
    ):
        if not isinstance(
            value,
            bool,
        ):
            (
                ChartOfAccountAPIService
                ._raise_field_error(
                    field,
                    (
                        "This field must be "
                        "a boolean."
                    ),
                )
            )

        return value

    @staticmethod
    def _normalize_account_type(
        value,
    ):
        normalized = (
            ChartOfAccountAPIService
            ._normalize_required_text(
                value,
                field="account_type",
                maximum_length=30,
            )
            .upper()
        )

        if (
            normalized
            not in
            ChartOfAccountAPIService
            .ACCOUNT_TYPES
        ):
            (
                ChartOfAccountAPIService
                ._raise_field_error(
                    "account_type",
                    (
                        "Select a valid account "
                        "type."
                    ),
                )
            )

        return normalized

    @staticmethod
    def validate_create_payload(
        payload,
    ):
        (
            ChartOfAccountAPIService
            ._validate_payload_object(
                payload
            )
        )

        (
            ChartOfAccountAPIService
            ._validate_allowed_fields(
                payload,
                allowed_fields=(
                    ChartOfAccountAPIService
                    .CREATE_FIELDS
                ),
            )
        )

        missing_fields = [
            field
            for field
            in (
                "account_code",
                "account_name",
                "account_type",
            )
            if field not in payload
        ]

        if missing_fields:
            raise (
                ChartOfAccountAPIValidationError(
                    details={
                        field: [
                            "This field is required.",
                        ]
                        for field
                        in missing_fields
                    },
                )
            )

        values = {
            "account_code": (
                ChartOfAccountAPIService
                ._normalize_required_text(
                    payload.get(
                        "account_code"
                    ),
                    field="account_code",
                    maximum_length=30,
                )
                .upper()
            ),
            "account_name": (
                ChartOfAccountAPIService
                ._normalize_required_text(
                    payload.get(
                        "account_name"
                    ),
                    field="account_name",
                    maximum_length=150,
                )
            ),
            "account_type": (
                ChartOfAccountAPIService
                ._normalize_account_type(
                    payload.get(
                        "account_type"
                    )
                )
            ),
            "account_subtype": (
                ChartOfAccountAPIService
                ._normalize_optional_text(
                    payload.get(
                        "account_subtype",
                        "",
                    ),
                    field="account_subtype",
                    maximum_length=50,
                )
                .upper()
            ),
            "description": (
                ChartOfAccountAPIService
                ._normalize_optional_text(
                    payload.get(
                        "description",
                        "",
                    ),
                    field="description",
                    maximum_length=500,
                )
            ),
            "allow_manual_posting": (
                True
            ),
        }

        if (
            "allow_manual_posting"
            in payload
        ):
            values[
                "allow_manual_posting"
            ] = (
                ChartOfAccountAPIService
                ._normalize_boolean(
                    payload[
                        "allow_manual_posting"
                    ],
                    field=(
                        "allow_manual_posting"
                    ),
                )
            )

        return values

    @staticmethod
    def validate_update_payload(
        payload,
    ):
        (
            ChartOfAccountAPIService
            ._validate_payload_object(
                payload
            )
        )

        (
            ChartOfAccountAPIService
            ._validate_allowed_fields(
                payload,
                allowed_fields=(
                    ChartOfAccountAPIService
                    .UPDATE_FIELDS
                ),
            )
        )

        if not payload:
            raise (
                ChartOfAccountAPIValidationError(
                    details={
                        "body": [
                            (
                                "Provide at least one "
                                "editable field."
                            ),
                        ],
                    },
                )
            )

        values = {}

        if "account_name" in payload:
            values[
                "account_name"
            ] = (
                ChartOfAccountAPIService
                ._normalize_required_text(
                    payload[
                        "account_name"
                    ],
                    field="account_name",
                    maximum_length=150,
                )
            )

        if "account_subtype" in payload:
            values[
                "account_subtype"
            ] = (
                ChartOfAccountAPIService
                ._normalize_optional_text(
                    payload[
                        "account_subtype"
                    ],
                    field="account_subtype",
                    maximum_length=50,
                )
                .upper()
            )

        if "description" in payload:
            values[
                "description"
            ] = (
                ChartOfAccountAPIService
                ._normalize_optional_text(
                    payload[
                        "description"
                    ],
                    field="description",
                    maximum_length=500,
                )
            )

        if (
            "allow_manual_posting"
            in payload
        ):
            values[
                "allow_manual_posting"
            ] = (
                ChartOfAccountAPIService
                ._normalize_boolean(
                    payload[
                        "allow_manual_posting"
                    ],
                    field=(
                        "allow_manual_posting"
                    ),
                )
            )

        return values

    @staticmethod
    def get_account(
        *,
        organization,
        account_id,
    ):
        normalized_id = (
            ChartOfAccountAPIService
            ._normalize_identifier(
                account_id,
                field="account_id",
            )
        )

        account = (
            ChartOfAccountRepository
            .get_by_id(
                organization=organization,
                account_id=normalized_id,
            )
        )

        if not account:
            raise LookupError(
                "Chart of account not found."
            )

        return account

    @staticmethod
    def create_account(
        *,
        user,
        organization,
        payload,
    ):
        values = (
            ChartOfAccountAPIService
            .validate_create_payload(
                payload
            )
        )

        try:
            return (
                ChartOfAccountService
                .create_account(
                    user=user,
                    organization=organization,
                    **values,
                )
            )

        except PermissionError:
            raise

        except ValueError as exc:
            raise (
                ChartOfAccountAPIStateError(
                    message=str(
                        exc
                    ),
                    details={
                        "account": [
                            str(
                                exc
                            ),
                        ],
                    },
                )
            ) from exc

    @staticmethod
    def update_account(
        *,
        user,
        organization,
        account_id,
        payload,
    ):
        account = (
            ChartOfAccountAPIService
            .get_account(
                organization=organization,
                account_id=account_id,
            )
        )

        values = (
            ChartOfAccountAPIService
            .validate_update_payload(
                payload
            )
        )

        try:
            return (
                ChartOfAccountService
                .update_account(
                    user=user,
                    organization=organization,
                    account_id=str(
                        account.id
                    ),
                    **values,
                )
            )

        except PermissionError:
            raise

        except ValueError as exc:
            raise (
                ChartOfAccountAPIStateError(
                    message=str(
                        exc
                    ),
                    details={
                        "account": [
                            str(
                                exc
                            ),
                        ],
                    },
                )
            ) from exc

    @staticmethod
    def deactivate_account(
        *,
        user,
        organization,
        account_id,
    ):
        account = (
            ChartOfAccountAPIService
            .get_account(
                organization=organization,
                account_id=account_id,
            )
        )

        try:
            return (
                ChartOfAccountService
                .deactivate_account(
                    user=user,
                    organization=organization,
                    account_id=str(
                        account.id
                    ),
                )
            )

        except PermissionError:
            raise

        except ValueError as exc:
            raise (
                ChartOfAccountAPIStateError(
                    message=str(
                        exc
                    ),
                    details={
                        "account": [
                            str(
                                exc
                            ),
                        ],
                    },
                )
            ) from exc