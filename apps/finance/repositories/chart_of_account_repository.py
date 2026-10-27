from datetime import (
    datetime,
)

from mongoengine.errors import (
    ValidationError,
)

from apps.finance.models import (
    ChartOfAccount,
)


class ChartOfAccountRepository:

    @staticmethod
    def queryset_for_organization(
        *,
        organization,
    ):
        return ChartOfAccount.objects(
            organization=organization,
        )

    @staticmethod
    def create_account(
        *,
        organization,
        account_code,
        account_name,
        account_type,
        account_subtype,
        normal_balance,
        system_key,
        description,
        is_system_account,
        allow_manual_posting,
        created_by,
    ):
        account = ChartOfAccount(
            organization=organization,
            account_code=account_code,
            account_name=account_name,
            account_type=account_type,
            account_subtype=account_subtype,
            normal_balance=normal_balance,
            system_key=system_key,
            description=description,
            is_system_account=is_system_account,
            allow_manual_posting=(
                allow_manual_posting
            ),
            is_active=True,
            created_by=created_by,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        account.save()

        return account

    @staticmethod
    def get_by_id(
        *,
        organization,
        account_id,
    ):
        try:
            return (
                ChartOfAccountRepository
                .queryset_for_organization(
                    organization=organization,
                )
                .filter(
                    id=account_id,
                )
                .first()
            )

        except (
            ValidationError,
            TypeError,
            ValueError,
        ):
            return None

    @staticmethod
    def get_by_code(
        *,
        organization,
        account_code,
    ):
        return (
            ChartOfAccountRepository
            .queryset_for_organization(
                organization=organization,
            )
            .filter(
                account_code=str(
                    account_code
                ).strip(),
            )
            .first()
        )

    @staticmethod
    def get_by_system_key(
        *,
        organization,
        system_key,
        active_only=True,
    ):
        query = {
            "system_key":
                str(
                    system_key
                    or
                    ""
                )
                .strip()
                .upper(),
        }

        if active_only:
            query[
                "is_active"
            ] = True

        return (
            ChartOfAccountRepository
            .queryset_for_organization(
                organization=organization,
            )
            .filter(
                **query
            )
            .first()
        )

    @staticmethod
    def list_accounts(
        *,
        organization,
        account_type=None,
        is_active=None,
    ):
        query = {}

        if account_type is not None:
            query[
                "account_type"
            ] = str(
                account_type
            ).strip().upper()

        if is_active is not None:
            query[
                "is_active"
            ] = bool(
                is_active
            )

        return (
            ChartOfAccountRepository
            .queryset_for_organization(
                organization=organization,
            )
            .filter(
                **query
            )
            .order_by(
                "account_code",
                "id",
            )
        )

    @staticmethod
    def update_account(
        *,
        account,
        account_name=None,
        account_subtype=None,
        description=None,
        allow_manual_posting=None,
    ):
        if account_name is not None:
            account.account_name = (
                str(
                    account_name
                ).strip()
            )

        if account_subtype is not None:
            account.account_subtype = (
                str(
                    account_subtype
                ).strip()
            )

        if description is not None:
            account.description = (
                str(
                    description
                ).strip()
            )

        if allow_manual_posting is not None:
            account.allow_manual_posting = (
                bool(
                    allow_manual_posting
                )
            )

        account.updated_at = (
            datetime.utcnow()
        )

        account.save()

        return account

    @staticmethod
    def deactivate_account(
        *,
        account,
    ):
        account.is_active = False

        account.updated_at = (
            datetime.utcnow()
        )

        account.save()

        return account