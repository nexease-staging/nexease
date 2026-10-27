export function hasPermission(
  permissions: readonly string[],
  requiredPermission?: string,
): boolean {
  if (!requiredPermission) {
    return true;
  }

  return permissions.includes(
    requiredPermission,
  );
}

export function hasAnyPermission(
  permissions: readonly string[],
  requiredPermissions: readonly string[],
): boolean {
  if (
    requiredPermissions.length === 0
  ) {
    return true;
  }

  return requiredPermissions.some(
    (permission) =>
      permissions.includes(
        permission,
      ),
  );
}

export function hasAllPermissions(
  permissions: readonly string[],
  requiredPermissions: readonly string[],
): boolean {
  return requiredPermissions.every(
    (permission) =>
      permissions.includes(
        permission,
      ),
  );
}