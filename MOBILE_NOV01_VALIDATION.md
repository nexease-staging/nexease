# Barcode catalogue update validation — Android 1.2

- Frontend: 161 tests passed in 26 files, covering native scanner capture, web decoder/photo fallback, hardware input, catalogue listing and download actions.
- Backend: 44 tests passed against isolated mongomock storage. Includes generated/stable codes, supplied leading zeroes, duplicate create/update validation, blank-update generation, tenant isolation, catalogue permissions, backfill preservation and Excel text cells.
- Normal web build and mobile static export passed. Android Capacitor sync registered @capacitor/barcode-scanner 3.1.3.
- Android minimum SDK raised to 26 as required by the native scanner. APK version code 4 / version 1.2.
- No Android SDK compilation, signed APK, physical phone camera, USB/Bluetooth scanner or native save/share test was performed here. Rebuild/install and perform acceptance tests in MOBILE_UPDATE_NOV01.md.

Earlier update validation follows; earlier counts describe those runs only.

---

Camera hotfix (Android 1.1.1): bundled decoding tested with a rasterized Code 128 sample created by the NexEase label generator. Camera-to-product lookup, unsupported device enumeration, permission failure, cancelled camera acquisition, ordinary unreadable frames, photo decoding and hardware input are covered by component tests. Physical-phone camera operation remains unverified.

# Validation — 1 November 2026 mobile update

- Frontend: 157 tests passed in 25 test files, including mobile drawer text, account menu/logo, native session routing, notification opt-in/token removal and safe notification navigation.
- TypeScript: check passed.
- Clean frontend dependency installation (`npm ci`): passed.
- Backend: 52 tests passed against an isolated in-memory MongoDB substitute, including device registration validation/scoped deletion, authentication requirement, role-filtered reminders, cross-tenant delivery exclusion, native/web session expiry behavior, notification repository and public authentication regressions. Permission masters were seeded in the test database.
- Next.js mobile static export: passed.
- Capacitor Android sync: passed with the local-notifications and push-notifications plugins registered.
- Next.js normal web production build: passed.
- Icons: generated from a code-native vector mark; launcher raster inspected.

Limitations: This environment cannot run a working Chromium session, so the mobile menus/filter geometry have not been screenshot-verified here. No Android SDK/device build, signed APK, live Firebase delivery, device permission dialog, physical camera or USB/Bluetooth scanner test was performed. Follow MOBILE_UPDATE_NOV01.md for Firebase setup and device acceptance checks. Existing dependencies may retain audit findings; no new claim of a zero-vulnerability dependency tree is made.
