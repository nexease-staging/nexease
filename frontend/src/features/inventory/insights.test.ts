import { describe, expect, it } from "vitest";
import { groupBySupplier, type LowStockItem } from "./insights";
import { movementTypes } from "./movement-types";
import { reorderProblem } from "./components/reorder-sheet";

const item = (sku: string, supplier: string | null): LowStockItem => ({
  product_id: sku, sku, name: sku, unit: "BAG", cost_price: "100.00", on_hand: "2.00", reserved: "0.00", available: "2.00",
  reorder_level: "10.00", suggested_quantity: "18.00",
  supplier: supplier ? { id: supplier, code: supplier, name: supplier, last_rate: "95.00", last_po: "PO-1" } : null,
});

describe("groupBySupplier", () => {
  it("puts the supplier with most items first and items with no supplier last", () => {
    const groups = groupBySupplier([item("A", null), item("B", "OMC"), item("C", "OMC"), item("D", "SST")]);
    expect(groups.map((g) => g.supplier?.code ?? "none")).toEqual(["OMC", "SST", "none"]);
    expect(groups[0].items.map((i) => i.sku)).toEqual(["B", "C"]);
  });
});

describe("reorderProblem", () => {
  const line = (over = {}) => ({ item: item("CEM", "OMC"), quantity: "18", rate: "95", gst: "28", ...over });
  it("needs a supplier", () => expect(reorderProblem([line()], "")).toMatch(/supplier/));
  it("accepts a valid order", () => expect(reorderProblem([line()], "s1")).toBe(""));
  it("rejects zero or over-precise quantities, rates and bad GST", () => {
    expect(reorderProblem([line({ quantity: "0" })], "s1")).toMatch(/quantity/);
    expect(reorderProblem([line({ rate: "95.555" })], "s1")).toMatch(/rate/);
    expect(reorderProblem([line({ gst: "101" })], "s1")).toMatch(/GST/);
  });
});

describe("movementTypes", () => {
  it("marks stock-reducing movements as outgoing", () => {
    expect(movementTypes.STOCK_OUT.direction).toBe(-1);
    expect(movementTypes.TRANSFER_IN.direction).toBe(1);
    expect(movementTypes.RESERVATION.direction).toBe(0);
  });
});
