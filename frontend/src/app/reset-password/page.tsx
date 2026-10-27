import type {
  Metadata,
} from "next";

import {
  Suspense,
} from "react";

import {
  ResetPasswordForm,
} from "@/features/auth/components/reset-password-form";

export const metadata: Metadata = {
  title: "Reset password | NexEase",
};

function ResetPasswordFallback() {
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
        Loading password reset…
      </p>
    </div>
  );
}

export default function ResetPasswordPage() {
  return (
    <main className="mx-auto flex min-h-screen w-full max-w-md items-center px-6 py-12">
      <div className="w-full">
        <Suspense
          fallback={
            <ResetPasswordFallback />
          }
        >
          <ResetPasswordForm />
        </Suspense>
      </div>
    </main>
  );
}