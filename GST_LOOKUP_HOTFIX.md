# NexEase GST lookup hotfix - 05 Nov 2026

## First fix for this deployment: your keys are LIVE

Set the following in Render > backend service > Environment. Keep actual keys private:

GST_LOOKUP_PROVIDER=sandbox
GST_SANDBOX_ENV=live
GST_SANDBOX_API_KEY=YOUR_LIVE_API_KEY
GST_SANDBOX_API_SECRET=YOUR_MATCHING_LIVE_API_SECRET

Save and redeploy the backend. Confirm both keys belong to the same provider account and environment. Use a real valid GSTIN with live credentials. Check that your Sandbox account has GST Public Search API access and adequate billing/credits if required. Live keys against the Test host, or Test keys against the Live host, do not form a valid setup.

This message alone does not prove the deployment's original failure was an environment mismatch. The hotfix identifies the failing stage and status; it cannot activate your provider account or correct unknown credentials remotely.

## What changes

- Detect recognisable Live/Test credential prefix mismatches before sending them.
- Reports missing settings, invalid environment, authentication rejection, access denial, provider billing, rate limits, outages, network/TLS issues, invalid JSON, missing taxpayer data and GSTIN mismatches separately.
- Handles HTTP 200 GSTN business failures (including no-record errors), rather than reporting a generic failure.
- Refreshes a rejected cached token once, without retrying other provider failures blindly.
- Uses a body-free POST for authentication and the documented default public-search version 1.0.0 when none is configured.
- Keeps the provider access token raw in the authorization header, as documented (no Bearer prefix).
- Does not echo response bodies, API keys, API secrets or access tokens to the UI/logs. Logs only safe diagnostic codes, stage, HTTP status and a validated transaction reference.
- Rejects a different GSTIN in a test fixture instead of applying another taxpayer's details to a real customer.
- Adds `python manage.py check_gst_lookup`: configuration-only by default, no provider call and no credential values displayed. With `--gstin YOUR_GSTIN`, makes one lookup using the configured environment; provider usage may apply. Run in an environment containing the backend settings, such as Render Shell if available. This command does not change business records.

## Install this small ZIP in your existing Git checkout

The hotfix ZIP contains relative apps/ paths (no extra NexEase/ parent folder). Extract it into the folder containing manage.py, not into frontend. It includes only the changed backend files, focused tests and this note; it contains no .env.

For your current Windows checkout, if the downloaded ZIP is in Downloads:

```powershell
cd E:\NexEase-Git-20261105-004821
Expand-Archive -Path "$env:USERPROFILE\Downloads\NexEase_GST_Lookup_Hotfix.zip" -DestinationPath . -Force
git add apps/business/gst_provider.py apps/business/gst_lookup.py apps/business/tests_gst_provider.py apps/core/management/commands/check_gst_lookup.py GST_LOOKUP_HOTFIX.md
git commit -m "Improve GST lookup validation and provider diagnostics"
git push origin main
```

Redeploy the backend. No frontend rebuild or database migration is required for this backend hotfix.

## Next result to share

Retry from Customers or Suppliers. If lookup still fails, share only the safe error code/message, such as GST_AUTH_REJECTED, GST_ACCESS_DENIED, GST_PROVIDER_BILLING or GST_GSTIN_MISMATCH. Never share credentials or an authentication response/access token.

## Verification and references

49 backend regression tests passed, including 13 focused GST diagnostic tests plus the existing tier, stock and mailbox tests. Provider HTTP responses were mocked; no live API key, actual taxpayer lookup, account entitlement or Render deployment was tested. Exact production-runtime limitations remain documented in LAUNCH_VALIDATION.md.

Current provider references checked 05 Nov 2026:
- https://developer.sandbox.co.in/api-reference/authenticate
- https://developer.sandbox.co.in/api-reference/gst/compliance/endpoints/public/search_gstin
- https://help.sandbox.co.in/portal/en/kb/articles/sandbox-test-environment
