export type MigrationType =
  | "PRODUCTS"
  | "CATEGORIES"
  | "CUSTOMERS"
  | "SUPPLIERS"
  | "WAREHOUSES"
  | "INVENTORY"
  | "SALES_ORDERS"
  | "SALES_INVOICES"
  | "CUSTOMER_PAYMENTS"
  | "PURCHASE_ORDERS"
  | "GOODS_RECEIPTS"
  | "EMPLOYEES"
  | "VENDOR_BILLS"
  | "SUPPLIER_PAYMENTS";

export type MigrationStatus =
  | "CREATED"
  | "UPLOADED"
  | "VALIDATING"
  | "VALIDATED"
  | "IMPORTING"
  | "COMPLETED"
  | "COMPLETED_WITH_ERRORS"
  | "FAILED"
  | "CANCELLED";

export type MigrationMapping =
  Record<string, string>;

export type MigrationOptions =
  Record<string, unknown>;

export type MigrationResult =
  Record<string, unknown>;

export interface MigrationBatch {
  id: string;

  source_system: string;
  migration_type: MigrationType;
  status: MigrationStatus;

  upload_id: string | null;
  job_id: string | null;

  mapping: MigrationMapping;
  options: MigrationOptions;

  total_rows: number;
  valid_rows: number;
  invalid_rows: number;

  imported_rows: number;
  skipped_rows: number;
  failed_rows: number;

  validation_result: MigrationResult;
  import_result: MigrationResult;
  error_summary: MigrationResult;

  started_at: string | null;
  completed_at: string | null;

  created_at: string | null;
  updated_at: string | null;
}

export interface MigrationListData {
  migrations: MigrationBatch[];
  count: number;
}

export interface MigrationData {
  migration: MigrationBatch;
}

export interface CreateMigrationInput {
  source_system: string;
  migration_type: MigrationType;
  mapping?: MigrationMapping;
  options?: MigrationOptions;
}

export interface MigrationUploadedFile {
  upload_id: string;
  filename: string;
  extension: string;
  size: number;

  columns: string[];
  total_rows: number;

  sample_rows: Array<
    Record<string, unknown>
  >;

  sheet_name: string | null;
}

export interface MigrationUploadData {
  migration: MigrationBatch;
  file: MigrationUploadedFile;
}

export interface MigrationJob {
  id: string;
  job_type: string;
  status: string;
  attempts: number;
  max_attempts: number;
  created_at: string | null;
}

export interface MigrationJobData {
  migration: MigrationBatch;
  job: MigrationJob;
}