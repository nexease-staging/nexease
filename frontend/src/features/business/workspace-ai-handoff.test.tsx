import { render, screen } from "@testing-library/react";
import { expect, it, vi } from "vitest";
import BusinessWorkspace from "./workspace";
import { stashRecordPrefill } from "@/features/ai/handoff";
vi.mock("@/lib/api/client", () => ({ apiRequest: vi.fn(() => new Promise(() => {})), apiBinaryRequest: vi.fn() }));
vi.mock("@/lib/browser/download", () => ({ downloadBlob: vi.fn() }));
vi.mock("./gst-lookup", () => ({ default: () => null }));
vi.mock("@/components/search-select", () => ({ default: () => null }));
vi.mock("@/features/auth/auth-context", () => ({ useAuth: () => ({ authentication: { role: { permissions: ["expenses.manage"] } } }) }));
const schemas = { expenses: { label: "Daily expenses", permission: "expenses", fields: { payee: { label: "Paid to", type: "text", required: true }, amount: { label: "Amount", type: "number", required: true }, payment_mode: { label: "Payment mode", type: "select", required: true, choices: ["Cash", "UPI"] } } } };
vi.mock("@tanstack/react-query", () => ({
  useQueryClient: () => ({ invalidateQueries: () => Promise.resolve() }),
  useQuery: ({ queryKey }: { queryKey: string[] }) => (queryKey[0] === "business-config" ? { data: { schemas } } : { data: { records: [], total: 0 } }),
}));

it("opens the new-record form with values handed over by NexEase AI", async () => {
  stashRecordPrefill({ kind: "expenses", data: { payee: "HP pump", amount: "500", payment_mode: "Cheque", unknown: "x" } });
  render(<BusinessWorkspace kinds={["expenses"]} title="Daily expenses" description="x" />);
  expect(await screen.findByDisplayValue("HP pump")).toBeInTheDocument();
  expect(screen.getByDisplayValue("500")).toBeInTheDocument();
  // A mode the form does not offer is dropped, so the form's own default is used.
  expect(screen.queryByDisplayValue("Cheque")).not.toBeInTheDocument();
  expect(sessionStorage.getItem("nexease:ai-prefill")).toBeNull();
});

it("ignores a hand-off meant for another screen", async () => {
  stashRecordPrefill({ kind: "advances", data: { amount: "1" } });
  render(<BusinessWorkspace kinds={["expenses"]} title="Daily expenses" description="x" />);
  await new Promise((r) => setTimeout(r, 20));
  expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  expect(sessionStorage.getItem("nexease:ai-prefill")).not.toBeNull();
});
