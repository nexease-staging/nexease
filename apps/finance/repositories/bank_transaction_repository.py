from apps.finance.models import (
    BankTransaction,
)
from datetime import datetime

class BankTransactionRepository:

    @staticmethod
    def create_transaction(
        *,
        organization,
        bank_account,
        transaction_number,
        transaction_type,
        transaction_date,
        amount,
        balance_before,
        balance_after,
        reference_type,
        reference_id,
        external_reference,
        description,
        reconciliation_status,
        reconciled_at,
        created_by,
    ):
        transaction = BankTransaction(
            organization=organization,
            bank_account=bank_account,
            transaction_number=(
                transaction_number
            ),
            transaction_type=(
                transaction_type
            ),
            transaction_date=(
                transaction_date
            ),
            amount=amount,
            balance_before=(
                balance_before
            ),
            balance_after=(
                balance_after
            ),
            reference_type=(
                reference_type
            ),
            reference_id=(
                reference_id
            ),
            external_reference=(
                external_reference
            ),
            description=description,
            reconciliation_status=(
                reconciliation_status
            ),
            reconciled_at=reconciled_at,
            created_by=created_by,
        )

        transaction.save()

        return transaction

    @staticmethod
    def get_by_id(
        *,
        organization,
        transaction_id,
    ):
        return BankTransaction.objects(
            organization=organization,
            id=transaction_id,
        ).first()

    @staticmethod
    def get_opening_transaction(
        *,
        organization,
        bank_account,
    ):
        return BankTransaction.objects(
            organization=organization,
            bank_account=bank_account,
            transaction_type=(
                "OPENING_BALANCE"
            ),
        ).first()

    @staticmethod
    def list_by_account(
        *,
        organization,
        bank_account,
    ):
        return BankTransaction.objects(
            organization=organization,
            bank_account=bank_account,
        ).order_by(
            "transaction_date",
            "created_at",
        )

    @staticmethod
    def list_by_organization(
        *,
        organization,
    ):
        return BankTransaction.objects(
            organization=organization,
        ).order_by(
            "-transaction_date",
            "-created_at",
        )

    @staticmethod
    def get_by_reference(
        *,
        organization,
        bank_account,
        reference_type,
        reference_id,
    ):
        return BankTransaction.objects(
            organization=organization,
            bank_account=bank_account,
            reference_type=reference_type,
            reference_id=reference_id,
        ).first()

    @staticmethod
    def list_transactions(
        *,
        organization,
        bank_account=None,
        transaction_type=None,
        reconciliation_status=None,
    ):
        query = {
            "organization":
                organization,
        }

        if bank_account is not None:
            query["bank_account"] = (
                bank_account
            )

        if transaction_type:
            query["transaction_type"] = (
                transaction_type
            )

        if reconciliation_status:
            query[
                "reconciliation_status"
            ] = reconciliation_status

        return BankTransaction.objects(
            **query
        ).order_by(
            "-transaction_date",
            "-created_at",
        )

    @staticmethod
    def update_reconciliation(
        *,
        transaction,
        reconciliation_status,
        reconciled_at=None,
    ):
        transaction.reconciliation_status = (
            reconciliation_status
        )

        transaction.reconciled_at = (
            reconciled_at
        )

        transaction.save()

        return transaction

    @staticmethod
    def list_match_candidates(
        *,
        organization,
        bank_account,
        transaction_types,
        amount,
        date_from=None,
        date_to=None,
        reconciliation_status="UNRECONCILED",
    ):
        query = {
            "organization":
                organization,
            "bank_account":
                bank_account,
            "transaction_type__in":
                list(transaction_types),
            "amount":
                amount,
            "reconciliation_status":
                reconciliation_status,
        }

        if date_from is not None:
            query[
                "transaction_date__gte"
            ] = date_from

        if date_to is not None:
            query[
                "transaction_date__lte"
            ] = date_to

        return BankTransaction.objects(
            **query
        ).order_by(
            "transaction_date",
            "created_at",
        )

    @staticmethod
    def get_match_candidate_by_reference(
        *,
        organization,
        bank_account,
        transaction_types,
        amount,
        external_reference,
    ):
        return BankTransaction.objects(
            organization=organization,
            bank_account=bank_account,
            transaction_type__in=(
                list(transaction_types)
            ),
            amount=amount,
            external_reference=(
                external_reference
            ),
            reconciliation_status=(
                "UNRECONCILED"
            ),
        ).order_by(
            "transaction_date",
            "created_at",
        ).first()

    @staticmethod
    def queryset_for_organization(
        *,
        organization,
    ):
        return BankTransaction.objects(
            organization=organization,
        )