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
            "bank_statements.create",
        "name":
            "Create Bank Statements",
        "description":
            "Create and import bank statements.",
        "module":
            "finance",
    },
    {
        "code":
            "bank_statements.read",
        "name":
            "View Bank Statements",
        "description":
            "View bank statements and "
            "statement lines.",
        "module":
            "finance",
    },
    {
        "code":
            "bank_statements.reconcile",
        "name":
            "Reconcile Bank Statements",
        "description":
            "Match statement lines with "
            "bank ledger transactions.",
        "module":
            "finance",
    },
    {
        "code":
            "bank_statements.cancel",
        "name":
            "Cancel Bank Statements",
        "description":
            "Cancel bank statements that "
            "have not been fully reconciled.",
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
    "Bank statement permissions ready."
)