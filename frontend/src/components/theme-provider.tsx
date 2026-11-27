/* eslint-disable react-hooks/set-state-in-effect -- Synchronize saved browser theme after hydration. */
"use client";
import { createContext, useContext, useEffect, useState, type ReactNode } from "react";

/** "system" follows the phone or computer setting. Stored on the device. */
export type ThemeChoice = "light" | "dark" | "system";
type Resolved = "light" | "dark";
const KEY = "nexease-theme";
const Context = createContext<{ theme: Resolved; choice: ThemeChoice; setTheme: (theme: ThemeChoice) => void }>({ theme: "light", choice: "light", setTheme: () => {} });

const prefersDark = () => typeof window !== "undefined" && !!window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
const resolve = (c: ThemeChoice): Resolved => (c === "system" ? (prefersDark() ? "dark" : "light") : c);

function apply(theme: Resolved) {
  document.documentElement.dataset.theme = theme;
  document.querySelector('meta[name="theme-color"]')?.setAttribute("content", theme === "dark" ? "#031a2e" : "#116957");
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [choice, setChoice] = useState<ThemeChoice>("light");
  const [theme, setResolved] = useState<Resolved>("light");
  useEffect(() => {
    const saved = localStorage.getItem(KEY);
    const next: ThemeChoice = saved === "dark" || saved === "system" ? saved : "light";
    setChoice(next);
    setResolved(resolve(next));
    apply(resolve(next));
  }, []);
  useEffect(() => {
    if (choice !== "system" || !window.matchMedia) return;
    const m = window.matchMedia("(prefers-color-scheme: dark)");
    const on = () => { const r = resolve("system"); setResolved(r); apply(r); };
    m.addEventListener("change", on);
    return () => m.removeEventListener("change", on);
  }, [choice]);
  function setTheme(next: ThemeChoice) {
    setChoice(next);
    localStorage.setItem(KEY, next);
    const r = resolve(next);
    setResolved(r);
    apply(r);
  }
  return <Context.Provider value={{ theme, choice, setTheme }}>{children}</Context.Provider>;
}

export const useTheme = () => useContext(Context);

export function ThemeToggle() {
  const { theme, setTheme } = useContext(Context);
  return <button type="button" className="nx-button nx-secondary" onClick={() => setTheme(theme === "dark" ? "light" : "dark")}>{theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}</button>;
}

/** Light / Dark / Automatic, as on the phone's Settings screen. */
export function ThemeChooser() {
  const { choice, setTheme } = useContext(Context);
  return (
    <div className="nxp-seg" role="radiogroup" aria-label="Appearance">
      {([["light", "Light"], ["dark", "Dark"], ["system", "Automatic"]] as const).map(([k, l]) => (
        <button key={k} type="button" role="radio" aria-checked={choice === k} className={choice === k ? "on" : ""} onClick={() => setTheme(k)}>{l}</button>
      ))}
    </div>
  );
}
