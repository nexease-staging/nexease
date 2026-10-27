from datetime import datetime

from django.core.management.base import (
    BaseCommand,
    CommandError,
)

from apps.authorization.models import (
    Permission,
    Role,
)
from apps.authorization.permissions import (
    LEGACY_PERMISSION_REPLACEMENTS,
    PERMISSION_CATALOG,
)


class Command(BaseCommand):

    help = (
        "Synchronize permissions with the "
        "canonical permission catalog."
    )

    def add_arguments(
        self,
        parser,
    ):
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
        dry_run = bool(
            options["dry_run"]
        )

        created_count = 0
        updated_count = 0
        unchanged_count = 0
        reactivated_count = 0
        migrated_role_count = 0
        deactivated_legacy_count = 0

        canonical_permissions = {}

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    "DRY RUN — no changes will be saved."
                )
            )

        # ==================================================
        # CANONICAL PERMISSION SYNCHRONIZATION
        # ==================================================

        for code, data in (
            PERMISSION_CATALOG.items()
        ):
            permission = (
                Permission.objects(
                    code=code
                )
                .first()
            )

            if not permission:
                created_count += 1

                self.stdout.write(
                    self.style.SUCCESS(
                        f"Would create: {code}"
                        if dry_run
                        else
                        f"Created: {code}"
                    )
                )

                if not dry_run:
                    permission = Permission(
                        code=code,
                        name=data["name"],
                        description=(
                            data["description"]
                        ),
                        module=data["module"],
                        is_active=True,
                    )

                    permission.save(
                        force_insert=True
                    )

                    canonical_permissions[
                        code
                    ] = permission

                continue

            canonical_permissions[
                code
            ] = permission

            changed_fields = []

            if (
                permission.name
                !=
                data["name"]
            ):
                permission.name = (
                    data["name"]
                )

                changed_fields.append(
                    "name"
                )

            if (
                permission.description
                !=
                data["description"]
            ):
                permission.description = (
                    data["description"]
                )

                changed_fields.append(
                    "description"
                )

            if (
                permission.module
                !=
                data["module"]
            ):
                permission.module = (
                    data["module"]
                )

                changed_fields.append(
                    "module"
                )

            if not permission.is_active:
                permission.is_active = True

                changed_fields.append(
                    "is_active"
                )

                reactivated_count += 1

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
                        code
                        +
                        " ["
                        +
                        ", ".join(
                            changed_fields
                        )
                        +
                        "]"
                    )
                )

                if not dry_run:
                    permission.updated_at = (
                        datetime.utcnow()
                    )

                    permission.save()

            else:
                unchanged_count += 1

        # ==================================================
        # VALIDATE REPLACEMENT TARGETS
        # ==================================================

        missing_replacement_targets = [
            replacement_code

            for replacement_code
            in (
                LEGACY_PERMISSION_REPLACEMENTS
                .values()
            )

            if replacement_code
            not in PERMISSION_CATALOG
        ]

        if missing_replacement_targets:
            raise CommandError(
                (
                    "Legacy replacement targets "
                    "are missing from the catalog: "
                    +
                    ", ".join(
                        sorted(
                            missing_replacement_targets
                        )
                    )
                )
            )

        # ==================================================
        # MIGRATE LEGACY ROLE REFERENCES
        # ==================================================

        legacy_permissions = {
            permission.code:
                permission

            for permission
            in Permission.objects(
                code__in=list(
                    LEGACY_PERMISSION_REPLACEMENTS
                    .keys()
                )
            )
        }

        for role in Role.objects.all():
            original_permissions = (
                role.permissions
                or
                []
            )

            migrated_permissions = []
            seen_permission_ids = set()
            role_changed = False

            for permission in (
                original_permissions
            ):
                permission_code = getattr(
                    permission,
                    "code",
                    None,
                )

                target_permission = (
                    permission
                )

                if (
                    permission_code
                    in
                    LEGACY_PERMISSION_REPLACEMENTS
                ):
                    replacement_code = (
                        LEGACY_PERMISSION_REPLACEMENTS[
                            permission_code
                        ]
                    )

                    target_permission = (
                        canonical_permissions.get(
                            replacement_code
                        )
                        or
                        Permission.objects(
                            code=replacement_code,
                            is_active=True,
                        ).first()
                    )

                    if (
                        not target_permission
                        and
                        not dry_run
                    ):
                        raise CommandError(
                            (
                                "Replacement permission "
                                "not found: "
                                f"{replacement_code}"
                            )
                        )

                    role_changed = True

                target_id = getattr(
                    target_permission,
                    "id",
                    None,
                )

                if target_id is None:
                    # During a dry run, a newly planned
                    # replacement may not exist yet.
                    continue

                target_id = str(
                    target_id
                )

                if (
                    target_id
                    in seen_permission_ids
                ):
                    role_changed = True
                    continue

                seen_permission_ids.add(
                    target_id
                )

                migrated_permissions.append(
                    target_permission
                )

            if role_changed:
                migrated_role_count += 1

                self.stdout.write(
                    self.style.WARNING(
                        (
                            "Would migrate role: "
                            if dry_run
                            else
                            "Migrated role: "
                        )
                        +
                        role.name
                        +
                        " | organization="
                        +
                        str(
                            role.organization.id
                        )
                    )
                )

                if not dry_run:
                    role.permissions = (
                        migrated_permissions
                    )

                    role.updated_at = (
                        datetime.utcnow()
                    )

                    role.save()

        # ==================================================
        # DEACTIVATE LEGACY PERMISSIONS
        # ==================================================

        for code, permission in (
            legacy_permissions.items()
        ):
            if not permission.is_active:
                continue

            deactivated_legacy_count += 1

            self.stdout.write(
                self.style.WARNING(
                    (
                        "Would deactivate legacy: "
                        if dry_run
                        else
                        "Deactivated legacy: "
                    )
                    +
                    code
                )
            )

            if not dry_run:
                permission.is_active = False
                permission.updated_at = (
                    datetime.utcnow()
                )

                permission.save()

        # ==================================================
        # SUMMARY
        # ==================================================

        self.stdout.write("")
        self.stdout.write(
            "Permission synchronization summary:"
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

        self.stdout.write(
            f"Reactivated: {reactivated_count}"
        )

        self.stdout.write(
            (
                "Roles with legacy references "
                f"migrated: {migrated_role_count}"
            )
        )

        self.stdout.write(
            (
                "Legacy permissions deactivated: "
                f"{deactivated_legacy_count}"
            )
        )

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    "Dry run completed."
                )
            )

        else:
            self.stdout.write(
                self.style.SUCCESS(
                    (
                        "Permission synchronization "
                        "completed."
                    )
                )
            )