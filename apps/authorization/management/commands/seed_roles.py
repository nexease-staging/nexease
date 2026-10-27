from datetime import datetime

from bson import ObjectId
from bson.errors import InvalidId

from django.core.management.base import (
    BaseCommand,
    CommandError,
)

from apps.authorization.models import (
    Permission,
    Role,
)
from apps.authorization.roles import (
    ROLE_CATALOG,
)
from apps.organizations.models import (
    Organization,
)


class Command(BaseCommand):

    help = (
        "Synchronize default roles for "
        "an organization."
    )

    def add_arguments(
        self,
        parser,
    ):
        parser.add_argument(
            "--organization",
            required=True,
            help="Organization ID",
        )

        parser.add_argument(
            "--dry-run",
            action="store_true",
            help=(
                "Report required changes "
                "without modifying MongoDB."
            ),
        )

    def handle(
        self,
        *args,
        **options,
    ):
        organization_id = (
            options[
                "organization"
            ]
        )

        dry_run = bool(
            options[
                "dry_run"
            ]
        )

        # ==================================================
        # ORGANIZATION
        # ==================================================

        try:
            normalized_organization_id = (
                ObjectId(
                    str(
                        organization_id
                    )
                )
            )

        except (
            InvalidId,
            TypeError,
            ValueError,
        ) as exc:
            raise CommandError(
                "Enter a valid organization ID."
            ) from exc

        organization = (
            Organization.objects(
                id=normalized_organization_id
            )
            .first()
        )

        if not organization:
            raise CommandError(
                "Organization not found."
            )

        if not organization.is_active:
            raise CommandError(
                "Organization is inactive."
            )

        # ==================================================
        # REQUIRED PERMISSIONS
        # ==================================================

        required_codes = sorted({
            permission_code

            for role_data
            in ROLE_CATALOG.values()

            for permission_code
            in role_data[
                "permissions"
            ]
        })

        active_permissions = {
            permission.code:
                permission

            for permission
            in Permission.objects(
                code__in=required_codes,
                is_active=True,
            )
        }

        missing_permissions = sorted(
            set(
                required_codes
            )
            -
            set(
                active_permissions
            )
        )

        if missing_permissions:
            raise CommandError(
                (
                    "Required active permissions "
                    "are missing: "
                    +
                    ", ".join(
                        missing_permissions
                    )
                )
            )

        # ==================================================
        # SYNCHRONIZATION
        # ==================================================

        created_count = 0
        updated_count = 0
        unchanged_count = 0

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    "DRY RUN — no changes will be saved."
                )
            )

        for role_key, data in (
            ROLE_CATALOG.items()
        ):
            desired_permissions = [
                active_permissions[
                    permission_code
                ]

                for permission_code
                in data[
                    "permissions"
                ]
            ]

            role = (
                Role.objects(
                    organization=organization,
                    name=data["name"],
                )
                .first()
            )

            if not role:
                created_count += 1

                self.stdout.write(
                    self.style.SUCCESS(
                        (
                            "Would create: "
                            if dry_run
                            else
                            "Created: "
                        )
                        +
                        data["name"]
                        +
                        " | permissions="
                        +
                        str(
                            len(
                                desired_permissions
                            )
                        )
                    )
                )

                if not dry_run:
                    Role(
                        organization=organization,
                        name=data["name"],
                        description=(
                            data["description"]
                        ),
                        is_system=bool(
                            data["is_system"]
                        ),
                        permissions=(
                            desired_permissions
                        ),
                        is_active=True,
                    ).save(
                        force_insert=True
                    )

                continue

            changed_fields = []

            if (
                role.description
                !=
                data["description"]
            ):
                role.description = (
                    data["description"]
                )

                changed_fields.append(
                    "description"
                )

            if (
                bool(
                    role.is_system
                )
                !=
                bool(
                    data["is_system"]
                )
            ):
                role.is_system = bool(
                    data["is_system"]
                )

                changed_fields.append(
                    "is_system"
                )

            current_permission_ids = {
                str(
                    permission.id
                )

                for permission
                in (
                    role.permissions
                    or
                    []
                )
            }

            desired_permission_ids = {
                str(
                    permission.id
                )

                for permission
                in desired_permissions
            }

            if (
                current_permission_ids
                !=
                desired_permission_ids
            ):
                role.permissions = (
                    desired_permissions
                )

                changed_fields.append(
                    "permissions"
                )

            if changed_fields:
                updated_count += 1

                self.stdout.write(
                    self.style.WARNING(
                        (
                            "Would update: "
                            if dry_run
                            else
                            "Updated: "
                        )
                        +
                        data["name"]
                        +
                        " ["
                        +
                        ", ".join(
                            changed_fields
                        )
                        +
                        "]"
                        +
                        " | permissions="
                        +
                        str(
                            len(
                                desired_permissions
                            )
                        )
                    )
                )

                if not dry_run:
                    role.updated_at = (
                        datetime.utcnow()
                    )

                    role.save()

            else:
                unchanged_count += 1

                self.stdout.write(
                    (
                        "Unchanged: "
                        +
                        role_key
                        +
                        " | "
                        +
                        data["name"]
                    )
                )

        # ==================================================
        # SUMMARY
        # ==================================================

        self.stdout.write("")
        self.stdout.write(
            (
                "Organization: "
                f"{organization.name} "
                f"({organization.id})"
            )
        )

        self.stdout.write(
            f"Created: {created_count}"
        )

        self.stdout.write(
            f"Updated: {updated_count}"
        )

        self.stdout.write(
            f"Unchanged: {unchanged_count}"
        )

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    "Role synchronization dry run completed."
                )
            )

        else:
            self.stdout.write(
                self.style.SUCCESS(
                    "Role synchronization completed."
                )
            )