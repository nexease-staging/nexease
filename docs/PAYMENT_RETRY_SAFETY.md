# Customer and supplier payment retry safety

## Implemented
- Invoice and bill payment services acquire the existing organization lock before reloading the document and checking the outstanding amount. Bank transaction creation, bank transfer posting and bank-statement payment execution use the same reentrant lock.
- Both payment APIs accept `request_key` (16–100 letters, digits, underscores or hyphens). The invoice/bill dialogs retain an opaque request key in local browser storage until a successful response. An immediate submit guard prevents double clicks. Storage failure stops submission.
- The server stores a durable receipt keyed by organization, payment kind and request key. Replays require the same authenticated user and normalized payment details, and return the existing payment without moving money again, including after full settlement. Changed details are rejected. Existing callers without keys remain supported, but cannot replay a successful response by key.
- The server marks the operation `writing` before the first financial write. Ordinary pre-write validation errors remove the receipt so corrected input can be retried. An interruption after this boundary is retained as `writing` or `review_required`; both block further payment attempts for that document, even with a different key.
- Supplier payments now preflight bank/journal permissions and active system accounts, like customer payments.
- Payment failure no longer tries to erase financial evidence with compensating deletes. Bank-statement completion failures preserve the posted payment and journal, and flag the payment for review. Statement payments use deterministic retry keys.
- `ensure_reliability_indexes` installs the tenant/document/status receipt lookup index. Receipt `_id` uniqueness is supplied by MongoDB. Receipts have no TTL.

## Inspect an interrupted operation
Run against the intended environment only:

```powershell
.\.venv\Scripts\python.exe manage.py review_payment_operations --organization YOUR_ORGANIZATION_ID
.\.venv\Scripts\python.exe manage.py audit_customer_payment_links --organization YOUR_ORGANIZATION_ID
```

These commands are read-only. The first lists operation IDs, document IDs, payment numbers and lock presence for one organization. The second checks customer payment source links. Neither certifies bank balances or tax/GL correctness. Supplier payment source reconciliation still needs operator review.

Before repairs, back up the database, stop conflicting writers, and reconcile the payment, bank transaction, invoice/bill totals, journal and statement match. Do not delete a posted journal or erase a receipt to force a retry. No automatic repair/unlock command is included: the correct repair depends on which writes reached the database. A process killed while holding the organization lock requires reviewed recovery; locks intentionally do not expire while an earlier writer might still be running.

## Verification and limits
Regression tests run real customer/supplier payment, bank and journal service paths against isolated MongoMock storage, with permissions mocked. They cover successful replay, stale snapshots, overpayment, changed payload/user/tenant, concurrent requests, journal failure and statement-completion failure. Browser helper tests cover retry identity, document isolation and blocked storage. No live payments are sent.

This is **not a MongoDB multi-document transaction**, nor proof of all financial write paths. Real replica-set interruption/concurrency tests and review of credit notes, cancellations, imports, refunds and other writers remain necessary. Existing partial payments predating receipts are not repaired. Storing a payment locally before a journal failure may leave temporary inconsistent totals until reviewed reconciliation. The hold prevents compounding that inconsistency; it does not make the interrupted payment complete.

The retry guarantee applies to the same request key. Clearing browser storage, a separate browser/device, changed input or a legacy caller can create a new key after a completed payment; those are not automatically inferred to be duplicates. Use distinct references for independent payments and reconcile uncertain outcomes before recording another payment.

## Rollout
Deploy backend before the updated web/APK client; older backends reject `request_key`. Backend and workers must use the same code. Run `ensure_reliability_indexes`. Verify one customer and supplier payment and a repeated identical request on isolated staging before release. Rebuild the APK to include the updated dialogs. No deployment is performed by this code bundle.

### Checkpoint results (2026-11-10)
- Standalone backend suite: 274 passed, including 15 payment safety/operation tests.
- Invoice, purchasing, finance and bank-payment-suggestion API regression suites: 194 passed.
- Frontend: 44 test files, 207 tests passed.
- TypeScript and Next.js production build passed with a test API URL.
- ESLint: zero errors, 18 pre-existing warnings.
- `git diff --check`: passed.
- Not run: real MongoDB replica-set failover/kill tests, real bank/SMTP calls, Android build/device validation or deployment.
