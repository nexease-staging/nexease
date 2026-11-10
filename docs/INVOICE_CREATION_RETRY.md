# Invoice creation retry protection

## Included
- The direct/quick invoice and sales-order invoice HTTP endpoints accept `X-NexEase-Request-Key`. The web client supplies a durable opaque key, also used by the Capacitor build. CORS permits this header.
- Each receipt is scoped to organization, route and key, and bound to the authenticated user, body and numbering choice. A completed retry returns the original response and invoice ID. Reuse with changed details or another user is rejected. Current create permission is checked before replay.
- Request claims use MongoDB's unique `_id`. Concurrent attempts with the same key do not execute the creation path twice. Completed receipts do not expire.
- The browser retains the key after network failures and through CSRF refreshes; it clears it only after a successful response. Only a hash and opaque key are stored locally, not customer/item details. If storage is unavailable, creation stops before sending.
- Both invoice forms use immediate submission guards. A query-cache refresh failure after a successful save no longer sends users back into creation as though the save failed.
- Before record/stock writes, the receipt enters `writing`. Interrupted writes enter `review_required`, or remain in progress after a process crash. Retrying the same key, or submitting the same body/numbering with a new key while its receipt is unresolved, does not execute again.
- Direct stock failures retain the draft invoice instead of deleting its evidence. An invoice linked to an unfinished creation request cannot be issued until reviewed. There is no automatic repair or release.
- Pre-write validation failures remove the claim so corrected data can be submitted.

## Review an interruption

```powershell
.\.venv\Scripts\python.exe manage.py review_invoice_requests --organization YOUR_ORGANIZATION_ID
```

This is read-only, tenant-scoped, capped and reports truncation. It displays saved invoice IDs/numbers when available. Before any repair, back up the database and inspect customer/item/warehouse records, invoice lines, stock quantities/movements, numbering reservations and audit records. Do not delete the receipt to force a retry. A notification failure can produce a hold even though the invoice and stock succeeded; distinguish that from an incomplete stock write.

## Deployment order
1. Deploy backend and worker from the same commit before the frontend. Old backends ignore the header and cannot provide the guarantee.
2. Run `python manage.py ensure_reliability_indexes` against the intended staging database. It adds receipt lookup indexes without deleting history.
3. Deploy the frontend; rebuild/reinstall the APK for the client-side retry behavior.
4. On isolated staging, create one goods invoice, replay the same request key/body and confirm a single invoice and a single stock deduction. Test the sales-order path as well.

No deployment, production data changes or APK build is included in this bundle.

## Boundaries
- This is not a multi-document database transaction or automatic financial recovery. Interrupted writes can still leave partial records; they are held for review.
- Legacy clients and direct service callers without the header are not covered by HTTP request receipts. Workforce billing keys and AI proposal guards remain separate.
- A different body/numbering choice, another browser/device, cleared local storage or a deliberately new key after completion can represent a new request. The system does not infer all business duplicates across those cases. Inspect the existing invoice before changing an uncertain submission.
- Responses are replayed as original creation snapshots; they do not certify the invoice's current status or recreate a subsequently deleted invoice.
- Real MongoDB replica-set failover, physical Android devices and network interruption end-to-end testing remain outstanding. Do not describe this as full transaction atomicity or universal exactly-once invoice creation.

## Verification
- Standalone backend suite: 293 tests passed.
- Eight invoice creation integration tests passed, including actual direct invoice/customer/product/stock operations, lost-response replay, concurrent submission, changed payload/numbering, user/tenant/permission boundaries, corrected validation, injected post-stock/stock failures and sales-order replay. These use isolated MongoMock with permissions mocked.
- The eight tests were rerun after adding the issue-blocking check for unfinished drafts; the invoice API regression suite was also rerun.
- Frontend: 45 files / 213 tests passed. Includes persistent key, CSRF refresh, blocked storage and synchronous double-submit checks.
- TypeScript/Next.js production build passed. ESLint: zero errors, 18 existing warnings. No real external requests or financial transactions were made.
