from datetime import datetime

from apps.finance.models import (
    BankAccount,
)


class BankAccountRepository:

    @staticmethod
    def queryset_for_organization(
        *,
        organization,
    ):
        return BankAccount.objects(
            organization=organization,
        )
    @staticmethod
    def get_by_id(
        *,
        organization,
        bank_account_id,
    ):
        return (
            BankAccountRepository
            .queryset_for_organization(
                organization=organization,
            )
            .filter(
                id=bank_account_id,
            )
            .first()
        )

    @staticmethod
    def get_by_name(
        *,
        organization,
        account_name,
    ):
        return BankAccount.objects(
            organization=organization,
            account_name=account_name,
        ).first()

    @staticmethod
    def get_by_account_number(
        *,
        organization,
        account_number,
    ):
        return BankAccount.objects(
            organization=organization,
            account_number=account_number,
            account_type="BANK",
        ).first()

    @staticmethod
    def list_by_organization(
        *,
        organization,
        account_type=None,
        is_active=None,
    ):
        query = {}

        if account_type is not None:
            query[
                "account_type"
            ] = account_type

        if is_active is not None:
            query[
                "is_active"
            ] = is_active

        return (
            BankAccountRepository
            .queryset_for_organization(
                organization=organization,
            )
            .filter(
                **query
            )
            .order_by(
                "account_name",
                "id",
            )
        )

    @staticmethod
    def create_bank_account(
        *,
        organization,
        account_name,
        account_type,
        bank_name,
        account_number,
        ifsc_code,
        currency,
        opening_balance,
        current_balance,
        created_by,
    ):
        bank_account = BankAccount(
            organization=organization,
            account_name=account_name,
            account_type=account_type,
            bank_name=bank_name,
            account_number=account_number,
            ifsc_code=ifsc_code,
            currency=currency,
            opening_balance=opening_balance,
            current_balance=current_balance,
            is_active=True,
            created_by=created_by,
        )

        bank_account.save()

        return bank_account

    @staticmethod
    def update_details(
        *,
        bank_account,
        account_name,
        bank_name,
        account_number,
        ifsc_code,
    ):
        bank_account.account_name = (
            account_name
        )

        bank_account.bank_name = (
            bank_name
        )

        bank_account.account_number = (
            account_number
        )

        bank_account.ifsc_code = (
            ifsc_code
        )

        bank_account.updated_at = (
            datetime.utcnow()
        )

        bank_account.save()

        return bank_account

    @staticmethod
    def update_balance(
        *,
        bank_account,
        current_balance,
    ):
        bank_account.current_balance = (
            current_balance
        )

        bank_account.updated_at = (
            datetime.utcnow()
        )

        bank_account.save()

        return bank_account

    @staticmethod
    def set_active_status(
        *,
        bank_account,
        is_active,
    ):
        bank_account.is_active = (
            is_active
        )

        bank_account.updated_at = (
            datetime.utcnow()
        )

        bank_account.save()

        return bank_account