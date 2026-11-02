# UI, chat and invoice input update — Android 1.3 (code 5)

The attached Claude UI overlay has been integrated into the complete NexEase source: shared visual styles, dashboard overview, invoice list, quick-create actions and command palette. No separate overlay installer is needed.

## Chat
In NexEase AI, check the authorization checkbox and type your instruction. Press Enter or click Prepare entry. Shift+Enter adds a new line. Enter does not send while a request is running, when AI is unavailable, or during keyboard input composition. Preparation does not save a record: review the proposal, save the review and then confirm.

## Invoice
The customer field searches existing names/codes and also accepts a new customer name. Select a suggestion to use that customer's details. Editing the selected name clears that selection, so the previous customer's contact details are not carried into a new customer.

Each item has one search-or-create input. Select an existing product to fill its SKU, unit and price, or type a new item name. New records are created by the existing direct-invoice save flow. Quantity, rate, tax and discount remain visible. Type, HSN/SAC, SKU and unit are under the item's details disclosure.

The three buttons beside/below the item field are connected barcode scanner, camera and photo. For a keyboard-mode USB/Bluetooth scanner, press the scanner icon, scan, then send Enter; the decoded value is looked up and fills that invoice line. Camera and photo scans fill the same line. Scanning alone does not change inventory.

On the Barcode page and product form, the scan input uses a full-width row on small screens, with 44-pixel icon buttons below. Buttons have accessible labels and desktop hover titles. The Android native scanner from version 1.2 is retained.

## Apply
Back up the current project. Copy this complete source over E:\NexEase, preserving .env, frontend\.env.local, Firebase configuration and signing files. Stop the running frontend before npm ci or an Android build.

For the web frontend:

```powershell
Set-Location E:\NexEase\frontend
npm.cmd ci
npm.cmd run build
npm.cmd run start
```

Deploy the updated source to Render for hosted use. For the phone, rebuild and install the APK; copying source alone does not update the installed app:

```powershell
Set-Location E:\NexEase
$env:JAVA_HOME="C:\Program Files\Eclipse Adoptium\jdk-21.0.13.9-hotspot"
$env:ANDROID_HOME="$env:LOCALAPPDATA\Android\Sdk"
$env:NEXT_PUBLIC_API_BASE_URL="https://nexease-backend-staging.onrender.com/api/v1"
.\BUILD_ANDROID.cmd
```

Install frontend\android\app\build\outputs\apk\debug\app-debug.apk using the same signing key. Android 8.0 or newer is required.

## Checks
Frontend tests cover customer/item entry, stale search results, scanner input, Enter/Shift+Enter/IME/consent behavior and existing UI flows. Production web/mobile builds and Android plugin sync are checked before delivery. Physical device scanning and visual browser/device layout still require acceptance testing.

Try an existing customer, a new customer, an existing item and a new item; check the saved draft's details. Test scanner/camera/photo on the phone after rebuilding. Your private environment files are excluded from the ZIP.
