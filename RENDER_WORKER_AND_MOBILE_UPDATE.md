# NexEase: Render worker, navigation and session update

Deploy the updated backend and frontend from the same Git commit. Keep the
backend start command unchanged. Rebuild the APK for the mobile permission
refresh and updated navigation; the backend also recognizes existing Android
clients that send the native origin and Android user agent.

## Render background worker

1. In the Render dashboard choose **New → Background Worker**. Connect the same
   Git repository and branch as the backend. Use the same region and root
   directory as the Django backend (leave Root Directory empty if manage.py is
   at the repository root). Use Python and a paid worker instance.
2. Build command: `pip install -r requirements.txt`
3. Start command: `python manage.py run_background_worker`
4. Use the same relevant environment settings as the backend, ideally through a
   shared environment group. In particular, use the same MongoDB URI and
   database, application environment and Django secret, and copy the existing
   encryption keys for mailboxes and other encrypted settings. Use the same
   email settings, and set FRONTEND_BASE_URL to the actual HTTPS frontend URL.
   Reuse existing secret values; do not generate replacement encryption keys or
   add secrets to Git. If Atlas is restricted by IP, allow this worker's
   outbound ranges as well. No separate Redis service is needed for the
   existing MongoDB queue.
5. Check worker logs, then run `python manage.py check_delivery_setup` from an
   available Render shell for the same environment. Expect a recent heartbeat.
   Stop a local worker if it is pointed at the same hosted database while
   verifying Render. Send one document email and check its delivery log.

Forgot Password sends email directly from the Django backend. Verify
EMAIL_MODE=production, SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD,
DEFAULT_FROM_EMAIL, the appropriate TLS/SSL settings, and FRONTEND_BASE_URL on
the **backend** too. Render free web services block outbound SMTP ports 25,
465, and 587. A worker does not remove that restriction from the web service.
Test Forgot Password separately with your own account.

## Access and smoke tests

- Existing sessions will need to sign in again after deployment. One web
  session and one Android APK session can coexist per user. A new sign-in
  replaces the older session for that platform; tabs sharing the same browser
  session do not count separately.
- For Android notifications, use **My profile → Device notifications** and
  allow the prompt. If Android previously blocked it, use **Android Settings →
  Apps → NexEase → Notifications**. Background push requires the existing
  Firebase setup. Role permissions and subscription access remain server-side.
- To verify: sign in in two separate browsers, then on Android. The second
  browser should replace the first; Android and the second browser should
  remain signed in. Mark a notification read and confirm the badge decreases.
