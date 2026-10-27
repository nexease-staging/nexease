from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from apps.finance.models import (
    BankStatementLine,
)

from apps.finance.repositories.bank_statement_repository import (
    BankStatementRepository,
)

from apps.finance.repositories.bank_transaction_repository import (
    BankTransactionRepository,
)

from apps.finance.repositories.bank_statement_repository import (
    BankStatementRepository,
)
class BankStatementService:

    VALID_SOURCE_TYPES = {
        "MANUAL",
        "CSV",
        "XLSX",
    }

    VALID_STATUSES = {
        "IMPORTED",
        "PARTIALLY_RECONCILED",
        "RECONCILED",
        "CANCELLED",
    }

    @staticmethod
    def _check_permission(
        user,
        permission_code,
    ):
        if not user:
            raise ValueError(
                "User is required."
            )

        if not user.is_active:
            raise ValueError(
                "User is inactive."
            )

        if not user.has_permission(
            permission_code
        ):
            raise PermissionError(
                f"Permission denied: "
                f"{permission_code}"
            )

    @staticmethod
    def _check_organization(
        user,
        organization,
    ):
        if not organization:
            raise ValueError(
                "Organization is required."
            )

        if not user.organization:
            raise ValueError(
                "User has no organization."
            )

        if (
            user.organization.id
            != organization.id
        ):
            raise PermissionError(
                "User does not belong "
                "to this organization."
            )

    @staticmethod
    def _generate_statement_number():
        return (
            "BST-"
            + uuid4().hex[:12].upper()
        )

    @staticmethod
    def _build_lines(
        raw_lines,
    ):
        if not raw_lines:
            raise ValueError(
                "Bank statement must contain "
                "at least one line."
            )

        lines = []

        line_numbers = set()

        for raw_line in raw_lines:
            line_number = str(
                raw_line.get(
                    "line_number",
                    "",
                )
            ).strip()

            if not line_number:
                raise ValueError(
                    "Statement line number "
                    "is required."
                )

            if line_number in line_numbers:
                raise ValueError(
                    "Duplicate statement "
                    "line number."
                )

            line_numbers.add(
                line_number
            )

            transaction_date = (
                raw_line.get(
                    "transaction_date"
                )
            )

            if not transaction_date:
                raise ValueError(
                    "Transaction date is required "
                    "for every statement line."
                )

            debit_amount = Decimal(
                str(
                    raw_line.get(
                        "debit_amount",
                        0,
                    )
                )
            )

            credit_amount = Decimal(
                str(
                    raw_line.get(
                        "credit_amount",
                        0,
                    )
                )
            )

            if (
                debit_amount < 0
                or credit_amount < 0
            ):
                raise ValueError(
                    "Debit and credit amounts "
                    "cannot be negative."
                )

            if (
                debit_amount > 0
                and credit_amount > 0
            ):
                raise ValueError(
                    "A statement line cannot "
                    "contain both debit and credit."
                )

            if (
                debit_amount == 0
                and credit_amount == 0
            ):
                raise ValueError(
                    "Statement line must contain "
                    "a debit or credit amount."
                )

            running_balance_raw = (
                raw_line.get(
                    "running_balance"
                )
            )

            running_balance = None

            if (
                running_balance_raw
                is not None
            ):
                running_balance = Decimal(
                    str(
                        running_balance_raw
                    )
                )

            line = BankStatementLine(
                line_number=line_number,
                transaction_date=(
                    transaction_date
                ),
                value_date=raw_line.get(
                    "value_date"
                ),
                description=str(
                    raw_line.get(
                        "description",
                        "",
                    )
                ).strip(),
                external_reference=str(
                    raw_line.get(
                        "external_reference",
                        "",
                    )
                ).strip(),
                debit_amount=(
                    debit_amount
                ),
                credit_amount=(
                    credit_amount
                ),
                running_balance=(
                    running_balance
                ),
                match_status="UNMATCHED",
            )

            lines.append(
                line
            )

        return lines

    @staticmethod
    def create_statement(
        *,
        user,
        organization,
        bank_account,
        statement_start_date,
        statement_end_date,
        opening_balance,
        closing_balance,
        raw_lines,
        source_type="MANUAL",
        source_filename="",
    ):
        BankStatementService._check_permission(
            user,
            "bank_statements.create",
        )

        BankStatementService._check_organization(
            user,
            organization,
        )

        if not bank_account:
            raise ValueError(
                "Bank account is required."
            )

        if (
            bank_account.organization.id
            != organization.id
        ):
            raise PermissionError(
                "Bank account does not belong "
                "to this organization."
            )

        if not statement_start_date:
            raise ValueError(
                "Statement start date "
                "is required."
            )

        if not statement_end_date:
            raise ValueError(
                "Statement end date "
                "is required."
            )

        if (
            statement_end_date
            < statement_start_date
        ):
            raise ValueError(
                "Statement end date cannot "
                "be before start date."
            )

        source_type = str(
            source_type
        ).strip().upper()

        if (
            source_type
            not in BankStatementService
            .VALID_SOURCE_TYPES
        ):
            raise ValueError(
                "Invalid statement source type."
            )

        try:
            opening_balance = Decimal(
                str(
                    opening_balance
                )
            )

            closing_balance = Decimal(
                str(
                    closing_balance
                )
            )

        except Exception:
            raise ValueError(
                "Invalid statement balance."
            )

        lines = (
            BankStatementService._build_lines(
                raw_lines
            )
        )
        total_debits = sum(
            (
                line.debit_amount
                for line in lines
            ),
            Decimal("0"),
        )

        total_credits = sum(
            (
                line.credit_amount
                for line in lines
            ),
            Decimal("0"),
        )

        expected_closing = (
            opening_balance
            + total_credits
            - total_debits
        )

        if (
            expected_closing
            != closing_balance
        ):
            raise ValueError(
                "Statement balances do not "
                "reconcile with statement lines."
            )

        statement_number = (
            BankStatementService
            ._generate_statement_number()
        )

        return (
            BankStatementRepository
            .create_statement(
                organization=organization,
                statement_number=(
                    statement_number
                ),
                bank_account=bank_account,
                statement_start_date=(
                    statement_start_date
                ),
                statement_end_date=(
                    statement_end_date
                ),
                opening_balance=(
                    opening_balance
                ),
                closing_balance=(
                    closing_balance
                ),
                source_filename=str(
                    source_filename or ""
                ).strip(),
                source_type=source_type,
                lines=lines,
                created_by=user,
                status="IMPORTED",
            )
        )

    @staticmethod
    def get_statement(
        *,
        user,
        organization,
        statement_id,
    ):
        BankStatementService._check_permission(
            user,
            "bank_statements.read",
        )

        BankStatementService._check_organization(
            user,
            organization,
        )

        statement = (
            BankStatementRepository
            .get_by_id(
                organization=organization,
                statement_id=statement_id,
            )
        )

        if not statement:
            raise ValueError(
                "Bank statement not found."
            )

        return statement

    @staticmethod
    def list_statements(
        *,
        user,
        organization,
        bank_account=None,
        status=None,
    ):
        BankStatementService._check_permission(
            user,
            "bank_statements.read",
        )

        BankStatementService._check_organization(
            user,
            organization,
        )

        return (
            BankStatementRepository
            .list_by_organization(
                organization=organization,
                bank_account=bank_account,
                status=status,
            )
        )

    @staticmethod
    def cancel_statement(
        *,
        user,
        organization,
        statement,
    ):
        BankStatementService._check_permission(
            user,
            "bank_statements.cancel",
        )

        BankStatementService._check_organization(
            user,
            organization,
        )

        if not statement:
            raise ValueError(
                "Bank statement is required."
            )

        if (
            statement.organization.id
            != organization.id
        ):
            raise PermissionError(
                "Bank statement does not belong "
                "to this organization."
            )

        statement.reload()

        if (
            statement.status
            == "RECONCILED"
        ):
            raise ValueError(
                "Reconciled bank statements "
                "cannot be cancelled directly."
            )

        if (
            statement.status
            == "CANCELLED"
        ):
            raise ValueError(
                "Bank statement is already "
                "cancelled."
            )

        return (
            BankStatementRepository
            .update_status(
                statement=statement,
                status="CANCELLED",
                cancelled_at=(
                    datetime.utcnow()
                ),
            )
        )

    @staticmethod
    def _get_line_direction(
        line,
    ):
        if (
            line.credit_amount > Decimal("0")
            and line.debit_amount == Decimal("0")
        ):
            return {
                "direction": "IN",
                "amount": line.credit_amount,
                "transaction_types": {
                    "MONEY_IN",
                    "TRANSFER_IN",
                    "INTEREST",
                    "OTHER_IN",
                },
            }

        if (
            line.debit_amount > Decimal("0")
            and line.credit_amount == Decimal("0")
        ):
            return {
                "direction": "OUT",
                "amount": line.debit_amount,
                "transaction_types": {
                    "MONEY_OUT",
                    "TRANSFER_OUT",
                    "BANK_CHARGE",
                    "OTHER_OUT",
                },
            }

        raise ValueError(
            "Invalid statement line direction."
        )

    @staticmethod
    def find_match_candidate(
        *,
        user,
        organization,
        statement,
        line,
        date_tolerance_days=2,
    ):
        BankStatementService._check_permission(
            user,
            "bank_statements.reconcile",
        )

        BankStatementService._check_organization(
            user,
            organization,
        )

        if not statement:
            raise ValueError(
                "Bank statement is required."
            )

        if (
            statement.organization.id
            != organization.id
        ):
            raise PermissionError(
                "Bank statement does not belong "
                "to this organization."
            )

        if not line:
            raise ValueError(
                "Statement line is required."
            )

        if line.match_status != "UNMATCHED":
            raise ValueError(
                "Only unmatched statement lines "
                "can be matched."
            )

        direction_data = (
            BankStatementService
            ._get_line_direction(
                line
            )
        )

        amount = (
            direction_data["amount"]
        )

        transaction_types = (
            direction_data[
                "transaction_types"
            ]
        )

        bank_account = (
            statement.bank_account
        )
        if line.external_reference:
            exact_match = (
                BankTransactionRepository
                .get_match_candidate_by_reference(
                    organization=organization,
                    bank_account=bank_account,
                    transaction_types=(
                        transaction_types
                    ),
                    amount=amount,
                    external_reference=(
                        line.external_reference
                    ),
                )
            )

            if exact_match:
                return {
                    "match_type":
                        "EXACT_REFERENCE",
                    "transaction":
                        exact_match,
                }
        transaction_date = (
            line.transaction_date
        )

        date_from = (
            transaction_date
            - timedelta(
                days=date_tolerance_days
            )
        )

        date_to = (
            transaction_date
            + timedelta(
                days=date_tolerance_days
            )
        )

        candidates = (
            BankTransactionRepository
            .list_match_candidates(
                organization=organization,
                bank_account=bank_account,
                transaction_types=(
                    transaction_types
                ),
                amount=amount,
                date_from=date_from,
                date_to=date_to,
                reconciliation_status=(
                    "UNRECONCILED"
                ),
            )
        )

        candidate_list = list(
            candidates
        )

        if len(candidate_list) == 1:
            return {
                "match_type":
                    "AMOUNT_DATE",
                "transaction":
                    candidate_list[0],
            }

        if len(candidate_list) > 1:
            return {
                "match_type":
                    "AMBIGUOUS",
                "transaction":
                    None,
                "candidate_count":
                    len(candidate_list),
            }

        return {
            "match_type":
                "NO_MATCH",
            "transaction":
                None,
        }

    @staticmethod
    def apply_match(
        *,
        user,
        organization,
        statement,
        line,
        transaction,
    ):
        BankStatementService._check_permission(
            user,
            "bank_statements.reconcile",
        )

        BankStatementService._check_organization(
            user,
            organization,
        )

        if not statement:
            raise ValueError(
                "Bank statement is required."
            )

        if (
            statement.organization.id
            != organization.id
        ):
            raise PermissionError(
                "Bank statement does not belong "
                "to this organization."
            )

        if not line:
            raise ValueError(
                "Statement line is required."
            )

        if not transaction:
            raise ValueError(
                "Bank transaction is required."
            )

        if (
            transaction.organization.id
            != organization.id
        ):
            raise PermissionError(
                "Bank transaction does not belong "
                "to this organization."
            )

        if (
            transaction.bank_account.id
            != statement.bank_account.id
        ):
            raise ValueError(
                "Bank transaction does not belong "
                "to the statement bank account."
            )

        if (
            line.match_status
            != "UNMATCHED"
        ):
            raise ValueError(
                "Only unmatched statement lines "
                "can be matched."
            )
        if (
            line.matched_transaction
            is not None
        ):
            raise ValueError(
                "Statement line already has "
                "a matched transaction."
            )
        if (
            transaction.reconciliation_status
            != "UNRECONCILED"
        ):
            raise ValueError(
                "Only unreconciled bank transactions "
                "can be matched."
            )
        if (
            BankStatementService
            ._transaction_already_matched(
                organization=organization,
                transaction=transaction,
            )
        ):
            raise ValueError(
                "Bank transaction is already "
                "matched to a statement line."
            )
        
        direction_data = (
            BankStatementService
            ._get_line_direction(
                line
            )
        )

        if (
            transaction.transaction_type
            not in direction_data[
                "transaction_types"
            ]
        ):
            raise ValueError(
                "Statement line direction does not "
                "match bank transaction direction."
            )

        if (
            transaction.amount
            != direction_data["amount"]
        ):
            raise ValueError(
                "Statement line amount does not "
                "match bank transaction amount."
            )

        matched_at = (
            datetime.utcnow()
        )

        line.match_status = (
            "MATCHED"
        )

        line.matched_transaction = (
            transaction
        )

        line.matched_at = (
            matched_at
        )

        transaction = (
            BankTransactionRepository
            .update_reconciliation(
                transaction=transaction,
                reconciliation_status=(
                    "RECONCILED"
                ),
                reconciled_at=(
                    matched_at
                ),
            )
        )

        try:
            (
                BankStatementRepository
                .save_statement(
                    statement=statement
                )
            )

            statement = (
                BankStatementService
                .update_statement_reconciliation_status(
                    statement=statement,
                )
            )

        except Exception:
            try:
                (
                    BankTransactionRepository
                    .update_reconciliation(
                        transaction=transaction,
                        reconciliation_status=(
                            "UNRECONCILED"
                        ),
                        reconciled_at=None,
                    )
                )

                line.match_status = (
                    "UNMATCHED"
                )

                line.matched_transaction = None
                line.matched_at = None

            except Exception:
                pass

            raise

        return statement

    @staticmethod
    def auto_match_line(
        *,
        user,
        organization,
        statement,
        line,
        date_tolerance_days=2,
    ):
        result = (
            BankStatementService
            .find_match_candidate(
                user=user,
                organization=organization,
                statement=statement,
                line=line,
                date_tolerance_days=(
                    date_tolerance_days
                ),
            )
        )

        if result[
            "match_type"
        ] in {
            "NO_MATCH",
            "AMBIGUOUS",
        }:
            return result

        transaction = (
            result["transaction"]
        )

        BankStatementService.apply_match(
            user=user,
            organization=organization,
            statement=statement,
            line=line,
            transaction=transaction,
        )

        return {
            "match_type":
                result["match_type"],
            "transaction":
                transaction,
            "matched":
                True,
        }

    @staticmethod
    def update_statement_reconciliation_status(
        *,
        statement,
    ):
        if not statement:
            raise ValueError(
                "Bank statement is required."
            )

        if (
            statement.status
            == "CANCELLED"
        ):
            return statement

        total_lines = len(
            statement.lines
        )

        if total_lines == 0:
            return (
                BankStatementRepository
                .update_status(
                    statement=statement,
                    status="IMPORTED",
                    reconciled_at=None,
                )
            )

        active_lines = [
            line
            for line in statement.lines
            if (
                line.match_status
                != "IGNORED"
            )
        ]

        ignored_count = sum(
            1
            for line in statement.lines
            if (
                line.match_status
                == "IGNORED"
            )
        )

        matched_count = sum(
            1
            for line in active_lines
            if (
                line.match_status
                == "MATCHED"
            )
        )

        if not active_lines:
            new_status = (
                "RECONCILED"
            )

            reconciled_at = (
                datetime.utcnow()
            )

        elif (
            matched_count
            == len(active_lines)
        ):
            new_status = (
                "RECONCILED"
            )

            reconciled_at = (
                datetime.utcnow()
            )

        elif (
            matched_count > 0
            or ignored_count > 0
        ):
            new_status = (
                "PARTIALLY_RECONCILED"
            )

            reconciled_at = None

        else:
            new_status = (
                "IMPORTED"
            )

            reconciled_at = None

        return (
            BankStatementRepository
            .update_status(
                statement=statement,
                status=new_status,
                reconciled_at=(
                    reconciled_at
                ),
            )
        )

    @staticmethod
    def _transaction_already_matched(
        *,
        organization,
        transaction,
    ):
        from apps.finance.models import (
            BankStatement,
        )

        statements = BankStatement.objects(
            organization=organization,
            status__ne="CANCELLED",
        )

        return any(
            (
                line.match_status == "MATCHED"
                and line.matched_transaction is not None
                and line.matched_transaction.id
                == transaction.id
            )
            for statement in statements
            for line in statement.lines
        )

    @staticmethod
    def get_statement_line(
        *,
        statement,
        line_number,
    ):
        if not statement:
            raise ValueError(
                "Bank statement is required."
            )

        line_number = str(
            line_number
        ).strip()

        if not line_number:
            raise ValueError(
                "Statement line number is required."
            )

        line = next(
            (
                item
                for item in statement.lines
                if item.line_number
                == line_number
            ),
            None,
        )

        if not line:
            raise ValueError(
                "Bank statement line not found."
            )

        return line

    @staticmethod
    def ignore_statement_line(
        *,
        user,
        organization,
        statement,
        line,
    ):
        BankStatementService._check_permission(
            user,
            "bank_statements.reconcile",
        )

        BankStatementService._check_organization(
            user,
            organization,
        )

        if not statement:
            raise ValueError(
                "Bank statement is required."
            )

        if (
            statement.organization.id
            != organization.id
        ):
            raise PermissionError(
                "Bank statement does not belong "
                "to this organization."
            )

        if not line:
            raise ValueError(
                "Statement line is required."
            )

        #
        # Preserve the line identity BEFORE
        # reloading the parent document.
        #
        line_number = str(
            line.line_number
        )

        statement.reload()

        if (
            statement.status
            == "CANCELLED"
        ):
            raise ValueError(
                "Cancelled bank statements "
                "cannot be modified."
            )

        #
        # IMPORTANT:
        # statement.reload() creates fresh
        # embedded BankStatementLine objects.
        #
        # Therefore we must reacquire the line
        # from statement.lines.
        #
        current_line = next(
            (
                item
                for item in statement.lines
                if (
                    item.line_number
                    == line_number
                )
            ),
            None,
        )

        if not current_line:
            raise ValueError(
                "Bank statement line not found."
            )

        if (
            current_line.match_status
            == "MATCHED"
        ):
            raise ValueError(
                "Matched statement lines "
                "cannot be ignored."
            )

        if (
            current_line.match_status
            == "IGNORED"
        ):
            raise ValueError(
                "Statement line is already "
                "ignored."
            )

        if (
            current_line.match_status
            != "UNMATCHED"
        ):
            raise ValueError(
                "Only unmatched statement lines "
                "can be ignored."
            )

        if (
            current_line.matched_transaction
            is not None
        ):
            raise ValueError(
                "Statement line already has "
                "a matched transaction."
            )

        current_line.match_status = (
            "IGNORED"
        )

        current_line.matched_transaction = (
            None
        )

        current_line.matched_at = None

        (
            BankStatementRepository
            .save_statement(
                statement=statement
            )
        )

        statement.reload()

        statement = (
            BankStatementService
            .update_statement_reconciliation_status(
                statement=statement,
            )
        )

        return statement