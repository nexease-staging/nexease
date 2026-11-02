# Email, populated AI review and expanded sidebar — 2 November 2026

## What changed
- Sidebar rail and section groups start expanded. Users can collapse them manually. Mobile navigation still opens through its menu button.
- AI extraction now has explicit field mappings and examples for supported actions. Category name and description populate the review. Invoice customer, PO, dates, notes and supplied line amounts populate the review. Extra non-empty extracted fields are visible instead of silently hidden.
- Exact organization master matches fill existing party details, item units/HSN and missing invoice selling prices. Explicit user prices are preserved. Catalogue-derived prices show a review warning. Missing information is still requested instead of fabricated.
- Corrections retain the current edited review, and New request clears the previous proposal so a different entry can start cleanly. The review panel scrolls into view when a proposal is ready.
- Users can connect their registered mailbox under their avatar → My email, or Settings → My email. Document email uses that authenticated address as From and Reply-To. Arbitrary sender addresses are not accepted. Credentials are encrypted at rest and never returned by the API.

This is an upgrade to supported preparation/review actions, not an unrestricted agent for every application action. Supported kinds: category, product, invoice, supplier bill, purchase order, expense, advance, employee, site, assignment, monthly attendance, timesheet and leave request. One entry is prepared at a time. Records still require confirmation; invoices/bills remain drafts. Actual AI extraction depends on the prompt, supplied information, model and API availability. Live OpenAI extraction has not been tested with your account here.

## Install without losing Git
Overlay this source into your chosen working repository (currently E:\NexEase-Git), preserving .git, .env, frontend\.env.local, uploaded data, Firebase and signing files. Do not delete the folder. Commit/push the source and deploy backend, frontend and background worker from the same revision. Install requirements.txt and frontend dependencies using the existing setup process. Rebuild/install the Android APK for phone changes (version 1.4, code 6).

## Owner email setup
Generate a Fernet key locally once, using your existing environment:

```powershell
E:\NexEase\.venv\Scripts\python.exe -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Put the generated value in MAILBOX_ENCRYPTION_KEY in the backend environment and EVERY background worker environment. Keep it private and stable. Changing/removing it prevents decryption of existing mailbox credentials and requires reconnection. Do not commit it.

Per-user document sending does not use the shared default mailer. System mail, including password reset, still requires a real shared sender:

```dotenv
EMAIL_MODE=production
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=nexease.owner@gmail.com
SMTP_PASSWORD=YOUR_OWNER_MAILBOX_APP_PASSWORD
SMTP_USE_TLS=true
SMTP_USE_SSL=false
DEFAULT_FROM_EMAIL=nexease.owner@gmail.com
MAILBOX_ENCRYPTION_KEY=YOUR_GENERATED_FERNET_KEY
```

Remove the NEXEASE_STAGING_NO_EMAIL development bypass when enabling production system mail. Apply the real values privately in Render/environment files, then restart services. SMTP credentials and API keys are not included in this ZIP. Existing service-specific setup still applies; this code cannot activate an external mailbox or guarantee inbox delivery by itself.

Render free web services block SMTP ports 25, 465 and 587. This SMTP implementation therefore needs a paid Render instance or other hosting with outbound SMTP available. No Gmail/Microsoft OAuth connection is implemented by this update.
Reference: https://render.com/docs/free

## Each user's mailbox
1. The user's NexEase registered email must be the mailbox they connect.
2. Gmail: enable 2-Step Verification, then create an app password if eligible. Do not use the normal Google password. Some managed/Advanced Protection accounts do not permit app passwords.
3. Avatar → My email → select provider → enter app password → Authenticate & connect. Authentication is checked without sending a test email.
4. Send a document from its normal Email action. The background worker must be running for queued jobs, with the same MongoDB and encryption key.
5. Review Document logs for processing/failure status. SMTP acceptance does not guarantee inbox placement; providers can impose limits or classify mail as spam.
6. Disconnect removes stored credentials. Changing the registered email requires connecting the new mailbox.

Supported connectors: Gmail/Google Workspace, Yahoo and Microsoft 365 accounts that explicitly permit SMTP password authentication. OAuth-only accounts cannot connect through this version. Unconnected users receive a connection error instead of silently sending as someone else. Documents already queued will use the current sending user's mailbox at execution time.

Document support follows existing email actions: invoices, sales orders, credit notes, customer payments, purchase orders, vendor bills, vendor debit notes, supplier payments and goods receipts. This does not add email buttons to every report or payslip.
Gmail reference: https://support.google.com/accounts/answer/185833

## AI acceptance examples
- "Create category Safety Equipment, description Helmets and gloves." Review should already show both values.
- "Create invoice dated 2026-11-02 for Acme Supplies, PO PO-24, 3 Helmets at 500 each, GST 18%, discount 0, place of supply 27." Existing customer/item names should match only within your organization. Review every value; remaining fields may require an answer.
- Then type "Change quantity to 4 and rate to 450." Check other details remain intact.
- Click New request before preparing an unrelated entry.
- Enter prepares, Shift+Enter adds a line. Give processing consent first. Preparing never sends email or saves records automatically.

## Verification
166 frontend tests passed, including category/invoice populated review and navigation regressions. 12 targeted backend tests passed with isolated MongoDB mock storage, including mailbox encryption/scoping/authentication failure, real Django email backend integration with mocked SMTP, duplicate email-job replay protection and extracted review fields. Web/mobile builds and Capacitor sync checked. No real mailbox email, live OpenAI call, physical device or browser visual test was performed here.
