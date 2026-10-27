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


from apps.accounts.models import (
    User,
)

from apps.authorization.models import (
    Permission,
)


USER_EMAIL = "admin@example.com"

PERMISSION_CODES = [
    "bank_transactions.create",
    "bank_transactions.read",
    "bank_transactions.reconcile",
]


user = User.objects(
    email=USER_EMAIL
).first()


if not user:
    raise ValueError(
        f"User not found: {USER_EMAIL}"
    )


if not user.role:
    raise ValueError(
        "User has no role assigned."
    )


role = user.role


for code in PERMISSION_CODES:
    permission = Permission.objects(
        code=code,
        is_active=True,
    ).first()

    if not permission:
        raise ValueError(
            f"Permission not found: {code}"
        )

    already_assigned = any(
        existing.id
        == permission.id
        for existing
        in role.permissions
    )

    if already_assigned:
        print(
            "ALREADY ASSIGNED:",
            code,
        )

        continue

    role.permissions.append(
        permission
    )

    print(
        "ASSIGNED:",
        code,
    )


role.save()


print(
    "ROLE:",
    role.name
)

print(
    "Bank transaction permissions assigned."
)