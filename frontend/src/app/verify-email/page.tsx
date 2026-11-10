/* eslint-disable react-hooks/set-state-in-effect -- Hydrate the token from the browser URL after SSR. */
"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { apiRequest } from "@/lib/api/client";
export default function VerifyEmail() {
  const [token, setToken] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(false);
  useEffect(() => {
    setToken(new URLSearchParams(window.location.search).get("token") || "");
  }, []);
  return (
    <main className="mx-auto max-w-lg p-8">
      <h1 className="text-3xl font-semibold">Verify your NexEase email</h1>
      <p className="my-5">
        Confirm your address to share documents through NexEase. Replies will
        come to your verified address.
      </p>
      <button
        className="nx-button"
        disabled={!token || busy || done}
        onClick={async () => {
          setBusy(true);
          try {
            await apiRequest("/email/verify/confirm/", {
              method: "POST",
              body: { token },
            });
            setDone(true);
            setToken("");
            window.history.replaceState(null, "", "/verify-email");
            setMessage("Your email is verified. You can now share documents.");
          } catch (e) {
            setMessage((e as Error).message);
          } finally {
            setBusy(false);
          }
        }}
      >
        {busy ? "Verifying…" : done ? "Verified" : "Verify my email"}
      </button>
      {message && (
        <p role="status" className="my-5">
          {message}
        </p>
      )}
      <Link href="/settings#my-email" className="mt-5 block underline">
        Return to email settings
      </Link>
    </main>
  );
}
