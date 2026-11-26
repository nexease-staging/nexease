"use client";

import { useMemo, useRef, useState } from "react";
import { CheckCircle2, Circle, ListChecks, Wallet } from "lucide-react";
import SearchSelect from "@/components/search-select";
import { FieldHint, FormActions, FormSection, FormSheet } from "@/components/form/form-sheet";
import { useInvoiceBankAccounts } from "@/features/invoices/hooks";
import { useVendorBillBankAccounts } from "@/features/vendor-bills/hooks";
import { formatDate, formatMoney } from "@/lib/format";
import { METHODS, useOutstanding, usePartyOutstanding, useSettle, type Side, type SettleInput } from "../api";
import { autoAllocate, newRequestKey } from "../reminder";

const today = () => new Date(Date.now() + 330 * 60_000).toISOString().slice(0, 10);
const cents = (value: string | number) => Math.round(Number(value || 0) * 100);
const rupees = (value: number) => (value / 100).toFixed(2);

/**
 * Receive one payment from a customer (or pay one supplier) and split it across open
 * invoices/bills. Lines are filled oldest-due first and can be edited before saving.
 *
 * If saving stops half way, the form locks and offers "Finish recording": it resends the exact
 * same request, which the server replays safely, so nothing is paid twice.
 */
export type SettlePrefill = { amount?: string; method?: string; date?: string; reference?: string; notes?: string };

export default function SettleSheet({ side, partyId: initialParty, onClose, prefill }: { side: Side; partyId?: string; onClose: () => void; prefill?: SettlePrefill }) {
  const receivable = side === "receivable";
  const [partyId, setPartyId] = useState(initialParty ?? "");
  const [amount, setAmount] = useState(prefill?.amount ?? "");
  const [lines, setLines] = useState<Record<string, string>>({});
  const [method, setMethod] = useState(prefill?.method || "UPI");
  const [accountId, setAccountId] = useState("");
  const [date, setDate] = useState(prefill?.date || today());
  const [reference, setReference] = useState(prefill?.reference ?? "");
  const [notes, setNotes] = useState(prefill?.notes ?? "");
  // A prefilled amount is split across open documents once they load.
  const [pendingSplit, setPendingSplit] = useState(Boolean(prefill?.amount));
  const [error, setError] = useState("");
  const [locked, setLocked] = useState<SettleInput | null>(null);
  const requestKey = useRef(newRequestKey());

  const parties = useOutstanding(side);
  const party = usePartyOutstanding(side, partyId);
  const receiveAccounts = useInvoiceBankAccounts(receivable);
  const payAccounts = useVendorBillBankAccounts(!receivable);
  const accounts = useMemo(() => {
    const list = receivable ? receiveAccounts.data?.bank_accounts ?? [] : payAccounts.data ?? [];
    return list.filter((a) => a.is_active);
  }, [receivable, receiveAccounts.data, payAccounts.data]);
  const settle = useSettle();
  const documents = useMemo(() => party.data?.documents ?? [], [party.data]);
  if (pendingSplit && documents.length) {
    setPendingSplit(false);
    setLines(autoAllocate(documents, Number(amount) || 0));
  }

  // Cash goes to a cash account, everything else to a bank account, unless the user picks one.
  const fallback = accounts.find((a) => (a.account_type === "CASH") === (method === "CASH")) ?? accounts[0];
  const effectiveAccount = accounts.some((a) => a.id === accountId) ? accountId : fallback?.id ?? "";

  function pickParty(id: string) {
    setPartyId(id);
    setPendingSplit(false);
    setAmount("");
    setLines({});
    setError("");
    requestKey.current = newRequestKey();
  }

  function changeAmount(value: string) {
    setAmount(value);
    setLines(autoAllocate(documents, Number(value) || 0));
  }

  function toggle(id: string, outstanding: string) {
    setLines((prev) => {
      const next = { ...prev };
      if (next[id]) delete next[id];
      else next[id] = outstanding;
      return next;
    });
  }

  const allocated = Object.values(lines).reduce((sum, v) => sum + cents(v), 0);
  const total = cents(amount);
  const outstanding = cents(party.data?.total ?? 0);
  const overLine = documents.find((d) => lines[d.id] !== undefined && cents(lines[d.id]) > cents(d.outstanding));
  const problem = !partyId ? `Choose a ${receivable ? "customer" : "supplier"}.`
    : total <= 0 ? "Enter the amount."
    : total > outstanding ? `Amount is more than the ${formatMoney(rupees(outstanding))} outstanding. Advance payments are not supported yet.`
    : overLine ? `${overLine.number}: more than its outstanding ${formatMoney(overLine.outstanding)}.`
    : allocated !== total ? `Split ${formatMoney(rupees(allocated))} of ${formatMoney(rupees(total))}. Adjust the lines or the amount.`
    : !effectiveAccount ? "Choose the account the money moves through."
    : "";

  async function submit(body: SettleInput) {
    setError("");
    try {
      await settle.mutateAsync(body);
      onClose();
    } catch (exception) {
      const e = exception as Error & { status?: number };
      setError(e.message);
      // Some parts were recorded: freeze the request so the retry is identical.
      if (e.status === 422) setLocked(body);
    }
  }

  function save() {
    if (problem) {
      setError(problem);
      return;
    }
    void submit({
      side,
      party_id: partyId,
      amount: rupees(total),
      payment_method: method,
      bank_account_id: effectiveAccount,
      payment_date: date,
      reference_number: reference.trim(),
      notes: notes.trim(),
      allocations: documents.filter((d) => cents(lines[d.id] ?? 0) > 0).map((d) => ({ document_id: d.id, amount: rupees(cents(lines[d.id])) })),
      request_key: requestKey.current,
    });
  }

  const busy = settle.isPending;
  const disabled = busy || Boolean(locked);
  const noun = receivable ? "invoice" : "bill";
  return (
    <FormSheet
      title={receivable ? "Receive payment" : "Pay supplier"}
      subtitle={receivable ? "One receipt can settle several invoices." : "One payment can settle several bills."}
      onClose={onClose}
      busy={busy}
      size="lg"
    >
      <div className="flex flex-col gap-3.5">
        <FormSection title={receivable ? "Customer" : "Supplier"} icon={Wallet}>
          <div className="nxf-grid">
            <label className="block">
              {receivable ? "Customer" : "Supplier"} *
              <SearchSelect aria-label={receivable ? "Customer" : "Supplier"} value={partyId} disabled={disabled} onChange={(e) => pickParty(e.target.value)}>
                <option value="">{parties.isLoading ? "Loading…" : `Choose a ${receivable ? "customer" : "supplier"}`}</option>
                {(parties.data?.parties ?? []).map((p) => <option key={p.id} value={p.id}>{`${p.name} — ${formatMoney(p.outstanding)} due`}</option>)}
              </SearchSelect>
              <FieldHint>Only {receivable ? "customers" : "suppliers"} with something outstanding are listed.</FieldHint>
            </label>
            <label className="block">
              Amount *
              <input aria-label="Amount" inputMode="decimal" type="number" min="0.01" step="0.01" placeholder="0.00" value={amount} disabled={disabled || !partyId} onChange={(e) => changeAmount(e.target.value)} />
              {party.data ? (
                <FieldHint>
                  {formatMoney(party.data.total)} outstanding ·{" "}
                  <button type="button" className="font-semibold text-[var(--nx-primary)]" disabled={disabled} onClick={() => changeAmount(party.data.total)}>Settle in full</button>
                </FieldHint>
              ) : null}
            </label>
          </div>
        </FormSection>

        <FormSection title="Payment" icon={Wallet}>
          <div className="nxf-segment mb-3 flex-wrap" role="group" aria-label="Payment method">
            {METHODS.map((m) => <button key={m.value} type="button" aria-pressed={method === m.value} disabled={disabled} onClick={() => { setMethod(m.value); setAccountId(""); }}>{m.label}</button>)}
          </div>
          <div className="nxf-grid">
            <label className="block">
              {receivable ? "Received into" : "Paid from"} *
              <select aria-label={receivable ? "Received into" : "Paid from"} value={effectiveAccount} disabled={disabled} onChange={(e) => setAccountId(e.target.value)}>
                {!accounts.length ? <option value="">No active accounts — add one in Banking</option> : null}
                {accounts.map((a) => <option key={a.id} value={a.id}>{a.account_name}{a.masked_account_number ? ` · ${a.masked_account_number}` : ""}</option>)}
              </select>
            </label>
            <label className="block">
              Payment date *
              <input aria-label="Payment date" type="date" value={date} max={today()} disabled={disabled} onChange={(e) => setDate(e.target.value)} />
            </label>
            <label className="block">
              Reference
              <input aria-label="Reference" maxLength={90} placeholder={method === "CHEQUE" ? "Cheque number" : method === "CASH" ? "Optional" : "UTR / transaction id"} value={reference} disabled={disabled} onChange={(e) => setReference(e.target.value)} />
            </label>
            <label className="block">
              Notes
              <input aria-label="Notes" maxLength={900} value={notes} disabled={disabled} onChange={(e) => setNotes(e.target.value)} />
            </label>
          </div>
        </FormSection>

        <FormSection
          title={`Settle against ${noun}s`}
          icon={ListChecks}
          aside={documents.length ? <button type="button" className="nx-button nx-secondary nx-btn-sm" disabled={disabled || !total} onClick={() => setLines(autoAllocate(documents, total / 100))}>Oldest first</button> : null}
        >
          {!partyId ? <p className="nxf-hint">Choose a {receivable ? "customer" : "supplier"} to see open {noun}s.</p>
            : party.isLoading ? <div className="nx-skeleton h-24" aria-busy="true" />
            : party.error ? <p role="alert" className="nxf-error">{party.error.message}</p>
            : !documents.length ? <p className="nxf-hint">Nothing is outstanding.</p>
            : (
              <ul className="nxp-alloc" aria-label={`Open ${noun}s`}>
                {documents.map((d) => {
                  const on = lines[d.id] !== undefined;
                  const Mark = on ? CheckCircle2 : Circle;
                  const over = on && cents(lines[d.id]) > cents(d.outstanding);
                  return (
                    <li key={d.id} data-on={on || undefined}>
                      <button type="button" className="nxp-alloc-pick" aria-pressed={on} aria-label={`${on ? "Remove" : "Add"} ${d.number}`} disabled={disabled} onClick={() => toggle(d.id, d.outstanding)}>
                        <Mark size={18} aria-hidden="true" />
                      </button>
                      <span className="nxp-alloc-doc">
                        <strong>{d.number}</strong>
                        <span data-late={d.days_overdue > 0 || undefined}>{d.days_overdue > 0 ? `${d.days_overdue} days overdue` : d.due_date ? `Due ${formatDate(d.due_date)}` : formatDate(d.date)}</span>
                      </span>
                      <span className="nxp-alloc-due">{formatMoney(d.outstanding)}</span>
                      <input aria-label={`Amount for ${d.number}`} aria-invalid={over || undefined} inputMode="decimal" type="number" min="0" step="0.01" placeholder="0.00"
                        value={lines[d.id] ?? ""} disabled={disabled}
                        onChange={(e) => setLines((prev) => { const next = { ...prev }; if (e.target.value === "") delete next[d.id]; else next[d.id] = e.target.value; return next; })} />
                    </li>
                  );
                })}
              </ul>
            )}
          {total > 0 && allocated !== total && documents.length ? (
            <p className="nxf-hint mt-2">
              Split {formatMoney(rupees(allocated))} of {formatMoney(rupees(total))}.{" "}
              {allocated > 0 ? <button type="button" className="font-semibold text-[var(--nx-primary)]" disabled={disabled} onClick={() => setAmount(rupees(allocated))}>Use {formatMoney(rupees(allocated))} as the amount</button> : null}
            </p>
          ) : null}
        </FormSection>

        {error ? <p role="alert" className="nxf-error">{error}</p> : null}

        <FormActions total={formatMoney(rupees(total))}>
          <button type="button" className="nx-button nx-secondary" disabled={busy} onClick={onClose}>{locked ? "Close" : "Cancel"}</button>
          {locked ? (
            <button type="button" className="nx-button" disabled={busy} onClick={() => void submit(locked)}>{busy ? "Recording…" : "Finish recording"}</button>
          ) : (
            <button type="button" className="nx-button" disabled={busy} aria-disabled={Boolean(problem) || undefined} onClick={save}>
              {busy ? "Saving…" : receivable ? "Save receipt" : "Save payment"}
            </button>
          )}
        </FormActions>
      </div>
    </FormSheet>
  );
}
