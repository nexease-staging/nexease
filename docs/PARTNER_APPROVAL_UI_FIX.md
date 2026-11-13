# Partner approval feedback fix
Approval failures were rendered outside the native modal, behind its backdrop. The dialog now shows the server error directly. Lists show email verification status; approval is disabled for unverified email with clear instructions. Success explains that the approved applicant is under the Approved filter and must sign in again.
Backend email verification, password/TOTP and audit checks are unchanged. No live partner was approved by this patch.
Validation: two UI regression tests, scoped ESLint and web production build/TypeScript passed.
