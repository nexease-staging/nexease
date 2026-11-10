/** Consume Android Back before navigating away from an open overlay. */
export function dismissTopOverlay(): boolean {
  const dialogs = Array.from(document.querySelectorAll<HTMLDialogElement>('dialog[open]'));
  const dialog = dialogs.at(-1);
  if (dialog) {
    // Use cancel so busy/unsaved-change guards retain control of dismissal.
    const event = new Event('cancel', { cancelable: true });
    if (dialog.dispatchEvent(event)) dialog.close();
    return true;
  }
  const buttons = document.querySelectorAll<HTMLButtonElement>(
    '[aria-label="Close assistant"], [aria-label="Close navigation"], [role="dialog"] button[aria-label^="Close"]',
  );
  const closer = Array.from(buttons).reverse().find(button => {
    const rect = button.getBoundingClientRect();
    return rect.width > 0 && rect.height > 0 && rect.right > 0 && rect.left < window.innerWidth;
  });
  if (closer) { closer.click(); return true; }
  return false;
}
