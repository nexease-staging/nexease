export interface PermissionSummary {
  id: string;
  code: string;
  name: string;
  module: string;
  is_active: boolean;
}

export interface PermissionDetail
  extends PermissionSummary {
  description: string | null;
  created_at: string | null;
  updated_at: string | null;
}


export interface RoleOrganizationReference {
  id: string;
  name: string;
}

export interface RoleSummary {
  id: string;
  name: string;
  description: string | null;
  is_system: boolean;
  is_active: boolean;
  permission_count: number;
}

export interface RoleDetail
  extends RoleSummary {
  organization:
    RoleOrganizationReference | null;

  permissions:
    PermissionSummary[];

  permission_codes:
    string[];

  permissions_by_module:
    Record<string, string[]>;

  created_at:
    string | null;

  updated_at:
    string | null;
}


export interface PaginationData {
  page: number;
  page_size: number;
  total_items: number;
  total_pages: number;
  has_next: boolean;
  has_previous: boolean;
}


export interface RoleListData {
  roles: RoleSummary[];
  pagination: PaginationData;
  query: Record<string, unknown>;
}

export interface RoleData {
  role: RoleDetail;
}

export interface PermissionListData {
  permissions: PermissionDetail[];
  modules: string[];
  pagination: PaginationData;
  query: Record<string, unknown>;
}


export interface RoleListParameters {
  page?: number;
  page_size?: number;
  search?: string;
  is_active?: boolean;
  is_system?: boolean;
  sort?: string;
}

export interface PermissionListParameters {
  page?: number;
  page_size?: number;
  search?: string;
  module?: string;
  is_active?: boolean;
  sort?: string;
}


export interface CreateRoleInput {
  name: string;
  description?: string;
  permission_codes?: string[];
}

export interface UpdateRoleInput {
  name?: string;
  description?: string;
}

export interface AssignRolePermissionsInput {
  permission_codes: string[];
}


export interface RoleActivationData {
  role: RoleDetail;
  state_changed: boolean;
}

export interface RoleDeactivationData {
  role: RoleDetail;
  state_changed: boolean;
  assigned_active_users: number;
}