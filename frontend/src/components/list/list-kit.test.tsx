import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { Download, Plus } from "lucide-react";
import { CompactList, CompactRow, ListScreen, ListState, Pager } from "./list-kit";

describe("list kit", () => {
  it("opens a row without triggering it from a row action", () => {
    const open = vi.fn();
    const download = vi.fn();
    render(
      <CompactList label="Invoices" columns={[{ label: "Customer" }, { label: "Total" }]}>
        <CompactRow title="Sharma Traders" subtitle="INV-1 · 26 Nov" amount="₹1,180.00" onOpen={open} openLabel="View INV-1" actions={[{ icon: Download, label: "Download PDF INV-1", onClick: download }]} />
      </CompactList>,
    );
    fireEvent.click(screen.getByRole("button", { name: "Download PDF INV-1" }));
    expect(download).toHaveBeenCalledTimes(1);
    expect(open).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "View INV-1" }));
    expect(open).toHaveBeenCalledTimes(1);
  });

  it("renders the primary action in the header and in the mobile action bar", () => {
    const create = vi.fn();
    render(<ListScreen title="Invoices" primary={{ label: "New invoice", icon: Plus, onClick: create }}><p>rows</p></ListScreen>);
    const buttons = screen.getAllByRole("button", { name: "New invoice" });
    expect(buttons).toHaveLength(2);
    expect(screen.getByRole("toolbar", { name: "Invoices actions" })).toContainElement(buttons[1]);
    fireEvent.click(buttons[1]);
    expect(create).toHaveBeenCalled();
  });

  it("shows error with retry, then empty state", () => {
    const retry = vi.fn();
    const { rerender } = render(<ListState loading={false} error={new Error("Network down")} onRetry={retry} isEmpty emptyIcon={Plus} emptyTitle="None"><p>rows</p></ListState>);
    expect(screen.getByRole("alert")).toHaveTextContent("Network down");
    fireEvent.click(screen.getByRole("button", { name: "Retry" }));
    expect(retry).toHaveBeenCalled();
    rerender(<ListState loading={false} isEmpty emptyIcon={Plus} emptyTitle="No invoices yet"><p>rows</p></ListState>);
    expect(screen.getByText("No invoices yet")).toBeInTheDocument();
  });

  it("pages forward and disables previous on the first page", () => {
    const onPage = vi.fn();
    render(<Pager noun="invoices" onPage={onPage} pagination={{ page: 1, total_pages: 3, total_items: 60, has_next: true, has_previous: false }} />);
    expect(screen.getByText(/60 invoices · page 1 of 3/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Previous page" })).toBeDisabled();
    fireEvent.click(screen.getByRole("button", { name: "Next page" }));
    expect(onPage).toHaveBeenCalledWith(2);
  });
});
