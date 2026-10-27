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
            "purchase_returns.read",
        "name":
            "View Purchase Returns",
        "description":
            "View purchase returns.",
        "module":
            "purchasing",
    },
    {
        "code":
            "purchase_returns.create",
        "name":
            "Create Purchase Returns",
        "description":
            "Create purchase returns.",
        "module":
            "purchasing",
    },
    {
        "code":
            "purchase_returns.confirm",
        "name":
            "Confirm Purchase Returns",
        "description":
            "Confirm purchase returns "
            "and return stock to suppliers.",
        "module":
            "purchasing",
    },
    {
        "code":
            "purchase_returns.cancel",
        "name":
            "Cancel Purchase Returns",
        "description":
            "Cancel draft purchase returns.",
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
    "Purchase return permissions ready."
)