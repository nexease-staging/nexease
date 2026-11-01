"use client";
import { Capacitor, CapacitorCookies } from '@capacitor/core';
import { SERVER_KEY, savedServer } from '@/lib/mobile-config';
export default function MobileConnection() {
  const server = savedServer();
  if (!server) return null;
  async function reset() {
    if (!window.confirm('Disconnect this device from the current server?')) return;
    if (Capacitor.isNativePlatform()) await CapacitorCookies.clearCookies({ url: server });
    localStorage.removeItem(SERVER_KEY);
    window.location.replace('/');
  }
  return <div className="mt-5 text-center text-xs text-slate-500"><p className="break-all">Connected to {new URL(server).host}</p><button type="button" className="mt-2 underline" onClick={()=>void reset()}>Change server</button></div>;
}
