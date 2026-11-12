# NexEase consolidated pilot release candidate — 13 November 2026

## What is included
All UI work after 2c71734, including per-line rupee/percentage invoice discounts; clickable invoice cards; reordered invoice detail view; mobile Returns, Migration and Administration tables; Android Back dismissal for account and notification menus.
Earlier branch changes remain included in the repository: reliability guards, partner review/payout-recording flows, shared-register form safeguards and mobile records across principal modules.

## Verified on this candidate
- Standalone backend: 297 tests passed.
- Original application backend suite: 966 tests passed.
- Frontend: 230 tests passed across 49 files.
- Web production build and TypeScript passed.
- ESLint: zero errors, 18 existing warnings.
- Android static export: see delivery result; this is not native APK compilation.
- git diff whitespace check and bundle verification.
Tests use isolated/mocked databases/providers. No live emails, payments or tenant records were created by these checks.

## Scope not completed — do not advertise as finished
- Runtime audit of every authenticated page/API, measured accessibility/contrast and all mobile viewports.
- Full atomic accounting/stock/payroll consistency and real-replica-set concurrency/interruption testing.
- Automatic recurring invoices/expenses, scheduled customer reminders, owner monthly summaries, complete low-stock/reorder automation.
- Draft autosave across long forms and exit guards for every legacy form.
- Full shared toolbar/form migration and clickable-card behaviour for every module.
- Live provider/renewal-alert delivery verification, commission payout corrections, automatic transfers/GL posting.
- Physical Android camera/photo scanning, push notifications, offline recovery, keyboard/back/accessibility and signed release/AAB validation.
- Final owner decisions on provider quotas and provisional Free limits.

This is a candidate for a controlled pilot, not evidence that the complete original specification has been delivered.

## Single PR rollout
1. Import the cumulative bundle on upgrade/reliability-nov10. It requires 2c71734 and includes the invoice update; fast-forward also works from 7bb7042.
2. Push, create/update the PR to main, and wait for GitHub checks.
3. Merge only after reviewing scope. Confirm Render frontend/backend/worker serve the intended branch/commit.
4. These new changes require no database migration. Earlier reliability indexes were reported created by the user.
5. Build the APK from the merged main using BUILD_ANDROID.cmd and the Singapore API base URL.
6. Perform the acceptance checks below before distributing beyond a small pilot.

## Pilot acceptance (web and phone)
- Login/logout, organization switching where supported, role restrictions.
- Create draft invoice: 3 × ₹100, 10% discount → ₹30 discount and ₹270 before tax. Compare saved invoice/PDF.
- Reject >100% discount and rupee discount above line value.
- Tap invoice card: detail opens. Payment button opens payment only.
- Review invoice/customer/dates/amounts before expanding description/edit controls.
- Record a payment once, refresh, confirm outstanding and ledger.
- Download/share/email PDF; verify mailbox receipt and worker job status.
- Edit a shared register, cancel discard confirmation, verify values remain; then confirm discard.
- Test keyboard, Android Back, account menu, notification menu, camera and photo barcode scans.
- Check long names/amounts, dark mode and large text on updated tables.
- Verify backend and worker logs show no unexpected errors.

## Build
Stop the local frontend dev server before BUILD_ANDROID.cmd to avoid locked node_modules.
Use JDK 21 and an installed Android SDK. The script builds a debug APK; Play Store distribution requires a separate signed release process.
