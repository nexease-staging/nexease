// Keep an uncertain request's key across modal close/reload. Never store payment details.
export async function paymentRetryKey(documentId: string, input: object) {
  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(JSON.stringify(input)));
  const hash = Array.from(new Uint8Array(digest), b => b.toString(16).padStart(2, "0")).join("");
  const storageKey = `nexease-payment:${documentId}:${hash}`;
  // Fail before sending if durable storage is unavailable: an unsafe retry is worse.
  let requestKey = localStorage.getItem(storageKey);
  if (!requestKey) {
    requestKey = crypto.randomUUID();
    localStorage.setItem(storageKey, requestKey);
  }
  return { requestKey, complete: () => localStorage.removeItem(storageKey) };
}
