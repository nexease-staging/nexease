import { describe, expect, it } from "vitest";
import { whatsappNumber } from "./phone";

describe("whatsappNumber", () => {
  it("adds India's code to 10-digit numbers", () => expect(whatsappNumber("098765 43210")).toBe("919876543210"));
  it("keeps numbers that already have a country code", () => expect(whatsappNumber("+91 98765 43210")).toBe("919876543210"));
  it("returns null for incomplete numbers", () => expect(whatsappNumber("12345")).toBeNull());
  it("returns null for empty input", () => expect(whatsappNumber(null)).toBeNull());
});
