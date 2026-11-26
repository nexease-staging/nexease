import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import ReportViewPage from "./page";

// During in-app navigation window.location still shows the previous page, so the id must
// come from Next's search params (this was the "Report not found" bug).
vi.mock("next/navigation", () => ({ useSearchParams: () => new URLSearchParams("id=sales%2Fitem") }));
vi.mock("next/dynamic", () => ({ default: () => ({ id }: { id: string }) => <p>viewer {id}</p> }));

describe("Report view page", () => {
  it("reads the report id from Next search params, not window.location", async () => {
    window.history.replaceState(null, "", "/reports");
    render(<ReportViewPage />);
    expect(await screen.findByText("viewer sales/item")).toBeInTheDocument();
  });
});
