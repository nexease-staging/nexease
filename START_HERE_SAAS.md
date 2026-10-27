# NexEase SaaS Edition — complete setup

Release prepared 25 October 2026. This ZIP contains the complete Django backend and Next.js frontend, including the earlier Professional Update. No coding is required to configure it. You will run commands, edit environment values and register provider accounts.

The integrations are implemented, but no live payment or AI-provider credentials were used during validation. Complete the test-mode acceptance steps before charging customers.

## 1. What is included

- NexEase ₹749, NexEase Plus ₹1,499 and NexEase Pro ₹1,999 monthly organization plans.
- Backend enforcement of users, products, active warehouses/employees, issued invoice and posted bill quotas. Normal forms and model-based imports use the same guards.
- Plus/Pro workforce, GST workpapers, advanced finance reports and bulk accountant exports. Base includes ordinary individual document PDFs, GL/TB, expenses and core operations.
- Pro multilingual AI proposals: daily expense, employee advance, draft sales invoice and draft supplier bill. These are the supported AI entry types in this release; it is not an unrestricted assistant for every screen or a general reporting chatbot.
- PDF/JPG/PNG extraction, editable review, exact master matching, total checks, duplicate-reference rejection and explicit confirmation.
- Razorpay monthly recurring subscriptions, verified activation, webhook reconciliation, cancellation of renewal and payment history.
- Private Owner Console with authenticator MFA, organization search, trials, suspension, user access/session/reset actions, module visibility, editable new-sale prices/allowances, customer support reports, payment history and audit logs.
- Welcome page with current pricing from the backend and Pro feature explanations.

## 2. Before replacing files

Stop your old backend, frontend and worker. Back up the old folder and MongoDB database. Test this version with a database COPY first. Do not point an old NexEase backend at the upgraded database at the same time.

Extract the archive. Its inner `NexEase` folder should become `E:\NexEase`, containing `manage.py`, `apps`, `frontend`, `requirements.txt` and this guide. Avoid `E:\NexEase\NexEase` nesting.

For an upgrade, copy your old `.env` to `E:\NexEase\.env` and old `frontend\.env.local` to `E:\NexEase\frontend\.env.local`. Preserve uploaded files. No database, secrets, Python environment, npm dependencies or `.next` build is included in the ZIP.

You may instead copy the new SOURCE contents into the existing project folder, preserving the private environment files. Do not copy an old frontend over the new one afterward.

## 3. Python setup

Open PowerShell:

```powershell
Set-Location E:\NexEase
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe scripts\configure_local.py
```

If you already have a working `.venv`, the creation step can be skipped. The helper creates missing environment files, appends the new settings, generates missing Django/owner encryption secrets and preserves existing credentials. It does not print secrets.

Open the backend environment file:

```powershell
notepad .env
```

Keep your correct existing MongoDB values. For a fresh installation, replace the local example connection with your Atlas connection string and database name:

```dotenv
MONGODB_URI=your_actual_mongodb_connection_string
MONGODB_DATABASE=nexease_staging
APP_ENV=development
DJANGO_DEBUG=true
ALLOWED_HOSTS=localhost,127.0.0.1
FRONTEND_ORIGINS=http://127.0.0.1:3000,http://localhost:3000
FRONTEND_BASE_URL=http://127.0.0.1:3000
SAAS_ENFORCEMENT=true
AI_ENABLED=false
PAYMENTS_ENABLED=false
```

The helper already supplies `DJANGO_SECRET_KEY` and `OWNER_ENCRYPTION_KEY` if missing. Do not replace valid generated values with placeholders. Keep a private backup of `.env`: changing the owner encryption key prevents decrypting the old MFA secret until owner recovery.

If creating Atlas for the first time: create a cluster, create a DATABASE user, allow the IP address of the computer/server connecting, and copy the Drivers/Python connection string. Atlas website login is different from the database user. Replace its password placeholder locally; percent-encode special characters in the URI password. For an existing installation retain its working connection settings.

## 4. Prepare plans and existing accounts

For an upgrade with existing organizations, explicitly grant a 30-day Pro trial:

```powershell
.\.venv\Scripts\python.exe manage.py upgrade_saas --legacy-trial-days 30
.\.venv\Scripts\python.exe manage.py check
```

The trial option applies ONLY to organizations without an existing membership. Running it again does not extend trials or overwrite paid subscriptions. It does not reset payroll, invoices, attendance or payments.

For a fresh empty database, run `upgrade_saas` without the trial option. After customer signup, grant the organization a trial from Owner Console, or let it purchase a published plan.

If upgrading directly from the original IMS rather than the Professional/Automation Update, first follow the prior `upgrade_nexease` step in SETUP_AND_UPGRADE.md for the invoice index change.

## 5. Create your private owner account

In the project root:

```powershell
.\.venv\Scripts\python.exe manage.py setup_owner
```

Enter your owner email, then a strong password twice. Password typing is hidden. The command shows an authenticator setup secret once.

On your phone, open your authenticator app and add a time-based account manually:

- Account name: NexEase Owner
- Key: the secret shown in your terminal
- Type: time based; six digits, 30 seconds

Keep this secret private. Do not send it in chat. Owner accounts cannot be created through public signup or assigned by customer Admins. There is one platform owner account in this release.

If you lose the authenticator or owner password, recover through the trusted server terminal:

```powershell
.\.venv\Scripts\python.exe manage.py setup_owner --recover
```

Recovery replaces the password/MFA secret and revokes existing owner sessions. This is a server-operator procedure, not a public recovery page.

## 6. Frontend setup

Open a second PowerShell window:

```powershell
Set-Location E:\NexEase\frontend
node --version
npm.cmd --version
npm.cmd ci
notepad .env.local
```

If Node is missing, install a current supported Node.js LTS release from https://nodejs.org/ and reopen PowerShell. The frontend environment file should contain:

```dotenv
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000/api/v1
```

No OpenAI secret, Razorpay secret, webhook secret or owner encryption key belongs in the frontend. Only the backend serves the public Razorpay checkout key when needed.

## 7. Start all three processes

Backend terminal:

```powershell
Set-Location E:\NexEase
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

Frontend terminal:

```powershell
Set-Location E:\NexEase\frontend
npm.cmd run dev
```

Worker terminal:

```powershell
Set-Location E:\NexEase
.\.venv\Scripts\python.exe manage.py run_background_worker --sleep 2 --lease-seconds 300
```

Leave all three windows open. You can use `START_NEXEASE.ps1` on later starts if your PowerShell policy permits local scripts; the explicit commands above do not require changing execution policy.

Use http://127.0.0.1:3000 consistently for this setup.

- Welcome: http://127.0.0.1:3000/
- Customer login: http://127.0.0.1:3000/login
- Owner Console: http://127.0.0.1:3000/owner
- Customer subscription: http://127.0.0.1:3000/subscription

Log out/in after upgrading so new permissions refresh. In customer Settings → Business modules & books, prepare/repair system accounts. If Expenses is missing, enable Daily expense tracker and check `expenses.read/manage` for custom roles.

## 8. Use Owner Console before purchasing any APIs

Sign in with owner email, password and authenticator code. The owner session expires after 30 minutes. Financial/customer mutations require the owner password and a NEW code; the same 30-second code cannot be reused after login or an action.

1. Search and select an organization.
2. Enter a reason/support reference.
3. To grant a trial, choose `grant trial`, select plan and days, enter fresh owner credentials and Apply.
4. To inspect users/reports, click Open audited customer report. This is a recorded support access action. Reports show the most recent 100 documents/journals/activities and 12 payroll/AI periods, not a complete accounting audit export.
5. Choose a user and disable/enable access, revoke sessions or send a reset email. Existing passwords are never displayed.
6. Module on/off actions alter sidebar visibility. They do not override plan entitlements or role permissions.
7. Edit plan pricing/limits under Plan pricing and allowances. Save draft pricing, then publish a gateway plan after configuring payments.

Changes to prices/limits apply to NEW subscriptions and newly granted trials. Existing subscribers keep the price and allowance snapshot they purchased. Plus/Pro feature groups are fixed in this release; the console edits prices and numeric allowances, not arbitrary feature code.

Your customer Admin account and platform owner account are separate. A customer login cannot enter Owner Console.

## 9. Get the AI API key

1. Go to https://platform.openai.com/ and sign in/create an account.
2. Create/select a project for NexEase.
3. Enable API billing/credits in the platform billing settings. ChatGPT Plus does not pay for NexEase API requests.
4. Create a project API key in the API Keys section. Save the secret privately when it is shown.
5. Configure project usage alerts and check model access. This implementation defaults to `gpt-5.4-mini`; if unavailable, select a supported image-input Responses model that supports the same structured-output and reasoning settings, then validate it before customers use it. Do not blindly substitute an incompatible model.
6. In `E:\NexEase\.env`, set:

```dotenv
OPENAI_API_KEY=your_actual_secret_key
OPENAI_MODEL=gpt-5.4-mini
AI_ENABLED=true
AI_ORG_BUDGET_UNITS=5000
AI_GLOBAL_DAILY_REQUEST_LIMIT=200
REQUEST_TIMEOUT_SECONDS=120
```

Restart the backend and worker after changing environment values. These are server settings, never frontend variables.

The organization safeguard reserves 10 internal budget units per preparation plus 5 per scan page, up to the configured total per subscription period. It retains these reservations on provider failures because the provider may already have charged. These units are NOT rupees/dollars or an exact API bill. Provider usage/charges, model prices and your alerts remain authoritative. The daily global request limit is an additional cap across all organizations. Subscription chat/page allowances are separately enforced.

AI test:

1. Ensure your organization has an active Pro trial.
2. Open the bottom-right NexEase AI button.
3. Enter `Today I paid 500 rupees for petrol by UPI to ABC Petrol Pump for a site visit.`
4. Confirm the provider-processing consent checkbox and click Prepare entry.
5. Review date, payee, amount, category, payment mode and account. Save review & match masters.
6. Confirm & save once. Verify Expenses and GL.
7. Upload a dummy supplier bill PDF/photo. Review source, supplier code, SKU, quantity, price, tax, discount and total. Confirm creates a DRAFT bill; it does not automatically post the bill, pay it or receive stock.

Documents: up to 8 MB, ten PDF pages or one JPG/PNG image. Encrypted PDFs must be unlocked first. Files are retained in MongoDB for 30 days using a TTL index; deletion timing is approximate. Extracted proposals/audit/billing records have separate retention and are not deleted by that file TTL. Source retention consumes MongoDB storage; include that storage in your hosting budget and monitor Atlas capacity.

If a request times out, inspect Recent proposals before repeating it. A proposal saved once returns the same result on confirmation retry. If it says `needs_review` or `committing`, check existing source records and accounting recovery before creating anything again. Source save and journal posting are not a single database transaction. Supported validation errors with no saved source return the proposal to review.

## 10. Create a Razorpay account and use TEST mode first

1. Go to https://razorpay.com/ and create your business account.
2. Complete the business/bank/identity verification requested for your entity. Confirm Razorpay Subscriptions is available/enabled for the account; gateway signup alone may not enable every recurring payment method.
3. Open the Razorpay Dashboard and select Test Mode.
4. Go to Account & Settings → API Keys and generate test keys. Save both Key ID and Key Secret securely.
5. Keep test and live keys separate. Never enter real card details into a test scenario unless the provider explicitly instructs it; use Razorpay's current official test instructions.

Payments cannot operate from API keys alone: publish your actual subscription terms, privacy policy, cancellation/refund policy and contact information on public HTTPS pages. The app will keep checkout disabled until the URL settings and readiness flag are supplied. The software checks configuration, not the legal adequacy of your policies.

## 11. Configure the payment webhook

Razorpay needs a public HTTPS BACKEND URL to send events. `127.0.0.1` and `localhost` cannot receive provider webhooks. Use your staging Render backend for the first test, with a staging MongoDB database and matching staging frontend. A local browser callback can verify payment, but is not a replacement for renewal webhooks.

In Razorpay Test Mode → Account & Settings → Webhooks, add:

```text
https://YOUR-STAGING-BACKEND/api/v1/saas/webhook/
```

Generate a random webhook secret locally:

```powershell
.\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(40))"
```

Enter the same secret in Razorpay's webhook form and backend `RAZORPAY_WEBHOOK_SECRET`. It is separate from the API Key Secret.

Enable relevant events available on your account: `subscription.authenticated`, `subscription.activated`, `subscription.charged`, `subscription.pending`, `subscription.halted`, `subscription.cancelled`, `subscription.completed`, `payment.captured`, `refund.processed`.

The server verifies the raw webhook signature and fetches current provider data. Access is granted only for a captured, matching-currency/matching-amount paid subscription invoice covering the current billing period. Mandate authentication alone does not grant paid access. Repeated events do not extend/reset the period.

## 12. Backend payment environment values

On your staging backend (local `.env` or Render Environment settings), configure:

```dotenv
RAZORPAY_KEY_ID=your_test_key_id
RAZORPAY_KEY_SECRET=your_test_key_secret
RAZORPAY_WEBHOOK_SECRET=your_chosen_webhook_secret
PAYMENTS_ENABLED=true
BILLING_TERMS_READY=true
BILLING_TERMS_URL=https://your-public-site/terms
PRIVACY_URL=https://your-public-site/privacy
REFUND_POLICY_URL=https://your-public-site/refunds
```

For hosted deployment, configure the existing production settings correctly: `APP_ENV=production`, `DJANGO_DEBUG=false`, HTTPS frontend origins/base URL, backend allowed host, secure cookies, MongoDB credentials and SMTP. Do not use localhost values for deployed frontend/backend communication. See SETUP_AND_UPGRADE.md for the underlying production checks. The frontend API base URL is a build-time setting: rebuild after changing it.

## 13. Publish the plans and test purchase

Restart/redeploy after configuration. In Owner Console → Plan pricing and allowances:

1. Choose NexEase; review ₹749 and limits.
2. Enter reason/password/fresh authenticator code and Publish gateway plan.
3. Repeat for Plus ₹1,499 and Pro ₹1,999.

The app creates the monthly Razorpay plans; you do not need to copy plan IDs manually. Test plan IDs cannot be used with live keys. Saving a new price unpublishes checkout until a new gateway plan is published.

Initial displayed prices are FINAL checkout amounts, with no automatic extra GST calculation. Before selling, decide the correct final amount/tax presentation with your accountant and adjust prices/policies. Gateway receipts and the payment history are not a complete GST tax-invoicing/settlement-accounting system for your NexEase business.

Using a customer Admin account:

1. Open Subscription & usage.
2. Review terms and authorize the recurring monthly payment.
3. Select Subscribe and complete the official Razorpay test flow.
4. Wait for verified activation or click Refresh payment status.
5. Confirm the Pro features appear only for Pro, and Basic/Plus cannot call AI endpoints.
6. Test cancellation, renewal, failed payment and refund using the provider's test workflow.

Customers can cancel renewal from Subscription. Paid access remains through its verified period. This release changes plans by cancelling renewal and starting a new plan after the paid period ends; it does not calculate mid-cycle proration. Each subscription is created for a maximum of 120 monthly cycles. The checkout does not apply coupons/add-ons or annual plans.

Refunds are issued through the Razorpay Dashboard, not the NexEase console. Any refund detected against the current period blocks that period's paid access pending review. A refund does not itself cancel the provider's future recurring schedule; cancel renewal separately when your policy requires it.

## 14. Reconcile missed webhooks

Configure a hosting scheduled job to run regularly, for example every 15 minutes:

```text
python manage.py reconcile_subscriptions
```

For a local manual check:

```powershell
.\.venv\Scripts\python.exe manage.py reconcile_subscriptions
```

The owner can also use the `reconcile` action with a subscription ID. Do not mark a payment successful by hand merely because a customer supplies a screenshot. Owner trial grants are explicitly separate from verified paid subscriptions.

If remote subscription creation succeeds but local storage fails/times out, inspect the Razorpay dashboard before creating another subscription. Remote provider operations and MongoDB writes cannot be one atomic transaction; resolve any orphan gateway subscription before retrying.

## 15. Password-reset emails

Development email mode does not deliver real email. Configure your email provider's SMTP service and verified sender for actual password-reset emails:

```dotenv
EMAIL_MODE=production
SMTP_HOST=your_provider_smtp_host
SMTP_PORT=587
SMTP_USERNAME=your_smtp_username
SMTP_PASSWORD=your_smtp_password_or_app_password
SMTP_USE_TLS=true
SMTP_USE_SSL=false
DEFAULT_FROM_EMAIL=your_verified_sender_address
FRONTEND_BASE_URL=https://your-frontend-domain
```

Use the port/TLS values supplied by your provider. Restart and test a reset on an account you control. Passwords are never readable; resets use the existing expiring token flow. Your owner account uses terminal MFA recovery instead.

## 16. Going live

After your Razorpay account is approved and test acceptance succeeds:

- Use a separate production database/project from staging.
- Add LIVE Razorpay keys and a LIVE webhook with its own secret.
- Publish each plan again in Owner Console under live mode.
- Confirm final prices, policy links, contact details and supported payment methods.
- Use production HTTPS, private secrets, backups and working email.
- Perform a small controlled live purchase, confirm verified access, then test your agreed cancellation/refund process.
- Monitor Razorpay settlements, OpenAI usage and owner audit history. These external bills/fees are separate from your subscription revenue.

Do not expose Django `runserver` or Next `npm run dev` as the production service. Use your production WSGI/frontend deployment and preserve existing environment security checks. AI requests can take up to 75 seconds; use a backend/proxy timeout of at least 120 seconds or move to a background extraction worker before high-volume use. The current AI flow is synchronous and should be load-tested for your hosting size.

## 17. Plan limits and operations

| Limit | NexEase | Plus | Pro |
|---|---:|---:|---:|
| Monthly price | ₹749 | ₹1,499 | ₹1,999 |
| Active users including organization Admin | 2 | 5 | 10 |
| Issued sales invoices per billing period | 100 | 500 | 2,000 |
| Posted vendor bills per billing period | 100 | 500 | 2,000 |
| Products (all records) | 500 | 5,000 | 20,000 |
| Active warehouses | 1 | 3 | 10 |
| Active employees | 0 | 25 | 100 |
| AI chat requests | 0 | 0 | 300 |
| Scan pages | 0 | 0 | 100 |

Scans consume pages, not chat allowance as well. Repeated scans consume pages again. Failed extraction with no usable result restores customer chat/page allowance, while keeping the internal cost reservation. Issued invoices still count after cancellation. Drafts do not consume invoice/bill issue allowance. Counters start with this release and a subscription/trial period; historical issued documents are not backfilled into new counters. Trial allowance applies over that trial period.

At expiry, data is retained and base read views remain available; writes and paid-only modules need renewed access. Suspended accounts are blocked from business data access but can still reach account/subscription support screens. Downgrades do not delete anything; a new lower plan cannot be purchased while active resources exceed its limits. Existing over-limit legacy organizations can retain records, but cannot add the limited resource.

Existing plan/report/workforce limitations from UPDATE_PROFESSIONAL.md still apply. In particular, gross daily expenses do not claim GST ITC, payment ledger entries do not initiate bank transfers, and statutory reports require review.

## 18. Troubleshooting

- `ModuleNotFoundError`: install requirements from THIS package using its `.venv` Python.
- MongoDB unknown organization fields: you are running an older folder against an updated database. Use this complete package rather than deleting database fields.
- `Plan required`: run the explicit legacy-trial upgrade for old organizations or grant an owner trial; do not disable enforcement on a customer deployment.
- Owner login rejects the code: use automatic phone time; wait for the next code if it was just used. Recover from the trusted terminal if needed.
- Provider disabled: check backend `.env`, restart and inspect owner configuration status.
- AI `needs_review`: look for the saved source before retrying. Use accounting recovery if the source exists but its journal failed. Never blindly create it again.
- Payment captured but no access: refresh/reconcile; inspect webhook delivery and plan/amount/mode. No manual payment-success flag exists.
- Stale write lock after server interruption: STOP ALL backend/worker instances, then run `manage.py recover_saas_lock ORGANIZATION_ID`, confirm STOPPED and restart. Do not remove a lock while writers are running.
- Reports in Owner Console are a limited support view; customer accountant exports remain in the regular application.

## Official provider references

- OpenAI key/setup: https://developers.openai.com/api/docs/quickstart
- OpenAI file input: https://developers.openai.com/api/docs/guides/file-inputs
- OpenAI pricing/model: https://developers.openai.com/api/docs/models/gpt-5.4-mini
- Razorpay subscription integration: https://razorpay.com/docs/payments/subscriptions/integration-guide/
- Razorpay webhook validation/testing: https://razorpay.com/docs/webhooks/validate-test/
- Razorpay API keys: https://razorpay.com/docs/payments/dashboard/account-settings/api-keys/
- Razorpay subscription API examples: https://github.com/razorpay/razorpay-python/blob/master/documents/subscription.md

Provider dashboard labels, availability, fees and policies can change. Follow the current official account screens where labels differ.
