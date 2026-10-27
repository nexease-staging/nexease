import type {
  APIPagination,
  APIQueryMetadata,
} from "@/lib/api/types";

export interface UserRoleReference {
  id: string;
  name: string;
  is_active: boolean;
}

export interface UserOrganizationReference {
  id: string;
  name: string;
}

export interface UserSummary {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  is_active: boolean;
  role: UserRoleReference | null;
}

export interface UserDetail
  extends UserSummary {
  organization:
    UserOrganizationReference | null;

  created_at: string | null;
  updated_at: string | null;
}

export interface UserListData {
  users: UserSummary[];
  pagination: APIPagination;
  query: APIQueryMetadata;
}

export interface UserData {
  user: UserDetail;
}

export interface UserListParameters {
  page?: number;
  page_size?: number;
  search?: string;
  is_active?: boolean;
  sort?: string;
}

export interface CreateUserInput {
  email: string;
  first_name: string;
  last_name: string;
  password: string;
  password_confirmation: string;
  role_id: string;
}

export interface UpdateUserInput {
  email?: string;
  first_name?: string;
  last_name?: string;
  role_id?: string;
}

export interface RoleSummary {
  id: string;
  name: string;
  description: string | null;
  is_system: boolean;
  is_active: boolean;
  permission_count: number;
}

export interface RoleListData {
  roles: RoleSummary[];
  pagination: APIPagination;
  query: APIQueryMetadata;
}

export interface RoleListParameters {
  page?: number;
  page_size?: number;
  search?: string;
  is_active?: boolean;
  is_system?: boolean;
  sort?: string;
}