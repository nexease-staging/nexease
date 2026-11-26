import "@fontsource-variable/bricolage-grotesque";
import Link from "next/link";
import { ArrowUpRight, Check, Lock, MonitorSmartphone, Plug, RefreshCw, ShieldCheck, Smartphone, UserCheck } from "lucide-react";
import SiteFooter from "@/components/site-footer";
import ContactNexEase from "@/components/contact-nexease";
import Relay from "@/components/marketing/relay";
import SiteNav from "@/components/marketing/site-nav";
import { AndroidButton, ConnectorButton } from "@/components/marketing/download-buttons";
import Pricing from "@/features/saas/pricing";

const fromTally = ["Companies, groups and ledgers with balances, GSTIN and contacts", "Every voucher: sales, purchase, receipt, payment, journal, notes, orders", "Stock items, units, godowns and closing stock",
  "Debtors and creditors become your customers and suppliers", "Deletions and cancellations in Tally"];
const toTally = ["Invoices, purchase bills, credit and debit notes", "Receipts and payments, settled against bills", "Sales and purchase orders, expenses, journals",
  "New customers, suppliers and stock items", "Edits and cancellations, on the same Tally voucher"];

const areas: { name: string; items: [string, string][] }[] = [
  { name: "Tally on the go", items: [["Live dashboard", "Sales, purchases, receivables, payables, cash and bank, updated from Tally."], ["Party statements", "Running balance, pending bills and overdue days for any ledger."], ["Day book, registers, trial balance", "Read Tally reports on the phone, export to Excel."], ["Entries back into Tally", "Make an invoice or receipt in NexEase; it appears in Tally."]] },
  { name: "Sales and GST", items: [["Six invoice formats", "One choice applies to invoices, quotations, orders, notes and challans."], ["E-invoice and e-way bill", "Generate IRN and e-way bills from the invoice."], ["GST returns", "GSTR-1 and GSTR-3B workings, GSTR-2B matching and IMS actions."], ["Share on WhatsApp and email", "Send the PDF and a message; a live link always shows today's figures."]] },
  { name: "Stock and purchases", items: [["Inventory", "Warehouses, transfers, barcodes and stock movements."], ["Purchasing", "Purchase orders, goods receipts, bills and returns."], ["Manufacturing", "Production orders that move raw materials and finished stock together."], ["Bill scanning", "Turn a photo or PDF of a bill into a draft entry."]] },
  { name: "Money and people", items: [["Finance", "Profit and loss, balance sheet, cash flow, banking and ledgers."], ["Collections", "Outstanding by party with WhatsApp reminders and payments."], ["Workforce and payroll", "Attendance for staff and site workers, payroll and payslips."], ["Daily expenses", "Fuel, travel and utilities with payment modes and references."]] },
];

const faqs: [string, string][] = [
  ["Do I need to change anything in Tally?", "No add-on or TDL. Turn on Tally's connection port once (F1 → Settings → Connectivity → Client/Server, port 9000), install the connector on the same computer and enter the pairing code from NexEase."],
  ["How fresh is the data on my phone?", "The connector checks Tally every 30 seconds while Tally is open. Only what changed is sent, so a busy day syncs in seconds. If the computer is off, NexEase shows the last synced figures and catches up when Tally opens again."],
  ["Will entries made in NexEase create duplicates in Tally?", "No. Each entry carries its own ID, so editing it changes the same Tally voucher and cancelling it cancels that voucher. Data that came from Tally is never sent back."],
  ["Which ledgers do NexEase invoices post to?", "You choose the sales, purchase, GST, cash, bank and round-off ledgers once in NexEase → Tally → Settings. NexEase suggests them from your Tally chart of accounts."],
  ["Can my accountant still work in Tally?", "Yes. Tally stays your main books. NexEase reads from it and writes to it, so both of you see the same numbers."],
  ["Can I manage my own staff as well as site workers?", "Yes. Mark employees as in-house or assign site workers to customers. Attendance supports both."],
  ["Does NexEase file statutory returns automatically?", "Tax reports are preparation workpapers. Applicability, rates and filing need review before you file."],
];

export default function Home() {
  return (
    <main className="nx-marketing nxw min-h-screen">
      <SiteNav />

      <section className="nxw-hero">
        <div className="nxw-wrap nxw-hero-grid">
          <h1>Tally on your desk.<br />Your business in your pocket.</h1>
          <div className="nxw-hero-side">
            <p>NexEase keeps TallyPrime and your phone in sync, both ways. See outstanding, stock and every voucher live, send a ledger on WhatsApp from anywhere, and run billing, GST, inventory and payroll in the same place.</p>
            <div className="nxw-hero-cta">
              <ConnectorButton />
              <Link href="/signup" className="nxw-text-cta">Create your workspace first <ArrowUpRight size={17} /></Link>
            </div>
            <p className="nxw-fine">Free 14-day trial. The connector pairs with your NexEase workspace using a one-time code.</p>
          </div>
        </div>
        <div className="nxw-wrap"><Relay /></div>
      </section>

      <section className="nxw-facts" aria-label="At a glance">
        <div className="nxw-wrap nxw-facts-row">
          <p><b>30 s</b> between Tally and your phone</p>
          <p><b>2-way</b> sync, with no duplicate vouchers</p>
          <p><b>0</b> add-ons or TDL inside Tally</p>
          <p><b>13</b> kinds of entries written back to Tally</p>
        </div>
      </section>

      <section id="tally" className="nxw-section">
        <div className="nxw-wrap">
          <h2 className="nxw-h2">Connect Tally in three steps</h2>
          <p className="nxw-lead">The connector is a small Windows app that sits next to Tally. It only talks to Tally on that computer and to your NexEase workspace.</p>
          <ol className="nxw-steps">
            <li>
              <span className="nxw-step-n">1</span>
              <h3>Turn on Tally&apos;s port</h3>
              <p>In TallyPrime press F1 → Settings → Connectivity → Client/Server configuration. Set it to act as Both, ODBC Yes, port 9000.</p>
            </li>
            <li>
              <span className="nxw-step-n">2</span>
              <h3>Install the connector</h3>
              <p>Download it on the computer where Tally runs and open it. Tick “Start with Windows” so sync keeps running.</p>
              <ConnectorButton tone="light" />
            </li>
            <li>
              <span className="nxw-step-n">3</span>
              <h3>Pair and confirm ledgers</h3>
              <p>In NexEase open Finance → Tally sync, copy the pairing code into the connector, then confirm the suggested sales, GST and bank ledgers.</p>
            </li>
          </ol>

          <div className="nxw-sync">
            <div>
              <h3><RefreshCw size={18} />From Tally to NexEase</h3>
              <ul>{fromTally.map((x) => <li key={x}><Check size={16} />{x}</li>)}</ul>
            </div>
            <div>
              <h3><RefreshCw size={18} className="nxw-flip" />From NexEase to Tally</h3>
              <ul>{toTally.map((x) => <li key={x}><Check size={16} />{x}</li>)}</ul>
            </div>
          </div>
        </div>
      </section>

      <section id="features" className="nxw-section nxw-features">
        <div className="nxw-wrap">
          <h2 className="nxw-h2">Everything after the entry</h2>
          <p className="nxw-lead">Tally keeps the books. NexEase is where your team bills, collects, stocks, pays and shares — with the books always up to date.</p>
          <div className="nxw-areas">
            {areas.map((a) => (
              <section key={a.name} className="nxw-area">
                <h3>{a.name}</h3>
                <dl>{a.items.map(([t, d]) => <div key={t}><dt>{t}</dt><dd>{d}</dd></div>)}</dl>
              </section>
            ))}
          </div>
        </div>
      </section>

      <section id="mobile" className="nxw-section nxw-mobile">
        <div className="nxw-wrap nxw-mobile-grid">
          <div>
            <h2 className="nxw-h2">When a customer asks for their ledger, send it from your phone</h2>
            <p className="nxw-lead">Open the party, pick a period and tap WhatsApp. The PDF statement and a short message go together. It works away from the office, even when the Tally computer is off — the last synced figures are on your phone.</p>
            <ul className="nxw-ticks">
              <li><Check size={16} />Invoices, bills, receipts and statements as PDF on WhatsApp or email</li>
              <li><Check size={16} />Reminders for overdue bills with the amount and the bill list</li>
              <li><Check size={16} />Quick sale, receipt and payment entry; saved lists work offline</li>
              <li><Check size={16} />NexEase AI fills forms from a sentence or your voice</li>
            </ul>
            <div className="nxw-hero-cta"><AndroidButton /><Link href="/login" className="nxw-text-cta">Or open NexEase in your phone browser <ArrowUpRight size={17} /></Link></div>
          </div>
          <div className="nxw-share" aria-hidden="true">
            <div className="nxw-share-card">
              <b>Share statement · Krishna Hardware</b>
              <span className="nxw-share-period">This financial year</span>
              <span className="nxw-share-file">Statement-Krishna-Hardware.pdf</span>
              <p>Dear Krishna Hardware, please find your statement of account with Sharma Traders for 01 Apr 2026 to 27 Nov 2026. The balance due is ₹3,68,072.68.</p>
              <span className="nxw-share-btn">Send PDF on WhatsApp</span>
            </div>
          </div>
        </div>
      </section>

      <section className="nxw-section">
        <div className="nxw-wrap">
          <h2 className="nxw-h2">Your data stays under your control</h2>
          <div className="nxw-trust">
            <div><Lock size={22} /><h3>Encrypted in transit</h3><p>The connector and the app reach NexEase only over HTTPS. Nothing from Tally is stored on the connector computer.</p></div>
            <div><Plug size={22} /><h3>One-time pairing</h3><p>A code that works once and expires in 15 minutes links a computer to your workspace. Remove a computer and it stops at once.</p></div>
            <div><UserCheck size={22} /><h3>Roles and permissions</h3><p>Choose who sees finance, who can bill and who can change Tally settings. Actions are recorded.</p></div>
            <div><ShieldCheck size={22} /><h3>Links you can withdraw</h3><p>Shared document links expire after 30 days and can be withdrawn at any time.</p></div>
          </div>
        </div>
      </section>

      <section className="nxw-section">
        <div className="nxw-wrap">
          <div className="nxw-pro">
            <div>
              <h2>Tell it. Scan it. Review it.</h2>
              <p>NexEase Pro adds an entry assistant: describe an expense, invoice or supplier bill in your language, or upload a photo of a bill. NexEase prepares the fields; you review and confirm. Nothing is posted just because you upload a file.</p>
            </div>
            <div className="nxw-pro-side">
              <p><MonitorSmartphone size={18} />On desktop and phone</p>
              <p><Smartphone size={18} />Voice and photo input</p>
              <p><Check size={18} />Monthly AI and scan allowances in Pro</p>
            </div>
          </div>
        </div>
      </section>

      <section className="nxw-section">
        <div className="nxw-wrap">
          <h2 className="nxw-h2">Practical support for your next step</h2>
          <div className="nxw-services">{["Accounting and bookkeeping", "GST, ITR and TDS support", "Payroll support", "Finance automation and reporting", "Business registration support", "Software setup and Tally onboarding"].map((x) => <p key={x}><Check size={16} />{x}</p>)}</div>
          <p className="nxw-fine">Professional services are scoped and quoted separately from software subscriptions.</p>
          <div className="nxw-trial">
            <div><h3>Your first 14 days on NexEase Plus</h3><p>New workspaces get Plus from signup: Tally sync, inventory, workforce and reports. Then choose the plan that fits. AI is part of Pro.</p></div>
            <Link href="/signup" className="nxw-nav-start">Start your 14-day trial</Link>
          </div>
        </div>
      </section>

      <Pricing />
      <section className="nxw-wrap nxw-links">
        <Link className="nx-button" href="/pricing">All services and packages</Link>
        <a className="nx-button nx-secondary" href="/NexEase_Pricing.pdf" download>Download price list (PDF)</a>
        <Link className="nx-button nx-secondary" href="/deadlines">Compliance deadlines</Link>
        <Link className="nx-button nx-secondary" href="/partners">Become a partner</Link>
      </section>
      <ContactNexEase />

      <section id="questions" className="nxw-section nxw-faq">
        <div className="nxw-wrap nxw-narrow">
          <h2 className="nxw-h2">A few things worth knowing</h2>
          {faqs.map(([q, a]) => <details key={q}><summary>{q}</summary><p>{a}</p></details>)}
        </div>
      </section>

      <section className="nxw-final">
        <div className="nxw-wrap">
          <h2>Bring Tally to your phone today</h2>
          <p>Create a workspace, install the connector on the Tally computer, and your figures are on your phone in minutes.</p>
          <div className="nxw-final-cta"><ConnectorButton tone="light" /><AndroidButton tone="light" /><Link href="/signup" className="nxw-final-start">Create your workspace <ArrowUpRight size={18} /></Link></div>
          <p className="nxw-legal">Tally and TallyPrime are trademarks of Tally Solutions Pvt. Ltd. NexEase is not affiliated with Tally Solutions; the names are used only to describe compatibility.</p>
        </div>
      </section>
      <SiteFooter />
    </main>
  );
}
