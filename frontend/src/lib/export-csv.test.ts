import { describe, expect, it } from "vitest";
import { toCsv } from "./export-csv";

describe("toCsv", () => {
  it("quotes commas, quotes and newlines and starts with a BOM for Excel", () => {
    const csv = toCsv([{ a: 'Sharma, "Bros"', b: "line1\nline2" }], [
      { header: "Name", value: (r) => r.a },
      { header: "Note", value: (r) => r.b },
    ]);
    expect(csv.startsWith("﻿")).toBe(true);
    expect(csv.slice(1).split("\r\n")[1]).toBe('"Sharma, ""Bros""","line1\nline2"');
  });
  it("neutralises text that a spreadsheet would run as a formula, but keeps numbers", () => {
    const csv = toCsv([{ t: "=HYPERLINK(\"x\")", n: -5 }], [
      { header: "T", value: (r) => r.t },
      { header: "N", value: (r) => r.n },
    ]);
    expect(csv.split("\r\n")[1]).toBe(`"'=HYPERLINK(""x"")",-5`);
  });
  it("writes empty cells for missing values", () => {
    expect(toCsv([{}], [{ header: "X", value: () => null }]).split("\r\n")[1]).toBe("");
  });
});
