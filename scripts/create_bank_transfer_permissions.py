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
            "bank_transfers.create",
        "name":
            "Create Bank Transfers",
        "description":
            "Create transfers between "
            "bank and cash accounts.",
        "module":
            "finance",
    },
    {
        "code":
            "bank_transfers.read",
        "name":
            "View Bank Transfers",
        "description":
            "View bank and cash "
            "account transfers.",
        "module":
            "finance",
    },
    {
        "code":
            "bank_transfers.post",
        "name":
            "Post Bank Transfers",
        "description":
            "Post bank and cash "
            "account transfers.",
        "module":
            "finance",
    },
    {
        "code":
            "bank_transfers.cancel",
        "name":
            "Cancel Bank Transfers",
        "description":
            "Cancel draft bank and "
            "cash account transfers.",
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
    "Bank transfer permissions ready."
)
