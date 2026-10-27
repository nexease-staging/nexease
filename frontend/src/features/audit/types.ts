export type AuthenticationAuditEventType =
  | "LOGIN_SUCCESS"
  | "LOGIN_FAILED"
  | "LOGIN_BLOCKED"
  | "LOGOUT"
  | "LOGOUT_ALL";


export interface AuthenticationAuditUser {
  id: string;
  email: string;
}


export interface AuthenticationAuditIntegrity {
  hashed: boolean;
  verified: boolean;
}


export interface AuthenticationAuditLog {
  id: string;

  event_type:
    AuthenticationAuditEventType;

  user:
    AuthenticationAuditUser
    | null;

  identifier:
    string
    | null;

  ip_address:
    string
    | null;

  created_at:
    string
    | null;

  integrity:
    AuthenticationAuditIntegrity;
}


export interface AuthenticationAuditListData {
  authentication_audit_logs:
    AuthenticationAuditLog[];

  count: number;

  query: {
    event_type:
      string
      | null;

    identifier:
      string
      | null;

    ip_address:
      string
      | null;

    limit: number;
  };
}


export interface AuthenticationAuditListParameters {
  event_type?:
    AuthenticationAuditEventType;

  identifier?: string;

  ip_address?: string;

  limit?: number;
}