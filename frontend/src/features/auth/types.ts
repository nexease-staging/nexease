export interface AuthenticationState {
  type: "session";
  authenticated: boolean;
}

export interface AuthenticatedUser {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  full_name?: string;
  is_active: boolean;
}

export interface AuthenticatedOrganization {
  id: string;
  name: string;
  country?: string;
  currency?: string;
  timezone?: string;
  is_active?: boolean;
}

export interface AuthenticatedRole {
  id: string;
  name: string;
  is_active?: boolean;
  permissions: string[];
  permissions_by_module?: Record<
    string,
    string[]
  >;
}

export interface AuthenticationContext {
  authentication: AuthenticationState;
  user: AuthenticatedUser;
  organization: AuthenticatedOrganization;
  role: AuthenticatedRole;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface LoggedOutUser {
  id: string;
  email: string;
}

export interface LogoutData {
  authentication: AuthenticationState;
  logged_out_user: LoggedOutUser;
}

export interface LogoutAllData {
  authentication: AuthenticationState;
  logged_out_user?: LoggedOutUser;
  sessions_revoked?: number;
  revoked_sessions?: number;
}

export interface SignupInput {
  business_scope?: string;
  organization_name: string;
  organization_email: string;
  first_name: string;
  last_name: string;
  email: string;
  password: string;
  phone?: string;
}

export interface SignupOrganization {
  business_scope?: string;
  id: string;
  name: string;
  email: string;
}

export interface SignupUser {
  business_scope?: string;
  id: string;
  email: string;
  first_name: string;
  last_name: string;
}

export interface SignupRole {
  business_scope?: string;
  id: string;
  name: string;
}

export interface SignupResult {
  business_scope?: string;
  organization: SignupOrganization;
  user: SignupUser;
  role: SignupRole;
}

export interface ForgotPasswordInput {
  email: string;
}

export interface ForgotPasswordResult {
  message: string;
}

export interface ResetPasswordInput {
  token: string;
  new_password: string;
}

export interface ResetPasswordResult {
  message: string;
  sessions_revoked: number;
}