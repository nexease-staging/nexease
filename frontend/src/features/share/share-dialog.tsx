"use client";

import { useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Capacitor } from "@capacitor/core";
import { Filesystem, Directory } from "@capacitor/filesystem";
import { Share } from "@capacitor/share";
import { Check, Copy, Download, Eye, FileText, Link2, Loader2, Mail, MessageCircle, Send, Share2, X } from "lucide-react";
import { notify } from "@/components/nex-feedback";
import { downloadBlob } from "@/lib/browser/download";
import {
  STATEMENT_KINDS, fetchPdf, logShare, periods, prepare, revokeLink, sendEmail, waLink, waNumber, SHARE_EVENT, type Channel, type Prepared, type ShareTarget,
} from "./api";

async function blobToBase64(blob: Blob) {
  return await new Promise<string>((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result).split(",")[1]);
    reader.onerror = () => reject(new Error("Could not prepare the PDF."));
    reader.readAsDataURL(blob);
  });
}

/** Phone share sheet with the PDF attached (WhatsApp, Gmail, …). Returns false when this device cannot attach files. */
async function shareFile(blob: Blob, filename: string, text: string) {
  if (Capacitor.isNativePlatform()) {
    const path = `nexease-share/${Date.now()}-${filename.replace(/[^a-zA-Z0-9._-]/g, "_")}`;
    const file = await Filesystem.writeFile({ path, data: await blobToBase64(blob), directory: Directory.Cache, recursive: true });
    await Share.share({ title: filename, text, files: [file.uri], dialogTitle: "Send with WhatsApp or another app" });
    return true;
  }
  const file = new File([blob], filename, { type: "application/pdf" });
  const nav = navigator as Navigator & { canShare?: (d: ShareData) => boolean };
  if (typeof nav.share === "function" && nav.canShare?.({ files: [file] })) {
    try {
      await nav.share({ files: [file], text, title: filename });
    } catch (e) {
      if ((e as Error).name !== "AbortError") throw e;
    }
    return true;
  }
  return false;
}

function withLink(text: string, url: string | undefined, on: boolean) {
  return on && url ? `${text}\n\nView / download: ${url}` : text;
}

export function ShareDialog({ target, onClose }: { target: ShareTarget; onClose: () => void }) {
  const statement = STATEMENT_KINDS.includes(target.kind);
  const [period, setPeriod] = useState({ from: target.from ?? (statement ? periods()[0].from : undefined), to: target.to ?? (statement ? periods()[0].to : undefined) });
  const t: ShareTarget = useMemo(() => ({ ...target, ...period }), [target, period]);
  const q = useQuery({ queryKey: ["share", t.kind, t.id, t.side, t.from, t.to], queryFn: () => prepare(t) });
  const d = q.data;
  const [channel, setChannel] = useState<Channel>(target.channel ?? "whatsapp");
  const [phone, setPhone] = useState("");
  const [emails, setEmails] = useState("");
  const [cc, setCc] = useState("");
  const [waText, setWaText] = useState("");
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const [includeLink, setIncludeLink] = useState(true);
  const [emailLink, setEmailLink] = useState(false);
  const [attach, setAttach] = useState(true);
  const [busy, setBusy] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [sentTo, setSentTo] = useState<string | null>(null);
  const native = Capacitor.isNativePlatform();

  // Fill the form when the document is ready (and refresh the messages when the period changes).
  const [filledFor, setFilledFor] = useState<Prepared | null>(null);
  if (d && d !== filledFor) {
    setFilledFor(d);
    if (!filledFor) {
      setPhone(d.recipient.phone);
      setEmails(d.recipient.email);
    }
    setWaText(d.whatsapp);
    setSubject(d.subject);
    setBody(d.body);
  }

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  const message = withLink(waText, d?.link?.url, includeLink);

  async function pdfBlob() {
    const r = await fetchPdf(t);
    return r.blob;
  }

  async function run(name: string, fn: () => Promise<void>) {
    setBusy(name);
    try {
      await fn();
    } catch (e) {
      notify(e instanceof Error ? e.message : "Something went wrong.", "error");
    } finally {
      setBusy(null);
    }
  }

  const sendWhatsAppPdf = () => run("wa-pdf", async () => {
    if (!d) return;
    const shared = await shareFile(await pdfBlob(), d.filename, message);
    if (!shared) {
      window.open(waLink(phone, withLink(waText, d.link?.url, true)), "_blank", "noopener,noreferrer");
      notify("This browser can’t attach files, so WhatsApp opens with a link to the PDF instead.", "warning");
    }
    void logShare(t, "whatsapp", phone, d.number);
    setSentTo(`WhatsApp${phone ? ` · ${phone}` : ""}`);
  });

  const openChat = () => {
    if (!d) return;
    window.open(waLink(phone, withLink(waText, d.link?.url, true)), "_blank", "noopener,noreferrer");
    void logShare(t, "whatsapp", phone, d.number);
    setSentTo(`WhatsApp${phone ? ` · ${phone}` : ""}`);
  };

  const email = () => run("email", async () => {
    const r = await sendEmail(t, { recipients: emails, cc, subject, message: body, attach, link: emailLink });
    setSentTo(`Email · ${r.data.sent_to.join(", ")}`);
  });

  const copyLink = async () => {
    if (!d?.link) return;
    await navigator.clipboard?.writeText(d.link.url);
    setCopied(true);
    void logShare(t, "link", "", d.number);
    setTimeout(() => setCopied(false), 1800);
  };

  const download = () => run("download", async () => {
    if (!d) return;
    await downloadBlob(await pdfBlob(), d.filename);
  });

  const preview = () => run("preview", async () => {
    const url = URL.createObjectURL(await pdfBlob());
    window.open(url, "_blank", "noopener");
    setTimeout(() => URL.revokeObjectURL(url), 60_000);
  });

  const title = d ? (statement ? `Share statement · ${d.recipient.name}` : `Share ${d.label.toLowerCase()} ${d.number}`) : target.title ?? "Share";
  const validPhone = !!waNumber(phone);

  return (
    <div className="nxsh-backdrop" role="dialog" aria-modal="true" aria-label={title} onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="nxsh-sheet">
        <header>
          <div className="min-w-0"><strong>{title}</strong>{d?.recipient.name && !statement ? <span>{d.recipient.name}</span> : null}</div>
          <button type="button" className="nxsh-close" aria-label="Close" onClick={onClose}><X size={18} /></button>
        </header>
        {q.isPending ? <p className="nxsh-wait"><Loader2 size={18} className="animate-spin" />Preparing…</p> : q.error ? <p className="nxsh-error" role="alert">{(q.error as Error).message}</p> : d ? (
          <div className="nxsh-body">
            {statement ? (
              <div className="nxsh-periods">
                <div className="nxsh-chips" role="radiogroup" aria-label="Period">
                  {periods().map((p) => <button key={p.key} type="button" role="radio" aria-checked={period.from === p.from && period.to === p.to} onClick={() => setPeriod({ from: p.from, to: p.to })}>{p.label}</button>)}
                </div>
                <div className="nxsh-dates">
                  <label>From<input type="date" value={period.from ?? ""} onChange={(e) => e.target.value && setPeriod((p) => ({ ...p, from: e.target.value }))} /></label>
                  <label>To<input type="date" value={period.to ?? ""} onChange={(e) => e.target.value && setPeriod((p) => ({ ...p, to: e.target.value }))} /></label>
                </div>
                {typeof d.extra.balance === "number" ? <p className="nxsh-balance">Closing balance <strong>{new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR" }).format(Math.abs(d.extra.balance))}</strong> {d.extra.balance === 0 ? "· settled" : d.extra.side === "supplier" ? (d.extra.balance > 0 ? "· payable" : "· receivable") : d.extra.balance > 0 ? "· due from them" : "· in their credit"}</p> : null}
              </div>
            ) : null}

            <div className="nxsh-file">
              <FileText size={22} />
              <div className="min-w-0"><strong>{d.filename}</strong><span>PDF · always the latest figures</span></div>
              <button type="button" className="nxsh-icon" aria-label="Preview PDF" disabled={!!busy} onClick={preview}><Eye size={17} /></button>
              <button type="button" className="nxsh-icon" aria-label={native ? "Save or share PDF" : "Download PDF"} disabled={!!busy} onClick={download}>{native ? <Share2 size={17} /> : <Download size={17} />}</button>
            </div>

            <nav className="nxsh-tabs" role="tablist">
              {([["whatsapp", "WhatsApp", MessageCircle], ["email", "Email", Mail], ["link", "Link", Link2]] as const).map(([k, l, Icon]) => (
                <button key={k} type="button" role="tab" aria-selected={channel === k} onClick={() => setChannel(k)}><Icon size={16} />{l}</button>
              ))}
            </nav>

            {channel === "whatsapp" ? (
              <div className="nxsh-form">
                <label>WhatsApp number<input inputMode="tel" placeholder="Mobile number" value={phone} onChange={(e) => setPhone(e.target.value)} />{phone && !validPhone ? <em>Enter a 10-digit mobile number.</em> : null}</label>
                <label>Message<textarea rows={5} value={waText} onChange={(e) => setWaText(e.target.value)} /></label>
                <label className="nxsh-check"><input type="checkbox" checked={includeLink} onChange={(e) => setIncludeLink(e.target.checked)} />Add a link to the live PDF</label>
                <div className="nxsh-actions">
                  <button type="button" className="nx-button nxsh-wa" disabled={!!busy} onClick={sendWhatsAppPdf}>{busy === "wa-pdf" ? <Loader2 size={16} className="animate-spin" /> : <Share2 size={16} />}Send PDF on WhatsApp</button>
                  <button type="button" className="nx-button nx-secondary" disabled={!validPhone} onClick={openChat} title={validPhone ? undefined : "Add the number to open the chat directly"}><MessageCircle size={16} />Open chat{validPhone ? ` with ${phone}` : ""}</button>
                </div>
                <p className="nxsh-hint">{native ? "Pick WhatsApp in the share sheet, then the contact. The PDF and message go together." : "On a phone, the PDF is attached directly. On a computer, WhatsApp opens with the message and the link to the PDF."}</p>
              </div>
            ) : null}

            {channel === "email" ? (
              <div className="nxsh-form">
                <label>To<input type="email" multiple placeholder="name@example.com" value={emails} onChange={(e) => setEmails(e.target.value)} /></label>
                <label>Cc<input type="email" multiple placeholder="Optional" value={cc} onChange={(e) => setCc(e.target.value)} /></label>
                <label>Subject<input value={subject} onChange={(e) => setSubject(e.target.value)} /></label>
                <label>Message<textarea rows={8} value={body} onChange={(e) => setBody(e.target.value)} /></label>
                <div className="nxsh-row">
                  <label className="nxsh-check"><input type="checkbox" checked={attach} onChange={(e) => setAttach(e.target.checked)} />Attach PDF</label>
                  <label className="nxsh-check"><input type="checkbox" checked={emailLink} onChange={(e) => setEmailLink(e.target.checked)} />Add live link</label>
                </div>
                <div className="nxsh-actions"><button type="button" className="nx-button" disabled={!!busy || !emails.trim() || (!attach && !emailLink)} onClick={email}>{busy === "email" ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}Send email</button></div>
              </div>
            ) : null}

            {channel === "link" && d.link ? (
              <div className="nxsh-form">
                <p className="nxsh-hint">Anyone with this link can open the PDF — no login needed. It always shows the latest figures and works until {new Date(d.link.expires).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" })}.{d.link.views ? ` Opened ${d.link.views} time${d.link.views === 1 ? "" : "s"}.` : ""}</p>
                <div className="nxsh-link"><input readOnly value={d.link.url} aria-label="Share link" onFocus={(e) => e.target.select()} /><button type="button" className="nx-button nx-secondary" onClick={() => void copyLink()}>{copied ? <Check size={16} /> : <Copy size={16} />}{copied ? "Copied" : "Copy"}</button></div>
                <div className="nxsh-actions">
                  <button type="button" className="nxsh-text" onClick={() => run("revoke", async () => { await revokeLink(d.link!.token); await q.refetch(); })}>Withdraw this link</button>
                </div>
              </div>
            ) : null}

            {sentTo ? <p className="nxsh-ok"><Check size={16} />Shared · {sentTo}</p> : null}
            {d.history.length ? (
              <details className="nxsh-history"><summary>Shared {d.history.length === 5 ? "5+" : d.history.length} time{d.history.length === 1 ? "" : "s"} before</summary>
                <ul>{d.history.map((h, i) => <li key={i}><span>{h.channel === "email" ? "Email" : h.channel === "whatsapp" ? "WhatsApp" : h.channel === "link" ? "Link copied" : "Shared"}{h.recipients.length ? ` · ${h.recipients.join(", ")}` : ""}</span><time>{new Date(h.at).toLocaleString("en-IN", { day: "numeric", month: "short", hour: "numeric", minute: "2-digit" })}</time></li>)}</ul>
              </details>
            ) : null}
          </div>
        ) : null}
      </div>
    </div>
  );
}

/** Mounted once in the app shell. */
export default function ShareHost() {
  const [target, setTarget] = useState<(ShareTarget & { key: number }) | null>(null);
  useEffect(() => {
    const on = (e: Event) => setTarget({ ...(e as CustomEvent<ShareTarget>).detail, key: Date.now() });
    window.addEventListener(SHARE_EVENT, on);
    return () => window.removeEventListener(SHARE_EVENT, on);
  }, []);
  return target ? <ShareDialog key={target.key} target={target} onClose={() => setTarget(null)} /> : null;
}

