# Migration rejection feedback — 13 November 2026

## Fixed
- The API create allowlist omitted Employees, Goods Receipts, Vendor Bills, Customer Payments and Supplier Payments even though these were offered in the UI and supported by migration services.
- Upload, validation and import errors now retain API field-level reasons instead of showing only the generic heading.
- Mapping validation identifies the missing or incorrectly mapped field.
- Batch responses expose rejected row numbers and validation reasons, without normalized source records. The UI shows up to 200 rejected rows per batch to bound response size.
- Migration history entries can be opened to review stored validation issues.
- Corrected mappings can be validated again; changing files clears stale mapping selections.

## Validation
- 272 existing migration tests passed against an isolated test database.
- 3 new backend regression tests passed.
- 2 frontend error-formatting tests passed.
- Scoped ESLint, TypeScript check and production frontend build passed.
- No live customer migration was run and the customer's rejected input file was not provided. These fixes resolve confirmed code defects; a specific file may still require corrections shown by its validation report.

## Apply
Import the bundle into the existing upgrade branch, then push and merge through the normal PR process. Deploy backend and frontend. No new database migration or index command is required for this patch. Rebuild the Android app to include the frontend changes.

## User workflow
Choose migration type, upload CSV/XLSX, check mappings and validate. Read Corrections needed for the row number (header is row 1), field and reason. Fix the file and upload again, or correct mapping and revalidate. Import stays blocked for invalid rows. For an older batch, click its type in Migration history to view stored validation issues.
