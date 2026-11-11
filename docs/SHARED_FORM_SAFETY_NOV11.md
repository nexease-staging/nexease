# Shared register form safety — 11 November 2026

Applies to BusinessWorkspace register forms (including Workforce, Expenses and GST registers):
- Close, Cancel, Escape and Android dialog Back request confirmation before discarding changed values.
- Browser unload/reload registers the browser's native unsaved-change warning; browser support/interaction requirements apply.
- Save uses an immediate ref lock to suppress repeated submits while a request is pending.
- Inputs and Cancel are disabled during save; the existing dialog busy guard protects Close/Back.
- Sticky Save/Cancel footer uses labelled icons.
- Failed list invalidation after a successful server save is no longer reported as a failed save.

Regression coverage includes unchanged close, cancelled discard, busy dismissal, repeated confirmation suppression and actual shared-form duplicate submit.

This is not durable server-side idempotency for these registers: after an ambiguous network failure, verify the register before retrying a financial entry. It does not add autosaved drafts, guarantee warnings on every client-side navigation, or retrofit every separate legacy form.
The reusable exit guard is opt-in and currently applied to BusinessWorkspace only.

The accompanying cumulative bundle includes the finance and workforce/banking layout batches since 91fa101. No backend/database changes. Rebuild the APK only when ready to test the consolidated UI on a physical device.
