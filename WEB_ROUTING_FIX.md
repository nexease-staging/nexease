# Web login and Workforce navigation fix

Browser login now opens /dashboard. Native Capacitor app login continues to open /home.
Workforce navigation groups are merged after module and permission filtering, preserving unique feature links and a single Workforce section.

Apply: stop the frontend, copy the frontend folder from this archive over the existing frontend folder (keep your .env.local), then restart START_LOCAL_FRONTEND.cmd. No database upgrade or dependency reinstall is required for this fix.
Production: rebuild and redeploy the frontend. Existing native apps retain their current routing; rebuild them to receive the duplicate navigation fix.

Validation: 140 frontend tests passed across 22 files; TypeScript check passed.
