# NexEase reference UI update — 7 November 2026

## What changed
- Teal application header, clickable NexEase branding, desktop module menus, mobile navigation drawer, and consistent light panels. All existing module routes remain in the package.
- Module navigation retains role permission checks and Pro restrictions on e-invoice and e-way bill links. The mobile More directory remains available.
- Dashboard: business setup links, Analytics / Quick links switch, existing live KPIs and charts, existing date filters and refresh.
- Organisation signup: compact labelled form with help link, business type, organisation/admin email and credentials. Optional business address is saved by the backend. Old API clients may omit it.
- Invoice entry: side-by-side customer and document panels on desktop, item grid, tax and discount breakdown, expandable PO/service/delivery/terms fields and draft review. Phone layout uses item cards rather than an oversized desktop grid.
- Customer, supplier and product entry use right-side drawers. Sales order entry has the matching wider editor surface. Existing create, confirm, fulfil, issue, payment, cancellation and review operations have not been replaced by mock actions.
- Public home, pricing and deadline pages use a four-column NexEase footer with genuine contact, service and resource links. No competitor contact details or unapproved store badges are copied.
- START_NEXEASE.ps1 starts from its own directory and supplies local environment overrides, avoiding the APP_ENV problem from the previous setup.

## Run this update on Windows
1. Stop any running old backend/frontend with Ctrl+C.
2. Extract the ZIP. Use the inner NexEase folder containing manage.py.
3. Copy your existing working .env into that folder. Preserve ALL encryption keys and credentials.
4. Check MONGODB_DATABASE. A copy of the app connected to nexease_staging writes to the same staging database; changing folders does not isolate data.
5. In PowerShell in the new NexEase folder:

    py -3.13 -m venv .venv
    .\.venv\Scripts\python.exe -m pip install -r requirements.txt
    Set-Location frontend
    npm.cmd ci
    Set-Location ..
    .\START_NEXEASE.ps1

6. Open http://127.0.0.1:3000 when the frontend is Ready. /dashboard is the analytics view; /home retains the simpler task view.
7. Only if you want queued jobs processed in the selected database, run START_NEXEASE.ps1 -WithWorker instead.

If Windows blocks running .ps1 files, use START_LOCAL_BACKEND.cmd and START_LOCAL_FRONTEND.cmd separately. Neither requires changing your machine's execution policy.

## Deployment
The signup address enhancement changes both backend and frontend: deploy both from this same package. No database reset or destructive migration is required. Retain your existing production environment, database and encryption keys. Local development overrides belong only in local processes, not Render settings.

For Android, install dependencies and build the mobile web export using npm.cmd run mobile:build, followed by npm.cmd run mobile:sync. Rebuild the Android app to include this UI. A ZIP of source code is not an APK or a Play Store-ready signed AAB.

## What must still be checked in your environment
Use demo data and your chosen test database:
- New organisation signup and saved address; existing organisation sign-in and password reset.
- Customer/product lookup, barcode entry, GST lookup with your provider credentials.
- Draft invoice totals and non-taxable classifications, issue, PDF, document email and native share.
- Sales order creation, confirmation, fulfilment; stock transfers, purchases and returns.
- Workforce attendance, payroll, finance and all three subscription tiers.
- Browser and APK at narrow widths; open/close menus, keyboard focus, forms, account menu and notifications.

Read REFERENCE_FEATURE_GAPS.md before advertising parity with another product.
