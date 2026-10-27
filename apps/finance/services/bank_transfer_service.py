from decimal import Decimal
from uuid import uuid4

from datetime import datetime
from apps.finance.repositories.bank_transaction_repository import (
    BankTransactionRepository,
)
from apps.finance.repositories.bank_transfer_repository import (
    BankTransferRepository,
)

from apps.finance.services.bank_transaction_service import (
    BankTransactionService,
)


class BankTransferService:

    VALID_STATUSES = {
        "DRAFT",
        "POSTED",
        "CANCELLED",
    }

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
    def _generate_transfer_number():
        return (
            "TRF-"
            + uuid4().hex[:12].upper()
        )

    @staticmethod
    def _validate_accounts(
        *,
        organization,
        source_account,
        destination_account,
    ):
        if not source_account:
            raise ValueError(
                "Source account is required."
            )

        if not destination_account:
            raise ValueError(
                "Destination account is required."
            )

        if (
            source_account.organization.id
            != organization.id
        ):
            raise PermissionError(
                "Source account does not belong "
                "to this organization."
            )

        if (
            destination_account.organization.id
            != organization.id
        ):
            raise PermissionError(
                "Destination account does not belong "
                "to this organization."
            )

        if (
            source_account.id
            == destination_account.id
        ):
            raise ValueError(
                "Source and destination accounts "
                "must be different."
            )

        if not source_account.is_active:
            raise ValueError(
                "Source account is inactive."
            )

        if not destination_account.is_active:
            raise ValueError(
                "Destination account is inactive."
            )

        if (
            source_account.currency
            != destination_account.currency
        ):
            raise ValueError(
                "Source and destination account "
                "currencies must match."
            )

    @staticmethod
    def create_transfer(
        *,
        user,
        organization,
        source_account,
        destination_account,
        transfer_date,
        amount,
        reference="",
        notes="",
    ):
        BankTransferService._check_permission(
            user,
            "bank_transfers.create",
        )

        BankTransferService._check_organization(
            user,
            organization,
        )

        BankTransferService._validate_accounts(
            organization=organization,
            source_account=source_account,
            destination_account=(
                destination_account
            ),
        )

        if not transfer_date:
            raise ValueError(
                "Transfer date is required."
            )

        try:
            amount = Decimal(
                str(amount)
            )

        except Exception:
            raise ValueError(
                "Invalid transfer amount."
            )

        if amount <= 0:
            raise ValueError(
                "Transfer amount must be "
                "greater than zero."
            )

        reference = str(
            reference or ""
        ).strip()

        notes = str(
            notes or ""
        ).strip()

        transfer_number = (
            BankTransferService
            ._generate_transfer_number()
        )

        return (
            BankTransferRepository
            .create_transfer(
                organization=organization,
                transfer_number=(
                    transfer_number
                ),
                source_account=(
                    source_account
                ),
                destination_account=(
                    destination_account
                ),
                transfer_date=transfer_date,
                amount=amount,
                reference=reference,
                notes=notes,
                created_by=user,
            )
        )

    @staticmethod
    def post_transfer(
        *,
        user,
        organization,
        transfer,
    ):
        BankTransferService._check_permission(
            user,
            "bank_transfers.post",
        )

        BankTransferService._check_organization(
            user,
            organization,
        )

        if not transfer:
            raise ValueError(
                "Bank transfer is required."
            )

        if (
            transfer.organization.id
            != organization.id
        ):
            raise PermissionError(
                "Bank transfer does not belong "
                "to this organization."
            )

        transfer.reload()

        if transfer.status != "DRAFT":
            raise ValueError(
                "Only draft bank transfers "
                "can be posted."
            )

        source_account = (
            transfer.source_account
        )

        destination_account = (
            transfer.destination_account
        )

        if not source_account:
            raise ValueError(
                "Transfer has no source account."
            )

        if not destination_account:
            raise ValueError(
                "Transfer has no destination account."
            )

        source_account.reload()
        destination_account.reload()

        BankTransferService._validate_accounts(
            organization=organization,
            source_account=source_account,
            destination_account=(
                destination_account
            ),
        )

        try:
            amount = Decimal(
                str(
                    transfer.amount
                )
            )

        except Exception:
            raise ValueError(
                "Invalid transfer amount."
            )

        if amount <= 0:
            raise ValueError(
                "Transfer amount must be "
                "greater than zero."
            )

        source_balance_before = Decimal(
            str(
                source_account.current_balance
            )
        )

        destination_balance_before = Decimal(
            str(
                destination_account.current_balance
            )
        )

        reference_type = (
            "BANK_TRANSFER"
        )

        reference_id = (
            transfer.transfer_number
        )

        #
        # A posted transfer must not already
        # have ledger entries.
        #
        existing_source_transaction = (
            BankTransactionRepository
            .get_by_reference(
                organization=organization,
                bank_account=source_account,
                reference_type=reference_type,
                reference_id=reference_id,
            )
        )

        existing_destination_transaction = (
            BankTransactionRepository
            .get_by_reference(
                organization=organization,
                bank_account=destination_account,
                reference_type=reference_type,
                reference_id=reference_id,
            )
        )

        if (
            existing_source_transaction
            or existing_destination_transaction
        ):
            raise ValueError(
                "Bank transfer transactions "
                "already exist."
            )

        source_transaction = None
        destination_transaction = None

        try:
            #
            # 1. Remove money from source.
            #
            source_transaction = (
                BankTransactionService
                .create_transaction(
                    user=user,
                    organization=organization,
                    permission_code=(
                        "bank_transfers.post"
                    ),
                    bank_account=(
                        source_account
                    ),
                    transaction_type=(
                        "TRANSFER_OUT"
                    ),
                    amount=amount,
                    transaction_date=(
                        transfer.transfer_date
                    ),
                    reference_type=(
                        reference_type
                    ),
                    reference_id=(
                        reference_id
                    ),
                    external_reference=(
                        transfer.reference
                    ),
                    description=(
                        "Transfer to "
                        f"{destination_account.account_name} "
                        f"({transfer.transfer_number})"
                    ),
                )
            )

            #
            # 2. Add money to destination.
            #
            destination_transaction = (
                BankTransactionService
                .create_transaction(
                    user=user,
                    organization=organization,
                    permission_code=(
                        "bank_transfers.post"
                    ),
                    bank_account=(
                        destination_account
                    ),
                    transaction_type=(
                        "TRANSFER_IN"
                    ),
                    amount=amount,
                    transaction_date=(
                        transfer.transfer_date
                    ),
                    reference_type=(
                        reference_type
                    ),
                    reference_id=(
                        reference_id
                    ),
                    external_reference=(
                        transfer.reference
                    ),
                    description=(
                        "Transfer from "
                        f"{source_account.account_name} "
                        f"({transfer.transfer_number})"
                    ),
                )
            )

            #
            # 3. Verify both account balances.
            #
            source_account.reload()
            destination_account.reload()

            expected_source_balance = (
                source_balance_before
                - amount
            )

            expected_destination_balance = (
                destination_balance_before
                + amount
            )

            if (
                source_account.current_balance
                != expected_source_balance
            ):
                raise ValueError(
                    "Source account balance "
                    "did not update correctly."
                )

            if (
                destination_account.current_balance
                != expected_destination_balance
            ):
                raise ValueError(
                    "Destination account balance "
                    "did not update correctly."
                )

            #
            # 4. Verify organization total cash
            # remains unchanged.
            #
            total_before = (
                source_balance_before
                + destination_balance_before
            )

            total_after = (
                source_account.current_balance
                + destination_account.current_balance
            )

            if total_before != total_after:
                raise ValueError(
                    "Transfer balance integrity "
                    "check failed."
                )

            #
            # 5. Mark transfer posted only after
            # both ledger entries are successful.
            #
            transfer = (
                BankTransferRepository
                .update_status(
                    transfer=transfer,
                    status="POSTED",
                    posted_at=(
                        datetime.utcnow()
                    ),
                )
            )

            return transfer

        except Exception:
            #
            # Best-effort compensation.
            #
            # A real MongoDB transaction should
            # eventually replace this for stronger
            # multi-document atomicity.
            #

            if destination_transaction:
                try:
                    destination_transaction.delete()
                except Exception:
                    pass

            if source_transaction:
                try:
                    source_transaction.delete()
                except Exception:
                    pass

            try:
                source_account.reload()

                source_account.current_balance = (
                    source_balance_before
                )

                source_account.updated_at = (
                    datetime.utcnow()
                )

                source_account.save()

            except Exception:
                pass

            try:
                destination_account.reload()

                destination_account.current_balance = (
                    destination_balance_before
                )

                destination_account.updated_at = (
                    datetime.utcnow()
                )

                destination_account.save()

            except Exception:
                pass

            #
            # If status somehow changed before
            # the failure, restore DRAFT.
            #
            try:
                transfer.reload()

                if transfer.status != "DRAFT":
                    transfer.status = "DRAFT"
                    transfer.posted_at = None
                    transfer.updated_at = (
                        datetime.utcnow()
                    )
                    transfer.save()

            except Exception:
                pass

            raise

    @staticmethod
    def cancel_transfer(
        *,
        user,
        organization,
        transfer,
    ):
        BankTransferService._check_permission(
            user,
            "bank_transfers.cancel",
        )

        BankTransferService._check_organization(
            user,
            organization,
        )

        if not transfer:
            raise ValueError(
                "Bank transfer is required."
            )

        if (
            transfer.organization.id
            != organization.id
        ):
            raise PermissionError(
                "Bank transfer does not belong "
                "to this organization."
            )

        transfer.reload()

        if transfer.status == "POSTED":
            raise ValueError(
                "Posted bank transfers cannot "
                "be cancelled directly."
            )

        if transfer.status == "CANCELLED":
            raise ValueError(
                "Bank transfer is already cancelled."
            )

        if transfer.status != "DRAFT":
            raise ValueError(
                "Only draft bank transfers "
                "can be cancelled."
            )

        return (
            BankTransferRepository
            .update_status(
                transfer=transfer,
                status="CANCELLED",
                cancelled_at=(
                    datetime.utcnow()
                ),
            )
        )