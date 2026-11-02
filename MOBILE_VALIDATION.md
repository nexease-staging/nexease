# NexEase Easy Mobile validation — October 31, 2026

## Source
NexEase_Workforce_Upgrade.zip, latest resolved Library version 3.
SHA-256: 75d2e71c7adf52181b37dde296d8ad6579ab30494c86ab541166842c362dcfa9
Android/iOS container and native adapters carried forward from the previous NexEase mobile package; backend and business screens come from the newer web ZIP.

## Checks completed in this environment
- 131 backend update tests passed using isolated mongomock data.
- 883 existing backend regression tests passed; Django system checks reported no issues.
- 132 frontend tests passed across 19 files, covering invoice submission and mode changes, mobile URL validation, permission-filtered actions, period selection, balance privacy and advanced-tool preferences.
- Next.js production mobile export and TypeScript compilation passed, generating 73 static pages including workforce subpages.

## Limits
Browser visual/interaction checks were attempted but blocked by the environment's Chromium process-singleton socket restriction. No screenshot-based acceptance claim is made.
Android SDK and Xcode are not available here: Gradle native compilation, Xcode compilation, release signing and physical-device testing were not completed. This ZIP is source plus bundled web assets/native projects, not an APK/IPA.
Tests use mocked API responses and isolated database data. No live customer data was changed; no paid AI, payment, email or GST-provider transaction was run.
The simplified home and menu are new; specialist finance, tax and workforce pages retain existing controls. Some data grids still scroll horizontally. This is a Capacitor mobile app using the existing React screens and Django API, not a separate React Native rewrite.
The inherited dependency tree may contain deprecation/security advisories; this is not a comprehensive security audit or app-store approval.

## Release notes
Mobile configuration remains HTTPS-only with explicit origins and CSRF protection. Native downloads use the share sheet. The Android launcher now requires JDK 21 explicitly, avoiding the previously reported Java 25 incompatibility.

## CSRF hotfix
See CSRF_HOTFIX.md. Native API calls now bypass the automatic fetch patch and send Origin, Referer and CSRF token via CapacitorHttp.request directly. Eight new transport tests pass; physical-device acceptance remains pending.
