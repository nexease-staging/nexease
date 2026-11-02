# NexEase UI and permissions update — 31 October 2026

## Changes
- Production CSRF trusts configured FRONTEND_ORIGINS, and the explicit staging no-email flag is retained. These preserve the deployment fixes discussed earlier.
- Shared workforce/expense record creation and editing now opens a native modal instead of expanding below the register. Quick purchases, site billing and team assignment use modal forms too. Existing master/document creation dialogs are retained. Add-item row controls remain within their parent document form.
- Compact plus-icon creation buttons have accessible names and hover titles. Save, cancel and other consequential decisions retain readable labels.
- Success, error, warning and confirmation popups use the NexEase green theme, rounded cards, status icons and reduced-motion support. Existing browser confirmations in the protected app are replaced. Mutation feedback is shared; authentication and AI proposal preparation are excluded from generic success notices.
- Module settings use visible toggle switches. Shared boolean record fields use switches; multi-select rows remain checkboxes.
- Issued/partially-paid/paid invoices: only the active tenant's system Admin can edit descriptions and presentation fields such as PO reference, site, service dates, terms, bank details and format. This rule holds even if the draft admin-only toggle is off. Cancelled invoices stay locked. Before/after values are recorded in the audit log. Amounts, customer, quantity, price, HSN/SAC and GST classification remain locked after issue; use the existing credit-note/correction workflow for financial corrections. This release does not add arbitrary financial rewriting of posted invoices.
- New `products.read_cost` permission (Products → Read cost price). Upgrade grants it to active system Admin roles. Grant it explicitly to other roles in Settings → Roles. Product master cost fields are removed recursively from JSON responses for users without this permission; product editing omits the hidden cost so ordinary edits do not reset it. Purchase prices, financial reports and inventory valuation remain governed by their own permissions; this is not a blanket ban on all financial information.
- Barcode scan focuses the hardware scanner input. USB/Bluetooth scanners must already be paired and configured as keyboard input with an Enter suffix. The web app cannot pair or power on those devices. Use camera requests permission and starts decoding; a camera selector appears when multiple cameras are available. ZXing is bundled as a fallback when native barcode detection is unavailable. Camera tracks stop after a scan or when the component closes.
- Search dropdowns stay inside native dialogs, avoiding the earlier hidden-popup problem.

## Install on Windows
1. Back up your source and database. Preserve `.env`, `frontend/.env.local`, `.venv`, uploads and your Git directory.
2. Review `UI_CHANGED_FILES.txt`. Copy those source files from this package into E:\NexEase. The current complete package also includes the mobile integration. Follow COMPLETE_UPDATE_README.md for installation; this changed-file list describes the earlier UI-only release.
3. Run in PowerShell:

```powershell
Set-Location E:\NexEase
.\.venv\Scripts\python.exe manage.py upgrade_workforce
.\.venv\Scripts\python.exe manage.py check
Set-Location E:\NexEase\frontend
npm.cmd ci
$env:NEXT_PUBLIC_API_BASE_URL = "http://127.0.0.1:8000/api/v1"
npm.cmd run test:run
npm.cmd run build
```

4. Start with the existing local launchers. Log out and back in to refresh permissions.
5. Commit reviewed source changes. Deploy backend, frontend and background worker from the same revision. Use the staging backend URL, not the local URL above, for Render's frontend build environment. Run `python manage.py upgrade_workforce` in the deployed backend environment if it uses a different database.

## Acceptance checks
- Click plus on customer/product creation and Add record on workforce/expenses: form opens above the register; Escape/Cancel closes without saving.
- Save a valid record: green success card. Submit an invalid record: error card plus form validation. Cancel a confirmation: no operation occurs.
- Disable/enable a module and refresh navigation; disabled modules remain blocked server-side.
- Sign in as a non-admin without Read cost price: master costs are absent from API JSON, lookup suggestions and product edit. Edit the product name; the stored cost must remain unchanged. Grant the permission, re-login and verify the value is visible.
- As Admin, edit an issued invoice PO number and descriptions. Download the PDF and inspect it. Total and journals must stay unchanged. As non-admin, those controls must be absent and a direct request rejected, including with draft admin-only disabled.
- Scan a known barcode using a paired keyboard scanner. Try a missing barcode. Allow camera permission, select the correct camera and scan a printed Code128 label. Deny permission and confirm a useful error appears. Close the screen and confirm the camera indicator turns off.

## Validation and limits
Backend isolated upgrade tests: 161 passed; existing backend suite: 883 passed. Frontend: 119 tests passed; Next.js production build and TypeScript passed. Tests use isolated/mocked data and do not prove the live deployment or physical scanner works. Browser screenshot validation was attempted but Chromium could not start because this environment blocked its socket; final visual/device checks are listed above. The reference video was inspected for its restrained navigation/panel style; the supplied image guided the feedback cards. This is an interaction update, not a pixel-for-pixel clone of that dashboard or a new AI analytics engine.
