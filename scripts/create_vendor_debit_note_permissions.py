import os
import sys

import django


BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

sys.path.append(BASE_DIR)

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
            "vendor_debit_notes.read",
        "name":
            "View Vendor Debit Notes",
        "description":
            "View vendor debit notes.",
        "module":
            "purchasing",
    },
    {
        "code":
            "vendor_debit_notes.create",
        "name":
            "Create Vendor Debit Notes",
        "description":
            "Create vendor debit notes "
            "from confirmed purchase returns.",
        "module":
            "purchasing",
    },
    {
        "code":
            "vendor_debit_notes.issue",
        "name":
            "Issue Vendor Debit Notes",
        "description":
            "Issue vendor debit notes "
            "and apply them against "
            "supplier payables.",
        "module":
            "purchasing",
    },
    {
        "code":
            "vendor_debit_notes.cancel",
        "name":
            "Cancel Vendor Debit Notes",
        "description":
            "Cancel draft vendor "
            "debit notes.",
        "module":
            "purchasing",
    },
]


for data in PERMISSIONS:
    permission = Permission.objects(
        code=data["code"]
    ).first()

    if permission:
        permission.name = data["name"]
        permission.description = (
            data["description"]
        )
        permission.module = data["module"]
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
    "Vendor debit note permissions ready."
)
