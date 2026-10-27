from decimal import Decimal
from uuid import uuid4
from datetime import datetime
from apps.finance.repositories.bank_account_repository import (
    BankAccountRepository,
)

from apps.finance.repositories.bank_transaction_repository import (
    BankTransactionRepository,
)


class BankTransactionService:

    IN_TYPES = {
        "MONEY_IN",
        "OTHER_IN",
        "INTEREST",
        "TRANSFER_IN",
    }

    OUT_TYPES = {
        "MONEY_OUT",
        "OTHER_OUT",
        "BANK_CHARGE",
        "TRANSFER_OUT",
    }

    VALID_TRANSACTION_TYPES = (
        IN_TYPES
        | OUT_TYPES
    )

    @staticmethod
    def _check_permission(
        user,
        permission_code,
    ):
        if not user.has_permission(
            permission_code
        ):
            raise PermissionError(
                "Permission denied."
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

        if (
            not user.organization
            or user.organization.id
            != organization.id
        ):
            raise PermissionError(
                "User does not belong "
                "to this organization."
            )

    @staticmethod
    def _generate_transaction_number():
        return (
            "BTX-"
            + uuid4().hex[:12].upper()
        )

    @staticmethod
    def _calculate_balance_after(
        *,
        balance_before,
        transaction_type,
        amount,
    ):
        if (
            transaction_type
            in BankTransactionService
            .IN_TYPES
        ):
            return (
                balance_before
                + amount
            )

        if (
            transaction_type
            in BankTransactionService
            .OUT_TYPES
        ):
            return (
                balance_before
                - amount
            )

        raise ValueError(
            "Invalid transaction type."
        )

    @staticmethod
    def create_transaction(
        *,
        user,
        organization,
        bank_account,
        transaction_type,
        amount,
        transaction_date,
        reference_type="",
        reference_id="",
        external_reference="",
        description="",
        permission_code=(
            "bank_transactions.create"
        ),
    ):
        if permission_code not in {
            "bank_transactions.create",
            "bank_transfers.post",
        }:
            raise ValueError(
                "Invalid transaction permission."
            )

        BankTransactionService._check_permission(
            user,
            permission_code,
        )

        BankTransactionService._check_organization(
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

        if not bank_account.is_active:
            raise ValueError(
                "Cannot post transactions "
                "to an inactive account."
            )

        transaction_type = str(
            transaction_type
        ).strip().upper()

        if (
            transaction_type
            not in BankTransactionService
            .VALID_TRANSACTION_TYPES
        ):
            raise ValueError(
                "Invalid transaction type."
            )

        try:
            amount = Decimal(
                str(amount)
            )
        except Exception:
            raise ValueError(
                "Invalid transaction amount."
            )

        if amount <= 0:
            raise ValueError(
                "Transaction amount must be "
                "greater than zero."
            )

        if not transaction_date:
            raise ValueError(
                "Transaction date is required."
            )
        reference_type = str(
            reference_type or ""
        ).strip()

        reference_id = str(
            reference_id or ""
        ).strip()
        if bool(reference_type) != bool(
            reference_id
        ):
            raise ValueError(
                "reference_type and reference_id "
                "must be provided together."
            )

        if (
            reference_type
            and reference_id
        ):
            existing = (
                BankTransactionRepository
                .get_by_reference(
                    organization=organization,
                    bank_account=bank_account,
                    reference_type=(
                        reference_type
                    ),
                    reference_id=(
                        reference_id
                    ),
                )
            )

            if existing:
                raise ValueError(
                    "Transaction already exists "
                    "for this reference."
                )

        external_reference = str(
            external_reference or ""
        ).strip()

        description = str(
            description or ""
        ).strip()

        bank_account.reload()

        balance_before = Decimal(
            str(
                bank_account.current_balance
            )
        )

        balance_after = (
            BankTransactionService
            ._calculate_balance_after(
                balance_before=(
                    balance_before
                ),
                transaction_type=(
                    transaction_type
                ),
                amount=amount,
            )
        )
        transaction = (
            BankTransactionRepository
            .create_transaction(
                organization=organization,
                bank_account=bank_account,
                transaction_number=(
                    BankTransactionService
                    ._generate_transaction_number()
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
                    "UNRECONCILED"
                ),
                reconciled_at=None,
                created_by=user,
            )
        )

        try:
            (
                BankAccountRepository
                .update_balance(
                    bank_account=bank_account,
                    current_balance=(
                        balance_after
                    ),
                )
            )

        except Exception:
            transaction.delete()
            raise

        return transaction

    @staticmethod
    def get_transaction(
        *,
        user,
        organization,
        transaction_id,
    ):
        BankTransactionService._check_permission(
            user,
            "bank_transactions.read",
        )

        BankTransactionService._check_organization(
            user,
            organization,
        )

        transaction = (
            BankTransactionRepository
            .get_by_id(
                organization=organization,
                transaction_id=transaction_id,
            )
        )

        if not transaction:
            raise ValueError(
                "Bank transaction not found."
            )

        return transaction

    @staticmethod
    def list_transactions(
        *,
        user,
        organization,
        bank_account=None,
        transaction_type=None,
        reconciliation_status=None,
    ):
        BankTransactionService._check_permission(
            user,
            "bank_transactions.read",
        )

        BankTransactionService._check_organization(
            user,
            organization,
        )

        if bank_account is not None:
            if (
                bank_account.organization.id
                != organization.id
            ):
                raise PermissionError(
                    "Bank account does not belong "
                    "to this organization."
                )

        # Normalize transaction type
        if transaction_type:
            transaction_type = (
                str(transaction_type)
                .strip()
                .upper()
            )

        # ADD THE VALIDATION HERE
        if transaction_type:
            valid_read_types = {
                "OPENING_BALANCE",
                "MONEY_IN",
                "MONEY_OUT",
                "TRANSFER_IN",
                "TRANSFER_OUT",
                "BANK_CHARGE",
                "INTEREST",
                "OTHER_IN",
                "OTHER_OUT",
            }

            if (
                transaction_type
                not in valid_read_types
            ):
                raise ValueError(
                    "Invalid transaction type."
                )

        # Reconciliation validation
        if reconciliation_status:
            reconciliation_status = (
                str(reconciliation_status)
                .strip()
                .upper()
            )

            if reconciliation_status not in {
                "UNRECONCILED",
                "RECONCILED",
            }:
                raise ValueError(
                    "Invalid reconciliation status."
                )

        # Repository query
        return (
            BankTransactionRepository
            .list_transactions(
                organization=organization,
                bank_account=bank_account,
                transaction_type=(
                    transaction_type
                ),
                reconciliation_status=(
                    reconciliation_status
                ),
            )
        )

    @staticmethod
    def reconcile_transaction(
        *,
        user,
        organization,
        transaction,
    ):
        BankTransactionService._check_permission(
            user,
            "bank_transactions.reconcile",
        )

        BankTransactionService._check_organization(
            user,
            organization,
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

        transaction.reload()

        if (
            transaction.reconciliation_status
            == "RECONCILED"
        ):
            raise ValueError(
                "Bank transaction is already "
                "reconciled."
            )

        if (
            transaction.reconciliation_status
            != "UNRECONCILED"
        ):
            raise ValueError(
                "Invalid reconciliation status."
            )

        return (
            BankTransactionRepository
            .update_reconciliation(
                transaction=transaction,
                reconciliation_status=(
                    "RECONCILED"
                ),
                reconciled_at=(
                    datetime.utcnow()
                ),
            )
        )