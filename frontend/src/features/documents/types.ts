export type DocumentType =
  | "INVOICE"
  | "SALES_ORDER"
  | "CREDIT_NOTE"
  | "CUSTOMER_PAYMENT"
  | "PURCHASE_ORDER"
  | "VENDOR_BILL"
  | "VENDOR_DEBIT_NOTE"
  | "SUPPLIER_PAYMENT"
  | "GOODS_RECEIPT";

export type ExportResourceType =
  | "GENERAL_LEDGER"
  | "TRIAL_BALANCE"
  | "CASH_FLOW"
  | "FINANCE_AUDIT";

export type ExportFormat =
  | "csv"
  | "xlsx";

export interface DocumentEmailInput {
  recipient_email?: string;
  subject?: string;
  message?: string;
}

export interface DocumentEmailDelivery {
  id: string;
  status: string;
  channel: string;
  recipient: string;
}

export interface DocumentEmailResult {
  document_type: DocumentType;
  document_id: string;
  recipient: string;

  recipient_overridden?: boolean;
  custom_subject?: boolean;
  custom_message?: boolean;

  sent_count: number;

  delivery: DocumentEmailDelivery;
}

export interface DocumentEmailData {
  document: DocumentEmailResult;
}

export interface DocumentLogUser {
  id: string;
  email: string;
}

export interface DocumentAccessLog {
  id: string;

  user:
    | DocumentLogUser
    | null;

  document_type: string;
  document_id: string;
  document_number: string;
  action: string;

  created_at:
    | string
    | null;
}

export interface DocumentAccessLogData {
  logs: DocumentAccessLog[];
}

export interface DocumentAccessLogParameters {
  document_type?: string;
  action?: string;
  document_number?: string;
  user_id?: string;
  limit?: number;
}

export interface DocumentDeliveryLog {
  id: string;

  document_type: string;
  document_id: string;
  document_number: string;

  channel: string;
  recipient: string;

  subject:
    | string
    | null;

  status: string;

  recipient_overridden: boolean;
  custom_subject: boolean;
  custom_message: boolean;

  error_message:
    | string
    | null;

  sent_at:
    | string
    | null;

  created_at:
    | string
    | null;

  updated_at:
    | string
    | null;
}

export interface DocumentDeliveryLogData {
  logs: DocumentDeliveryLog[];
}

export interface DocumentDeliveryLogParameters {
  document_type?: string;
  channel?: string;
  status?: string;
  recipient?: string;
  document_number?: string;
  subject?: string;

  recipient_overridden?:
    | boolean;

  custom_subject?:
    | boolean;

  custom_message?:
    | boolean;

  limit?: number;
}

export type DocumentLogSummary =
  Record<string, unknown>;

export interface DocumentLogSummaryData {
  summary: DocumentLogSummary;
}

export interface ExportParameters {
  [key: string]:
    | string
    | number
    | boolean
    | undefined;
}