import os
import sys
from decimal import Decimal
from uuid import uuid4

import django


BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

sys.path.append(
    BASE_DIR
)

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings",
)

django.setup()


from apps.finance.models import (
    BankAccount,
    BankTransaction,
)


accounts = BankAccount.objects


for account in accounts:
    existing = BankTransaction.objects(
        organization=account.organization,
        bank_account=account,
        transaction_type="OPENING_BALANCE",
    ).first()

    if existing:
        print(
            "SKIPPED:",
            account.account_name,
            "- opening transaction already exists",
        )

        continue

    opening_balance = Decimal(
        str(
            account.opening_balance
        )
    )

    transaction = BankTransaction(
        organization=account.organization,
        bank_account=account,
        transaction_number=(
            "BTX-"
            + uuid4().hex[:12].upper()
        ),
        transaction_type="OPENING_BALANCE",
        transaction_date=(
            account.created_at
        ),
        amount=abs(
            opening_balance
        ),
        balance_before=Decimal("0"),
        balance_after=(
            opening_balance
        ),
        reference_type=(
            "BANK_ACCOUNT_OPENING"
        ),
        reference_id=str(
            account.id
        ),
        description=(
            f"Opening balance for "
            f"{account.account_name}"
        ),
        reconciliation_status=(
            "RECONCILED"
        ),
        reconciled_at=(
            account.created_at
        ),
        created_by=(
            account.created_by
        ),
    )

    transaction.save()

    print(
        "CREATED:",
        account.account_name,
        "| opening:",
        opening_balance,
    )


print(
    "Opening balance backfill complete."
)