from datetime import datetime

from apps.finance.models import (
    BankStatement,
)


class BankStatementRepository:

    @staticmethod
    def create_statement(
        *,
        organization,
        statement_number,
        bank_account,
        statement_start_date,
        statement_end_date,
        opening_balance,
        closing_balance,
        source_filename,
        source_type,
        lines,
        created_by,
        status="IMPORTED",
    ):
        statement = BankStatement(
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
            source_filename=(
                source_filename
            ),
            source_type=source_type,
            status=status,
            lines=lines,
            created_by=created_by,
        )

        statement.save()

        return statement

    @staticmethod
    def get_by_id(
        *,
        organization,
        statement_id,
    ):
        return BankStatement.objects(
            organization=organization,
            id=statement_id,
        ).first()

    @staticmethod
    def get_by_statement_number(
        *,
        organization,
        statement_number,
    ):
        return BankStatement.objects(
            organization=organization,
            statement_number=(
                statement_number
            ),
        ).first()

    @staticmethod
    def list_by_organization(
        *,
        organization,
        bank_account=None,
        status=None,
    ):
        query = {
            "organization":
                organization,
        }

        if bank_account is not None:
            query[
                "bank_account"
            ] = bank_account

        if status is not None:
            query[
                "status"
            ] = status

        return BankStatement.objects(
            **query
        ).order_by(
            "-statement_start_date",
            "-created_at",
        )

    @staticmethod
    def update_status(
        *,
        statement,
        status,
        reconciled_at=None,
        cancelled_at=None,
    ):
        statement.status = status

        if reconciled_at is not None:
            statement.reconciled_at = (
                reconciled_at
            )

        if cancelled_at is not None:
            statement.cancelled_at = (
                cancelled_at
            )

        statement.updated_at = (
            datetime.utcnow()
        )

        statement.save()

        return statement

    @staticmethod
    def save_statement(
        *,
        statement,
    ):
        statement.updated_at = (
            datetime.utcnow()
        )

        statement.save()

        return statement

    @staticmethod
    def queryset_for_organization(
        *,
        organization,
    ):
        return BankStatement.objects(
            organization=organization,
        )