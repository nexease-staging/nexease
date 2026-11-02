# Latest barcode update — Android 1.2 (version code 4)

This section supersedes the camera hotfix below. The APK now opens the native Capacitor scanner using Android ML Kit. Web browsers retain bundled ZXing scanning and Scan photo. The native scanner requires Android 8.0 or later. Physical-phone testing is still required; the camera fix has not been verified on your device.

## Install

1. Back up your project. Overlay this source while preserving `.env`, `frontend/.env.local`, Firebase configuration, signing keys and uploaded files. These personal files are not included.
2. Deploy/restart the updated backend as well as the frontend. New catalogue endpoints and automatic barcode assignment require the updated backend.
3. Stop the running frontend before building to avoid the Windows lightningcss file lock. From `E:\NexEase` run:

```powershell
$env:JAVA_HOME="C:\Program Files\Eclipse Adoptium\jdk-21.0.13.9-hotspot"
$env:ANDROID_HOME="$env:LOCALAPPDATA\Android\Sdk"
$env:NEXT_PUBLIC_API_BASE_URL="https://nexease-backend-staging.onrender.com/api/v1"
.\BUILD_ANDROID.cmd
```

4. Install `frontend\android\app\build\outputs\apk\debug\app-debug.apk` on the phone using the same signing key. Updating source alone does not update the installed APK.

## Add products and scan

- Products → Add → Barcode: type/paste a supplier barcode, or expand **Scan barcode into product**.
- **Use camera** opens the native scanner in the rebuilt APK; allow camera permission. A successful read fills the product barcode field without searching for an existing product. Complete the required product fields and save.
- For a USB/Bluetooth scanner, pair/connect it in keyboard (HID) mode. Focus Barcode or press **Scan barcode** in the expanded scanner, then scan. An Enter suffix captures the number without submitting the whole product form. Serial-only/proprietary scanners require their vendor integration and are not supported by this keyboard-input path.
- Leave Barcode blank to assign a stable internal `NX…` Code 128 number on save. It is an internal inventory identifier, not an assigned retail EAN/GS1 number. Supplied codes are preserved, including leading zeroes.
- Duplicate supplied barcodes are rejected by product create/edit API validation within the organization. Historical duplicates are not silently rewritten.

## Barcode list and downloads

- Barcode now lists all saved products/services, including inactive items, rather than only the items scanned this session.
- **Download all barcodes (Excel)** exports the whole organization catalogue, irrespective of the current search/page. Barcode numbers remain text to preserve leading zeroes.
- Select items → **Download selected labels** produces printable Code 128 PDF labels, up to 50 selected items at once. Label printing supports 1–48 printable ASCII characters; longer stored codes still appear in Excel.
- On Android the document opens the native save/share sheet. Choose an installed destination to save/share it.
- **Generate missing barcodes** fills older blank barcode fields. It requires product-update permission and preserves existing codes. This is optional for old records; new blank-barcode products generate automatically.
- Scanning from the Barcode page looks up a product and shows inventory balances; scanning alone does not change stock.

## Acceptance test

1. Add a test product with supplier barcode `000123456789` using a connected scanner. Save and check that the leading zeroes remain.
2. Add another product with Barcode blank. Save and confirm an `NX…` value appears in Barcode list.
3. Download that product's PDF label. Print it at actual size or display it clearly on another screen.
4. In the rebuilt app open Barcode → Use camera. Scan the complete label with white margins visible; verify the matching product appears.
5. Add another product, expand Scan barcode into product, scan a different supplier label and verify its number fills the field before saving.
6. Download Excel and check both products. If native camera access fails, allow Camera under Android Settings → Apps → NexEase → Permissions, retry, then try Scan photo.

---

# Camera scanner hotfix — Android version 1.1.1 (code 3)

The scanner now uses the bundled ZXing decoder for generated Code 128 and common retail linear barcodes, rather than trusting an optional WebView BarcodeDetector. It shows Opening / Scanning / Finding product / failure messages, keeps scanning after ordinary unreadable frames, and offers Scan photo as a fallback. Photos are decoded locally, not uploaded. Camera-list enumeration failure no longer prevents scanning. Stopping or leaving the scanner releases camera tracks.

Install this source, preserve environment/Firebase/signing files, stop the web frontend and rebuild with BUILD_ANDROID.cmd. Install the new app-debug.apk on your phone using the same signing key. Updating source on your computer alone does not update the installed app. No product recreation or database changes are required.

Test: Barcode → Use camera, allow permission, scan a printed label or a barcode on a second screen. Keep the full bars and white margins visible. If the live scan fails, use Scan photo and take a sharp picture. Successful scanning should display the decoded value and then the matching product. If the camera never opens, check Android Settings → Apps → NexEase → Permissions → Camera.

Physical-device validation is still required. This fix addresses camera-decoder compatibility and makes camera failures visible; it does not establish which device-specific issue caused the original report.

---

# NexEase mobile and web update — 1 November 2026

## Apply this update
Stop the frontend and backend. Copy this complete NexEase source over your existing folder, preserving `.env`, `frontend/.env.local`, Firebase files, signing keys, `.git`, and uploaded data. This ZIP contains no personal environment files or signing credentials.

For normal web use, run `npm.cmd ci` inside `frontend`, then restart `START_LOCAL_BACKEND.cmd` and `START_LOCAL_FRONTEND.cmd`. The account avatar now opens My profile, Subscription & usage, Business logo & invoice settings (with permission), and Log out. Upload the organization logo in Settings → Invoices; it becomes the avatar on web and mobile. My profile displays name, email, organization and role; it does not change account details.

## Build the new Android APK
Stop the NexEase web frontend before building: npm ci replaces node_modules and a running dev server can lock lightningcss on Windows.

PowerShell from E:\NexEase:

```powershell
$env:JAVA_HOME="C:\Program Files\Eclipse Adoptium\jdk-21.0.13.9-hotspot"
$env:ANDROID_HOME="$env:LOCALAPPDATA\Android\Sdk"
$env:NEXT_PUBLIC_API_BASE_URL="https://nexease-backend-staging.onrender.com/api/v1"
.\BUILD_ANDROID.cmd
```

Use your actual installed JDK 21 path if different. Node 22+, Android SDK 36 and Build Tools 36.0.0 are required. The launcher now stops immediately if dependency installation fails. Output: `frontend\android\app\build\outputs\apk\debug\app-debug.apk`. Install the APK over the existing app with the same signing key. No signed production APK is included.

## Mobile behavior
- The hamburger drawer displays labels even when the desktop rail is collapsed.
- Notification and account menus stay within the narrow screen and scroll vertically. Escape dismisses them.
- Standard list filter groups (27 filter groups across 26 pages) use compact rows on phones. Search stays on its own row; Customer, Status and Sort share a row on Invoices. Record-entry forms retain their existing layouts.
- Android launcher and monochrome notification icons use the green NexEase N mark.
- Native launch checks the server session before entering Home. The web retains /dashboard after login and returns signed-in visitors there from the landing page. Deploy the updated backend with `NEXEASE_MOBILE_ENABLED=true` for the explicit https://localhost origin and 30-day native sessions. Web sessions retain their existing expiry. Logout, session revocation, inactive accounts and expiry still require a new login; this is not offline authentication.
- Use camera requests Android camera permission and opens the camera view. Permission denied guidance points to Android app settings. USB/Bluetooth keyboard scanners must be paired in device settings first; Scan barcode focuses the input and Enter submits. NexEase cannot pair arbitrary proprietary scanners. Camera and scanner operation need a physical-device acceptance test.

## Device activity notifications
Open the bell or My profile and enable Device notifications. Android asks permission; no permission is bypassed. Successful saved actions using the shared feedback flow create local Android notifications. Reading pages does not create notifications. Notification text may be visible on the lock screen according to the phone's privacy settings.

## Background alerts: required Firebase setup
Closed-app alerts cannot work from the ZIP alone. These steps require your Firebase project and deployment settings.

1. In Firebase create/register the Android app with package ID `com.nexease.business`.
2. Download its `google-services.json` to `frontend/android/app/google-services.json`. This Android client configuration is different from the private server service account.
3. Create a Firebase Admin service account. Store it only on the Render backend/worker as a secret file; set `GOOGLE_APPLICATION_CREDENTIALS` to its absolute path. Alternatively set `FIREBASE_SERVICE_ACCOUNT_JSON` to the service-account JSON in a secret environment variable. Never put the service account in the frontend, APK, repository or public ZIP.
4. Set `NEXEASE_PUSH_ENABLED=true` on the backend and notification worker, and `NEXEASE_MOBILE_ENABLED=true` on the backend. Preserve your existing database, web origins and other secrets.
5. Change the backend/notification-worker install command to `pip install -r requirements-mobile.txt` and deploy this backend code.
6. Add ONE Render background worker, using the same source/database/Firebase settings, with start command `python manage.py run_notification_worker`. This is separate from the existing `run_background_worker` job worker; keep that worker running too.
7. Rebuild the APK. The mobile build detects google-services.json and enables push registration. Sign in, enable Device notifications, and allow Android notifications.

The worker delivers new in-app notifications to their registered recipient and creates overdue invoice, overdue supplier bill and out-of-stock reminders approximately every six hours, filtered by current read permissions. Counts/details remain in the authenticated notification list; lock-screen reminder titles identify the category with generic body text. It does not broadcast every employee's actions to every user. Devices are isolated by user and organization; logout/disable removes registration, and logout-all/password session revocation removes server device records. Failed transient delivery is retried, with Android notification tags reducing duplicate display. Do not run multiple notification-worker instances.

Without Firebase setup, saved-action notifications can work while using the app, but closed-app business alerts are unavailable. Android may delay delivery because of network, battery settings or force-stop; delivery is not guaranteed at an exact time.

## Acceptance checks on your phone
1. Install, allow requested permissions, sign in, close and reopen: Home opens while the session is valid.
2. Open hamburger: expand a group and verify link labels. Open bell and account menu in portrait and landscape; neither should extend beyond the viewport.
3. Upload an organization logo on web, then refresh the app: avatar uses the logo. Verify role-specific menu links and logout.
4. On Invoices, change Customer / Status / Sort on one row; repeat list-filter checks on Products and Customers.
5. Camera: allow, scan a known barcode, deny permission and retry, then stop camera. Test the paired hardware scanner with an Enter suffix.
6. Enable notifications, save a test record, check Android notification shade. Disable notifications and confirm no new local notifications.
7. After Firebase configuration, close/background the app and run `python manage.py run_notification_worker --once` on the server using a test organization with overdue invoices/bills or out-of-stock inventory. Verify the device receives the relevant reminder; tap it and check navigation. Test restricted-role and logout behavior on a shared device.

Automated checks are documented in MOBILE_NOV01_VALIDATION.md. Firebase delivery, Android permission dialogs, hardware scanners and APK installation require your configured physical device and are not claimed as tested here.
