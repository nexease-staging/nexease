import type {
  Metadata,
} from "next";

import SignupForm from "@/features/auth/components/signup-form";

export const metadata: Metadata = {
  title:
    "Create organization | NexEase",
  description:
    "Create a NexEase organization and administrator account.",
};

export default function SignupPage() {
  return (
    <main
      className="
        min-h-screen bg-slate-50
        px-4 py-12
      "
    >
      <div
        className="
          mx-auto w-full max-w-xl
        "
      >
        <SignupForm />
      </div>
    </main>
  );
}