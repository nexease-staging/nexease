# NexEase launch update - pricing, branding, GST lookup and AI stock

## Included

- Welcome-page navigation to /pricing and /deadlines, plus package preview.
- /pricing: service pricing, seven price categories, discounted combos, current software plan catalogue and WhatsApp enquiry link.
- /NexEase_Pricing.pdf: public PDF download. This is the approved branded four-page price list, with your contact details.
- Browser favicon and Apple home-screen icon derived from the logo on your supplied business card. Header uses the same icon.
- /deadlines: live IST days + HH:MM:SS countdown, scheme/category filtering, official source links, expiry handling and five-minute data refresh.
- GST standard rules distinguish monthly and QRMP quarterly periods and 22nd/24th state groups. They are NOT represented as verified current extensions. Other statutory deadlines and extensions require explicit owner configuration, below.
- GST lookup supports Sandbox public GSTIN search using backend-only authentication, cached access tokens, one token refresh on 401, nested response mapping, safe failure and no automatic record writes.
- GST autofill in customer, supplier, direct invoice, quick purchase and organisation GST-registration review forms. Review and save each record normally. Public GST lookup does not promise private phone/email data, bank details, HSN, prices, turnover or invoice history.
- AI stock action matches existing active goods by exact name or SKU inside the current organisation; no new product is created. A single active warehouse is preselected. Multiple warehouses require selection. Confirming writes through existing inventory services and stock ledger, respecting permissions and reserved stock.
- Simple English add/remove stock commands have a deterministic parser so this exact request cannot be mistaken for product creation. Other phrasing/languages use the configured model and the new structured stock-action schema.
- Broader existing AI actions retain their existing prepare/review/confirm flows. This is not a claim of arbitrary universal task execution.

## Install safely on Windows

1. Back up your existing folder and database. Extract the updated NexEase directory over your working source in E:\NexEase, preserving your real .env, frontend/.env.local, mobile signing keys and keystore. The ZIP contains no real credentials or production data.
2. Activate your existing Python virtual environment and install project requirements if needed:

```powershell
cd E:\NexEase
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py check
python manage.py set_launch_prices
cd frontend
npm ci
npm run build
cd ..
```

Use your actual virtual environment directory if it is named .venv. The project dependency pins are unchanged.

The first plan-catalogue request runs a one-time upgrade of existing displayed prices to 749 / 999 / 1299. Changed published catalogue rows become unpublished and lose their old gateway-plan link, preventing checkout against the wrong amount. Republish replacement gateway plans in /owner if you use online checkout. Existing paid subscriptions and unfinished checkout snapshots keep their contracted prices; no charges are changed. The set_launch_prices command is available for an explicitly requested later reset and refuses to alter a still-published catalogue.

3. Push reviewed source changes:

```powershell
git status
git add .
git diff --cached --stat
git commit -m "Add pricing calendar branding GST lookup and AI stock actions"
git push origin main
```

Ensure .env and private signing files are ignored before staging. Do not replace Render environment variables with a blank example file. Redeploy BOTH backend and frontend. If using a bundled Android/iOS app, rebuild and install the app using the existing build scripts; a web redeploy alone does not replace a previously bundled frontend.

## Obtain and configure GST API access

Provider implemented: Sandbox, https://sandbox.co.in/gst . Do not buy a different provider expecting its key to work with this adapter.

1. Create a provider account at https://console.sandbox.co.in/ . Request access to the **public Search GSTIN** API. Confirm current billing, account verification and live-access requirements with the provider.
2. In Settings > API Keys, generate Test credentials first. Use Test and Live credentials with their matching environment; provider test responses need not represent actual taxpayer data.
3. In Render BACKEND environment variables, add:

```dotenv
GST_LOOKUP_PROVIDER=sandbox
GST_SANDBOX_ENV=test
GST_SANDBOX_API_KEY=YOUR_TEST_API_KEY
GST_SANDBOX_API_SECRET=YOUR_TEST_API_SECRET
```

No key belongs in NEXT_PUBLIC_* variables, the browser, mobile source or Git. No separate GST_LOOKUP_URL or GST_LOOKUP_TOKEN is required for this provider. GST_SANDBOX_API_VERSION is optional and should only be set when required by your account's documented version.

4. Redeploy backend. Fetch a documented provider test GSTIN in Customers or Suppliers. Verify name, legal name, address, state code and status before saving. A GSTIN lookup doesn't file returns.
5. After obtaining Live access, replace both credentials and set GST_SANDBOX_ENV=live. Redeploy again and test a known actual GSTIN. The app authenticates automatically and caches the raw token; do not paste a manually generated token into code.

Official references checked 04 Nov 2026:
- Keys: https://help.sandbox.co.in/portal/en/kb/articles/generate-your-api-keys
- Authenticate: https://sandbox-docs.readme.io/reference/authenticate-api
- Public search: https://sandbox-docs.readme.io/reference/search-gstin-api
- Test/live hosts: https://sandbox-docs.readme.io/reference/gst-test-cases

The search API uses POST /gst/compliance/public/gstin/search with {"gstin":"..."}, x-api-key and a RAW authorization token (not Bearer). This adapter handles that. It is distinct from taxpayer OTP authentication needed for private return data or filing.

If you already operate a custom normalized API, use GST_LOOKUP_PROVIDER=adapter with the existing GST_LOOKUP_URL and GST_LOOKUP_TOKEN contract. The generic endpoint must return gstin, name and optional address/state/email/phone at the top level.

## AI setup and acceptance check

Keep these backend values enabled using your actual working model and API account:

```dotenv
AI_ENABLED=true
OPENAI_API_KEY=YOUR_NEW_PRIVATE_OPENAI_API_KEY
OPENAI_MODEL=gpt-5.4-mini
```

Use a model available to your API project that supports the Responses API and structured output. A paid API key alone does not add business actions; the action implementation is included in this update. If a key was pasted into chat or shared publicly, revoke it and use a new private key.

Use an active Pro membership/owner-granted Pro trial with AI enabled for the organisation and module. Users need inventory.adjust; they also need inventory.create when creating the first balance row in a warehouse. Existing stock changes use the same permissions as the ordinary inventory screen.

1. Confirm an active goods product called Bisleri exists (or use its exact SKU) and check current quantity, for example 20.
2. Open NexEase AI and send: `add bisleri 100 qty in stock`.
3. Review should show **stock adjustment**, existing product/SKU, **+100** and the warehouse. If there are multiple warehouses, choose one and save the review. It must not ask to create a new product or enter a category/price.
4. Click **Confirm stock update**. The balance should become 120 with one new ledger movement, reference type AI_STOCK. Sending a command prepares the action; confirmation performs it.
5. Confirming the same proposal again must leave 120, not 220. A genuinely new proposal is a new business instruction.
6. Test removal: `remove Bisleri 10 qty from stock`. Removing reserved or unavailable stock is blocked. Absolute balance instructions such as "set stock to 100" are different from adding 100; use the ordinary screen or clarify the intended change.

Unknown or ambiguous names are not guessed; choose exact names/SKUs. An interrupted write is marked needs_review, not silently retried. Check the ledger before creating another command for the same movement.

No live OpenAI/GST call or production database update was performed during preparation. Verify both integrations in staging with your private credentials before a client demonstration.

## Maintain real deadlines and extensions

Standard GST dates use published general rules; official extensions are not automatically scraped. Confirm current notifications. The calendar must not claim that every standard date is the legally final date for every customer.

Add reviewed, period-specific rows using backend `NEXEASE_DEADLINES_JSON`, a JSON array. Empty array [] retains standard GST guidance. Required fields per row: id, title, category, period, applies_to, due_at (ISO date/time WITH offset), source_url (HTTPS), verified_on (YYYY-MM-DD). Optional note. Use a genuine notification source and actual reviewed date, not a placeholder. Maximum 200 rows.

For an official extension, use the SAME id as the standard row to replace it. Example baseline ID structure: GSTR-3B-2026-10 means the October 2026 monthly period; quarterly IDs include quarter and due-day group, e.g. GSTR-3B-2026-Q3-22. Inspect GET /api/v1/saas/deadlines/ for exact IDs.

Add TDS, PF/ESI, ITR, professional tax or ROC rows only for the applicable filing period and verified date. Do not apply a monthly 20th to every return. State/event/turnover conditions belong in applies_to and note. Deploy backend after changing Render environment configuration. The page refreshes calendar data every five minutes and clocks every second. It does not send reminders or mark returns as filed.

Sources for general GST rules:
- https://tutorial.gst.gov.in/downloads/news/creative_faqs_on_gstr1a_fo_cr25785.pdf
- https://tutorial.gst.gov.in/offlineutilities/returns/QRMP_Advisory.pdf
- https://sgst.uk.gov.in/return-payment/

## Pricing maintenance

Software defaults are in apps/saas/entitlements.py; actual existing catalogue prices are managed in /owner. Individual service and combo display prices are in frontend/src/features/saas/service-prices.json. If changing prices later, also regenerate the downloadable PDF so they agree. The approved price sheet excludes applicable taxes; the existing software payment integration shows its final checkout amount. Confirm your tax treatment before publishing a checkout; this update does not alter payment calculation or existing contracts.

## Verification details

See LAUNCH_VALIDATION.md for the actual executed checks and limitations. No Render/GitHub production deployment was performed from this workspace.

## 05 Nov 2026: tier and sidebar update

- Basic ₹749: Inventory, Sales, Purchasing and daily expense recording. Workforce, GST workpapers and the full Finance module are blocked. AI/scan unavailable.
- Plus ₹999: Workforce, GST workpapers, Finance and advanced reports included. AI/scan unavailable.
- Pro ₹1,299: all modules included, including AI/scan, within usage limits and normal role permissions.
- Existing membership snapshots cannot grant AI to Plus or unlock paid modules for Basic. Set SAAS_ENFORCEMENT=true in production. Administrator module switches and role permissions still apply.
- Sidebar starts expanded; groups start closed and behave as a single-open accordion. Sidebar header uses NexEase branding and shows the customer organisation below it. The main app header retains the customer identity.
- Only Needs attention and Recent activity were removed from the dashboard overview. Greeting, quick actions, KPI cards, dates and charts remain.
- GST keys: API Key -> GST_SANDBOX_API_KEY; API Secret -> GST_SANDBOX_API_SECRET. Store both in Render backend environment, not frontend or Git. Set GST_LOOKUP_PROVIDER=sandbox and GST_SANDBOX_ENV=test or live to match the key environment. Redeploy the backend.

After deploying both services, reopen the welcome/pricing page to apply the one-time catalogue migration, then check the price cards. Rebuild bundled Android/iOS apps for the new menus and branding.
