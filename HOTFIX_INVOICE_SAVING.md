# Invoice saving hotfix — 31 October 2026

The shared invoice form opens a native HTML dialog. The previous numbering confirmation used a normal positioned overlay, which appeared behind the native dialog and was not clickable. The API client waited for that confirmation, so the invoice stayed on Saving and the backend showed only GET /business/numbers/.

Numbering confirmation now uses its own native modal. Save continues the request; Cancel/Escape returns to the populated invoice form. Unmounting the prompt cancels the pending creation instead of leaving an unresolved promise. A late numbering response cannot overwrite a newer prompt or a manual choice.

## Apply only this hotfix to an already installed October operations update

1. Stop the frontend using Ctrl+C.
2. Extract the latest ZIP into a separate folder.
3. Copy `NexEase/frontend/src/features/business/numbering-ui.tsx` from the ZIP to `E:\NexEase\frontend\src\features\business\numbering-ui.tsx`, replacing that file.
4. Run `E:\NexEase\START_LOCAL_FRONTEND.cmd`.
5. Hard-refresh the browser. Check the invoice list before retrying the interrupted entry.
6. Click Save draft invoice. A visible Invoice number dialog should open above it. Choose Automatic or Manual, then Save with this numbering. The backend should now receive the invoice POST.

No database migration or dependency installation is required for this frontend-only hotfix. For a production frontend, rebuild and redeploy the frontend after copying the source.

Validation: all 114 frontend tests passed, including native-dialog opening above an existing modal, Escape cancellation, pending-request cleanup, direct and order invoice forms. Production build/TypeScript passed. Browser/device visual verification remains subject to the limitation described in VALIDATION_OCT31.md.
