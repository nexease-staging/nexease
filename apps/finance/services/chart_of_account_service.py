from datetime import datetime

from apps.authorization.services import (
    AuthorizationService,
)

from apps.finance.repositories.chart_of_account_repository import (
    ChartOfAccountRepository,
)


class ChartOfAccountService:

    VALID_ACCOUNT_TYPES = {
        "ASSET",
        "LIABILITY",
        "EQUITY",
        "REVENUE",
        "EXPENSE",
    }

    NORMAL_BALANCE_BY_TYPE = {
        "ASSET": "DEBIT",
        "EXPENSE": "DEBIT",
        "LIABILITY": "CREDIT",
        "EQUITY": "CREDIT",
        "REVENUE": "CREDIT",
    }

    DEFAULT_ACCOUNTS = [
        # ==================================================
        # ASSETS
        # ==================================================
        {
            "account_code": "1000",
            "account_name": "Cash",
            "account_type": "ASSET",
            "account_subtype": "CURRENT_ASSET",
            "normal_balance": "DEBIT",
            "system_key": "CASH",
            "description": "Cash on hand.",
            "is_system_account": True,
            "allow_manual_posting": True,
        },
        {
            "account_code": "1010",
            "account_name": "Bank",
            "account_type": "ASSET",
            "account_subtype": "CURRENT_ASSET",
            "normal_balance": "DEBIT",
            "system_key": "BANK",
            "description": "Bank account control account.",
            "is_system_account": True,
            "allow_manual_posting": True,
        },
        {
            "account_code": "1100",
            "account_name": "Accounts Receivable",
            "account_type": "ASSET",
            "account_subtype": "CURRENT_ASSET",
            "normal_balance": "DEBIT",
            "system_key": "ACCOUNTS_RECEIVABLE",
            "description": "Amounts due from customers.",
            "is_system_account": True,
            "allow_manual_posting": False,
        },
        {
            "account_code": "1200",
            "account_name": "Inventory",
            "account_type": "ASSET",
            "account_subtype": "CURRENT_ASSET",
            "normal_balance": "DEBIT",
            "system_key": "INVENTORY",
            "description": "Inventory control account.",
            "is_system_account": True,
            "allow_manual_posting": False,
        },
        {
            "account_code": "1300",
            "account_name": "Input Tax Credit",
            "account_type": "ASSET",
            "account_subtype": "CURRENT_ASSET",
            "normal_balance": "DEBIT",
            "system_key": "INPUT_TAX",
            "description": "Recoverable input tax credit.",
            "is_system_account": True,
            "allow_manual_posting": False,
        },
        {
            "account_code": "1400",
            "account_name": "Prepaid Expenses",
            "account_type": "ASSET",
            "account_subtype": "CURRENT_ASSET",
            "normal_balance": "DEBIT",
            "system_key": "PREPAID_EXPENSE",
            "description": "Expenses paid in advance.",
            "is_system_account": False,
            "allow_manual_posting": True,
        },

        # ==================================================
        # LIABILITIES
        # ==================================================
        {
            "account_code": "2000",
            "account_name": "Accounts Payable",
            "account_type": "LIABILITY",
            "account_subtype": "CURRENT_LIABILITY",
            "normal_balance": "CREDIT",
            "system_key": "ACCOUNTS_PAYABLE",
            "description": "Amounts payable to suppliers.",
            "is_system_account": True,
            "allow_manual_posting": False,
        },
        {
            "account_code": "2100",
            "account_name": "Output Tax Payable",
            "account_type": "LIABILITY",
            "account_subtype": "CURRENT_LIABILITY",
            "normal_balance": "CREDIT",
            "system_key": "OUTPUT_TAX",
            "description": "Output tax collected on sales.",
            "is_system_account": True,
            "allow_manual_posting": False,
        },
        {
            "account_code": "2200",
            "account_name": "Tax Payable",
            "account_type": "LIABILITY",
            "account_subtype": "CURRENT_LIABILITY",
            "normal_balance": "CREDIT",
            "system_key": "TAX_PAYABLE",
            "description": "General statutory tax payable.",
            "is_system_account": False,
            "allow_manual_posting": True,
        },

        # ==================================================
        # EQUITY
        # ==================================================
        {
            "account_code": "3000",
            "account_name": "Owner's Equity",
            "account_type": "EQUITY",
            "account_subtype": "CAPITAL",
            "normal_balance": "CREDIT",
            "system_key": "OWNERS_EQUITY",
            "description": "Owner or shareholder capital.",
            "is_system_account": True,
            "allow_manual_posting": True,
        },
        {
            "account_code": "3100",
            "account_name": "Retained Earnings",
            "account_type": "EQUITY",
            "account_subtype": "RETAINED_EARNINGS",
            "normal_balance": "CREDIT",
            "system_key": "RETAINED_EARNINGS",
            "description": "Accumulated retained earnings.",
            "is_system_account": True,
            "allow_manual_posting": False,
        },

        # ==================================================
        # REVENUE
        # ==================================================
        {
            "account_code": "4000",
            "account_name": "Sales Revenue",
            "account_type": "REVENUE",
            "account_subtype": "OPERATING_REVENUE",
            "normal_balance": "CREDIT",
            "system_key": "SALES_REVENUE",
            "description": "Revenue from product sales.",
            "is_system_account": True,
            "allow_manual_posting": False,
        },
        {
            "account_code": "4100",
            "account_name": "Other Income",
            "account_type": "REVENUE",
            "account_subtype": "OTHER_REVENUE",
            "normal_balance": "CREDIT",
            "system_key": "OTHER_INCOME",
            "description": "Other non-core income.",
            "is_system_account": False,
            "allow_manual_posting": True,
        },

        # ==================================================
        # EXPENSES
        # ==================================================
        {
            "account_code": "5000",
            "account_name": "Cost of Goods Sold",
            "account_type": "EXPENSE",
            "account_subtype": "COST_OF_SALES",
            "normal_balance": "DEBIT",
            "system_key": "COST_OF_GOODS_SOLD",
            "description": "Cost of inventory sold.",
            "is_system_account": True,
            "allow_manual_posting": False,
        },
        {
            "account_code": "5100",
            "account_name": "Purchase Expense",
            "account_type": "EXPENSE",
            "account_subtype": "OPERATING_EXPENSE",
            "normal_balance": "DEBIT",
            "system_key": "PURCHASE_EXPENSE",
            "description": "Purchases expensed directly.",
            "is_system_account": True,
            "allow_manual_posting": False,
        },
        {
            "account_code": "5200",
            "account_name": "Bank Charges",
            "account_type": "EXPENSE",
            "account_subtype": "FINANCE_EXPENSE",
            "normal_balance": "DEBIT",
            "system_key": "BANK_CHARGES",
            "description": "Banking and transaction charges.",
            "is_system_account": True,
            "allow_manual_posting": True,
        },
        {
            "account_code": "5900",
            "account_name": "Other Expenses",
            "account_type": "EXPENSE",
            "account_subtype": "OTHER_EXPENSE",
            "normal_balance": "DEBIT",
            "system_key": "OTHER_EXPENSE",
            "description": "Other operating expenses.",
            "is_system_account": False,
            "allow_manual_posting": True,
        },
    ]

    # ==================================================
    # COMMON VALIDATION
    # ==================================================

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

        if not AuthorizationService.has_permission(
            user,
            permission_code,
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
    def _clean_required_text(
        value,
        field_name,
    ):
        value = str(
            value or ""
        ).strip()

        if not value:
            raise ValueError(
                f"{field_name} is required."
            )

        return value

    @staticmethod
    def _normalize_account_type(
        account_type,
    ):
        account_type = str(
            account_type or ""
        ).strip().upper()

        if (
            account_type
            not in ChartOfAccountService
            .VALID_ACCOUNT_TYPES
        ):
            raise ValueError(
                "Invalid account type."
            )

        return account_type

    @staticmethod
    def _normal_balance_for_type(
        account_type,
    ):
        return (
            ChartOfAccountService
            .NORMAL_BALANCE_BY_TYPE[
                account_type
            ]
        )

    # ==================================================
    # CREATE USER ACCOUNT
    # ==================================================

    @staticmethod
    def create_account(
        *,
        user,
        organization,
        account_code,
        account_name,
        account_type,
        account_subtype="",
        description="",
        allow_manual_posting=True,
    ):
        ChartOfAccountService._check_permission(
            user,
            "chart_of_accounts.create",
        )

        ChartOfAccountService._check_organization(
            user,
            organization,
        )

        account_code = (
            ChartOfAccountService
            ._clean_required_text(
                account_code,
                "Account code",
            )
        )

        account_name = (
            ChartOfAccountService
            ._clean_required_text(
                account_name,
                "Account name",
            )
        )

        account_type = (
            ChartOfAccountService
            ._normalize_account_type(
                account_type
            )
        )

        account_subtype = str(
            account_subtype or ""
        ).strip().upper()

        description = str(
            description or ""
        ).strip()

        existing = (
            ChartOfAccountRepository
            .get_by_code(
                organization=organization,
                account_code=account_code,
            )
        )

        if existing:
            raise ValueError(
                "Account code already exists."
            )

        normal_balance = (
            ChartOfAccountService
            ._normal_balance_for_type(
                account_type
            )
        )

        return (
            ChartOfAccountRepository
            .create_account(
                organization=organization,
                account_code=account_code,
                account_name=account_name,
                account_type=account_type,
                account_subtype=account_subtype,
                normal_balance=normal_balance,
                system_key="",
                description=description,
                is_system_account=False,
                allow_manual_posting=bool(
                    allow_manual_posting
                ),
                created_by=user,
            )
        )

    # ==================================================
    # GET ACCOUNT
    # ==================================================

    @staticmethod
    def get_account(
        *,
        user,
        organization,
        account_id,
    ):
        ChartOfAccountService._check_permission(
            user,
            "chart_of_accounts.read",
        )

        ChartOfAccountService._check_organization(
            user,
            organization,
        )

        if not account_id:
            raise ValueError(
                "Account ID is required."
            )

        account = (
            ChartOfAccountRepository
            .get_by_id(
                organization=organization,
                account_id=account_id,
            )
        )

        if not account:
            raise ValueError(
                "Chart of account not found."
            )

        return account

    # ==================================================
    # GET SYSTEM ACCOUNT
    # ==================================================

    @staticmethod
    def get_system_account(
        *,
        organization,
        system_key,
    ):
        system_key = str(
            system_key or ""
        ).strip().upper()

        if not system_key:
            raise ValueError(
                "System key is required."
            )

        account = (
            ChartOfAccountRepository
            .get_by_system_key(
                organization=organization,
                system_key=system_key,
                active_only=True,
            )
        )

        if not account:
            from apps.accounts.models import User
            from apps.business.books import ensure_accounts
            owner=User.objects(organization=organization).first()
            if owner:
                ensure_accounts(organization,owner)
                account=ChartOfAccountRepository.get_by_system_key(organization=organization,system_key=system_key,active_only=True)
        if not account:
            raise ValueError(
                f"System account not found: "
                f"{system_key}"
            )

        return account

    # ==================================================
    # LIST
    # ==================================================

    @staticmethod
    def list_accounts(
        *,
        user,
        organization,
        account_type=None,
        is_active=None,
    ):
        ChartOfAccountService._check_permission(
            user,
            "chart_of_accounts.read",
        )

        ChartOfAccountService._check_organization(
            user,
            organization,
        )

        if account_type is not None:
            account_type = (
                ChartOfAccountService
                ._normalize_account_type(
                    account_type
                )
            )

        return (
            ChartOfAccountRepository
            .list_accounts(
                organization=organization,
                account_type=account_type,
                is_active=is_active,
            )
        )

    # ==================================================
    # UPDATE
    # ==================================================

    @staticmethod
    def update_account(
        *,
        user,
        organization,
        account_id,
        account_name=None,
        account_subtype=None,
        description=None,
        allow_manual_posting=None,
    ):
        ChartOfAccountService._check_permission(
            user,
            "chart_of_accounts.update",
        )

        ChartOfAccountService._check_organization(
            user,
            organization,
        )

        account = (
            ChartOfAccountRepository
            .get_by_id(
                organization=organization,
                account_id=account_id,
            )
        )

        if not account:
            raise ValueError(
                "Chart of account not found."
            )

        if (
            account_name is not None
        ):
            account_name = (
                ChartOfAccountService
                ._clean_required_text(
                    account_name,
                    "Account name",
                )
            )

        if (
            account_subtype
            is not None
        ):
            account_subtype = str(
                account_subtype
            ).strip().upper()

        if (
            description
            is not None
        ):
            description = str(
                description
            ).strip()

        if (
            account.is_system_account
            and
            allow_manual_posting
            is not None
            and
            bool(
                allow_manual_posting
            )
            != account.allow_manual_posting
        ):
            raise ValueError(
                "Manual posting setting cannot "
                "be changed for system accounts."
            )

        return (
            ChartOfAccountRepository
            .update_account(
                account=account,
                account_name=account_name,
                account_subtype=(
                    account_subtype
                ),
                description=description,
                allow_manual_posting=(
                    allow_manual_posting
                ),
            )
        )

    # ==================================================
    # DEACTIVATE
    # ==================================================

    @staticmethod
    def deactivate_account(
        *,
        user,
        organization,
        account_id,
    ):
        ChartOfAccountService._check_permission(
            user,
            "chart_of_accounts.deactivate",
        )

        ChartOfAccountService._check_organization(
            user,
            organization,
        )

        account = (
            ChartOfAccountRepository
            .get_by_id(
                organization=organization,
                account_id=account_id,
            )
        )

        if not account:
            raise ValueError(
                "Chart of account not found."
            )

        if not account.is_active:
            raise ValueError(
                "Account is already inactive."
            )

        if account.is_system_account:
            raise ValueError(
                "System accounts cannot "
                "be deactivated."
            )

        return (
            ChartOfAccountRepository
            .deactivate_account(
                account=account
            )
        )

    # ==================================================
    # DEFAULT ACCOUNT SEEDING
    # ==================================================

    @staticmethod
    def seed_default_accounts(
        *,
        user,
        organization,
    ):
        ChartOfAccountService._check_permission(
            user,
            "chart_of_accounts.create",
        )

        ChartOfAccountService._check_organization(
            user,
            organization,
        )

        created = []
        existing = []

        for account_data in (
            ChartOfAccountService
            .DEFAULT_ACCOUNTS
        ):
            account = (
                ChartOfAccountRepository
                .get_by_code(
                    organization=organization,
                    account_code=(
                        account_data[
                            "account_code"
                        ]
                    ),
                )
            )

            if account:
                existing.append(
                    account
                )
                continue

            account = (
                ChartOfAccountRepository
                .create_account(
                    organization=organization,
                    account_code=(
                        account_data[
                            "account_code"
                        ]
                    ),
                    account_name=(
                        account_data[
                            "account_name"
                        ]
                    ),
                    account_type=(
                        account_data[
                            "account_type"
                        ]
                    ),
                    account_subtype=(
                        account_data[
                            "account_subtype"
                        ]
                    ),
                    normal_balance=(
                        account_data[
                            "normal_balance"
                        ]
                    ),
                    system_key=(
                        account_data[
                            "system_key"
                        ]
                    ),
                    description=(
                        account_data[
                            "description"
                        ]
                    ),
                    is_system_account=(
                        account_data[
                            "is_system_account"
                        ]
                    ),
                    allow_manual_posting=(
                        account_data[
                            "allow_manual_posting"
                        ]
                    ),
                    created_by=user,
                )
            )

            created.append(
                account
            )

        return {
            "created":
                created,
            "existing":
                existing,
        }