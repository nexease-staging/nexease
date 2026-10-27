from datetime import (
    date,
    datetime,
    time,
)
from decimal import (
    Decimal,
    InvalidOperation,
)

from bson import (
    ObjectId,
)

from apps.finance.repositories.bank_account_repository import (
    BankAccountRepository,
)
from apps.finance.repositories.bank_statement_repository import (
    BankStatementRepository,
)
from apps.finance.repositories.bank_transaction_repository import (
    BankTransactionRepository,
)
from apps.finance.services.bank_statement_service import (
    BankStatementService,
)


class BankStatementAPIValidationError(
    ValueError
):

    def __init__(
        self,
        *,
        message=(
            "Bank statement validation failed."
        ),
        details=None,
    ):
        super().__init__(
            message
        )

        self.message = message
        self.details = details or {}


class BankStatementAPIStateError(
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


class BankStatementAPIService:

    @staticmethod
    def _field_error(
        field,
        message,
    ):
        raise (
            BankStatementAPIValidationError(
                details={
                    field: [
                        message,
                    ],
                },
            )
        )

    @staticmethod
    def _identifier(
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
                BankStatementAPIService
                ._field_error(
                    field,
                    (
                        "This field must contain "
                        "a valid ObjectId."
                    ),
                )
            )

        return value.strip()

    @staticmethod
    def _required_text(
        value,
        *,
        field,
        maximum_length,
    ):
        if not isinstance(
            value,
            str,
        ):
            (
                BankStatementAPIService
                ._field_error(
                    field,
                    (
                        "This field must be "
                        "a string."
                    ),
                )
            )

        value = value.strip()

        if not value:
            (
                BankStatementAPIService
                ._field_error(
                    field,
                    "This field is required.",
                )
            )

        if len(
            value
        ) > maximum_length:
            (
                BankStatementAPIService
                ._field_error(
                    field,
                    (
                        "This field must not exceed "
                        f"{maximum_length} characters."
                    ),
                )
            )

        return value

    @staticmethod
    def _datetime(
        value,
        *,
        field,
    ):
        if isinstance(
            value,
            datetime,
        ):
            return value

        if (
            isinstance(
                value,
                date,
            )
            and
            not isinstance(
                value,
                datetime,
            )
        ):
            return datetime.combine(
                value,
                time.min,
            )

        if not isinstance(
            value,
            str,
        ):
            (
                BankStatementAPIService
                ._field_error(
                    field,
                    (
                        "Use an ISO-8601 date "
                        "or datetime."
                    ),
                )
            )

        value = value.strip()

        if not value:
            (
                BankStatementAPIService
                ._field_error(
                    field,
                    "This field is required.",
                )
            )

        try:
            if len(
                value
            ) == 10:
                return datetime.combine(
                    date.fromisoformat(
                        value
                    ),
                    time.min,
                )

            return datetime.fromisoformat(
                value.replace(
                    "Z",
                    "+00:00",
                )
            )

        except ValueError:
            (
                BankStatementAPIService
                ._field_error(
                    field,
                    (
                        "Use an ISO-8601 date "
                        "or datetime."
                    ),
                )
            )

    @staticmethod
    def _decimal(
        value,
        *,
        field,
    ):
        if isinstance(
            value,
            bool,
        ):
            (
                BankStatementAPIService
                ._field_error(
                    field,
                    "Enter a valid decimal amount.",
                )
            )

        try:
            amount = Decimal(
                str(
                    value
                )
            )

        except (
            InvalidOperation,
            TypeError,
            ValueError,
        ):
            (
                BankStatementAPIService
                ._field_error(
                    field,
                    "Enter a valid decimal amount.",
                )
            )

        if not amount.is_finite():
            (
                BankStatementAPIService
                ._field_error(
                    field,
                    "Enter a finite decimal amount.",
                )
            )

        decimal_places = (
            -amount.as_tuple().exponent
            if amount.as_tuple().exponent < 0
            else 0
        )

        if decimal_places > 2:
            (
                BankStatementAPIService
                ._field_error(
                    field,
                    (
                        "Amount must not have more "
                        "than 2 decimal places."
                    ),
                )
            )

        return amount

    @staticmethod
    def _statement(
        *,
        organization,
        statement_id,
    ):
        statement_id = (
            BankStatementAPIService
            ._identifier(
                statement_id,
                field="statement_id",
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
    def create_statement(
        *,
        user,
        organization,
        bank_account_id,
        statement_start_date,
        statement_end_date,
        opening_balance,
        closing_balance,
        raw_lines,
        source_type,
        source_filename,
    ):
        bank_account_id = (
            BankStatementAPIService
            ._identifier(
                bank_account_id,
                field="bank_account_id",
            )
        )

        bank_account = (
            BankAccountRepository
            .get_by_id(
                organization=organization,
                bank_account_id=(
                    bank_account_id
                ),
            )
        )

        if not bank_account:
            (
                BankStatementAPIService
                ._field_error(
                    "bank_account_id",
                    (
                        "Select a valid bank "
                        "account."
                    ),
                )
            )

        start_date = (
            BankStatementAPIService
            ._datetime(
                statement_start_date,
                field=(
                    "statement_start_date"
                ),
            )
        )

        end_date = (
            BankStatementAPIService
            ._datetime(
                statement_end_date,
                field=(
                    "statement_end_date"
                ),
            )
        )

        if end_date < start_date:
            (
                BankStatementAPIService
                ._field_error(
                    "statement_end_date",
                    (
                        "End date cannot be before "
                        "start date."
                    ),
                )
            )

        opening_balance = (
            BankStatementAPIService
            ._decimal(
                opening_balance,
                field="opening_balance",
            )
        )

        closing_balance = (
            BankStatementAPIService
            ._decimal(
                closing_balance,
                field="closing_balance",
            )
        )

        source_filename = str(
            source_filename
            or
            ""
        ).strip()

        if len(
            source_filename
        ) > 255:
            (
                BankStatementAPIService
                ._field_error(
                    "file",
                    (
                        "Filename must not exceed "
                        "255 characters."
                    ),
                )
            )

        if not isinstance(
            raw_lines,
            list,
        ):
            (
                BankStatementAPIService
                ._field_error(
                    "file",
                    (
                        "Statement parser must "
                        "return a list of rows."
                    ),
                )
            )

        try:
            return (
                BankStatementService
                .create_statement(
                    user=user,
                    organization=organization,
                    bank_account=bank_account,
                    statement_start_date=(
                        start_date
                    ),
                    statement_end_date=(
                        end_date
                    ),
                    opening_balance=(
                        opening_balance
                    ),
                    closing_balance=(
                        closing_balance
                    ),
                    raw_lines=raw_lines,
                    source_type=source_type,
                    source_filename=(
                        source_filename
                    ),
                )
            )

        except PermissionError:
            raise

        except ValueError as exc:
            raise (
                BankStatementAPIStateError(
                    message=str(
                        exc
                    ),
                )
            ) from exc

    @staticmethod
    def get_statement(
        *,
        organization,
        statement_id,
    ):
        return (
            BankStatementAPIService
            ._statement(
                organization=organization,
                statement_id=statement_id,
            )
        )

    @staticmethod
    def cancel_statement(
        *,
        user,
        organization,
        statement_id,
    ):
        statement = (
            BankStatementAPIService
            ._statement(
                organization=organization,
                statement_id=statement_id,
            )
        )

        try:
            return (
                BankStatementService
                .cancel_statement(
                    user=user,
                    organization=organization,
                    statement=statement,
                )
            )

        except PermissionError:
            raise

        except ValueError as exc:
            raise (
                BankStatementAPIStateError(
                    message=str(
                        exc
                    ),
                )
            ) from exc

    @staticmethod
    def auto_match_line(
        *,
        user,
        organization,
        statement_id,
        line_number,
        date_tolerance_days=2,
    ):
        statement = (
            BankStatementAPIService
            ._statement(
                organization=organization,
                statement_id=statement_id,
            )
        )

        line_number = (
            BankStatementAPIService
            ._required_text(
                line_number,
                field="line_number",
                maximum_length=50,
            )
        )

        try:
            tolerance = int(
                date_tolerance_days
            )

        except (
            TypeError,
            ValueError,
        ):
            (
                BankStatementAPIService
                ._field_error(
                    "date_tolerance_days",
                    (
                        "Enter a valid whole "
                        "number."
                    ),
                )
            )

        if (
            tolerance < 0
            or
            tolerance > 30
        ):
            (
                BankStatementAPIService
                ._field_error(
                    "date_tolerance_days",
                    (
                        "Use a value between "
                        "0 and 30."
                    ),
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

            result = (
                BankStatementService
                .auto_match_line(
                    user=user,
                    organization=organization,
                    statement=statement,
                    line=line,
                    date_tolerance_days=(
                        tolerance
                    ),
                )
            )

            statement.reload()

            line = (
                BankStatementService
                .get_statement_line(
                    statement=statement,
                    line_number=line_number,
                )
            )

            return {
                **result,
                "statement":
                    statement,
                "line":
                    line,
            }

        except PermissionError:
            raise

        except ValueError as exc:
            raise (
                BankStatementAPIStateError(
                    message=str(
                        exc
                    ),
                )
            ) from exc

    @staticmethod
    def match_line(
        *,
        user,
        organization,
        statement_id,
        line_number,
        transaction_id,
    ):
        statement = (
            BankStatementAPIService
            ._statement(
                organization=organization,
                statement_id=statement_id,
            )
        )

        line_number = (
            BankStatementAPIService
            ._required_text(
                line_number,
                field="line_number",
                maximum_length=50,
            )
        )

        transaction_id = (
            BankStatementAPIService
            ._identifier(
                transaction_id,
                field="transaction_id",
            )
        )

        transaction = (
            BankTransactionRepository
            .get_by_id(
                organization=organization,
                transaction_id=transaction_id,
            )
        )

        if not transaction:
            (
                BankStatementAPIService
                ._field_error(
                    "transaction_id",
                    (
                        "Select a valid bank "
                        "transaction."
                    ),
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

            statement = (
                BankStatementService
                .apply_match(
                    user=user,
                    organization=organization,
                    statement=statement,
                    line=line,
                    transaction=transaction,
                )
            )

            statement.reload()

            line = (
                BankStatementService
                .get_statement_line(
                    statement=statement,
                    line_number=line_number,
                )
            )

            return {
                "statement":
                    statement,
                "line":
                    line,
                "transaction":
                    transaction,
            }

        except PermissionError:
            raise

        except ValueError as exc:
            raise (
                BankStatementAPIStateError(
                    message=str(
                        exc
                    ),
                )
            ) from exc

    @staticmethod
    def ignore_line(
        *,
        user,
        organization,
        statement_id,
        line_number,
    ):
        statement = (
            BankStatementAPIService
            ._statement(
                organization=organization,
                statement_id=statement_id,
            )
        )

        line_number = (
            BankStatementAPIService
            ._required_text(
                line_number,
                field="line_number",
                maximum_length=50,
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

            statement = (
                BankStatementService
                .ignore_statement_line(
                    user=user,
                    organization=organization,
                    statement=statement,
                    line=line,
                )
            )

            statement.reload()

            line = (
                BankStatementService
                .get_statement_line(
                    statement=statement,
                    line_number=line_number,
                )
            )

            return {
                "statement":
                    statement,
                "line":
                    line,
            }

        except PermissionError:
            raise

        except ValueError as exc:
            raise (
                BankStatementAPIStateError(
                    message=str(
                        exc
                    ),
                )
            ) from exc