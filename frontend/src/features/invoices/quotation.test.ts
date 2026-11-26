import { describe, expect, it } from "vitest";
import { quotationState, type Quotation } from "./quotation";

const q = (over: Partial<Quotation> = {}): Quotation => ({ number: "QT-1", customer: "A", date: "2026-11-01", valid_until: "2026-11-30", notes: "", total: "100", items: [], ...over });

describe("quotationState", () => {
  it("is open before the validity date", () => expect(quotationState(q(), "2026-11-26").label).toBe("Open"));
  it("is expired after the validity date", () => expect(quotationState(q(), "2026-12-01").label).toBe("Expired"));
  it("shows the converted document type", () => expect(quotationState(q({ conversion: { kind: "order", status: "done", id: "x", number: "SO-1" } }), "2026-12-01").label).toBe("Ordered"));
  it("shows conversions awaiting review", () => expect(quotationState(q({ conversion: { kind: "invoice", status: "pending" } })).label).toBe("Converting"));
});
