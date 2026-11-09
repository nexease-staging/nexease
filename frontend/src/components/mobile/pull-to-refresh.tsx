"use client";
import { useEffect, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { Capacitor } from "@capacitor/core";

/** Refreshes data without reloading the WebView or erasing an unfinished form. */
export default function PullToRefresh() {
  const qc = useQueryClient();
  const [pull, setPull] = useState(0);
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    if (!Capacitor.isNativePlatform()) return;
    const main = document.querySelector<HTMLElement>("main.nx-workspace-main");
    if (!main) return;
    let start: number | null = null;
    let distance = 0;
    let horizontal = 0;
    let refreshing = false;
    const begin = (event: TouchEvent) => {
      const target = event.target as HTMLElement;
      if (
        main.scrollTop > 0 ||
        event.touches.length !== 1 ||
        document.querySelector("dialog[open]") ||
        target.closest(
          "input,textarea,select,button,a,[contenteditable=true],form",
        )
      )
        return;
      start = event.touches[0].clientY;
      horizontal = event.touches[0].clientX;
      distance = 0;
    };
    const move = (event: TouchEvent) => {
      if (start === null || refreshing || event.touches.length !== 1) return;
      const dy = event.touches[0].clientY - start;
      const dx = Math.abs(event.touches[0].clientX - horizontal);
      if (dy <= 0 || dx > Math.abs(dy) || main.scrollTop > 0) {
        start = null;
        distance = 0;
        setPull(0);
        return;
      }
      distance = Math.min(dy, 130);
      setPull(distance);
      if (event.cancelable) event.preventDefault();
    };
    const end = () => {
      const ready = start !== null && distance >= 90;
      start = null;
      distance = 0;
      setPull(0);
      if (!ready || refreshing) return;
      refreshing = true;
      setBusy(true);
      void qc.invalidateQueries({ refetchType: "active" }).finally(() => {
        refreshing = false;
        setBusy(false);
      });
    };
    const cancel = () => {
      start = null;
      distance = 0;
      setPull(0);
    };
    main.addEventListener("touchstart", begin, { passive: true });
    main.addEventListener("touchmove", move, { passive: false });
    main.addEventListener("touchend", end);
    main.addEventListener("touchcancel", cancel);
    return () => {
      main.removeEventListener("touchstart", begin);
      main.removeEventListener("touchmove", move);
      main.removeEventListener("touchend", end);
      main.removeEventListener("touchcancel", cancel);
    };
  }, [qc]);
  if (!pull && !busy) return null;
  return (
    <div
      role="status"
      className="fixed left-1/2 top-24 z-40 -translate-x-1/2 rounded-full border bg-white px-4 py-2 text-sm text-slate-900 shadow"
    >
      {busy
        ? "Refreshing…"
        : pull >= 90
          ? "Release to refresh"
          : "Pull to refresh"}
    </div>
  );
}
