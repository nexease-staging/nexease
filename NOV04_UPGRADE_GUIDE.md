# NexEase upgrade — 4 November 2026

## Changes and checks

| Request | Behaviour / verification |
|---|---|
| Expense → advance | Select Employee advance in Daily expenses, choose employee, enter amount/payment/reference. Paid-to fills automatically. One advance-register record and journal are created, without an expense journal. Payroll manage and Workforce access are required. Repeating the same reference is rejected. |
| Issued invoice admin edit | Existing detail/description controls are now exposed for issued/part-paid/paid invoices, independent of the invoice-issue UI gate. Only system Admin can edit issued details. PO/terms/descriptions/format are editable. Financial quantities, rates, customer, GST classification and totals remain protected by the existing correction workflow; this is not unrestricted rewriting of posted accounts. |
| Employee AP | Accounts Payable has a separate employee salary balance from approved payroll minus recorded payments. Example: 10,000 approved less 2,500 paid = 7,500. Draft attendance/payroll does not post a payable; supplier totals are unchanged. |
| Web/app UI | Shared icon controls for common export/download/email/view/refresh actions with accessible labels; aligned filters and search-icon padding; compact invoice KPIs; non-sticky invoice create bar; smaller mobile AI launcher. Save/confirm/cancel/contextual payment actions retain wording. Check Products/Invoices/reports at mobile and desktop widths. |
| Performance | Account setup batches account reads; configuration batches permission reads per request; workspace search debounces 300ms; app resume refetches only stale active queries; fewer failed-read retries. Live 15-second latency was not measured; no specific speed guarantee. |
| Email | Pending-queue worker-heartbeat guidance, retained retry hotfix and new read-only diagnostic command. Same backend for web/app. A connected mailbox still needs a continuously running worker. |
| PDFs | Ten invoice formats share a selected accent colour. Sales/purchase/payment PDFs have matching tinted surfaces and logo; payslips/workforce PDF reports also use branding. Choose Settings → Invoices colour/logo and download documents. Printed identity does not change ledger data. |
| Sidebar | A bounded organisation logo and name replace the brand mark in the sidebar when uploaded. |
| Contact | Contact NexEase link at sidebar bottom. WhatsApp-only +91 92097 53378; nexease.contact@gmail.com; @nexease.ai. |
| Landing page | Expanded professional services, animation respecting reduced motion, trial CTA and quotation form. Visit `/` signed out. Signed-in web users retain dashboard routing; native users retain home routing. No invented customer testimonials are published; genuine consented statements can be added later. |
| Trial | One 14-day Plus trial starts at new organisation signup, not each login. Existing memberships are preserved. AI remains Pro. Expired trials cannot continue restricted writes without an eligible subscription/owner action. |

## Install locally

Back up your working folder and environment files. Stop frontend/backend/worker processes. Copy the ZIP's NexEase contents into E:\NexEase, preserving `.env`, `frontend/.env.local` and `.git`. The ZIP excludes credentials and generated dependencies/builds.

```powershell
Set-Location E:\NexEase
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py check
```

Add to backend `.env`:

```dotenv
CONTACT_EMAIL=nexease.contact@gmail.com
```

Quotation notifications and password resets use existing system SMTP configuration: EMAIL_MODE=production, SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, SMTP_USE_TLS, SMTP_USE_SSL and DEFAULT_FROM_EMAIL. Document email uses each sending user's Settings → My email connection. Preserve the existing MAILBOX_ENCRYPTION_KEY, identical on backend and workers using the same database. Never paste keys or app passwords into Git/chat.

Run these in separate terminals:

```powershell
Set-Location E:\NexEase
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

```powershell
Set-Location E:\NexEase
.\.venv\Scripts\python.exe manage.py run_background_worker
```

```powershell
Set-Location E:\NexEase\frontend
npm.cmd ci
npm.cmd run dev
```

No database wipe or migration is required. START_BACKGROUND_WORKER.cmd is also included. Closing the worker terminal stops processing.

## Delivery diagnosis and Render

```powershell
Set-Location E:\NexEase
.\.venv\Scripts\python.exe manage.py check_delivery_setup
```

This read-only command prints configuration presence, worker heartbeat and queue counts, never credentials. It does not send messages. For FAILED documents review the actual error; do not resend PENDING jobs.

Deploy frontend, backend and a continuous background worker from the updated Git branch/merge. Worker start command: `python manage.py run_background_worker`. Backend/worker need the same MongoDB database, system SMTP environment and MAILBOX_ENCRYPTION_KEY. A local worker is not a permanent hosted service.

Render free web services sleep after inactivity and block SMTP ports 25/465/587. Use a service/host that permits the configured SMTP connection. An always-on worker is required. Upgrading a workspace plan alone does not upgrade individual service compute. Source: https://render.com/docs/free

Quotations are saved to `nexease_quotations` with a reference, then forwarded by the worker via system SMTP to CONTACT_EMAIL. The visitor is Reply-To, never a user-controlled destination. Failed sends retry up to three attempts. `sent` means SMTP accepted the message, not guaranteed inbox placement. Check spam. A worker crash during delivery leaves `sending` for operator review before retry, because acknowledgement may be ambiguous. No new owner-console quotation-management screen is included.

## Android build

Close frontend dev server before building to avoid locked Node files. Deploy the updated backend first.

```powershell
Set-Location E:\NexEase
$env:JAVA_HOME="C:\Program Files\Eclipse Adoptium\jdk-21.0.13.9-hotspot"
$env:ANDROID_HOME="$env:LOCALAPPDATA\Android\Sdk"
$env:NEXT_PUBLIC_API_BASE_URL="https://nexease-backend-staging.onrender.com/api/v1"
.\BUILD_ANDROID.cmd
```

Version 1.5 / code 7. This ZIP contains source, not a compiled/signed APK.

## Validation limits

Isolated backend tests cover advances and journal idempotency, permissions/payables, trial expiry/non-reset, quotation input validation/fixed destination, worker retries and mailbox encryption. Authentication, professional accounting and workforce/PDF suites were also tested. Frontend unit tests, web build and mobile export are checked. SMTP is mocked; real inbox delivery and physical-device behaviour require deployment testing. Browser visual testing was attempted but local Chromium was blocked by the environment. SHA256SUMS describes packaged source bytes, not a checkout after Git line-ending conversion.
