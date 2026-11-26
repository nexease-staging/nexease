"use client";

import { useState } from "react";
import { Building2, Globe2, Phone, RotateCcw, Save } from "lucide-react";
import { FieldHint, FormSection } from "@/components/form/form-sheet";
import EmptyState from "@/components/ui/empty-state";
import ScopeSettings from "@/features/business/scope-settings";
import { useAuth } from "@/features/auth/auth-context";
import { useOrganization, useUpdateOrganization } from "@/features/organizations/hooks";
import type { OrganizationDetail, UpdateOrganizationInput } from "@/features/organizations/types";
import { hasPermission } from "@/lib/authorization/permissions";

type Form = Required<UpdateOrganizationInput>;
const fromOrganization = (o: OrganizationDetail): Form => ({ name: o.name, email: o.email, phone: o.phone ?? "", address: o.address ?? "", country: o.country, currency: o.currency, timezone: o.timezone });
const normal = (f: Form): Form => ({ name: f.name.trim(), email: f.email.trim(), phone: f.phone.trim(), address: f.address.trim(), country: f.country.trim(), currency: f.currency.trim().toUpperCase(), timezone: f.timezone.trim() });
const TIMEZONES = ["Asia/Kolkata", "Asia/Dubai", "Asia/Singapore", "Europe/London", "America/New_York", "UTC"];

/** Business profile: the name, contact details and region printed on invoices, payslips and emails. */
export default function OrganizationPage() {
  const { authentication, refreshAuthentication } = useAuth();
  const canUpdate = hasPermission(authentication?.role.permissions ?? [], "organizations.update");
  const organization = useOrganization(Boolean(authentication));
  const update = useUpdateOrganization();
  const [override, setOverride] = useState<Form | null>(null);
  const [message, setMessage] = useState<{ tone: "ok" | "error"; text: string } | null>(null);

  if (!authentication) return null;
  if (!canUpdate) return <div className="nx-card"><EmptyState icon={Building2} title="Business profile unavailable" description="Your role does not include the organizations.update permission." /></div>;
  if (organization.isPending) return <div className="nx-skeleton h-64" aria-busy="true" aria-label="Loading business profile" />;
  if (organization.error || !organization.data) return <p role="alert" className="nxl-error">{organization.error?.message ?? "Could not load the business profile."}</p>;

  const saved = fromOrganization(organization.data);
  const form = override ?? saved;
  const changed = JSON.stringify(normal(form)) !== JSON.stringify(normal(saved));
  const set = (key: keyof Form, value: string) => { setOverride({ ...form, [key]: value }); setMessage(null); };
  const missing = (["name", "email"] as const).filter((k) => !form[k].trim());

  async function save(e: React.FormEvent) {
    e.preventDefault();
    if (missing.length) {
      setMessage({ tone: "error", text: "Business name and email are required." });
      return;
    }
    setMessage(null);
    try {
      const updated = await update.mutateAsync(normal(form));
      setOverride(fromOrganization(updated));
      await refreshAuthentication();
      setMessage({ tone: "ok", text: "Business profile saved." });
    } catch (error) {
      setMessage({ tone: "error", text: error instanceof Error ? error.message : "Could not save the business profile." });
    }
  }

  const field = (key: keyof Form, label: string, props: React.InputHTMLAttributes<HTMLInputElement> = {}) => (
    <label className="block">
      {label}
      <input className="nx-input" aria-label={label} value={form[key]} onChange={(e) => set(key, e.target.value)} {...props} />
    </label>
  );

  return (
    <div className="nxl-screen">
      <header className="nxl-header">
        <div className="min-w-0">
          <h1>Business profile</h1>
          <p className="nx-muted">Printed on invoices, payslips and emails. Keep it the same as your GST registration.</p>
        </div>
      </header>
      <form onSubmit={save} className="nxf-body nxs-org flex flex-col gap-3.5 !overflow-visible !p-0">
        <FormSection title="Business" icon={Building2}>
          <div className="nxf-grid">
            {field("name", "Business name *", { required: true, maxLength: 200, autoComplete: "organization" })}
            {field("email", "Business email *", { type: "email", required: true, autoComplete: "email" })}
          </div>
        </FormSection>
        <FormSection title="Contact" icon={Phone}>
          <div className="nxf-grid">
            {field("phone", "Phone", { type: "tel", inputMode: "tel", autoComplete: "tel" })}
            <label className="block md:col-span-2">
              Address
              <textarea className="nx-input" aria-label="Address" rows={3} value={form.address} onChange={(e) => set("address", e.target.value)} />
              <FieldHint>Street, city, state and PIN code, as on your GST certificate.</FieldHint>
            </label>
          </div>
        </FormSection>
        <FormSection title="Region" icon={Globe2}>
          <div className="nxf-grid">
            {field("country", "Country", { autoComplete: "country-name" })}
            {field("currency", "Currency", { maxLength: 3, placeholder: "INR" })}
            <label className="block">
              Time zone
              <input className="nx-input" aria-label="Time zone" list="nx-timezones" value={form.timezone} onChange={(e) => set("timezone", e.target.value)} />
              <datalist id="nx-timezones">{TIMEZONES.map((t) => <option key={t} value={t} />)}</datalist>
              <FieldHint>Dates and day-end totals follow this time zone.</FieldHint>
            </label>
          </div>
        </FormSection>
        {message ? <p role={message.tone === "error" ? "alert" : "status"} className={message.tone === "error" ? "nxf-error" : "nxs-ok"}>{message.text}</p> : null}
        <div className="nxs-org-actions">
          <button type="button" className="nx-button nx-secondary" disabled={!changed || update.isPending} onClick={() => { setOverride(null); setMessage(null); }}><RotateCcw size={16} aria-hidden="true" />Undo changes</button>
          <button type="submit" className="nx-button" disabled={!changed || update.isPending}><Save size={16} aria-hidden="true" />{update.isPending ? "Saving…" : "Save profile"}</button>
        </div>
      </form>
      <div className="mt-4"><ScopeSettings /></div>
    </div>
  );
}
