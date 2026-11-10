# Partner email, statements and external payout recording

## Implemented
- Partner email verification and password reset via expiring, single-use links (one hour). Reset rotates partner session generation, invalidating existing sessions.
- Owner approval now requires verified partner email. Existing approved accounts can request verification before exports/payouts.
- Encrypted token emails and stable-key welcome emails use the existing background worker. Registration does not call SMTP. Sender: `NexEase <nexease.contact@gmail.com>`.
- CSV and PDF statements from the partner portal, live-only and session-scoped. CSV escapes formula-leading values. At most 10,000 commission rows per export; larger exports require support.
- `/owner/partner-payouts` records an externally completed payment against one commission. Fresh owner password/TOTP, positive GST-reviewed amount, verified approved partner, exact amount match and external payment reference are required. One immutable record per commission prevents repeated submission from duplicating it. Owner identity, reason and timestamp are stored with the record.

## What payout recording means
This does not initiate a transfer, verify a bank settlement, calculate withholding tax or post GL journals. It records the owner's assertion that a payment was completed externally. It currently supports one full payout per commission, not partial or consolidated batch payouts. Changes to commissions after refunds do not overwrite recorded payouts; statement commission and payout columns must be reconciled. Corrections/reversals and a dedicated discrepancy workflow remain to be built.

## Configuration and staging
Backend and worker must share database, Django signing key and `OWNER_ENCRYPTION_KEY` (existing Fernet key). Do not rotate this key without migrating queued encrypted mail. `FRONTEND_BASE_URL` must be HTTPS and point to the matching frontend. Configure authenticated production SMTP authorized for the sender, set EMAIL_MODE=production and run the existing background worker. No secrets are included in this update.

In development mail remains pending. SMTP ambiguity is held as review_required (or sending on a process crash); automatic resend is intentionally avoided because SMTP cannot guarantee exactly-once delivery. A user can request a fresh verification/reset link within rate limits. Superseded, expired and changed-generation links are cancelled before delivery. Do not manually resend an ambiguous welcome without checking provider logs.

## Staging walkthrough
1. Apply as partner. Observe a queued welcome; verify no SMTP blocking in registration.
2. Sign in and request email verification. Open the link, explicitly confirm, then refresh/sign in again. Reusing the link must fail.
3. Owner approves only after email verification. Sign in again and confirm live statements belong to that partner.
4. Sign out, request password reset. Set a strong password via link. Old password and old sessions must fail; reused link must fail.
5. Download CSV/PDF; compare net subscription, refund, commission and recorded payout values to source records. Check another partner cannot export these records.
6. In isolated test data, record a payout through the owner page using `test:payment_id`. Repeat submission: no duplicate. Wrong amount or unreviewed GST must reject. Do not create fictitious live payout records.

## Still outstanding
Real SMTP inbox verification, authenticated browser/PDF visual QA, Android testing, automated GST source ingestion, bank-transfer integration, accounting/GL linkage, payout corrections, batch payouts and the wider audit/UI/automation scope. No deployment or live messages/payments were performed by this implementation.

## Validation checkpoint
The full isolated backend run passed 257 tests before the final two delivery tests and payout-display addition. The final partner-focused run passed all 27 tests. Frontend regression passed all 204 tests across 43 files with two workers. Production build/TypeScript and targeted lint passed; no live provider delivery, browser visual review or physical Android testing is implied.
