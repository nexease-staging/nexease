Latest mobile/web update (1 November 2026): read MOBILE_UPDATE_NOV01.md for the updated APK build, account menu, notification setup and device acceptance checks.

# Complete NexEase web + mobile source update

This package combines the Workforce/UI upgrade with the Easy Mobile integration. The prior package manifest replaced mobile dependencies while mobile source files stayed in your project. That mismatch caused `Cannot resolve @capacitor/core` in both transport tests and production builds.

## Apply on Windows
1. Stop the local servers and back up E:\NexEase.
2. Extract the ZIP. Copy the contents of its NexEase folder into E:\NexEase, replacing source files. Do not delete your existing project or environment files.
3. Use Node.js 22 or newer for the included Capacitor 8 tooling (validation used Node 24). Your existing `.env`, `frontend/.env.local`, `.venv`, `.git` and uploads stay in place. Neither `.env` nor `.env.local` is included anywhere in the ZIP. Dependency folders and generated builds are excluded too.
4. Run in PowerShell:

```powershell
Set-Location E:\NexEase
.\INSTALL_COMBINED_UPDATE.cmd
```

The script removes only the obsolete frontend/vitest.config.ts (replaced by vitest.config.mts), runs the permission upgrade and Django checks, installs the exact combined lockfile, runs frontend tests and creates a local web build. It does not change your environment files. The local API URL it sets lasts only inside the script; Render must retain its HTTPS backend URL.

5. Restart using START_LOCAL_BACKEND.cmd and START_LOCAL_FRONTEND.cmd. Sign out/in to reload permissions.

## Mobile
The Capacitor configuration, Android/iOS source projects, native HTTP transport (including Origin/Referer/CSRF), mobile connection screen, download/share helpers and mobile build scripts are included. Web dialogs, cost permission, invoice edit guards and barcode fallback are retained. The desktop navigation remains available, with mobile bottom navigation on smaller screens.

Rebuild mobile assets before syncing:

```powershell
Set-Location E:\NexEase\frontend
npm.cmd run mobile:build
npm.cmd run mobile:sync
```

Then use the included Android build launcher or native IDE. iOS compilation/signing requires macOS and Xcode. A passing web/static export does not certify a signed device application.

## Configuration
Keep the correct FRONTEND_ORIGINS, including the staging frontend and https://localhost for the native app, in your backend environment. Production CSRF uses this configured list. Never commit credentials. Deploy backend, frontend and worker from the same reviewed commit.

## Other fixes
- Capacitor dependencies and mobile scripts are merged with the barcode dependency, not substituted for them.
- The Vitest configuration uses ESM (.mts); tests wait for sales-order form initialization instead of emitting React act warnings.
- The resolver install script is narrowly permitted through package.json rather than allowing every dependency's script.
- UI_UPGRADE_OCT31.md explains the feature boundaries: issued invoice edits cover presentation/description fields; financial totals stay locked. Product cost visibility is separate from purchasing/ledger access.

See COMBINED_VALIDATION.md for actual validation results and remaining dependency findings.

The dependency lockfile explicitly resolves AJV 8 for the optional form-resolver peer alongside ESLint’s AJV 6. This fixes the clean-install lockfile mismatch without --force or --legacy-peer-deps.
