from bson import (
    ObjectId,
)

from apps.finance.repositories.bank_payment_suggestion_repository import (
    BankPaymentSuggestionRepository,
)
from apps.finance.repositories.bank_statement_repository import (
    BankStatementRepository,
)
from apps.finance.services.bank_payment_suggestion_service import (
    BankPaymentSuggestionService,
)
from apps.finance.services.bank_statement_service import (
    BankStatementService,
)


class BankPaymentSuggestionAPIValidationError(
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
        self.details = (
            details
            or
            {}
        )


class BankPaymentSuggestionAPIStateError(
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
        self.details = (
            details
            or
            {}
        )


class BankPaymentSuggestionAPIService:

    @staticmethod
    def _identifier(
        value,
        field_name,
    ):
        value = str(
            value
            or
            ""
        ).strip()

        if not value:
            raise (
                BankPaymentSuggestionAPIValidationError(
                    message=(
                        f"{field_name} is required."
                    ),
                    details={
                        field_name: [
                            f"{field_name} is required.",
                        ],
                    },
                )
            )

        if not ObjectId.is_valid(
            value
        ):
            raise (
                BankPaymentSuggestionAPIValidationError(
                    message=(
                        f"{field_name} is invalid."
                    ),
                    details={
                        field_name: [
                            (
                                f"{field_name} must be a "
                                "valid identifier."
                            ),
                        ],
                    },
                )
            )

        return value

    @staticmethod
    def _line_number(
        value,
    ):
        value = str(
            value
            or
            ""
        ).strip()

        if not value:
            raise (
                BankPaymentSuggestionAPIValidationError(
                    message=(
                        "line_number is required."
                    ),
                    details={
                        "line_number": [
                            (
                                "line_number is required."
                            ),
                        ],
                    },
                )
            )

        if len(value) > 50:
            raise (
                BankPaymentSuggestionAPIValidationError(
                    message=(
                        "line_number is invalid."
                    ),
                    details={
                        "line_number": [
                            (
                                "Use no more than "
                                "50 characters."
                            ),
                        ],
                    },
                )
            )

        return value

    @staticmethod
    def _get_statement(
        *,
        organization,
        statement_id,
    ):
        statement_id = (
            BankPaymentSuggestionAPIService
            ._identifier(
                statement_id,
                "statement_id",
            )
        )

        statement = (
            BankStatementRepository
            .get_by_id(
                organization=organization,
                statement_id=statement_id,
            )
        )

        if not statement:
            raise LookupError(
                "Bank statement not found."
            )

        return statement

    @staticmethod
    def _get_suggestion(
        *,
        organization,
        suggestion_id,
    ):
        suggestion_id = (
            BankPaymentSuggestionAPIService
            ._identifier(
                suggestion_id,
                "suggestion_id",
            )
        )

        suggestion = (
            BankPaymentSuggestionRepository
            .get_by_id(
                organization=organization,
                suggestion_id=suggestion_id,
            )
        )

        if not suggestion:
            raise LookupError(
                "Payment suggestion not found."
            )

        return suggestion

    @staticmethod
    def generate_suggestion(
        *,
        user,
        organization,
        statement_id,
        line_number,
    ):
        statement = (
            BankPaymentSuggestionAPIService
            ._get_statement(
                organization=organization,
                statement_id=statement_id,
            )
        )

        line_number = (
            BankPaymentSuggestionAPIService
            ._line_number(
                line_number
            )
        )

        try:
            line = (
                BankStatementService
                .get_statement_line(
                    statement=statement,
                    line_number=line_number,
                )
            )

            if line.match_status != "UNMATCHED":
                raise ValueError(
                    "Only unmatched statement lines "
                    "can generate suggestions."
                )

            suggestion = (
                BankPaymentSuggestionService
                .generate_suggestion(
                    user=user,
                    organization=organization,
                    statement=statement,
                    line=line,
                )
            )

        except ValueError as exc:
            raise (
                BankPaymentSuggestionAPIStateError(
                    message=str(
                        exc
                    ),
                    details={
                        "state": [
                            str(exc),
                        ],
                    },
                )
            ) from exc

        if not suggestion:
            raise (
                BankPaymentSuggestionAPIStateError(
                    message=(
                        "No matching payment candidate "
                        "was found."
                    ),
                    details={
                        "candidate": [
                            (
                                "No eligible invoice or "
                                "vendor bill matched this "
                                "statement line."
                            ),
                        ],
                    },
                )
            )

        return suggestion

    @staticmethod
    def get_suggestion(
        *,
        organization,
        suggestion_id,
    ):
        return (
            BankPaymentSuggestionAPIService
            ._get_suggestion(
                organization=organization,
                suggestion_id=suggestion_id,
            )
        )

    @staticmethod
    def confirm_suggestion(
        *,
        user,
        organization,
        suggestion_id,
    ):
        suggestion = (
            BankPaymentSuggestionAPIService
            ._get_suggestion(
                organization=organization,
                suggestion_id=suggestion_id,
            )
        )

        try:
            return (
                BankPaymentSuggestionService
                .confirm_suggestion(
                    user=user,
                    organization=organization,
                    suggestion=suggestion,
                )
            )

        except ValueError as exc:
            raise (
                BankPaymentSuggestionAPIStateError(
                    message=str(exc),
                    details={
                        "state": [
                            str(exc),
                        ],
                    },
                )
            ) from exc

    @staticmethod
    def reject_suggestion(
        *,
        user,
        organization,
        suggestion_id,
    ):
        suggestion = (
            BankPaymentSuggestionAPIService
            ._get_suggestion(
                organization=organization,
                suggestion_id=suggestion_id,
            )
        )

        try:
            return (
                BankPaymentSuggestionService
                .reject_suggestion(
                    user=user,
                    organization=organization,
                    suggestion=suggestion,
                )
            )

        except ValueError as exc:
            raise (
                BankPaymentSuggestionAPIStateError(
                    message=str(exc),
                    details={
                        "state": [
                            str(exc),
                        ],
                    },
                )
            ) from exc

    @staticmethod
    def execute_suggestion(
        *,
        user,
        organization,
        suggestion_id,
    ):
        suggestion = (
            BankPaymentSuggestionAPIService
            ._get_suggestion(
                organization=organization,
                suggestion_id=suggestion_id,
            )
        )

        try:
            if (
                suggestion.suggestion_type
                ==
                "CUSTOMER_RECEIPT"
            ):
                return (
                    BankPaymentSuggestionService
                    .execute_customer_receipt(
                        user=user,
                        organization=organization,
                        suggestion=suggestion,
                    )
                )

            if (
                suggestion.suggestion_type
                ==
                "SUPPLIER_PAYMENT"
            ):
                return (
                    BankPaymentSuggestionService
                    .execute_supplier_payment(
                        user=user,
                        organization=organization,
                        suggestion=suggestion,
                    )
                )

            raise ValueError(
                "Invalid payment suggestion type."
            )

        except ValueError as exc:
            raise (
                BankPaymentSuggestionAPIStateError(
                    message=str(exc),
                    details={
                        "state": [
                            str(exc),
                        ],
                    },
                )
            ) from exc
