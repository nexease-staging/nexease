"use client";
import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { apiBinaryRequest, apiRequest } from "@/lib/api/client";
import { downloadBlob } from "@/lib/browser/download";
import { confirmAction, notify } from "@/components/nex-feedback";
import NexDialog from "@/components/nex-dialog";
type Contact = { id: string; name: string; email: string; phone: string };
export function PayslipPreview({
  runId,
  employeeId,
  onClose,
}: {
  runId: string;
  employeeId: string;
  onClose: () => void;
}) {
  const [url, setUrl] = useState("");
  const [error, setError] = useState("");
  const [blob, setBlob] = useState<Blob | null>(null);
  useEffect(() => {
    let active = true;
    let local = "";
    void apiBinaryRequest(
      `/business/workforce/payslips/${runId}/?employee_id=${employeeId}`,
    )
      .then((r) => {
        if (active) {
          local = URL.createObjectURL(r.blob);
          setBlob(r.blob);
          setUrl(local);
        }
      })
      .catch((e) => {
        if (active) setError(e.message);
      });
    return () => {
      active = false;
      if (local) URL.revokeObjectURL(local);
    };
  }, [runId, employeeId]);
  return (
    <NexDialog title="Payslip PDF preview" onClose={onClose}>
      <div className="mb-4 flex gap-2">
        <button
          disabled={!blob}
          className="nx-button"
          onClick={() =>
            blob &&
            void downloadBlob(blob, "Payslip.pdf").catch((e) =>
              setError(e.message),
            )
          }
        >
          Download / share PDF
        </button>
        <button
          disabled={!url}
          className="nx-button nx-secondary"
          onClick={() => {
            const frame = document.getElementById(
              "payslip-pdf",
            ) as HTMLIFrameElement | null;
            try {
              frame?.contentWindow?.print();
            } catch {
              setError("Open the downloaded PDF to print.");
            }
          }}
        >
          Print payslip
        </button>
      </div>
      {error && <p role="alert">{error}</p>}
      {url ? (
        <iframe
          id="payslip-pdf"
          title="Payslip"
          src={url}
          className="h-[65vh] w-full border"
        />
      ) : (
        <p role="status">Loading PDF…</p>
      )}
      <p className="mt-3 text-xs text-slate-500">
        If your device cannot preview or print PDFs here, open the downloaded
        PDF in its PDF viewer.
      </p>
    </NexDialog>
  );
}
export function PayslipDistribution({
  runId,
  month,
}: {
  runId: string;
  month: string;
}) {
  const q = useQuery({
    queryKey: ["payslip-contacts", runId],
    queryFn: async () =>
      (
        await apiRequest<{ employees: Contact[] }>(
          `/business/workforce/payslip-distribution/${runId}/`,
        )
      ).data,
  });
  const [ids, setIds] = useState<string[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [queue, setQueue] = useState<Contact[]>([]);
  const selected = q.data?.employees.filter((e) => ids.includes(e.id)) ?? [];
  async function email() {
    if (
      !(await confirmAction(
        `Email separate payslips to ${selected.length} selected employees? Each employee receives only their own payslip.`,
      ))
    )
      return;
    setBusy(true);
    setError("");
    try {
      const r = await apiRequest<{ queued: unknown[]; skipped: unknown[] }>(
        `/business/workforce/payslip-distribution/${runId}/`,
        { method: "POST", body: { employee_ids: ids } },
      );
      notify(
        `${r.data.queued.length} payslip email jobs queued. ${r.data.skipped.length} skipped because employee email is missing or invalid. Check Background jobs for delivery.`,
      );
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function download(employee?: Contact) {
    setBusy(true);
    setError("");
    try {
      const suffix = employee
        ? `employee_id=${employee.id}`
        : `employee_ids=${encodeURIComponent(ids.join(","))}`;
      const r = await apiBinaryRequest(
        `/business/workforce/payslips/${runId}/?${suffix}`,
      );
      await downloadBlob(
        r.blob,
        employee
          ? `Payslip-${employee.name}-${month}.pdf`
          : `Payslips-${month}.zip`,
      );
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <details className="my-4 rounded-xl border p-4">
      <summary className="cursor-pointer font-semibold">
        Bulk payslip distribution
      </summary>
      {q.error && <p role="alert">{q.error.message}</p>}
      <p className="my-3 text-sm text-slate-500">
        Select employees for separate emails or a guided WhatsApp sharing queue.
        Confirm WhatsApp attachments and recipients individually.
      </p>
      <label className="flex gap-2">
        <input
          type="checkbox"
          checked={
            !!q.data?.employees.length && ids.length === q.data.employees.length
          }
          onChange={(e) =>
            setIds(
              e.target.checked
                ? (q.data?.employees.map((x) => x.id) ?? [])
                : [],
            )
          }
        />
        Select all
      </label>
      <div className="my-3 max-h-60 space-y-2 overflow-y-auto">
        {q.data?.employees.map((e) => (
          <label key={e.id} className="flex gap-2 text-sm">
            <input
              type="checkbox"
              checked={ids.includes(e.id)}
              onChange={(event) =>
                setIds(
                  event.target.checked
                    ? [...ids, e.id]
                    : ids.filter((x) => x !== e.id),
                )
              }
            />
            {e.name} · {e.email || "Email missing"} ·{" "}
            {e.phone || "Phone missing"}
          </label>
        ))}
      </div>
      <div className="flex flex-wrap gap-2">
        <button
          className="nx-button"
          disabled={busy || !ids.length || ids.length > 100}
          onClick={() => void email()}
        >
          Email selected
        </button>
        <button
          className="nx-button nx-secondary"
          disabled={busy || !ids.length}
          onClick={() => setQueue(selected)}
        >
          WhatsApp selected
        </button>
        <button
          className="nx-button nx-secondary"
          disabled={busy || !ids.length}
          onClick={() => void download()}
        >
          Download selected ZIP
        </button>
      </div>
      {error && <p role="alert">{error}</p>}
      {queue[0] && (
        <NexDialog
          title={`WhatsApp payslip: ${queue[0].name}`}
          onClose={() => setQueue([])}
          busy={busy}
        >
          <p className="mb-4">
            Download/share this employee’s PDF, then attach it in their WhatsApp
            conversation. Check the recipient before sending.
          </p>
          <div className="flex flex-wrap gap-3">
            <button
              className="nx-button"
              disabled={busy}
              onClick={() => void download(queue[0])}
            >
              Download / share this PDF
            </button>
            {queue[0].phone && (
              <a
                className="nx-button nx-secondary"
                href={`https://wa.me/${queue[0].phone.replace(/\D/g, "").length === 10 ? "91" : ""}${queue[0].phone.replace(/\D/g, "")}?text=${encodeURIComponent(`Hello ${queue[0].name}, please find your payslip for ${month}.`)}`}
                target="_blank"
                rel="noopener noreferrer"
              >
                Open employee WhatsApp
              </a>
            )}
            <button
              className="nx-button nx-secondary"
              onClick={() => setQueue(queue.slice(1))}
            >
              Next employee
            </button>
          </div>
        </NexDialog>
      )}
    </details>
  );
}
