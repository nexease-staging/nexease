import { describe, expect, it } from "vitest";
import { applyAnswer, customerPrefill, invoicePrefill, paymentPrefill, purchasePrefill, recordPrefill, type Entry } from "./forms";

const entry = (kind: string, fields: Record<string, string>, items: Record<string, string>[] = []): Entry => ({ kind, fields, items, questions: [], warnings: [] });

describe("NexEase AI form mapping", () => {
  it("fills an invoice with customer, lines and billing details, leaving blanks to form defaults", () => {
    const p = invoicePrefill(entry("invoice", { party_name: "Sharma Traders", party_gstin: "27ABCDE1234F1Z5", date: "2026-11-20", po_number: "PO-7", supply_type: "taxable", notes: "" }, [{ name: "Cement", quantity: "10", unit_price: "380", tax_rate: "18", unit: "", sku: "" }, { name: "", sku: "" }]));
    expect(p.customer).toEqual({ name: "Sharma Traders", gstin: "27ABCDE1234F1Z5" });
    expect(p.items).toEqual([{ name: "Cement", quantity: "10", unit_price: "380", tax_rate: "18" }]);
    expect(p.date).toBe("2026-11-20");
    expect(p.notes).toBeUndefined();
    expect(p.supply).toBe("taxable");
    expect(p.details).toEqual({ po_number: "PO-7" });
  });

  it("applies a quick answer to a line, creating it when the AI had none", () => {
    const e = entry("invoice", { party_name: "A" });
    const next = applyAnswer(e, "items.0.name", "Helmet");
    expect(next.items[0].name).toBe("Helmet");
    expect(e.items).toHaveLength(0);
    expect(applyAnswer(next, "items.0.unit_price", "500").items[0]).toMatchObject({ name: "Helmet", unit_price: "500" });
  });

  it("keeps customer name and party name in step", () => {
    expect(applyAnswer(entry("customer", {}), "name", "Mehta").fields).toMatchObject({ name: "Mehta", party_name: "Mehta" });
    expect(customerPrefill(entry("customer", { name: "Mehta", phone: "9876543210", party_address: "Pune" }))).toEqual({ name: "Mehta", phone: "9876543210", billing_address: "Pune" });
  });

  it("maps payment modes to the payment screen's methods", () => {
    expect(paymentPrefill(entry("payment_in", { amount: "5000", payment_mode: "Bank transfer", date: "2026-11-26" }))).toEqual({ amount: "5000", method: "BANK_TRANSFER", date: "2026-11-26" });
    expect(paymentPrefill(entry("payment_in", { amount: "1", payment_mode: "" })).method).toBeUndefined();
  });

  it("sends expense payee and today's date to the record form", () => {
    const d = recordPrefill(entry("expense", { party_name: "HP pump", amount: "500", payment_mode: "Card", category: "Petrol / fuel" }), "expenses");
    expect(d).toMatchObject({ payee: "HP pump", amount: "500", payment_mode: "Debit card", description: "Petrol / fuel" });
    expect(d.date).toMatch(/^\d{4}-\d{2}-\d{2}$/);
    expect(recordPrefill(entry("expense", { amount: "1" }), "expenses", "665f1c2ab4e8a90012345678").reference).toBe("AI-12345678");
  });

  it("purchase header always has a date", () => {
    expect(purchasePrefill(entry("bill", { party_name: "Om Steel" })).header?.date).toMatch(/^\d{4}-/);
  });
});
