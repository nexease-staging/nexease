import os
import sys

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


from apps.authorization.models import (
    Permission,
)


PERMISSIONS = [
    {
        "code":
            "bank_transactions.create",
        "name":
            "Create Bank Transactions",
        "description":
            "Create cash and bank "
            "ledger transactions.",
        "module":
            "finance",
    },
    {
        "code":
            "bank_transactions.read",
        "name":
            "View Bank Transactions",
        "description":
            "View cash and bank "
            "ledger transactions.",
        "module":
            "finance",
    },
    {
        "code":
            "bank_transactions.reconcile",
        "name":
            "Reconcile Bank Transactions",
        "description":
            "Reconcile cash and bank "
            "transactions.",
        "module":
            "finance",
    },
]


for data in PERMISSIONS:
    permission = Permission.objects(
        code=data["code"]
    ).first()

    if permission:
        permission.name = (
            data["name"]
        )

        permission.description = (
            data["description"]
        )

        permission.module = (
            data["module"]
        )

        permission.is_active = True

        permission.save()

        print(
            "UPDATED:",
            permission.code,
        )

    else:
        permission = Permission(
            code=data["code"],
            name=data["name"],
            description=(
                data["description"]
            ),
            module=data["module"],
            is_active=True,
        )

        permission.save()

        print(
            "CREATED:",
            permission.code,
        )


print(
    "Bank transaction permissions ready."
)