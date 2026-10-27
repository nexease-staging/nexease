# SaaS Edition — 25 October 2026

Added platform-owner MFA console, explicit trials and three subscription plans; serialized quota checks; Razorpay recurring checkout and verified current-period activation; payment history and webhook recovery; Pro AI draft extraction, review and confirmation; PDF/photo input; pricing and Pro feature sections on the welcome page. Added START_HERE_SAAS.md and an environment preparation helper. See that guide for feature limits and production acceptance requirements.

# 22 October 2026 — workforce automation

Daily attendance board; automatic/manual payroll inputs; approved advance recovery; partial salary payments and balances; client/site lookup; draft invoices from approved site work; employee migration; automatic/manual display numbering and sequences. See UPDATE_AUTOMATION.md.

# NexEase update — 21 October 2026

## Existing modules retained

Inventory, warehouses, stock movements/transfers, customers/suppliers, sales/purchase orders, receipts, invoices/vendor bills, payments, returns/notes, accounts payable/receivable, banking, chart of accounts, journals, ledger, trial balance, reporting, authentication, permissions, document delivery, background jobs and the original migration workflows.

## Added and changed

- `apps/business/`: explicit record schemas, tenant-scoped CRUD, role checks, optimistic revision updates, audit entries, payroll calculations/workflow/export, labour export, direct billing/purchase entry and GST workpapers.
- `apps/organizations/`: business scope persisted and returned in organisation responses; validated updates.
- `apps/accounts/`: signup accepts validated business scope. Password-reset cleanup now uses the latest persisted generation after token insertion so a late-arriving stale token does not remain unused in storage.
- `apps/authorization/`: payroll/labour/taxation read/manage permission definitions, automatically included in the built-in administrator catalog.
- `apps/migration/`: financial import schemas, validation/dispatch, Excel templates, mapping endpoint and partial mapping auto-detection. Validation-job idempotency includes batch update time to permit revalidation after a mapping edit.
- `Invoice.sales_order` and `VendorBill.purchase_order` are optional for direct entries. Invoice SO uniqueness uses a partial index. Legacy document serialization tolerates missing order references; order-based return services reject incompatible direct bills cleanly.
- `upgrade_nexease` command replaces the legacy invoice index and synchronises permissions/built-in roles.
- Frontend: new landing page, NexEase styling, theme preference, grouped navigation, scope settings, workforce/taxation pages, direct-entry forms and migration mapping/template controls.
- Example environment files, 13 sample workbooks, isolated new-feature tests and reproducible existing-suite runner.

## Compatibility choices

Database collection names, existing route names, session configuration and original dependency pins were retained. This avoids renaming live data and internal API contracts solely for branding. No actual customer data or production secrets were inserted.

Read `FEATURE_STATUS.md` for partial capabilities and workflows that still require integration or manual reconciliation.
