import type {
  Metadata,
} from "next";

import {
  ForgotPasswordForm,
} from "@/features/auth/components/forgot-password-form";

export const metadata: Metadata = {
  title: "Forgot password | NexEase",
};

export default function ForgotPasswordPage() {
  return (
    <main className="mx-auto flex min-h-screen w-full max-w-md items-center px-6 py-12">
      <div className="w-full">
        <ForgotPasswordForm />
      </div>
    </main>
  );
}