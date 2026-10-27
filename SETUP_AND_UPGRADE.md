> **SaaS Edition:** Start with [START_HERE_SAAS.md](START_HERE_SAAS.md). It describes owner setup, subscriptions, AI, payment configuration and current limits.

> **Professional Update (24 October 2026):** Start with [UPDATE_PROFESSIONAL.md](UPDATE_PROFESSIONAL.md). It supersedes older workflow/accounting limitations below where explicitly described.

# Setup and upgrade

For an already-running NexEase test installation, follow UPDATE_AUTOMATION.md first. The steps below also cover fresh installs and upgrades from the original IMS.

## 1. Keep the original project and database backup

Extract this archive into a **new folder**, e.g. `F:\NexEase-Updated`. Test it against a copy of your MongoDB database first. Keep the original project and database backup until you have reviewed the workflows. This package does not include your production database, credentials, dependency environments or built frontend.

The layout is one backend project root containing `manage.py` and one `frontend` subfolder. Do not nest the new frontend inside the old frontend.

## 2. Backend

Use your supported Python installation (the checks here ran on Python 3.12). In PowerShell, from the extracted project root:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env`: supply your development/staging MongoDB connection and a new random Django secret. Keep your production secrets outside this archive. Example settings are for local development only. Use the existing production environment validation requirements when deploying.

For a fresh database, create the permission catalog before signing up:

```powershell
.\.venv\Scripts\python.exe manage.py seed_permissions
```

For an existing database, stop the application and background workers, take a database backup, then run:

```powershell
.\.venv\Scripts\python.exe manage.py upgrade_nexease
```

This command replaces the old unique `(organization, sales_order)` invoice index with a partial unique index that applies only when a sales order exists. This allows multiple direct invoices while preserving one invoice per sales order. It also seeds the new permissions and synchronises built-in roles for active organisations. **Review custom roles** and assign `payroll.read/manage`, `labour.read/manage` and `taxation.read/manage` as appropriate. Labour lookup access returns worker name/code, not salary or bank data.

If the index command fails, do not resume writes: resolve the index/data error on the staging copy first. This command is intended for real MongoDB; the test mock does not prove production index behaviour.

Run the backend:

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

In a second terminal, run the existing worker (required for queued migration validation/import and existing background jobs):

```powershell
.\.venv\Scripts\python.exe manage.py run_background_worker
```

Keep the backend and worker connected to the same staging database.

## 3. Frontend

Use a compatible Node.js installation (tested here with Node 24). In a third PowerShell terminal:

```powershell
cd frontend
Copy-Item .env.example .env.local
npm ci
npm run dev
```

Open `http://127.0.0.1:3000`. Keep frontend and backend hostnames consistent (both `127.0.0.1` or both `localhost`) to avoid cookie/CORS confusion. `NEXT_PUBLIC_API_BASE_URL` must be set before building. In deployment it must be your HTTPS backend URL ending in `/api/v1`.

Production frontend check:

```powershell
npm run build
npm start
```

The user-facing theme preference is saved in that browser. No production hosting changes were made for you.

## 4. First-use checklist

1. Sign in with an existing administrator or sign up after seeding permissions.
2. Choose business scope in Administration → Organization.
3. Choose appearance in Administration → Settings.
4. Review master records, warehouse opening quantities and accounting system accounts.
5. Try migration on a small sample. Download its template, fill `Data`, upload, map columns, validate, review and import. The `Example only` sheet is not imported.
6. For labour: create employees, sites, assignments and timesheets. Approve timesheets before exporting billing totals.
7. For payroll: enter a dated contribution policy, verify coverage/rates, enter monthly attendance and deductions, calculate, review employee payslips, approve, then record the external payment reference.
8. For direct billing: review auto-created masters and the notification. Creating an invoice does not dispatch stock. Existing order-based fulfilment remains the normal stock movement workflow.
9. For GST: classify source transactions in the review register and reconcile the exported workpaper. Use official GST tools for statutory validation/submission.

## 5. Testing

The additional test runner uses **mongomock** and its own isolated database; it does not connect to the `.env` production database:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-test.txt
.\.venv\Scripts\python.exe tests_nexease\test_release.py
.\.venv\Scripts\python.exe tests_nexease\run_existing_suite.py
cd frontend
npm run test:run
```

Before live use, perform end-to-end testing with real MongoDB and your own staging data, including posting, payments, returns, payroll approval, worker jobs, exports and backup/restore. See the material limitations in `FEATURE_STATUS.md`.
