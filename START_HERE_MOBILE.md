# NexEase Easy Mobile — start here

This release uses NexEase_Workforce_Upgrade.zip, Library version 3 (October 31), as its backend and feature base. It contains a simplified mobile interface and locally bundled Android/iOS projects, not a signed installer. Existing feature screens and role checks remain; specialist screens retain their detailed workflows.

## What changed
- Home: sales summary, amounts customers owe, amounts owed to suppliers, everyday actions and attention items.
- Bottom navigation: Home, Sales, Items and More. Tabs and actions respect permissions.
- More: searchable feature menu, persistent Advanced tools toggle, theme control and server settings.
- Today / month / financial-year radio controls and a hide-amounts button.
- Invoice items become labeled cards on narrow screens; optional customer and delivery details remain expandable.
- Boolean workforce fields use accessible switches. Existing search selectors, barcode, AI review and OCR workflows remain.
- All 14 workforce subpages are bundled for mobile navigation.
- Native file sharing for exports; payroll PDF action uses the backend PDF endpoint instead of browser printing.
- Explicit mobile origin support in Django and removal of the old hard-coded frontend CSRF domain.
- JDK 21 check catches the Java 25 / class-file-69 failure before installing packages.

## 1. Keep your existing project safe
Extract this ZIP to a NEW folder, e.g. E:\NexEase_Easy_Mobile. Open the inner NexEase folder. Do not overwrite your existing .env, database, signing keys or production settings. The new home uses the same backend records; this is not a separate database.

## 2. Android on Windows
Install Node.js 22 or newer, Android Studio and JDK 21. In Android Studio's SDK Manager install Android SDK Platform 36 and Build Tools 36.0.0. Install SDK command-line tools and accept SDK licenses if prompted.

If Java 25 is installed, use JDK 21 for THIS project. In a Command Prompt opened in this folder:

    set "JAVA_HOME=C:\actual\path\to\your\jdk-21"
    BUILD_ANDROID.cmd

Replace the example path with your installed JDK 21 directory (it contains bin\java.exe). Alternatively set JAVA_HOME through Windows Environment Variables and reopen the launcher. Do not set it to the bin folder.

The launcher installs dependencies, builds mobile screens, syncs Android assets and runs Gradle. On success it opens:

    frontend\android\app\build\outputs\apk\debug\app-debug.apk

Copy this APK to your phone and install it for testing. Installing over an existing app requires the same signing key. Preserve your previous debug keystore if upgrading an existing installation; do not uninstall just to bypass a signing error without considering local settings.

## 3. Backend deployment
Deploy this package's Django changes to the same backend, preserving database and secret settings. In Render use the environment variable names below (read by this package):

    ALLOWED_HOSTS=nexease-backend-staging.onrender.com
    NEXEASE_MOBILE_ENABLED=true

Preserve any additional required hosts in ALLOWED_HOSTS, comma-separated. FRONTEND_ORIGINS must contain your actual HTTPS web frontend origin. CSRF_TRUSTED_ORIGINS may list additional trusted HTTPS origins. Mobile https://localhost is appended only when NEXEASE_MOBILE_ENABLED=true. Never disable CSRF or set wildcard hosts/origins.

Open /api/v1/auth/csrf/ on the backend and confirm a successful JSON response. HTTP 400 with DisallowedHost means ALLOWED_HOSTS is wrong. A background worker is separate from this check; deploy it for features that queue work.

## 4. Connect the app
The first screen is prefilled with https://nexease-backend-staging.onrender.com. Change it if necessary, tap Connect securely, then sign in normally. Connection waits up to 60 seconds to allow a sleeping backend to start. More → Change server disconnects this device. Passwords and API secrets are not bundled.

## 5. iPhone
On a Mac install Node.js, Xcode and the iOS SDK required by Capacitor 8. Run BUILD_IOS.command (or bash BUILD_IOS.command in Terminal). It builds screens, syncs the iOS project and opens Xcode. Choose your Apple signing team and device, then build. App Store/TestFlight distribution requires your Apple developer account and signing setup.

## Everyday usage
Home → Bill a customer → New invoice → customer → items → GST treatment → Save draft invoice. Review the draft before issuing it. Direct invoices do not dispatch stock; use the existing order/fulfilment workflow for stock dispatch.

Use More to find attendance, payroll, purchases, reports, settings and subscriptions. Enable Advanced tools for accounting/admin. Hiding a tool is not a permission change: roles and backend authorization remain authoritative. Internet is required; this release does not save offline business entries.

## Acceptance checklist before distribution
Test on real Android and iPhone devices: connect; login/logout; create a draft invoice; issue it using a test tenant; share PDF; upload photo/PDF; barcode camera/manual entry; attendance; payroll PDF; keyboard/back button; offline/reconnect; restricted role access; subscription enforcement. Test using staging data before production.

See MOBILE_VALIDATION.md for exact completed checks and remaining limits. Older validation documents describe the source release, not additional checks performed for this mobile build.
