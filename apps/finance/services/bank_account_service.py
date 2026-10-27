from uuid import uuid4

from apps.finance.repositories.bank_transaction_repository import (
    BankTransactionRepository,
)
from decimal import Decimal

from apps.finance.repositories.bank_account_repository import (
    BankAccountRepository,
)


class BankAccountService:

    VALID_ACCOUNT_TYPES = {
        "BANK",
        "CASH",
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
    def _clean_text(
        value,
    ):
        if value is None:
            return ""

        return str(
            value
        ).strip()

    @staticmethod
    def create_bank_account(
        *,
        user,
        organization,
        account_name,
        account_type,
        bank_name="",
        account_number="",
        ifsc_code="",
        currency="INR",
        opening_balance=0,
    ):
        BankAccountService._check_permission(
            user,
            "bank_accounts.create",
        )

        BankAccountService._check_organization(
            user,
            organization,
        )

        account_name = (
            BankAccountService
            ._clean_text(
                account_name
            )
        )

        account_type = (
            BankAccountService
            ._clean_text(
                account_type
            )
            .upper()
        )

        bank_name = (
            BankAccountService
            ._clean_text(
                bank_name
            )
        )

        account_number = (
            BankAccountService
            ._clean_text(
                account_number
            )
        )

        ifsc_code = (
            BankAccountService
            ._clean_text(
                ifsc_code
            )
            .upper()
        )

        currency = (
            BankAccountService
            ._clean_text(
                currency
            )
            .upper()
        )

        if not account_name:
            raise ValueError(
                "Account name is required."
            )

        if (
            account_type
            not in BankAccountService
            .VALID_ACCOUNT_TYPES
        ):
            raise ValueError(
                "Invalid account type."
            )

        if not currency:
            raise ValueError(
                "Currency is required."
            )

        try:
            opening_balance = Decimal(
                str(opening_balance)
            )
        except Exception:
            raise ValueError(
                "Invalid opening balance."
            )

        existing = (
            BankAccountRepository
            .get_by_name(
                organization=organization,
                account_name=account_name,
            )
        )

        if existing:
            raise ValueError(
                "Bank account name already exists."
            )
        if account_type == "BANK":
            if not bank_name:
                raise ValueError(
                    "Bank name is required "
                    "for bank accounts."
                )

            if not account_number:
                raise ValueError(
                    "Account number is required "
                    "for bank accounts."
                )

            existing_number = (
                BankAccountRepository
                .get_by_account_number(
                    organization=organization,
                    account_number=(
                        account_number
                    ),
                )
            )

            if existing_number:
                raise ValueError(
                    "Bank account number "
                    "already exists."
                )

        elif account_type == "CASH":
            if bank_name:
                raise ValueError(
                    "Cash accounts cannot "
                    "have a bank name."
                )

            if account_number:
                raise ValueError(
                    "Cash accounts cannot "
                    "have an account number."
                )

            if ifsc_code:
                raise ValueError(
                    "Cash accounts cannot "
                    "have an IFSC code."
                )

        bank_account = (
            BankAccountRepository
            .create_bank_account(
                organization=organization,
                account_name=account_name,
                account_type=account_type,
                bank_name=bank_name,
                account_number=(
                    account_number
                ),
                ifsc_code=ifsc_code,
                currency=currency,
                opening_balance=(
                    opening_balance
                ),
                current_balance=(
                    opening_balance
                ),
                created_by=user,
            )
        )

        try:
            (
                BankAccountService
                ._create_opening_transaction(
                    bank_account=bank_account,
                    user=user,
                )
            )

        except Exception:
            # Account creation is not considered
            # complete without its opening ledger.
            #
            # At this stage the account has just
            # been created and cannot yet have
            # legitimate downstream transactions.
            bank_account.delete()

            raise

        return bank_account

    
    @staticmethod
    def get_bank_account(
        *,
        user,
        organization,
        bank_account_id,
    ):
        BankAccountService._check_permission(
            user,
            "bank_accounts.read",
        )

        BankAccountService._check_organization(
            user,
            organization,
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
            raise ValueError(
                "Bank account not found."
            )

        return bank_account

    @staticmethod
    def list_bank_accounts(
        *,
        user,
        organization,
        account_type=None,
        is_active=None,
    ):
        BankAccountService._check_permission(
            user,
            "bank_accounts.read",
        )

        BankAccountService._check_organization(
            user,
            organization,
        )

        if account_type is not None:
            account_type = (
                BankAccountService
                ._clean_text(
                    account_type
                )
                .upper()
            )

            if (
                account_type
                not in BankAccountService
                .VALID_ACCOUNT_TYPES
            ):
                raise ValueError(
                    "Invalid account type."
                )

        return (
            BankAccountRepository
            .list_by_organization(
                organization=organization,
                account_type=account_type,
                is_active=is_active,
            )
        )

    @staticmethod
    def update_bank_account(
        *,
        user,
        organization,
        bank_account,
        account_name,
        bank_name="",
        account_number="",
        ifsc_code="",
    ):
        BankAccountService._check_permission(
            user,
            "bank_accounts.update",
        )

        BankAccountService._check_organization(
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

        account_name = (
            BankAccountService
            ._clean_text(
                account_name
            )
        )

        bank_name = (
            BankAccountService
            ._clean_text(
                bank_name
            )
        )

        account_number = (
            BankAccountService
            ._clean_text(
                account_number
            )
        )

        ifsc_code = (
            BankAccountService
            ._clean_text(
                ifsc_code
            )
            .upper()
        )

        if not account_name:
            raise ValueError(
                "Account name is required."
            )

        existing_name = (
            BankAccountRepository
            .get_by_name(
                organization=organization,
                account_name=account_name,
            )
        )

        if (
            existing_name
            and existing_name.id
            != bank_account.id
        ):
            raise ValueError(
                "Bank account name already exists."
            )
        if bank_account.account_type == "BANK":
            if not bank_name:
                raise ValueError(
                    "Bank name is required "
                    "for bank accounts."
                )

            if not account_number:
                raise ValueError(
                    "Account number is required "
                    "for bank accounts."
                )

            existing_number = (
                BankAccountRepository
                .get_by_account_number(
                    organization=organization,
                    account_number=(
                        account_number
                    ),
                )
            )

            if (
                existing_number
                and existing_number.id
                != bank_account.id
            ):
                raise ValueError(
                    "Bank account number "
                    "already exists."
                )

        elif bank_account.account_type == "CASH":
            if (
                bank_name
                or account_number
                or ifsc_code
            ):
                raise ValueError(
                    "Cash accounts cannot contain "
                    "bank details."
                )

        return (
            BankAccountRepository
            .update_details(
                bank_account=bank_account,
                account_name=account_name,
                bank_name=bank_name,
                account_number=(
                    account_number
                ),
                ifsc_code=ifsc_code,
            )
        )

    @staticmethod
    def deactivate_bank_account(
        *,
        user,
        organization,
        bank_account,
    ):
        BankAccountService._check_permission(
            user,
            "bank_accounts.deactivate",
        )

        BankAccountService._check_organization(
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
                "Bank account is already inactive."
            )

        return (
            BankAccountRepository
            .set_active_status(
                bank_account=bank_account,
                is_active=False,
            )
        )

    @staticmethod
    def _create_opening_transaction(
        *,
        bank_account,
        user,
    ):
        existing = (
            BankTransactionRepository
            .get_opening_transaction(
                organization=(
                    bank_account.organization
                ),
                bank_account=(
                    bank_account
                ),
            )
        )

        if existing:
            raise ValueError(
                "Opening balance transaction "
                "already exists."
            )

        opening_balance = Decimal(
            str(
                bank_account.opening_balance
            )
        )

        return (
            BankTransactionRepository
            .create_transaction(
                organization=(
                    bank_account.organization
                ),
                bank_account=bank_account,
                transaction_number=(
                    "BTX-"
                    + uuid4()
                    .hex[:12]
                    .upper()
                ),
                transaction_type=(
                    "OPENING_BALANCE"
                ),
                transaction_date=(
                    bank_account.created_at
                ),
                amount=abs(
                    opening_balance
                ),
                balance_before=(
                    Decimal("0")
                ),
                balance_after=(
                    opening_balance
                ),
                reference_type=(
                    "BANK_ACCOUNT_OPENING"
                ),
                reference_id=str(
                    bank_account.id
                ),
                external_reference="",
                description=(
                    "Opening balance for "
                    f"{bank_account.account_name}"
                ),
                reconciliation_status=(
                    "RECONCILED"
                ),
                reconciled_at=(
                    bank_account.created_at
                ),
                created_by=user,
            )
        )