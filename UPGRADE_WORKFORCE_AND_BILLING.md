# NexEase goods, services and Workforce upgrade

This package updates your existing Django + Next.js application. It does not connect to or modify your Atlas database until you install it and run the upgrade locally.

## Install on Windows

1. Stop Django, Next.js and the background worker. Back up your current project and Atlas database before upgrading.
2. Extract the ZIP to a separate folder. Copy the contents of its `NexEase` folder into `E:\NexEase`, replacing source files. **Keep your existing `.env`, `frontend\.env.local`, uploads and virtual environment.** The archive contains no live environment files or credentials.
3. In PowerShell:

```powershell
Set-Location E:\NexEase
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py upgrade_workforce
.\.venv\Scripts\python.exe manage.py check
Set-Location E:\NexEase\frontend
npm.cmd ci
npm.cmd run build
```

4. Start the backend in its own PowerShell window:

```powershell
Set-Location E:\NexEase
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

5. Start the frontend in another window:

```powershell
Set-Location E:\NexEase\frontend
npm.cmd run dev
```

6. Restart your background worker if you use it, then log out and back into the business account so the upgraded Admin permissions are loaded.

The upgrade adds workforce, expense and taxation permissions only to active system Admin roles. Custom roles are unchanged. The existing `LABOUR-SERVICE` master is converted to Service only when no inventory record exists for it. Any skipped conversion is printed for review. Existing invoices, payroll, journals, plan entitlements and secrets are not rewritten.

## Start here

- **Products:** choose Goods or Service; enter HSN or six-digit SAC. Existing products default to Goods. Type is immutable after creation to protect inventory history. Use a new service master for other existing goods masters that represent services.
- **Taxation:** configure your GST registration and supplier state. Review the correct classification and rate for your business with your accountant; the app does not guess a labour-supply SAC or rate.
- **Settings → Invoice formats & logo:** choose one of ten named styles, upload PNG/JPG logo, and set bank details, terms and signatory.
- **Invoices:** direct entry and sales-order billing both ask for GST treatment. Enter PO details, service dates, site, shipping address and place of supply. Draft invoice details can also be edited in the detail dialog. Issue only after review.
- **Workforce dashboard:** `/workforce`. The old `/payroll` and `/labour` bookmarks open this workspace.
- **Workforce → Settings:** effective-dated contribution policies; default daily attendance hours; maximum automatic advance recovery percentage; payslip footer; links to pay, statutory, leave, numbering, role and accounting settings.

## Included workflows

### Goods, services, invoices and accounts

Goods/service type and HSN/SAC are persisted on product masters and snapshotted onto invoice lines. Services do not create stock reservations or movements during order fulfilment, purchase receipt or returns. Existing order screens still require a warehouse reference; direct service invoices do not require one.

Ten named invoice styles are available (Classic ledger, Modern blue, Minimal ink, Executive navy, Emerald studio, Service statement, Contractor works, Compact register, Elegant violet, Bold graphite). They offer different colours and grid, striped, minimal, banner and compact treatments. All include the same business data; preview cards are visual guides, and the downloaded PDF is authoritative.

Classified invoices capture supplier GSTIN/state and show HSN/SAC, PO number/date, service period, site, shipping address, payment/bank details and CGST/SGST/UTGST or IGST totals. Branding defaults are copied to invoices when details are saved. Issued invoice details are locked. Old invoices remain unclassified until reviewed; old issued documents are not silently rewritten.

Service revenue posts to its own control account. Reviewed GST tax heads post to separate CGST, SGST/UTGST and IGST control accounts. Credit-note journals reverse the matching source controls. Existing general accounting controls and source-based duplicate protection remain in use. Payroll, employee advances and salary payments retain the existing automatic accounting integration.

### GST preparation

The GSTR-1 / GSTR-3B workbooks now include classified **issued** invoices automatically, with source reconciliation, HSN/SAC invoice lines, an HSN/SAC summary and a GSTR-3B outward-supply review summary. Draft and cancelled invoices are excluded. A manual reviewed register row with the exact source invoice ID replaces that invoice's automatic contribution; enter the complete replacement amount, not a delta.

Supported invoice classifications in this release: regular taxable, exempt, nil-rated, non-GST and unregistered supplier. Composition invoicing, exports/SEZ, reverse-charge invoices, cess, amendments, full ITC calculation and portal upload JSON are **not** implemented by this upgrade. Credit/debit notes and other adjustments still require explicit reconciliation. Unregistered sales remain separately classified and must not be treated as registered outward tax liability.

These are preparation workbooks, not filed returns or complete portal-ready returns. Validate the period, registration, HSN/SAC, place of supply, tax treatment, rounding and adjustments before filing through the official GST system.

Official references checked for this upgrade:
- https://tutorial.gst.gov.in/userguide/returns/Creation_of_Outward_Supplies_Return_in_GSTR-1.htm
- https://tutorial.gst.gov.in/userguide/returns/GSTR3B.htm
- https://tutorial.gst.gov.in/downloads/news/updated_advisory_on_hsn_validation_21.01.25.pdf
- https://taxinformation.cbic.gov.in/content-page/explore-act/1000736/1000001

Employee-to-employer employment services and the agency's supply to its customer are distinct transactions. Payroll is not automatically added to outward GST sales.

### Workforce, reports and payslips

Dedicated navigation separates Employees, Sites, Assignments, Daily attendance, Timesheets, Leave & approvals, Monthly pay inputs, Pay runs, Payslips, Advances, Client billing, Accounts, Reports and Settings.

Approved payroll supports employee PDF payslips, a ZIP containing all employee slips, and individual device sharing when supported. If file sharing is unavailable, download the PDF and attach it manually. There is no automatic bulk email/WhatsApp dispatch in this release. Sharing or downloading does not pay salaries.

Every workforce register has full Excel/CSV/PDF exports through Reports, without the screen's 1,000-row truncation. Existing payroll/payment Excel, site-billing and accountant-pack exports remain available. Payroll retains monthly runs; half-day, paid-weekly-off and exceptional wage calculations continue to use reviewed manual monthly inputs. Attendance defaults and recovery settings affect new calculations; approved historical runs remain locked.

### AI and voice

Supported confirmed creation actions: expense, employee advance, draft sales invoice, draft supplier bill, draft purchase order, category, product, employee, site, assignment, monthly attendance, daily timesheet, and leave request. Existing role permissions, tenant checks and domain validation still apply. Related employee/site/category selections are available during review. AI does not have arbitrary database access or permission to change security settings.

Text requests may use the user's preferred language. Voice uses the browser's SpeechRecognition implementation, with a language selector, microphone permission and editable transcript. Availability and recognition accuracy depend on browser/device/language; unsupported browsers show a typing/dictation fallback. Browser speech services may process audio. Review the transcript and proposal before confirmation.

This does **not** mean every application operation is AI-enabled: payments, payroll approval, posting, cancellation, role changes and GST filing remain in their reviewed application workflows. API billing is still required. No live OpenAI call or paid provider test was performed while preparing this package.

## Verify locally before using live records

Use a test organisation to create a service master, generate an invoice with PO/SAC/logo, issue it, inspect its journal, and download its GST workpaper. Then approve a sample payroll and check individual and bulk payslips. Try voice input and an AI employee/PO proposal. Review custom role permissions and validate a real business bill before posting it.

If you need to roll back, stop the app and restore the backed-up source and database together. The older strict MongoEngine models may not accept newly added fields, so source-only rollback after using the new features is not recommended.
