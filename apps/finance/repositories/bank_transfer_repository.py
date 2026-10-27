from datetime import datetime

from apps.finance.models import (
    BankTransfer,
)


class BankTransferRepository:

    @staticmethod
    def create_transfer(
        *,
        organization,
        transfer_number,
        source_account,
        destination_account,
        transfer_date,
        amount,
        reference,
        notes,
        created_by,
    ):
        transfer = BankTransfer(
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
            transfer_date=(
                transfer_date
            ),
            amount=amount,
            status="DRAFT",
            reference=reference,
            notes=notes,
            created_by=created_by,
        )

        transfer.save()

        return transfer

    @staticmethod
    def get_by_id(
        *,
        organization,
        transfer_id,
    ):
        return BankTransfer.objects(
            organization=organization,
            id=transfer_id,
        ).first()

    @staticmethod
    def get_by_transfer_number(
        *,
        organization,
        transfer_number,
    ):
        return BankTransfer.objects(
            organization=organization,
            transfer_number=(
                transfer_number
            ),
        ).first()

    @staticmethod
    def list_by_organization(
        *,
        organization,
        status=None,
    ):
        query = {
            "organization":
                organization,
        }

        if status:
            query["status"] = status

        return BankTransfer.objects(
            **query
        ).order_by(
            "-transfer_date",
            "-created_at",
        )

    @staticmethod
    def update_status(
        *,
        transfer,
        status,
        posted_at=None,
        cancelled_at=None,
    ):
        transfer.status = status

        if posted_at is not None:
            transfer.posted_at = (
                posted_at
            )

        if cancelled_at is not None:
            transfer.cancelled_at = (
                cancelled_at
            )

        transfer.updated_at = (
            datetime.utcnow()
        )

        transfer.save()

        return transfer

    @staticmethod
    def queryset_for_organization(
        *,
        organization,
    ):
        return BankTransfer.objects(
            organization=organization,
        )