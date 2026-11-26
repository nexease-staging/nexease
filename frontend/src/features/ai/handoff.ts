/**
 * Hands a prefilled record from NexEase AI to the screen that owns its form.
 * The assistant stores the values, navigates to the screen, and the screen opens its
 * "New …" form with them. Values expire quickly so a stale hand-off never reopens.
 */
const KEY = "nexease:ai-prefill";
export const AI_PREFILL_EVENT = "nexease:ai-prefill";
const MAX_AGE_MS = 2 * 60_000;

export type RecordHandoff = { kind: string; data: Record<string, string | boolean> };

export function stashRecordPrefill(handoff: RecordHandoff) {
  try {
    sessionStorage.setItem(KEY, JSON.stringify({ ...handoff, at: Date.now() }));
  } catch {
    /* storage can be unavailable (private mode); the event below still reaches an open screen */
  }
  window.dispatchEvent(new CustomEvent(AI_PREFILL_EVENT));
}

/** Takes the pending hand-off if it belongs to one of these record kinds. */
export function takeRecordPrefill(kinds: string[]): RecordHandoff | null {
  let raw: string | null = null;
  try {
    raw = sessionStorage.getItem(KEY);
  } catch {
    return null;
  }
  if (!raw) return null;
  try {
    const value = JSON.parse(raw) as RecordHandoff & { at: number };
    if (Date.now() - value.at > MAX_AGE_MS) {
      sessionStorage.removeItem(KEY);
      return null;
    }
    if (!kinds.includes(value.kind)) return null;
    sessionStorage.removeItem(KEY);
    return { kind: value.kind, data: value.data ?? {} };
  } catch {
    sessionStorage.removeItem(KEY);
    return null;
  }
}
