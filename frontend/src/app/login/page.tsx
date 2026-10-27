import type {
  Metadata,
} from "next";

import {
  Suspense,
} from "react";

import LoginForm from "@/features/auth/components/login-form";

export const metadata: Metadata = {
  title: "Sign in | NexEase",
  description:
    "Sign in to the NexEase workspace.",
};

function LoginFormFallback() {
  return (
    <div
      className="
        rounded-2xl border border-slate-200
        bg-white p-8 shadow-sm
      "
    >
      <p
        className="
          text-center text-sm
          text-slate-500
        "
      >
        Loading sign in…
      </p>
    </div>
  );
}

export default function LoginPage() {
  return (
    <main
      className="
        flex min-h-screen items-center
        justify-center bg-slate-50
        px-4 py-12
      "
    >
      <div className="w-full max-w-md">
        <Suspense
          fallback={
            <LoginFormFallback />
          }
        >
          <LoginForm />
        </Suspense>
      </div>
    </main>
  );
}