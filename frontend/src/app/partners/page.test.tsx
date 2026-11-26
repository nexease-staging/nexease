import { render, screen, fireEvent, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import Partners from "./page";
import { estimate, perClient } from "@/features/partners/earnings";

const request = vi.hoisted(() => vi.fn());
vi.mock("@/lib/api/client", () => ({ apiRequest: request, apiBinaryRequest: vi.fn() }));
vi.mock("next/link", () => ({ default: ({ children, href, className }: { children: React.ReactNode; href: string; className?: string }) => <a href={href} className={className}>{children}</a> }));

const approved = { name: "CA Meera Joshi", email: "meera@ca.in", status: "approved", email_verified: true, referral_code: "abc", short_code: "NX7K4P2Q" };

describe("Partner portal", () => {
  beforeEach(() => request.mockReset());

  it("shows rates and the application form without implying approval", async () => {
    request.mockResolvedValue({ data: { partner: null } });
    render(<Partners />);
    fireEvent.click(await screen.findByRole("button", { name: "New here? Apply to become a partner" }));
    expect(screen.getByRole("heading", { name: "Apply to become a partner" })).toBeInTheDocument();
    expect(screen.getByLabelText("Full name")).toBeInTheDocument();
    expect(screen.getByText("20%")).toBeInTheDocument();
    expect(screen.getByRole("region", { name: "Earnings calculator" })).toBeInTheDocument();
  });

  it("keeps pending applicants out of statements and shows their progress", async () => {
    request.mockResolvedValue({ data: { partner: { name: "P", email: "p@example.com", status: "pending", email_verified: true } } });
    render(<Partners />);
    const status = await screen.findByRole("region", { name: "Application status" });
    expect(within(status).getByText("Email verified")).toBeInTheDocument();
    expect(request).toHaveBeenCalledTimes(1); // no dashboard call
    expect(screen.queryByRole("button", { name: "Download statement CSV" })).not.toBeInTheDocument();
  });

  it("shows the short code, referred businesses and GST holds without inventing earnings", async () => {
    request.mockImplementation((path?: string) => Promise.resolve({ data: String(path ?? "").includes("session") ? { partner: approved } : {
      partner: approved, entries: [{ payment_id: "pay1", paid_at: 1764000000, percent: 20, amount_paise: null, status: "tax_review_required" }],
      totals: { review_paise: 0, held: 1 }, total: 1, referral_total: 1, paid_total: 1,
      referrals: [{ reference: "o1", business: "Sharma Traders", date: "2026-11-20T10:00:00", plan: "NexEase Plus", status: "Paid" }],
    } }));
    render(<Partners />);
    const share = await screen.findByRole("region", { name: "Your referral code" });
    expect(within(share).getByText("NX7K4P2Q")).toBeInTheDocument();
    const wa = within(share).getByRole("link", { name: /Share on WhatsApp/ });
    expect(decodeURIComponent(wa.getAttribute("href") ?? "")).toContain("/signup?ref=NX7K4P2Q");
    expect(screen.getByText("Sharma Traders")).toBeInTheDocument();
    expect(screen.getByText("Held: GST check")).toBeInTheDocument();
    expect(screen.getByText("Held")).toBeInTheDocument();
    expect(screen.getByText("₹0.00")).toBeInTheDocument();
  });
});

describe("earnings maths", () => {
  it("pays on the price excluding GST: 20% first payment, 10% renewals", () => {
    expect(Math.round(perClient(3499, "annual").firstYear)).toBe(593); // 3499 / 1.18 × 20%
    expect(Math.round(perClient(3499, "annual").laterYear)).toBe(297);
    expect(Math.round(perClient(349, "monthly").firstYear)).toBe(384); // 20% + 11 × 10%
    expect(Math.round(estimate(20, "plus", "monthly").laterYear)).toBe(7098);
  });
});
