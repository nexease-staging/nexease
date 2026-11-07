> Baseline report for the prior UI release. See NAVY_THEME_VALIDATION.md for the latest theme/setup update.

# Validation — 7 November 2026

Passed:
- Frontend TypeScript check.
- 33 frontend test files, 184 tests. Includes invoice creation and totals, signup address payload/password validation, module menu switching, permission and Pro gating.
- 10 isolated backend/signup tests using mongomock. Includes public signup API, saved optional business address, backwards compatibility, rejection of invalid address before records are created.
- Production web build: 80 prerendered pages.
- Mobile static web export: 80 prerendered pages.
- ZIP integrity, source comparison for changed files, preservation of all previous archive entries, SHA-256 manifest generation.

Not completed:
- Visual browser inspection of this running build: the browser could not reach the local development server.
- Physical Android/iOS testing, signed APK/AAB generation, Play review.
- End-to-end live SMTP/provider/payment/GST operations, real customer migrations or every NexEase business transaction.
- GoGSTBill feature parity. See REFERENCE_FEATURE_GAPS.md.

All backend checks used isolated synthetic data. No production credentials or customer data are included.
