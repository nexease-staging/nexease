import { describe, expect, it } from "vitest";
import { isBillOverdue } from "./status";

const bill = (over = {}) => ({ status: "POSTED" as const, due_date: "2026-11-20", balance_due: "500.00", ...over });

describe("isBillOverdue", () => {
  it("flags an unpaid posted bill past its due date", () => expect(isBillOverdue(bill(), "2026-11-26")).toBe(true));
  it("is not overdue on the due date", () => expect(isBillOverdue(bill(), "2026-11-20")).toBe(false));
  it("ignores paid, draft and fully settled bills", () => {
    expect(isBillOverdue(bill({ status: "PAID" }), "2026-11-26")).toBe(false);
    expect(isBillOverdue(bill({ status: "DRAFT" }), "2026-11-26")).toBe(false);
    expect(isBillOverdue(bill({ balance_due: "0.00" }), "2026-11-26")).toBe(false);
  });
  it("needs a due date", () => expect(isBillOverdue(bill({ due_date: null }), "2026-11-26")).toBe(false));
});
