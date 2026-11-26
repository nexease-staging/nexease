import { describe, expect, it } from "vitest";
import { directInvoiceProblem } from "./direct-invoice-rules";

const line = (over: Partial<{ sku: string; name: string; quantity: string; unit_price: string }> = {}) => ({ sku: "", name: "Cement bag", quantity: "1", unit_price: "100", ...over });

describe("directInvoiceProblem", () => {
  it("accepts values the server accepts", () => {
    expect(directInvoiceProblem([line({ quantity: "2.5", unit_price: "84.75" })], "2026-11-26", "2026-12-10")).toBe("");
  });
  it("rejects a rate with more than two decimals before the server does", () => {
    expect(directInvoiceProblem([line({ unit_price: "84.746" })], "2026-11-26", "")).toMatch(/rate can have at most 2 decimal/);
  });
  it("rejects a quantity with more than two decimals", () => {
    expect(directInvoiceProblem([line({ quantity: "1.125" })], "2026-11-26", "")).toMatch(/quantity can have at most 2 decimal/);
  });
  it("flags the same catalogue item added twice, case-insensitively", () => {
    expect(directInvoiceProblem([line({ sku: "cem-01" }), line({ sku: "CEM-01" })], "2026-11-26", "")).toMatch(/added twice/);
  });
  it("allows several new items without a code", () => {
    expect(directInvoiceProblem([line(), line({ name: "Sand" })], "2026-11-26", "")).toBe("");
  });
  it("rejects a due date before the invoice date", () => {
    expect(directInvoiceProblem([line()], "2026-11-26", "2026-11-20")).toMatch(/Due date/);
  });
  it("ignores empty lines", () => {
    expect(directInvoiceProblem([line(), line({ name: "", unit_price: "1.999" })], "2026-11-26", "")).toBe("");
  });
});
