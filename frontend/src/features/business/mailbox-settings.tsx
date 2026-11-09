"use client";
import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { apiRequest } from "@/lib/api/client";
type Mailbox = {
  connected: boolean;
  verified: boolean;
  email: string;
  provider: string;
  configured: boolean;
};
export default function MailboxSettings() {
  const qc = useQueryClient();
  const q = useQuery({
    queryKey: ["my-mailbox"],
    queryFn: async () => (await apiRequest<Mailbox>("/email/mailbox/")).data,
    refetchOnWindowFocus: true,
  });
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  return (
    <section id="my-email" className="nx-panel space-y-4">
      <h2 className="text-lg font-semibold">My email — document sharing</h2>
      <p>
        Verify your registered email using a link. No mailbox password is
        required.
      </p>
      {q.isLoading ? (
        <p>Loading…</p>
      ) : q.error ? (
        <p role="alert">{q.error.message}</p>
      ) : (
        <>
          <p className="font-medium">{q.data?.email}</p>
          <p>
            {q.data?.verified
              ? "Email verified"
              : q.data?.connected
                ? "Authenticated mailbox connected"
                : "Email not verified"}
          </p>
          <p className="text-sm text-slate-500">
            Verified-only sharing uses NexEase’s configured sender, with your
            address in Reply-To. An existing authenticated mailbox can continue
            sending directly from your email.
          </p>
          <div className="flex flex-wrap gap-3">
            {!q.data?.verified && (
              <button
                className="nx-button"
                disabled={busy}
                onClick={async () => {
                  setBusy(true);
                  try {
                    await apiRequest("/email/verify/request/", {
                      method: "POST",
                    });
                    setMessage(
                      "Verification link sent. Check your inbox and spam folder.",
                    );
                  } catch (e) {
                    setMessage((e as Error).message);
                  } finally {
                    setBusy(false);
                  }
                }}
              >
                {busy ? "Sending…" : "Send verification link"}
              </button>
            )}
            <button
              className="nx-button nx-secondary"
              onClick={() =>
                void qc.invalidateQueries({ queryKey: ["my-mailbox"] })
              }
            >
              Refresh status
            </button>
          </div>
        </>
      )}
      {message && <p role="status">{message}</p>}
    </section>
  );
}
