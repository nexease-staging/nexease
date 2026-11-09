"use client";
import { useEffect, useState } from "react";
import { apiRequest } from "@/lib/api/client";
import NexDialog from "@/components/nex-dialog";
import { notify } from "@/components/nex-feedback";
export default function ReorderLevel({
  productId,
  onClose,
}: {
  productId: string;
  onClose: () => void;
}) {
  const [level, setLevel] = useState("0");
  const [enabled, setEnabled] = useState(true);
  const [name, setName] = useState("");
  const [quantity, setQuantity] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(true);
  useEffect(() => {
    let active = true;
    void apiRequest<{
      level: string;
      enabled: boolean;
      product_name: string;
      quantity: string;
    }>(`/business/reorder/${productId}/`)
      .then((r) => {
        if (active) {
          setLevel(r.data.level);
          setEnabled(r.data.enabled);
          setName(r.data.product_name);
          setQuantity(r.data.quantity);
        }
      })
      .catch((e) => {
        if (active) setError(e.message);
      })
      .finally(() => {
        if (active) setBusy(false);
      });
    return () => {
      active = false;
    };
  }, [productId]);
  return (
    <NexDialog title="Reorder alert" onClose={onClose} busy={busy}>
      <form
        onSubmit={async (e) => {
          e.preventDefault();
          setBusy(true);
          setError("");
          try {
            await apiRequest(`/business/reorder/${productId}/`, {
              method: "POST",
              body: { level, enabled },
            });
            onClose();
            notify(
              "Reorder level saved. Low-stock alerts appear in your notification bell.",
            );
          } catch (e) {
            setError((e as Error).message);
          } finally {
            setBusy(false);
          }
        }}
      >
        <p>
          {name} · Current stock: {quantity}
        </p>
        <label className="mt-4 block">
          Reorder level
          <input
            className="nx-input"
            type="number"
            min="0"
            step="0.01"
            required
            value={level}
            onChange={(e) => setLevel(e.target.value)}
          />
        </label>
        <label className="my-4 flex gap-2">
          <input
            type="checkbox"
            checked={enabled}
            onChange={(e) => setEnabled(e.target.checked)}
          />
          Alert when total stock falls below this level
        </label>
        {error && <p role="alert">{error}</p>}
        <button disabled={busy} className="nx-button">
          Save reorder level
        </button>
      </form>
    </NexDialog>
  );
}
