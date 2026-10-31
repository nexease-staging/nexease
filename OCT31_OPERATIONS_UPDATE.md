# NexEase operations update — 31 October 2026

This is a complete source package built on the Workforce Upgrade. Keep your existing database connection, secret keys, environment files and uploads. No production database was accessed while preparing this update.

## Install on your Windows PC

1. Back up your existing source and Atlas database. Stop backend, frontend and background worker.
2. Extract this ZIP to a separate folder. Copy the contents of its NexEase folder over E:\NexEase. Keep .env, frontend\.env.local, .venv and uploads. The package includes no live credentials.
3. Run PowerShell:

```powershell
Set-Location E:\NexEase
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:APP_ENV = "development"
$env:DJANGO_DEBUG = "true"
$env:FRONTEND_ORIGINS = "http://127.0.0.1:3000,http://localhost:3000"
$env:FRONTEND_BASE_URL = "http://127.0.0.1:3000"
$env:TRUST_PROXY_SSL_HEADER = "false"
.\.venv\Scripts\python.exe manage.py upgrade_workforce
.\.venv\Scripts\python.exe manage.py check
Set-Location E:\NexEase\frontend
npm.cmd ci
$env:NEXT_PUBLIC_API_BASE_URL = "http://127.0.0.1:8000/api/v1"
npm.cmd run build
```

4. Double-click START_LOCAL_BACKEND.cmd and START_LOCAL_FRONTEND.cmd. Leave both windows running. Open http://127.0.0.1:3000 (use this same hostname for frontend and API).
5. Restart your background worker in another configured window if used. Log out and in. Keep SAAS_ENFORCEMENT=true and grant your test organisation a trial in /owner.

The launchers set local development options in their own process; they do not change Render or bypass subscriptions. Atlas IP access must allow your current PC. Do not deploy these launchers on Render; retain the production Gunicorn and HTTPS configuration there.

## What changed

1. Sidebar starts collapsed; navigation groups also start collapsed.
2. Normal and quick invoice entry use the same modal with Direct / Sales order tabs. Order billing still requires an eligible fulfilled order. Direct entry does not require an order or warehouse.
3. GST lookup is available in customer creation (including the New customer dialog inside sales orders) and direct invoices. Typing a complete GSTIN triggers lookup. Existing tenant customers are matched first. External lookup needs a provider adapter, described below.
4. Direct invoice requires customer name, invoice date, at least one item with quantity/rate, and explicit tax treatment. Customer codes and new item SKUs are generated when blank. Email, phone, due date, PO and extra details are optional. Registered supplies still require legally relevant tax details and HSN/SAC through validation.
5. Existing customer/item suggestions remain available. Selecting an existing customer preserves its identity; entering a new customer creates a reviewable master when saving. It does not silently update an existing customer's details.
6. Barcode workspace: exact barcode/SKU lookup, warehouse on-hand/reserved/available balances, Code128 PDF labels, hardware keyboard-scanner input and camera scanning when the browser supports BarcodeDetector. Product selectors using the shared search control offer scanning; the direct invoice offers scan-to-add/increment. Use standard receipt, fulfilment and transfer workflows to post stock changes. Scanning alone never changes stock.
7. Settings > Business modules contains Workforce, Expenses, Taxation, Finance, Barcode, AI and Admin-only invoice editing switches. Backend checks enforce disabled modules. AI is enabled at organisation level by default but still requires an eligible Pro subscription and configured provider credentials. Disabling Finance blocks direct finance tools; necessary accounting postings for other enabled workflows continue.
8. Organisation logo is managed at Invoice formats & business identity, linked from Organisation settings, shown in expanded navigation and snapshotted onto new invoice details. Existing issued invoices retain their saved branding.
9. The supplied NexEase logo appears in navigation and login.
10. PDF download no longer requires customer/supplier email. Actual email delivery still requires a recipient address.
11. Monthly pay inputs can populate automatically when an employee/month is selected. The Populate month action fills the full month from approved timesheets/daily attendance and approved leave explicitly classified as paid. It retains saved allowances, deductions and statutory wage bases. Payroll calculation defaults to Automatic mode and rechecks sources before approval. Approved payroll is locked.
12. Invoices page offers selection and ZIP download of up to 50 PDFs per request (50 MB compressed limit), including customers without email. Files use safe names plus document IDs and are restricted to the current tenant.

Invoice editing controls cover the existing draft details and line-description editors. Issued invoices remain locked even for administrators; this update does not permit rewriting posted financial history. The Admin-only option defaults on and identifies the active system Admin role.

## GST provider configuration — external autofill is not live until configured

There is no provider credential in this package. The backend supports an explicitly configured HTTPS adapter, not scraping the GST portal or bypassing captcha. The owner must obtain authorised access from a GST data provider and map its response to this contract:

```dotenv
GST_LOOKUP_URL=https://YOUR-ADAPTER-HOST/gstin
GST_LOOKUP_TOKEN=YOUR_PRIVATE_ADAPTER_TOKEN
```

Backend request:
- GET configured URL with `gstin=...` query parameter.
- `Authorization: Bearer <GST_LOOKUP_TOKEN>`.
- 12-second timeout, 64 KB response limit, redirects rejected.

Required JSON response:

```json
{
  "gstin": "THE_REQUESTED_GSTIN",
  "name": "Registered legal or trade name",
  "address": "Registered address",
  "state": "Maharashtra",
  "email": "",
  "phone": ""
}
```

The supplied GSTIN must match the requested GSTIN. Name is required. Address/state/contact fields are optional. Map provider-specific nested fields in your adapter; this is not a drop-in URL setting for every commercial API. Keep credentials server-side. Phone/email may not be available from GST data and must remain blank rather than be invented. Existing tenant masters can supply previously saved contacts. Review lookup results before saving. No live GST provider was tested.

## Barcode setup and limits

1. Edit a goods product and enter its unique barcode; existing SKU is the fallback label value.
2. Connect a USB/Bluetooth scanner configured as a keyboard with Enter suffix.
3. Focus Scan barcode in /barcode, a supported product selector, or the direct invoice.
4. Scan; verify the exact product. Repeated direct-invoice scans increment its quantity.
5. Print labels for scanned products from /barcode. Labels use Code128 for 1–48 printable ASCII characters; existing retail codes can still be looked up by their stored value.
6. For camera scanning, allow camera access on HTTPS or localhost. Browsers without BarcodeDetector show a hardware/manual fallback. No camera images are uploaded.

Camera recognition and physical scanner/printer hardware require testing on your device. This is not a GS1 identifier registration service, serial/batch traceability engine or offline stock synchronisation system. Label scans need a mapped product; unknown values are rejected.

## Payroll rules to verify

- Daily attendance creates approved timesheets; draft timesheets are excluded.
- Multiple shifts on the same date count once for paid days, but their approved hours are added.
- Full-day paid leave adds paid days; work/paid-leave overlap is rejected.
- Other leave categories are not silently treated as paid. Partial-day paid leave and piece-rate work still require manual monthly inputs.
- PF/ESI members need reviewed monthly contribution wage bases and the applicable policy; the program does not infer legal applicability.
- Populate month does not approve payroll or make payments. Review regenerated day/hour/recovery fields before saving/approval.
- Changes to sources invalidate an automatic draft at approval and require recalculation.

## Acceptance checks

- Log in and see collapsed sidebar, then expand it and open individual groups.
- Create a direct draft with only new customer name, item name, quantity, rate and appropriate tax treatment. Codes should be automatic; email not required.
- Select an existing customer in a second invoice; verify customer count does not increase.
- Open normal invoice creation; switch between the same dialog's order/direct tabs.
- Fetch an existing customer by GSTIN. Without provider setup, an unknown GSTIN must show a clear configuration message, not invented data.
- Download customer invoice and supplier document without email. Select two invoices and verify both PDFs in the ZIP.
- Disable Barcode, refresh, and verify both menu and API access are blocked. Restore it; scan known/unknown codes and print labels.
- Sign in as a non-Admin user with invoice permissions. Draft edit controls should be hidden and direct edit API calls denied while Admin-only is on.
- Mark an employee's 8-hour day and approve one full paid leave day. Populate monthly inputs: 2 paid days, 8 regular hours. Confirm saved allowances remain.
- Approve payroll; attempt to repopulate the month and confirm it is rejected.
- Use a second organisation to verify records, barcode matches, logos and ZIP downloads are isolated.

See VALIDATION_OCT31.md for checks run on this package. The original UPGRADE_WORKFORCE_AND_BILLING.md still describes GST workpaper and AI scope limits. In particular, exports are not filed GST returns.
