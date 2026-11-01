# Android/iOS login CSRF hotfix — October 31

Observed error: `Referer checking failed - no Referer` on POST /api/v1/auth/login/ while GET /api/v1/auth/csrf/ succeeds.

The automatic Capacitor fetch patch constructs a browser Request before forwarding write requests. Origin is a browser-controlled header and may be removed there. API calls now use CapacitorHttp.request directly on native platforms, carrying explicit Origin https://localhost, Referer https://localhost/ and the CSRF token. CSRF bootstrap and API calls share the native transport. Web browsers retain normal fetch behavior. No CSRF exemption or server-side bypass was added.

## Install this update
1. Close build tools using the previous mobile folder.
2. Extract this updated ZIP into a NEW folder, or copy only the updated frontend/src/lib/api/transport.ts, frontend/src/lib/api/client.ts and frontend/src/components/mobile/mobile-gate.tsx into the matching paths in your current mobile project. Copying all three files is required.
3. Open PowerShell in the NexEase folder and run:

    $env:JAVA_HOME = "C:\Program Files\Eclipse Adoptium\jdk-21.0.12.101-hotspot"
    $env:Path = "$env:JAVA_HOME\bin;$env:Path"
    .\BUILD_ANDROID.cmd

4. Install the newly generated app-debug.apk on your phone over the existing app using the same signing key. Reopen and retry login.
5. Keep NEXEASE_MOBILE_ENABLED=true in Render and use this package's mobile-compatible backend settings. They append https://localhost to CSRF_TRUSTED_ORIGINS. If the previous mobile backend settings are already deployed, this client hotfix requires no further Django code change.

If login still fails, send the new CSRF log reason. A subsequent untrusted-origin or missing-cookie error is distinct from the missing-Referer failure and must be investigated separately. Do not disable CSRF.

Validation: 132 frontend tests pass, including 8 new native-transport tests for headers, CSRF bootstrap, JSON error preservation, multipart file/text uploads, binary responses, no-content responses, browser behavior and HTTPS enforcement. Mobile export and native-project synchronization are verified separately. Physical-device login/session continuity still requires testing on your device; mocked transport tests do not establish real-device success.
