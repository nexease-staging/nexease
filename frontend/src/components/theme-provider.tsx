"use client";
import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
type Theme = "light" | "dark";
const Context = createContext<{theme:Theme;setTheme:(theme:Theme)=>void}>({theme:"light",setTheme:()=>{}});
export function ThemeProvider({children}:{children:ReactNode}) {
 const [theme,setValue]=useState<Theme>("light");
 useEffect(()=>{ const value=localStorage.getItem("nexease-theme"); const next=value==="dark"?"dark":"light"; setValue(next); document.documentElement.dataset.theme=next; },[]);
 function setTheme(next:Theme){setValue(next);localStorage.setItem("nexease-theme",next);document.documentElement.dataset.theme=next;}
 return <Context.Provider value={{theme,setTheme}}>{children}</Context.Provider>;
}
export function ThemeToggle(){const {theme,setTheme}=useContext(Context);return <button type="button" className="nx-button nx-secondary" onClick={()=>setTheme(theme==="dark"?"light":"dark")}>{theme==="dark"?"Switch to light mode":"Switch to dark mode"}</button>;}
