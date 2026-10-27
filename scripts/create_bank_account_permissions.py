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
            "bank_accounts.create",
        "name":
            "Create Bank Accounts",
        "description":
            "Create bank and cash accounts.",
        "module":
            "finance",
    },
    {
        "code":
            "bank_accounts.read",
        "name":
            "View Bank Accounts",
        "description":
            "View bank and cash accounts "
            "and their balances.",
        "module":
            "finance",
    },
    {
        "code":
            "bank_accounts.update",
        "name":
            "Update Bank Accounts",
        "description":
            "Update bank and cash account "
            "details.",
        "module":
            "finance",
    },
    {
        "code":
            "bank_accounts.deactivate",
        "name":
            "Deactivate Bank Accounts",
        "description":
            "Deactivate bank and cash accounts "
            "without deleting transaction history.",
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
    "Bank account permissions ready."
)