# Reliability upgrade fixes — 10 November 2026

Baseline main: 51ee883. These are code/test results, not a production certification.

| ID | Severity | Screen/file | Root cause and change | Evidence |
|---|---|---|---|---|
| COST-001 | High | business/gst_lookup.py; saas/provider_guard.py | Sandbox calls had no persistent cache or monthly quota. Added tenant-scoped 30-day cache, unique in-flight claim and atomic paid-attempt reservation. Quota exhaustion blocks the provider. | Cache expiry, tenant isolation, quota, in-flight and failure tests |
| COST-002 | High | saas/provider_guard.py | Different concurrent lookups can initialize the same monthly counter. Duplicate insert races are tolerated; conditional atomic increments enforce the cap. | Atomic query reviewed; real Mongo stress testing pending |
| AI-001 | Medium | saas/ai.py | Identical extraction requests called the provider again. Cache scoped to tenant, user, model and input; existing permission, token and usage checks retained. | Cost-guard unit suite; full AI workflow untested |
| LIMIT-001 | High | entitlements.py; upgrade_plan_limits.py | Plan defaults differed from requested capacities. Added Free and requested capacities, explicit audited migration, Free activation, and persistent e-invoice reservations. | Plan constants and reservation tests; activation UI not end-to-end tested |
| ALERT-001 | High | saas/alerts.py; worker | No durable renewal events. Unique per-cycle/date/user/channel events, atomic claims and IST scheduling now run through existing worker. | Simulated dates, concurrent scans/delivery, restart tests |
| ALERT-002 | High | saas/alerts.py | Retrying an ambiguous SMTP response risks duplicate mail. Failed sends are held for review; in-app delivery safely replays its unique notification key. | Timeout test; SMTP exactly-once delivery is not guaranteed |
| ALERT-003 | Medium | saas/alerts.py | Queued reminders can become stale after renewal. Recheck current membership cycle before delivery and cancel old-cycle events. | Renewal-before-delivery regression |
| WELCOME-001 | Medium | organization_signup_service.py | Added asynchronous welcome events for signup, with stable per-user event identity. | Duplicate-enqueue test; signup integration suite reported separately |
| UI-001 | Medium | stat-card.tsx | Truncation hid critical financial values. Labels/captions wrap; amounts remain visible, optional exact-value disclosure on unlinked cards. | Component test |
| UI-002 | Medium | app-shell.tsx; globals.css | Global plus and large assistant obscured records. Removed global plus; compact assistant above navigation and increased bottom padding. | Build/type-check; physical-device verification pending |
| UI-003 | Medium | invoices-view.tsx | Stacked filters and actions consumed mobile space. Compact toolbar, horizontal KPIs/chips, filter sheet and compact cards. | Component suite; 390×844 acceptance not visually verified |
| DATE-001 | Medium | lib/format.ts | Device timezone could change overdue classification. Derive business date in IST. | Two boundary/paid-state tests |
| MOBILE-001 | Medium | mobile-runtime.tsx | Native status contrast and keyboard handling were incomplete. Light status icons over navy, safe areas, scroll focused input and catch plugin failures. | Type-check/build only; APK/device tests pending |

## Test maintenance and limitations
Stale tests now distinguish read-only master lookup from invoice creation and use the existing paid prices, which this upgrade does not change. Ref assignment was moved out of render where appropriate. Scoped React lint exceptions remain for intentional effect-driven hydration/reset flows and a ref-forwarding render prop; they are not evidence that every hook pattern has been redesigned. Lint has 18 warnings and no errors.

Financial transactions, financial-year numbering, partner commissions and full route smoke coverage have not been fixed or certified by this patch. See AUDIT.md and UPGRADE_STATUS.md.

## Approved-policy follow-up
- COMMISSION-001: added review-only 20% first/10% renewal ledger with idempotent payment keys, refund recalculation and sandbox isolation. Nine focused tests; no payout functionality claimed.
- ALERT-004: approved default schedule is now 7,3,1 IST days before expiry. Explicit environment settings still override it.
- UI-004: corrected an accidental internal variable name in the access-denied user message.
