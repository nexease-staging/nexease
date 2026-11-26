import { downloads } from "@/config/downloads";

function WindowsMark() {
  return (
    <svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true" focusable="false">
      <path fill="currentColor" d="M3 5.2 10.4 4v7.3H3zm8.4-1.4L21 2.4v8.9h-9.6zM3 12.7h7.4V20L3 18.8zm8.4 0H21v8.9l-9.6-1.4z" />
    </svg>
  );
}

function AndroidMark() {
  return (
    <svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true" focusable="false">
      <path fill="currentColor" d="M17.6 9.5 19.4 6.4a.4.4 0 0 0-.7-.4l-1.8 3.1a11 11 0 0 0-9.8 0L5.3 6a.4.4 0 1 0-.7.4l1.8 3.1A10 10 0 0 0 1.5 17h21a10 10 0 0 0-4.9-7.5ZM7 14.3a1 1 0 1 1 0-2 1 1 0 0 1 0 2Zm10 0a1 1 0 1 1 0-2 1 1 0 0 1 0 2Z" />
    </svg>
  );
}

/** The Windows connector download: the main call to action of the welcome and download pages. */
export function ConnectorButton({ tone = "solid" }: { tone?: "solid" | "light" }) {
  const c = downloads.connector;
  return (
    <a className="nxw-dl" data-tone={tone} href={c.url} download>
      <WindowsMark />
      <span><b>Download Tally Connector</b><small>.exe for {c.needs} · {c.size}</small></span>
    </a>
  );
}

export function AndroidButton({ tone = "outline" }: { tone?: "outline" | "light" }) {
  const a = downloads.android;
  return (
    <a className="nxw-dl" data-tone={tone} href={a.url} download>
      <AndroidMark />
      <span><b>Get the Android app</b><small>.apk for {a.needs} · {a.size}</small></span>
    </a>
  );
}
