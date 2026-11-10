import { afterEach, describe, expect, it, vi } from "vitest";
import { webcrypto } from "node:crypto";
import { paymentRetryKey } from "./retry-key";

afterEach(() => { localStorage.clear(); vi.unstubAllGlobals(); vi.restoreAllMocks(); });
describe("payment retry identity", () => {
  it("retains the key after an uncertain response and removes it only on success", async () => {
    vi.stubGlobal("crypto", webcrypto);
    const input = { amount: "40", bank_account_id: "bank-1" };
    const first = await paymentRetryKey("invoice-1", input);
    const retry = await paymentRetryKey("invoice-1", input);
    expect(retry.requestKey).toBe(first.requestKey);
    retry.complete();
    expect((await paymentRetryKey("invoice-1", input)).requestKey).not.toBe(first.requestKey);
  });
  it("separates documents and payloads without storing payment details", async () => {
    vi.stubGlobal("crypto", webcrypto);
    const first = await paymentRetryKey("invoice-1", { amount: "40", notes: "private note" });
    const second = await paymentRetryKey("invoice-2", { amount: "40", notes: "private note" });
    const changed = await paymentRetryKey("invoice-1", { amount: "41", notes: "private note" });
    expect(new Set([first.requestKey, second.requestKey, changed.requestKey]).size).toBe(3);
    expect(JSON.stringify(localStorage)).not.toContain("private note");
  });
  it("fails before submission when durable browser storage is unavailable", async () => {
    vi.stubGlobal("crypto", webcrypto);
    vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => { throw new Error("Storage blocked"); });
    await expect(paymentRetryKey("invoice-1", { amount: "40" })).rejects.toThrow("Storage blocked");
  });
});
