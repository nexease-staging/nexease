# NexEase audit — 10 November 2026

Baseline: Git main 51ee883. Scope: requested cross-module reliability and mobile redesign.
This is an evidence ledger, not a claim that every runtime flow passes. Static inventory is complete for files listed below; authenticated browser/device, network and console checks are UNTESTED until performed.

## Confirmed findings (before changes)
| ID | Severity | Evidence | Status |
|---|---|---|---|
| COST-001 | High | apps/business/gst_lookup.py calls Sandbox without persistent result cache, single-flight claim or monthly tenant quota | Implemented; see BUGS_FIXED.md and verification limits |
| LIMIT-001 | High | New tier capacities differ from entitlements.DEFAULTS; no Free catalogue | Implemented; existing snapshots require explicit rollout |
| ALERT-001 | High | No subscription renewal outbox/scheduler found under apps/saas | Implemented; see BUGS_FIXED.md and verification limits |
| UI-001 | Medium | stat-card.tsx truncates amounts and captions; invoices uses 3 narrow columns | Implemented; see BUGS_FIXED.md and verification limits |
| UI-002 | Medium | app-shell renders global QuickCreate FAB over mobile content | Implemented; see BUGS_FIXED.md and verification limits |
| UI-003 | Medium | invoices-view stacks customer filter and large cards; refresh hidden on phones | Implemented; see BUGS_FIXED.md and verification limits |
| AI-001 | Medium | AI has token cap and usage reservations but no identical-input extraction cache | Implemented; see BUGS_FIXED.md and verification limits |
| PARTNER-001 | High | No partner lifecycle, commission or payout module found; business rules absent from supplied fragment | Blocked on rules; not implemented |

## Financial/linkage observations
Decimal is used in sales and payment services. This does not prove all rounding, posting, rollback and concurrency paths. Existing compensation-based writes are not equivalent to a Mongo replica-set transaction. No broad transaction or issued-document mutation change is approved by this audit. Preserve existing financial workflows until tested.
Overdue should be a derived display/filter state, preserving ISSUED/PARTIALLY_PAID payment transitions; a nightly job must not destroy partial-payment status.
SMTP cannot guarantee exactly-once delivery across a crash after acceptance. A durable unique event/channel key prevents repeated scheduling; an ambiguous send must remain held for reconciliation, not blindly retried.

## Page inventory
All entries initially: static file found; runtime, console, network, permissions, loading/error/empty states and 390×844 layout UNTESTED.

- `frontend/src/app/(protected)/accounts-payable/page.tsx` — UNTESTED
- `frontend/src/app/(protected)/accounts-receivable/page.tsx` — UNTESTED
- `frontend/src/app/(protected)/background-jobs/page.tsx` — UNTESTED
- `frontend/src/app/(protected)/banking/page.tsx` — UNTESTED
- `frontend/src/app/(protected)/barcode/page.tsx` — UNTESTED
- `frontend/src/app/(protected)/cash-flow/page.tsx` — UNTESTED
- `frontend/src/app/(protected)/chart-of-accounts/page.tsx` — UNTESTED
- `frontend/src/app/(protected)/contact/page.tsx` — UNTESTED
- `frontend/src/app/(protected)/credit-notes/page.tsx` — UNTESTED
- `frontend/src/app/(protected)/customer-payments/page.tsx` — UNTESTED
- `frontend/src/app/(protected)/customers/page.tsx` — UNTESTED
- `frontend/src/app/(protected)/dashboard/page.tsx` — UNTESTED
- `frontend/src/app/(protected)/data-migration/page.tsx` — UNTESTED
- `frontend/src/app/(protected)/delivery-challans/page.tsx` — UNTESTED
- `frontend/src/app/(protected)/document-logs/page.tsx` — UNTESTED
- `frontend/src/app/(protected)/e-invoices/page.tsx` — UNTESTED
- `frontend/src/app/(protected)/e-way-bills/page.tsx` — UNTESTED
- `frontend/src/app/(protected)/expenses/page.tsx` — UNTESTED
- `frontend/src/app/(protected)/finance-audit/page.tsx` — UNTESTED
- `frontend/src/app/(protected)/financial-dashboard/page.tsx` — UNTESTED
- `frontend/src/app/(protected)/general-ledger/page.tsx` — UNTESTED
- `frontend/src/app/(protected)/goods-receipts/page.tsx` — UNTESTED
- `frontend/src/app/(protected)/home/page.tsx` — UNTESTED
- `frontend/src/app/(protected)/inventory/page.tsx` — UNTESTED
- `frontend/src/app/(protected)/invoices/page.tsx` — UNTESTED
- `frontend/src/app/(protected)/journal-entries/page.tsx` — UNTESTED
- `frontend/src/app/(protected)/labour/page.tsx` — UNTESTED
- `frontend/src/app/(protected)/payroll/page.tsx` — UNTESTED
- `frontend/src/app/(protected)/products/page.tsx` — UNTESTED
- `frontend/src/app/(protected)/purchase-orders/page.tsx` — UNTESTED
- `frontend/src/app/(protected)/purchase-returns/page.tsx` — UNTESTED
- `frontend/src/app/(protected)/sales-orders/page.tsx` — UNTESTED
- `frontend/src/app/(protected)/sales-returns/page.tsx` — UNTESTED
- `frontend/src/app/(protected)/settings/audit/page.tsx` — UNTESTED
- `frontend/src/app/(protected)/settings/categories/page.tsx` — UNTESTED
- `frontend/src/app/(protected)/settings/invoices/page.tsx` — UNTESTED
- `frontend/src/app/(protected)/settings/modules/page.tsx` — UNTESTED
- `frontend/src/app/(protected)/settings/numbering/page.tsx` — UNTESTED
- `frontend/src/app/(protected)/settings/organization/page.tsx` — UNTESTED
- `frontend/src/app/(protected)/settings/page.tsx` — UNTESTED
- `frontend/src/app/(protected)/settings/permissions/page.tsx` — UNTESTED
- `frontend/src/app/(protected)/settings/roles/page.tsx` — UNTESTED
- `frontend/src/app/(protected)/settings/users/page.tsx` — UNTESTED
- `frontend/src/app/(protected)/stock-movements/page.tsx` — UNTESTED
- `frontend/src/app/(protected)/stock-transfers/page.tsx` — UNTESTED
- `frontend/src/app/(protected)/subscription/page.tsx` — UNTESTED
- `frontend/src/app/(protected)/suppliers/page.tsx` — UNTESTED
- `frontend/src/app/(protected)/taxation/page.tsx` — UNTESTED
- `frontend/src/app/(protected)/tools/page.tsx` — UNTESTED
- `frontend/src/app/(protected)/trial-balance/page.tsx` — UNTESTED
- `frontend/src/app/(protected)/vendor-bills/page.tsx` — UNTESTED
- `frontend/src/app/(protected)/vendor-debit-notes/page.tsx` — UNTESTED
- `frontend/src/app/(protected)/warehouses/page.tsx` — UNTESTED
- `frontend/src/app/(protected)/workforce/[section]/page.tsx` — UNTESTED
- `frontend/src/app/(protected)/workforce/page.tsx` — UNTESTED
- `frontend/src/app/deadlines/page.tsx` — UNTESTED
- `frontend/src/app/forgot-password/page.tsx` — UNTESTED
- `frontend/src/app/login/page.tsx` — UNTESTED
- `frontend/src/app/owner/page.tsx` — UNTESTED
- `frontend/src/app/page.tsx` — UNTESTED
- `frontend/src/app/pricing/page.tsx` — UNTESTED
- `frontend/src/app/reset-password/page.tsx` — UNTESTED
- `frontend/src/app/signup/page.tsx` — UNTESTED
- `frontend/src/app/verify-email/page.tsx` — UNTESTED

## API routing inventory
- `apps/accounts/api/v1/urls.py` — endpoint runtime/tenant isolation UNTESTED
- `apps/authorization/api/v1/urls.py` — endpoint runtime/tenant isolation UNTESTED
- `apps/business/urls.py` — endpoint runtime/tenant isolation UNTESTED
- `apps/core/api/v1/urls.py` — endpoint runtime/tenant isolation UNTESTED
- `apps/core/urls.py` — endpoint runtime/tenant isolation UNTESTED
- `apps/finance/api/v1/urls.py` — endpoint runtime/tenant isolation UNTESTED
- `apps/finance/urls.py` — endpoint runtime/tenant isolation UNTESTED
- `apps/inventory/api/v1/urls.py` — endpoint runtime/tenant isolation UNTESTED
- `apps/inventory/urls.py` — endpoint runtime/tenant isolation UNTESTED
- `apps/migration/api/v1/urls.py` — endpoint runtime/tenant isolation UNTESTED
- `apps/organizations/api/v1/urls.py` — endpoint runtime/tenant isolation UNTESTED
- `apps/products/api/v1/urls.py` — endpoint runtime/tenant isolation UNTESTED
- `apps/purchasing/api/v1/urls.py` — endpoint runtime/tenant isolation UNTESTED
- `apps/purchasing/urls.py` — endpoint runtime/tenant isolation UNTESTED
- `apps/saas/urls.py` — endpoint runtime/tenant isolation UNTESTED
- `apps/sales/api/v1/urls.py` — endpoint runtime/tenant isolation UNTESTED
- `apps/sales/urls.py` — endpoint runtime/tenant isolation UNTESTED

## Outstanding acceptance
Partner signup/approval/referral/commission/payout; recurring documents; automatic customer reminders; monthly summaries; all-page smoke tests; physical Capacitor checks; live provider delivery; financial concurrent rollback and migration. No “works” assertion without recorded evidence.

## Implementation checkpoint
See BUGS_FIXED.md for fixes, DESIGN_SYSTEM.md for adopted UI patterns, and UPGRADE_STATUS.md for rollout and unfinished scope. Page/API runtime entries remain UNTESTED; static inspection and unit tests do not replace a route walkthrough.

## New partner routes
`/partners`, `/owner/partners`, `/api/v1/saas/partners/session/`, `/api/v1/saas/partners/dashboard/`, `/api/v1/saas/owner/partners/`: implementation and automated regression coverage added. Authenticated visual, console/network and physical-device checks remain UNTESTED. See PARTNER_PORTAL.md for walkthrough and omissions.
