# Combined release validation

- Clean npm ci: passed from the combined manifest and lockfile.
- Frontend unit/component tests: 137 passed across 21 files, including the native API transport suite that previously could not resolve @capacitor/core.
- Mobile static export: passed (73 routes; no signed native binary produced).
- Web production build: passed (Next.js 16.4.3).
- Next.js version: 16.4.3; Vitest: 4.1.12; Zod: 4.6.6 or newer within the locked release.
- The earlier web/UI backend validation remains 161 isolated upgrade tests plus 883 existing tests. This merge does not change backend behavior from that validated release.
- Native HTTP transport retains Origin, Referer and CSRF headers. Browser requests retain browser fetch.
- Tests no longer emit the Vite CommonJS-config warning or sales-order React act warnings seen in the attached log.

## Dependency findings
Next.js and affected compatible dependencies were updated. The latest audit before final packaging reports zero high and zero critical vulnerabilities. 21 moderate development-tool findings remain in dependency chains involving ESLint glob matching and Capacitor CLI/Xcode utilities. The deprecated ESLint 9 and transitive uuid notices are not hidden: ESLint 9 is retained for compatibility with the React lint plugin. Do not use npm audit fix --force to downgrade Capacitor or other tools; suggested forced fixes can break this project.

Full current audit details are included in DEPENDENCY_AUDIT.json. npm audit may still exit non-zero for the documented moderate findings. A passing build is not a claim that every dependency is vulnerability-free.

## Scope
Web and mobile static exports are checked separately. Signed APK/iOS compilation, device login, physical camera/scanner operation and final visual acceptance must still be tested on the target devices. The build environment could not launch Chromium for screenshots. No production deployment or database reset was performed.
