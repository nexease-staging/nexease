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

import { hsnProblem, saleProblem } from "./direct-invoice-rules";

describe("saleProblem GST rules", () => {
  const ctx = { invoiceDate: "2026-11-26", dueDate: "", placeOfSupply: "27" };
  const item = (over = {}) => ({ sku: "", name: "Rice", quantity: "1", unit_price: "60", tax_rate: "0", item_type: "goods", hsn_code: "", ...over });

  it("requires HSN/SAC on taxable sales and points at the line", () => {
    expect(saleProblem([item({ tax_rate: "5" })], { ...ctx, supply: "taxable" })).toMatchObject({ line: 0, field: "hsn_code" });
  });
  it.each(["exempt", "nil_rated", "non_gst", "unregistered"])("lets %s sales leave HSN/SAC blank", (supply) => {
    expect(saleProblem([item()], { ...ctx, supply })).toBeNull();
  });
  it("still rejects a malformed code on non-taxable sales", () => {
    expect(saleProblem([item({ hsn_code: "123" })], { ...ctx, supply: "exempt" })?.message).toMatch(/4, 6 or 8 digits/);
  });
  it("rejects GST on a non-taxable sale, like the server", () => {
    expect(saleProblem([item({ tax_rate: "18", hsn_code: "1006" })], { ...ctx, supply: "exempt" })).toMatchObject({ field: "tax_rate" });
  });
  it("needs place of supply except for unregistered sellers", () => {
    expect(saleProblem([item()], { ...ctx, placeOfSupply: "", supply: "exempt" })).toMatchObject({ field: "place_of_supply" });
    expect(saleProblem([item()], { ...ctx, placeOfSupply: "", supply: "unregistered" })).toBeNull();
  });
  it("skips GST rules for quotations", () => {
    expect(saleProblem([item({ tax_rate: "18" })], { ...ctx, supply: "exempt", quotation: true })).toBeNull();
  });
  it("requires a 6-digit SAC for services", () => {
    expect(hsnProblem("9985", "service", "taxable")).toMatch(/6-digit SAC/);
    expect(hsnProblem("998519", "service", "taxable")).toBe("");
  });
});
