# Upgrade status and rollout

This branch is a reviewable first implementation, **not completion of the full requested upgrade**. No deployment, live email, live GST/OpenAI call, production database migration or APK release was performed.

## Implemented
Durable subscription/welcome outbox; IST renewal scheduler; guarded ambiguous email sends; cancellation of stale renewal events; persistent Sandbox GST cache/quota/single-flight; tenant/user-scoped AI extraction cache; e-invoice reservations; requested core plan capacities and Free activation; compact invoice toolbar/cards/filter sheet; clearer KPIs; removal of global mobile create overlay; native status/keyboard handling; audit inventory and regression tests.

## Before staging rollout
1. Back up database; use an isolated staging environment. Deploy backend and worker from the same commit.
2. Run `python manage.py ensure_reliability_indexes` to install cache TTL and polling indexes. Cache expiration is also checked in queries. Do not expire pending paid-provider claims automatically.
3. Run `python manage.py upgrade_plan_limits` to preview only. Owner must choose monthly GST lookup quotas first. Default zero deliberately blocks paid Sandbox calls; existing membership snapshots without this quota also block them.
4. After choosing quotas, use `upgrade_plan_limits --apply --gst-basic N --gst-plus N --gst-pro N` with actual integers. `--include-memberships` explicitly replaces existing membership limit snapshots. It does not delete excess resources or change plan prices. Review contractual allowances before applying.
5. Configure authenticated production SMTP authorized to send from `nexease.contact@gmail.com`. Welcome events queue independently of the renewal toggle. In development, attempted email events are held for review, not silently called delivered.
6. Renewal schedule is disabled by default: `SUBSCRIPTION_ALERTS_ENABLED=false`, `SUBSCRIPTION_ALERT_DAYS=7,3,1`. The owner has now approved 7,3,1 days before expiry, with no expiry-day reminder. Set SUBSCRIPTION_ALERT_DAYS=7,3,1 in staging; older tests also exercise other explicit schedules.
7. Keep `run_background_worker` running. Inspect `subscription_alerts` pending/sending/review_required records and provider claims. Never reset ambiguous email/paid-provider events automatically: reconcile with provider logs first.
8. Smoke-test signup, Free activation, subscription UI, GST quota errors, invoice list and keyboard/back/navigation on a real APK before merging/deploying.

## Delivery semantics
Unique event keys and atomic claims prevent duplicate scheduling/claiming. In-app notifications have a unique delivery key and safe replay. SMTP does not support an idempotency token; a crash after acceptance cannot prove delivery exactly once. Ambiguous sends are held, which avoids automatic duplicates but can require manual recovery of unsent mail. Provider claims also remain after a process crash to avoid duplicate billed requests. MongoMock tests do not prove distributed behavior on a real replica set.

## Pending requirements
- Complete authenticated browser/device audit of all 64 page files and 369 resolved API routes, including permissions/console/network/loading/empty/error states.
- Partner signup, approval, referrals, commissions, payouts and statements. Rates are now confirmed at 20% first payment and 10% renewal. A review-only operator ledger is implemented; public partner UI and payout/tax policy remain incomplete. See PARTNER_COMMISSION_RULES.md.
- Usage threshold alerts and partner welcome email integration; live verification of the approved renewal schedule.
- Full transactional accounting/stock/payroll linkage audit, financial-year invoice numbering and concurrent financial integration tests. Existing Decimal use alone is insufficient assurance.
- Automatic payment reminders, recurring invoices/expenses, low-stock automation, monthly summaries and long-form draft autosave.
- All-screen shared component migration, remaining invoice card actions/date filters, measured text contrast and three-card viewport acceptance.
- Full auth/tenant/ledger/commission test matrix, real provider integration and APK build/device QA.

Free users/invoices and paid core caps follow the request. Extra Free limits (30 bills, 100 products, one warehouse) are provisional; GST quotas default to zero. Existing paid prices are preserved. Owner must approve these unspecified commercial details before release.

## Verification
- Standalone backend suite: 232 tests pass (isolated MongoMock database).
- Frontend suite: 42 files, 201 tests pass; subsequent KPI/IST focused tests rerun after final markup adjustment.
- TypeScript passes. ESLint exits successfully with 0 errors and 18 warnings; scoped existing hydration/ref lint exceptions are documented in BUGS_FIXED.md.
- Next.js production build passes with a test API URL; this is not a deployed environment validation.
- Additional signup/worker/mailbox/document-email Django suites: 73 tests pass after seeding the permission catalogue and updating the mailbox fixture to include its tenant. All SMTP calls were mocked.
