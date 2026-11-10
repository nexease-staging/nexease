# Invoice numbering checkpoint

Existing invoice numbers are unchanged. Financial-year numbering is off by default.

## Behavior
- Invoice allocation checks both the atomic reservation collection and existing invoices, including older invoices created before reservations were recorded. Used numbers are skipped for automatic allocation and rejected for manual allocation.
- New invoice reservations contain organization, number, financial year, mode and time. Saving attaches the invoice ID. A failed model validation retry on the same object retains its number. A new request cannot take another request's reservation.
- Direct, sales-order, workforce and AI invoice flows pass the invoice date to numbering. Sales-order invoices without a supplied number now use the shared sequence instead of a UUID-style number.
- AI proposals retain ownership of their reserved number across corrected-form requests. Existing invoice edits do not invoke new-number allocation.
- Counters only advance. Do not delete reservations or decrement a counter to fill a gap.

## Optional financial-year sequence
In **Settings → Numbering → Invoice → Configure**, enable **Separate April–March invoice sequence (IST)** and choose the prefix, next number and minimum digits. This changes future automatic numbers only. Example: `INV-26-27/00001`.

The invoice date selects the financial year. An aware timestamp is converted to Asia/Kolkata first; date-only and naive document dates are treated as local calendar dates. March 31 belongs to the previous financial year; April 1 begins the next. Backdated invoices advance their own year's sequence. The preview uses the current year and is provisional. Settings change the current year's next value; other years begin at 1 unless they already have a counter.

Turning the option off resumes the legacy sequence without decreasing its counter. Manual numbers remain organization-wide unique, even across years. No existing invoice, journal, payment or tax document is renamed.

## Read-only investigation

```powershell
.\.venv\Scripts\python.exe manage.py audit_invoice_numbers --organization YOUR_ORGANIZATION_ID
```

This lists reservations with missing invoice documents or inconsistent links. It supports `--limit` up to 10000 and reports truncation. Older reservation rows without metadata are supported. It does not enumerate every possible numerical gap or every older invoice without a reservation. Unattached reservations can represent abandoned validation, deleted drafts or interrupted writes; investigate before deciding what happened.

## Limits
This is not a gap-free legal-numbering guarantee or a multi-document transaction. A crash between incrementing a counter and inserting its reservation can still leave a gap without reservation metadata. Existing data is not bulk migrated, and deleted/cancelled numbers are never automatically recycled. Real MongoDB replica-set interruption tests remain pending.

A unique invoice number does not make all invoice-creation requests idempotent. Repeated automatic-create requests may still produce different invoices; broader creation/recovery work remains. The existing workforce billing key and AI proposal state guards are preserved. No claim is made that this completes all financial workflows or GST filing validation.

## Rollout
Deploy backend before frontend and rebuild the APK for the new setting and preview. Keep backend and worker versions aligned. Test both legacy and financial-year numbering on isolated staging. No environment secrets are changed and no production deployment is included.

## Verification (2026-11-10)
- Backend suite: 284 passed, including nine numbering tests; one additional AI financial-year correction test passed separately after being added.
- Invoice API regression suite: 37 passed.
- Frontend: 44 files, 208 tests passed; all five numbering dialog tests rerun after the compact year-format adjustment.
- TypeScript/Next.js production build passed. ESLint: zero errors, 18 existing warnings.
- Whitespace check passed. All database tests used isolated MongoMock; no real customer records were changed.

If an AI proposal's reserved number belongs to a different financial year after its date is corrected, confirmation is blocked with instructions to clear the number and allocate a new one. The old reservation is retained for investigation.
