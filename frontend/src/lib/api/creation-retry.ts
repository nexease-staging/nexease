// Opaque retry identity only; invoice/customer details are never written to storage.
export async function creationRetryKey(path: string, body: unknown, numbering: string | null) {
  const encoded = new TextEncoder().encode(JSON.stringify({ path, body, numbering }));
  const digest = await crypto.subtle.digest("SHA-256", encoded);
  const hash = Array.from(new Uint8Array(digest), b => b.toString(16).padStart(2, "0")).join("");
  const storageKey = `nexease-invoice-request:${hash}`;
  let key = localStorage.getItem(storageKey);
  if (!key) {
    key = crypto.randomUUID();
    localStorage.setItem(storageKey, key);
  }
  return { key, complete: () => localStorage.removeItem(storageKey) };
}
