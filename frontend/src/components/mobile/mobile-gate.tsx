"use client";
import {apiFetch} from "@/lib/api/transport";
import { useEffect, useState, type ReactNode } from 'react';
import { Capacitor } from '@capacitor/core';
import { normalizeServer, savedServer, SERVER_KEY } from '@/lib/mobile-config';
export default function MobileGate({ children }: { children: ReactNode }) {
  const [ready, setReady] = useState(false);
  const [configure, setConfigure] = useState(false);
  const [address, setAddress] = useState('https://nexease-backend-staging.onrender.com');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    const mobile = Capacitor.isNativePlatform() || process.env.NEXT_PUBLIC_MOBILE_APP === 'true';
    setConfigure(mobile && !savedServer() && !process.env.NEXT_PUBLIC_API_BASE_URL);
    setReady(true);
  }, []);
  async function connect(event: React.FormEvent) {
    event.preventDefault(); setBusy(true); setError('');
    try {
      const base = normalizeServer(address);
      const response = await apiFetch(`${base}/auth/csrf/`, {
        credentials: 'include', headers: { Accept: 'application/json', ...(Capacitor.isNativePlatform() ? { Origin: 'https://localhost' } : {}) },
        signal: AbortSignal.timeout(60000),
      });
      const data = await response.json();
      if (!response.ok || !data.success || !data.data?.csrf?.token) throw new Error(response.status === 400 ? 'Server rejected this address (HTTP 400). Check ALLOWED_HOSTS in Render.' : `Connection failed (HTTP ${response.status}). Check that the updated Django backend is deployed.`);
      localStorage.setItem(SERVER_KEY, base);
      window.location.replace('/login/');
    } catch (e) { setError(e instanceof Error ? e.message : 'Unable to connect. Check your internet connection.'); }
    finally { setBusy(false); }
  }
  if (!ready) return <main className="nx-mobile-welcome"><p>Opening NexEase…</p></main>;
  if (!configure) return children;
  return <main className="nx-mobile-welcome"><form onSubmit={connect} className="nx-mobile-setup">
    <div className="nx-mobile-mark">N</div><p className="nx-eyebrow">YOUR BUSINESS, IN YOUR HAND</p>
    <h1>NexEase Mobile</h1><p>Connect to your existing NexEase backend. Your company, records and permissions stay together.</p>
    <label htmlFor="backend">Backend address</label><input id="backend" type="url" inputMode="url" autoCapitalize="none" autoCorrect="off" required placeholder="https://your-backend.onrender.com" value={address} onChange={e=>setAddress(e.target.value)} className="nx-input"/>
    <p className="text-xs">Use your Django server address. Your website address may be different.</p>
    {error && <p role="alert" className="text-red-700">{error}</p>}
    <button className="nx-button w-full" disabled={busy}>{busy ? 'Checking connection…' : 'Connect securely'}</button>
    <p className="text-xs">Already configured? Sign in with the same NexEase account after connecting. Internet is required for business operations.</p>
  </form></main>;
}
