# Partner portal increment

## Included
- `/partners`: separate registration/sign-in, pending status, referral link, live commission review statement and referral registration references, 25 records per page.
- `/owner/partners`: owner-only applications, status filter, approval/rejection/suspension dialog, fresh owner password and TOTP, audited decisions.
- Homepage partner link and owner-console applications link.
- Customer signup accepts an optional referral code (prefilled from `?ref=`), validates active approval and blocks same-email self-referral. Attribution occurs before checkout and is removed on signup rollback.
- Partner passwords are hashed, sessions rotate on login and expire after eight hours. Approval/status changes invalidate old partner sessions. Partner authentication does not authenticate organization APIs or owner APIs.
- Statements derive identity from the server session; caller-supplied partner IDs cannot select another statement. Live/test segregation and GST review holds remain enforced. Customer account/document details and payment credentials are not exposed.

## Staging walkthrough
1. Open `/partners`, apply with a unique email and strong password. Sign in: pending review must appear without statements.
2. Sign in to `/owner`, open Partner applications. Verify applicant identity/email independently, then approve with password, fresh authenticator code and audit reason.
3. Sign in again at `/partners`. Copy referral link, open it in a separate browser session, and create a test customer organization. The optional referral field is visible/editable so attribution is not hidden.
4. Confirm one referral appears. Repeat signup with an inactive/random code: a clear validation error should appear, without creating an organization.
5. Reconcile test payments and GST evidence using existing operator tools. Test payments must NOT appear in the public live-only partner statement.
6. Use isolated fixtures for live-mode UI testing; do not charge real customers solely for QA. GST-missing rows show a hold, not a calculated commission. Commission amounts are still review-only.
7. Suspend the partner: subsequent dashboard API calls must reject the old session. Verify CSRF rejection for credential/approval POSTs.

## Remaining work / limitations
No automated email-ownership verification, partner password reset, partner welcome mail, CSV/PDF statement export, payout approval/recording, bank-transfer integration or partner-ledger GL posting in this increment. Owner approval requires independent identity/email verification. Do not present calculated review amounts as a payable obligation or completed payout. Same-email self-referral is blocked; broader identity matching requires a separate policy. Operator-created partner records without a portal password cannot be claimed just by entering their email; migration must be owner-controlled. The email unique index can fail if legacy data has duplicate partner emails: resolve those records before enabling portal registration.

The full NexEase upgrade remains incomplete. This increment has not been deployed or tested on physical Android devices. New routes need authenticated visual/mobile review before release.

## Validation results
- Backend isolated suite: 252 tests pass, including 8 new portal/auth/referral regressions.
- Frontend: 43 test files, 204 tests pass with two workers. The initial heavier parallel run had eight timing-related failures; the bounded-worker rerun passed without changing those assertions.
- Production Next.js build and TypeScript passed. The final effect scheduling adjustment was checked with targeted lint and portal tests.
- Full lint initially found two new effect-scheduling errors; both were corrected. Targeted lint of the changed portal/signup files now has zero errors and one existing image warning. The wider codebase's existing warnings remain.
- No live email/payment requests or production database changes were made. No browser/device visual certification is claimed.
