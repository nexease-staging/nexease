"use client";

import {
  useEffect,
  type ReactNode,
} from "react";

import {
  useRouter,
} from "next/navigation";

import {
  useAuth,
} from "@/features/auth/auth-context";

export default function RequireAuth({
  children,
}: {
  children: ReactNode;
}) {
  const router = useRouter();

  const {
    status,
    isAuthenticated,
  } = useAuth();

  useEffect(() => {
    if (
      status === "unauthenticated"
    ) {
      router.replace("/login");
    }
  }, [
    router,
    status,
  ]);

  if (status === "loading") {
    return (
      <main
        className="
          flex min-h-screen items-center
          justify-center bg-slate-50
        "
      >
        <div
          className="
            rounded-xl border
            border-slate-200 bg-white
            px-6 py-4 text-sm
            text-slate-600 shadow-sm
          "
        >
          Checking your session…
        </div>
      </main>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  return children;
}