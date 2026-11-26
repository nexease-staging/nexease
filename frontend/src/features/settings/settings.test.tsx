import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import SettingsHub from "./settings-hub";
import UsersPage from "@/app/(protected)/settings/users/page";
import OrganizationPage from "@/app/(protected)/settings/organization/page";
import { apiRequest } from "@/lib/api/client";

vi.mock("@/lib/api/client", () => ({ apiRequest: vi.fn() }));
vi.mock("next/link", () => ({ default: ({ href, children, ...rest }: { href: string; children: React.ReactNode }) => <a href={href} {...rest}>{children}</a> }));
vi.mock("@/components/theme-provider", () => ({ ThemeToggle: () => <button type="button">Switch to dark mode</button> }));
vi.mock("@/features/business/mailbox-settings", () => ({ default: () => <p>Mailbox</p> }));
vi.mock("@/features/business/scope-settings", () => ({ default: () => null }));
vi.mock("@/features/users/components/user-dialog", () => ({ default: ({ open, userId }: { open: boolean; userId: string | null }) => (open ? <div role="dialog">User {userId ?? "new"}</div> : null) }));
const confirm = vi.fn(async () => true);
vi.mock("@/components/nex-feedback", () => ({ confirmAction: (...args: unknown[]) => confirm(...(args as [])), notify: vi.fn() }));
const refreshAuthentication = vi.fn(async () => undefined);
let permissions: string[] = [];
vi.mock("@/features/auth/auth-context", () => ({
  useAuth: () => ({ authentication: { user: { id: "u1" }, organization: { name: "Demo Traders" }, role: { permissions } }, refreshAuthentication }),
}));

const wrap = (node: React.ReactNode) => render(<QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>{node}</QueryClientProvider>);

beforeEach(() => {
  vi.clearAllMocks();
  permissions = ["organizations.update", "users.read", "users.update", "users.activate", "users.deactivate", "users.create"];
});

describe("SettingsHub", () => {
  it("shows the setup checklist with what is left, and only permitted settings", async () => {
    vi.mocked(apiRequest).mockResolvedValue({ data: { done: 2, total: 4, percent: 50, items: [
      { key: "profile", title: "Business profile", description: "x", href: "/settings/organization", done: true },
      { key: "logo", title: "Logo on invoices", description: "Upload your logo", href: "/settings/invoices", done: false },
      { key: "team", title: "Invite your team", description: "y", href: "/settings/users", done: false },
      { key: "gst", title: "GST registration", description: "z", href: "/taxation", done: true },
    ] } } as never);
    wrap(<SettingsHub />);
    const setup = await screen.findByRole("region", { name: "Setup checklist" });
    expect(within(setup).getByText("2 of 4 done. Each step takes a minute or two.")).toBeInTheDocument();
    expect(within(setup).getByRole("link", { name: /Logo on invoices/ })).toHaveAttribute("href", "/settings/invoices");
    expect(within(setup).queryByText("GST registration")).not.toBeInTheDocument();
    fireEvent.click(within(setup).getByRole("button", { name: "Show 2 done" }));
    expect(within(setup).getByText("GST registration")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Users/ })).toHaveAttribute("href", "/settings/users");
    expect(screen.queryByRole("link", { name: /^Roles/ })).not.toBeInTheDocument(); // no roles.read
    fireEvent.change(screen.getByLabelText("Search settings"), { target: { value: "numbering" } });
    expect(screen.getByRole("link", { name: /Numbering/ })).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /Users/ })).not.toBeInTheDocument();
  });

  it("hides the checklist once everything is done", async () => {
    vi.mocked(apiRequest).mockResolvedValue({ data: { done: 1, total: 1, percent: 100, items: [{ key: "profile", title: "Business profile", description: "x", href: "/x", done: true }] } } as never);
    wrap(<SettingsHub />);
    await waitFor(() => expect(apiRequest).toHaveBeenCalled());
    expect(screen.queryByRole("region", { name: "Setup checklist" })).not.toBeInTheDocument();
  });
});

describe("UsersPage", () => {
  const user = (id: string, name: string, active: boolean) => ({ id, email: `${id}@x.in`, first_name: name.split(" ")[0], last_name: name.split(" ")[1] ?? "", full_name: name, is_active: active, role: { id: "r", name: "Accountant" } });
  it("lists users, protects your own access and turns others off after confirming", async () => {
    vi.mocked(apiRequest).mockImplementation(((path: string) => Promise.resolve(path.startsWith("/users/?")
      ? { data: { users: [user("u1", "Nikhil V", true), user("u2", "Asha Patil", true)], pagination: { page: 1, page_size: 25, total_items: 2, total_pages: 1, has_next: false, has_previous: false }, query: {} } }
      : { data: { user: user("u2", "Asha Patil", false) } })) as never);
    wrap(<UsersPage />);
    expect(await screen.findByText("Asha Patil")).toBeInTheDocument();
    expect(screen.getByText("You")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Turn off access for Nikhil V" })).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Turn off access for Asha Patil" }));
    await waitFor(() => expect(vi.mocked(apiRequest).mock.calls.some(([p]) => String(p).includes("u2") && String(p).includes("deactivate"))).toBe(true));
    expect(confirm).toHaveBeenCalledWith(expect.stringContaining("Turn off access for Asha Patil"));
    fireEvent.click(screen.getAllByRole("button", { name: "Invite user" })[0]);
    expect(screen.getByRole("dialog")).toHaveTextContent("User new");
  });
});

describe("OrganizationPage", () => {
  it("saves trimmed details and refreshes the signed-in session", async () => {
    const org = { id: "o1", name: "Demo Traders", email: "a@demo.in", phone: "", address: "", country: "India", currency: "INR", timezone: "Asia/Kolkata", is_active: true, created_at: null, updated_at: null };
    vi.mocked(apiRequest).mockImplementation(((path: string, options?: { method?: string; body?: object }) => Promise.resolve({ data: { organization: options?.method ? { ...org, ...options.body } : org } })) as never);
    wrap(<OrganizationPage />);
    const save = await screen.findByRole("button", { name: "Save profile" });
    expect(save).toBeDisabled();
    fireEvent.change(screen.getByLabelText("Phone"), { target: { value: " 9876543210 " } });
    fireEvent.change(screen.getByLabelText("Currency"), { target: { value: "inr" } });
    fireEvent.click(save);
    await waitFor(() => expect(refreshAuthentication).toHaveBeenCalled());
    const call = vi.mocked(apiRequest).mock.calls.find(([, o]) => (o as { method?: string } | undefined)?.method);
    expect((call![1] as { body: Record<string, string> }).body).toMatchObject({ phone: "9876543210", currency: "INR" });
    expect(await screen.findByRole("status")).toHaveTextContent("Business profile saved.");
  });
});
