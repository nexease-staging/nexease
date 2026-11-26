"use client";

import { useCallback, useEffect, useRef, useState, useSyncExternalStore } from "react";
import Link from "next/link";
import {
  BadgeIndianRupee, Building2, CheckCircle2, Circle, Clock, Copy, FileSpreadsheet, FileText, LogOut, MessageCircle,
  RefreshCw, Share2, ShieldCheck, Sparkles, Users,
} from "lucide-react";
import PasswordInput from "@/components/password-input";
import { ActionIcon, CompactList, CompactRow } from "@/components/list/list-kit";
import { Badge, type Tone } from "@/components/ui/badge";
import StatCard from "@/components/ui/stat-card";
import PartnerEmail from "@/features/saas/partner-email";
import { estimate, PLANS, rupees, type Billing } from "@/features/partners/earnings";
import { apiBinaryRequest, apiRequest } from "@/lib/api/client";

type Partner = { name: string; email: string; status: string; email_verified?: boolean; referral_code?: string; short_code?: string };
type Entry = { payment_id: string; paid_at: number; percent: number; amount_paise: number | null; recorded_payout_paise?: number; status: string };
type Referral = { reference: string; business: string; date: string; plan: string; status: string };
type Dashboard = { partner: Partner; entries: Entry[]; totals: { review_paise: number; held: number }; total: number; referral_total: number; paid_total?: number; referrals: Referral[] };

const paise = (v: number | null | undefined) => new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR" }).format((v ?? 0) / 100);
const day = (v: string | number) => new Date(typeof v === "number" ? v * 1000 : v).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" });
const subscribeLocation = () => () => {};
const hasEmailLink = () => new URLSearchParams(window.location.search).has("token");
const REFERRAL_TONE: Record<string, Tone> = { Paid: "success", Trial: "info", Free: "neutral", Inactive: "warning" };
const ENTRY_STATUS: Record<string, { label: string; tone: Tone }> = {
  review_required: { label: "In review", tone: "info" }, tax_review_required: { label: "Held: GST check", tone: "warning" },
  approved: { label: "Approved", tone: "success" }, paid: { label: "Paid", tone: "success" },
};

function Calculator() {
  const [clients, setClients] = useState(10);
  const [plan, setPlan] = useState("plus");
  const [billing, setBilling] = useState<Billing>("annual");
  const e = estimate(clients, plan, billing);
  return (
    <section className="nxp2-card" aria-label="Earnings calculator">
      <h2><Sparkles size={17} aria-hidden="true" />What you could earn</h2>
      <div className="nxp2-calc">
        <label>Businesses you refer<input className="nx-input" type="number" min={1} max={500} value={clients} onChange={(ev) => setClients(Math.max(1, Math.min(500, Number(ev.target.value) || 1)))} /></label>
        <label>Plan<select className="nx-input" value={plan} onChange={(ev) => setPlan(ev.target.value)}>{PLANS.map((p) => <option key={p.code} value={p.code}>{p.name} · ₹{p.monthly}/mo</option>)}</select></label>
        <div className="nxf-segment" role="group" aria-label="Billing">
          {(["annual", "monthly"] as const).map((b) => <button key={b} type="button" aria-pressed={billing === b} onClick={() => setBilling(b)}>{b === "annual" ? "Annual" : "Monthly"}</button>)}
        </div>
      </div>
      <div className="nxp2-calc-out">
        <div><span>First year</span><strong>{rupees(e.firstYear)}</strong></div>
        <div><span>Every year after</span><strong>{rupees(e.laterYear)}</strong></div>
      </div>
      <p className="nxp2-fine">Estimate: 20% of the first payment and 10% of every renewal, on the price excluding 18% GST, while the business stays subscribed. Actual commission follows verified payments.</p>
    </section>
  );
}

export default function PartnersPage() {
  const [partner, setPartner] = useState<Partner | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [register, setRegister] = useState(false);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [data, setData] = useState<Dashboard>();
  const [page, setPage] = useState(1);
  const [copied, setCopied] = useState("");
  const [verifiedNotice, setVerifiedNotice] = useState(false);
  const emailLink = useSyncExternalStore(subscribeLocation, hasEmailLink, () => false);
  const lock = useRef(false);
  const version = useRef(0);

  const load = useCallback(async () => {
    const current = ++version.current;
    try {
      const r = await apiRequest<{ partner: Partner | null }>("/saas/partners/session/");
      if (current !== version.current) return;
      setPartner(r.data.partner);
      if (r.data.partner?.status === "approved") {
        const d = await apiRequest<Dashboard>(`/saas/partners/dashboard/?page=${page}`);
        if (current !== version.current) return;
        setData(d.data);
        setPartner(d.data.partner);
      } else setData(undefined);
    } catch (e) {
      if (current === version.current) setMessage((e as Error).message);
    } finally {
      if (current === version.current) setLoading(false);
    }
  }, [page]);

  useEffect(() => {
    let active = true;
    void Promise.resolve().then(() => { if (active) void load(); });
    return () => { active = false; };
  }, [load]);

  async function submit(action: string) {
    if (lock.current) return;
    lock.current = true; setBusy(true); setMessage("");
    try {
      const r = await apiRequest<{ message?: string }>("/saas/partners/session/", { method: "POST", body: { action, name, email, password } });
      setPassword("");
      if (action === "register") setRegister(false);
      setMessage(action === "register" ? "Application submitted. Sign in with your partner email to verify it." : r.data.message || "");
      await load();
    } catch (e) {
      setMessage((e as Error).message);
    } finally {
      lock.current = false; setBusy(false);
    }
  }

  const code = partner?.short_code || partner?.referral_code || "";
  const link = typeof window === "undefined" || !code ? "" : `${window.location.origin}/signup?ref=${encodeURIComponent(code)}`;
  const shareText = `I use and recommend NexEase for GST billing, inventory, payments and payroll. Start free here: ${link}${partner?.short_code ? ` (referral code ${partner.short_code})` : ""}`;

  async function copy(value: string, what: string) {
    try {
      await navigator.clipboard.writeText(value);
      setCopied(what);
      setTimeout(() => setCopied(""), 1800);
    } catch {
      setMessage("Copy is blocked in this browser. Select the text and copy it.");
    }
  }

  async function download(format: "csv" | "pdf") {
    setBusy(true);
    try {
      const r = await apiBinaryRequest(`/saas/partners/statement/?format=${format}`);
      const url = URL.createObjectURL(r.blob);
      const a = document.createElement("a");
      a.href = url; a.download = `NexEase-partner-statement.${format}`; a.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch (e) {
      setMessage((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  const approved = partner?.status === "approved" && data;
  return (
    <main className="nxp2">
      <nav className="nxp2-top">
        <Link href="/" className="nxp2-brand">
          {/* eslint-disable-next-line @next/next/no-img-element -- plain img works in the static mobile export */}
          <img src="/nexease-brand-icon.png" alt="" width={28} height={28} />
          NexEase <span>Partners</span></Link>
        {partner ? <button type="button" className="nx-button nx-secondary nx-btn-sm" disabled={busy} onClick={() => void submit("logout")}><LogOut size={15} aria-hidden="true" />Sign out</button> : null}
      </nav>

      {!partner ? (
        <section className="nxp2-hero">
          <div>
            <p className="nxp2-kicker">NexEase Partner Program · for CAs, tax consultants and accountants</p>
            <h1>Help your clients move to simple GST billing. Earn on every subscription.</h1>
            <p>Your clients get billing, inventory, payments and payroll from ₹199 a month, with a free plan to start. You earn 20% of their first payment and 10% of every renewal.</p>
            <dl className="nxp2-rates">
              <div><dt>First payment</dt><dd>20%</dd></div>
              <div><dt>Every renewal</dt><dd>10%</dd></div>
              <div><dt>Plans from</dt><dd>₹199<small>/mo</small></dd></div>
            </dl>
            <ol className="nxp2-steps">
              {["Apply in a minute", "Verify your email", "We approve your account", "Share your code; earn as clients pay"].map((s, i) => <li key={s}><span>{i + 1}</span>{s}</li>)}
            </ol>
          </div>
          <form className="nxp2-card nxp2-form" onSubmit={(e) => { e.preventDefault(); void submit(register ? "register" : "login"); }}>
            <h2>{register ? "Apply to become a partner" : "Partner sign in"}</h2>
            {message ? <p role="status" className="nxp2-note">{message}</p> : null}
            {verifiedNotice ? <p role="status" className="nxp2-note">Email verified. We will review your application.</p> : null}
            {register ? <label>Full name<input className="nx-input" value={name} onChange={(e) => setName(e.target.value)} required maxLength={200} autoComplete="name" /></label> : null}
            <label>Email<input className="nx-input" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required maxLength={254} autoComplete="email" /></label>
            <label>Password<PasswordInput className="nx-input" value={password} onChange={(e) => setPassword(e.target.value)} required maxLength={128} autoComplete={register ? "new-password" : "current-password"} /></label>
            <button className="nx-button w-full justify-center" disabled={busy}>{busy ? "Please wait…" : register ? "Submit application" : "Sign in"}</button>
            <button type="button" className="nxp2-switch" onClick={() => { setRegister(!register); setMessage(""); }}>{register ? "Already a partner? Sign in" : "New here? Apply to become a partner"}</button>
          </form>
        </section>
      ) : null}

      {!partner && !loading ? <div className="nxp2-forgot">{emailLink ? <PartnerEmail onVerified={async () => { setVerifiedNotice(true); await load(); }} /> : <PartnerEmail />}</div> : null}
      {!partner ? <Calculator /> : null}

      {partner && !approved ? (
        <section className="nxp2-card nxp2-pending" aria-label="Application status">
          <h1>Hello {partner.name}</h1>
          <p>Your application is in progress. Here is where it stands.</p>
          <ol className="nxp2-timeline">
            <li data-done><CheckCircle2 size={18} aria-hidden="true" />Application received</li>
            <li data-done={partner.email_verified || undefined}>{partner.email_verified ? <CheckCircle2 size={18} aria-hidden="true" /> : <Circle size={18} aria-hidden="true" />}Email verified</li>
            <li>{<Clock size={18} aria-hidden="true" />}Approval by NexEase{partner.email_verified ? "" : " (after email verification)"}</li>
          </ol>
          {message ? <p role="status" className="nxp2-note">{message}</p> : null}
          <PartnerEmail email={partner.email} verified={partner.email_verified} approved={false} onVerified={async () => { setVerifiedNotice(true); await load(); }} />
          <button type="button" className="nx-button nx-secondary mt-3" onClick={() => void load()}><RefreshCw size={15} aria-hidden="true" />Check status</button>
        </section>
      ) : null}

      {approved ? (
        <>
          <header className="nxl-header nxp2-dash-head">
            <div className="min-w-0">
              <h1>Welcome, {partner.name}</h1>
              <p className="nx-muted">Share your code. When a business you refer pays for NexEase, your commission appears here.</p>
            </div>
            <div className="nxl-toolbar nxr-keep">
              <ActionIcon icon={FileSpreadsheet} label="Download statement CSV" onClick={() => void download("csv")} disabled={busy || !partner.email_verified} />
              <ActionIcon icon={FileText} label="Download statement PDF" onClick={() => void download("pdf")} disabled={busy || !partner.email_verified} />
              <ActionIcon icon={RefreshCw} label="Refresh" onClick={() => void load()} />
            </div>
          </header>
          {message ? <p role="status" className="nxp2-note">{message}</p> : null}

          <section className="nxp2-share" aria-label="Your referral code">
            <div>
              <span>Your referral code</span>
              <strong>{partner.short_code ?? "—"}</strong>
              <p>Clients enter it when they sign up, or use your link.</p>
            </div>
            <div className="nxp2-share-actions">
              <button type="button" className="nx-button nx-secondary" disabled={!partner.short_code} onClick={() => void copy(partner.short_code ?? "", "code")}><Copy size={15} aria-hidden="true" />{copied === "code" ? "Copied" : "Copy code"}</button>
              <button type="button" className="nx-button nx-secondary" disabled={!link} onClick={() => void copy(link, "link")}><Share2 size={15} aria-hidden="true" />{copied === "link" ? "Copied" : "Copy link"}</button>
              <a className="nx-button" href={`https://wa.me/?text=${encodeURIComponent(shareText)}`} target="_blank" rel="noopener noreferrer"><MessageCircle size={15} aria-hidden="true" />Share on WhatsApp</a>
            </div>
          </section>

          <div className="nx-kpi-strip mt-4" data-cols="4">
            <div><StatCard label="Businesses referred" icon={Building2} tone="info" value={String(data.referral_total)} hint="Signed up with your code" /></div>
            <div><StatCard label="Paying businesses" icon={Users} tone="success" value={String(data.paid_total ?? 0)} hint="Made at least one payment" /></div>
            <div><StatCard label="Commission" icon={BadgeIndianRupee} tone="violet" value={paise(data.totals.review_paise)} hint="Calculated so far" /></div>
            <div><StatCard label="Held for review" icon={ShieldCheck} tone={data.totals.held ? "warning" : "neutral"} value={String(data.totals.held)} hint="Waiting for GST check" /></div>
          </div>

          <div className="nxp2-grid">
            <section className="nxl-panel" aria-label="Referred businesses">
              <h2 className="nxw-panel-title px-4 pb-2 pt-3">Referred businesses</h2>
              {data.referrals.length ? (
                <CompactList label="Referred businesses" columns={[{ label: "Business" }, { label: "Plan" }, { label: "Status" }]}>
                  {data.referrals.map((r) => (
                    <CompactRow key={r.reference} title={r.business} subtitle={`${r.plan || "No plan"} · joined ${day(r.date)}`} meta={[r.plan || "—"]} badge={<Badge tone={REFERRAL_TONE[r.status] ?? "neutral"}>{r.status}</Badge>} />
                  ))}
                </CompactList>
              ) : (
                <p className="nxw-empty"><Share2 size={18} aria-hidden="true" />No businesses yet. Share your code with clients who issue GST invoices.</p>
              )}
            </section>
            <section className="nxl-panel" aria-label="Commission">
              <h2 className="nxw-panel-title px-4 pb-2 pt-3">Commission</h2>
              {data.entries.length ? (
                <CompactList label="Commission entries" columns={[{ label: "Payment" }, { label: "Rate" }, { label: "Commission" }]}>
                  {data.entries.map((e) => {
                    const s = ENTRY_STATUS[e.status] ?? { label: e.status.replaceAll("_", " "), tone: "neutral" as Tone };
                    return (
                      <CompactRow key={e.payment_id} title={day(e.paid_at)} subtitle={`${e.percent === 20 ? "First payment" : "Renewal"} · ${e.percent}%`} meta={[`${e.percent}%`]}
                        amount={e.amount_paise === null ? "Held" : paise(e.amount_paise)} amountHint={e.recorded_payout_paise ? `Paid out ${paise(e.recorded_payout_paise)}` : undefined}
                        badge={<Badge tone={s.tone}>{s.label}</Badge>} />
                    );
                  })}
                </CompactList>
              ) : (
                <p className="nxw-empty"><BadgeIndianRupee size={18} aria-hidden="true" />Commission appears after a referred business makes its first payment.</p>
              )}
              {data.total > 25 ? (
                <div className="nxl-pager"><span>Page {page}</span><span className="flex gap-2">
                  <button type="button" className="nx-button nx-secondary nx-btn-sm" disabled={page === 1} onClick={() => setPage(page - 1)}>Previous</button>
                  <button type="button" className="nx-button nx-secondary nx-btn-sm" disabled={page * 25 >= data.total} onClick={() => setPage(page + 1)}>Next</button>
                </span></div>
              ) : null}
            </section>
          </div>
          {!partner.email_verified ? <div className="mt-4"><PartnerEmail email={partner.email} verified={false} approved onVerified={load} /></div> : null}
          <Calculator />
        </>
      ) : null}
      <footer className="nxp2-foot">Questions? WhatsApp +91 92097 53378 · nexease.contact@gmail.com</footer>
    </main>
  );
}
