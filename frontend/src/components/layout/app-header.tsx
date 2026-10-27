"use client";

import {
  useState,
} from "react";

import {
  useRouter,
} from "next/navigation";

import {
  LogOut,
  Menu,
} from "lucide-react";

import {
  useAuth,
} from "@/features/auth/auth-context";

import NotificationMenu
  from "@/features/notifications/components/notification-menu";

interface AppHeaderProps {
  onOpenMobile: () => void;
}

export default function AppHeader({
  onOpenMobile,
}: AppHeaderProps) {
  const router = useRouter();

  const {
    authentication,
    signOut,
  } = useAuth();

  const [
    signingOut,
    setSigningOut,
  ] = useState(false);

  if (!authentication) {
    return null;
  }

  const {
    user,
    organization,
    role,
  } = authentication;

  const initials = (
    `${user.first_name[0] ?? ""}`
    +
    `${user.last_name[0] ?? ""}`
  ).toUpperCase();

  async function handleSignOut():
    Promise<void> {
    setSigningOut(true);

    try {
      await signOut();

    } catch {
      // An expired or already-cleared session
      // is equivalent to being signed out.

    } finally {
      router.replace("/login");
      router.refresh();
    }
  }

  return (
    <header
      className="
        sticky top-0 z-30 flex h-16 shrink-0
        items-center border-b
        border-slate-200 bg-white/95
        px-4 backdrop-blur
        sm:px-6
      "
    >
      <button
        type="button"
        aria-label="Open navigation"
        onClick={onOpenMobile}
        className="
          mr-3 rounded-lg p-2
          text-slate-600
          hover:bg-slate-100
          lg:hidden
        "
      >
        <Menu size={21} />
      </button>

      <div className="min-w-0 flex-1">
        <p
          className="
            truncate text-sm font-semibold
            text-slate-900
          "
        >
          {organization.name}
        </p>

        <p
          className="
            truncate text-xs text-slate-500
          "
        >
          {role.name}
        </p>
      </div>

      <div
        className="
          flex items-center gap-3
        "
      >
        <NotificationMenu />
        <div
          className="
            hidden text-right sm:block
          "
        >
          <p
            className="
              text-sm font-medium
              text-slate-900
            "
          >
            {user.full_name
              ||
              `${user.first_name} ${user.last_name}`}
          </p>

          <p
            className="
              text-xs text-slate-500
            "
          >
            {user.email}
          </p>
        </div>

        <div
          className="
            flex size-9 items-center
            justify-center rounded-full
            bg-blue-100 text-sm
            font-bold text-blue-700
          "
        >
          {initials || "U"}
        </div>

        <button
          type="button"
          aria-label="Sign out"
          title="Sign out"
          disabled={signingOut}
          onClick={() => {
            void handleSignOut();
          }}
          className="
            rounded-lg p-2
            text-slate-500
            hover:bg-red-50
            hover:text-red-600
            disabled:opacity-50
          "
        >
          <LogOut size={19} />
        </button>
      </div>
    </header>
  );
}