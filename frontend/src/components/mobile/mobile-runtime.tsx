"use client";
import { useEffect, useState } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { Capacitor, type PluginListenerHandle } from '@capacitor/core';
import { App } from '@capacitor/app';
import { Network } from '@capacitor/network';
import { Keyboard } from '@capacitor/keyboard';
import { clearOldShareFiles } from "@/lib/browser/download";
import { Browser } from '@capacitor/browser';
import { useQueryClient } from '@tanstack/react-query';
export default function MobileRuntime() {
  const [offline, setOffline] = useState(false);
  const router = useRouter(); const pathname = usePathname(); const queries = useQueryClient();
  useEffect(() => {
    const update = () => setOffline(!navigator.onLine);
    update(); window.addEventListener('online', update); window.addEventListener('offline', update);
    return () => { window.removeEventListener('online', update); window.removeEventListener('offline', update); };
  }, []);
  useEffect(() => {
    if (!Capacitor.isNativePlatform()) return;
    document.documentElement.dataset.native = 'true';
    void clearOldShareFiles();
    let disposed = false; const handles: PluginListenerHandle[] = [];
    const keep = async (p: Promise<PluginListenerHandle>) => { const h = await p; if (disposed) await h.remove(); else handles.push(h); };
    void keep(Network.addListener('networkStatusChange', s => { setOffline(!s.connected); if (s.connected) void queries.invalidateQueries(); }));
    void Network.getStatus().then(s => { if (!disposed) setOffline(!s.connected); });
    void keep(App.addListener('appStateChange', s => { if (s.isActive) void queries.invalidateQueries(); }));
    void keep(Keyboard.addListener('keyboardWillShow', () => { document.documentElement.dataset.keyboard = 'open'; }));
    void keep(Keyboard.addListener('keyboardWillHide', () => { delete document.documentElement.dataset.keyboard; }));
    const external = (event: MouseEvent) => {
      const anchor = (event.target as Element).closest?.('a');
      if (!anchor || !anchor.href || anchor.download) return;
      const url = new URL(anchor.href);
      if (url.origin !== window.location.origin && /^https?:$/.test(url.protocol)) {
        event.preventDefault(); void Browser.open({ url: url.href });
      }
    };
    document.addEventListener('click', external);
    return () => { disposed = true; handles.forEach(h => void h.remove()); document.removeEventListener('click', external); delete document.documentElement.dataset.keyboard; };
  }, [queries]);
  useEffect(() => {
    if (Capacitor.getPlatform() !== 'android') return;
    let removed = false; let handle: PluginListenerHandle | undefined;
    void App.addListener('backButton', ({ canGoBack }) => {
      const closer = Array.from(document.querySelectorAll<HTMLButtonElement>('[aria-label="Close assistant"], [aria-label="Close navigation"], [role="dialog"] button[aria-label="Close"]')).find(button => { const rect = button.getBoundingClientRect(); return rect.width > 0 && rect.height > 0 && rect.right > 0 && rect.left < window.innerWidth; });
      if (closer) { closer.click(); return; }
      if (!['/home','/home/','/dashboard','/dashboard/'].includes(pathname) && canGoBack) router.back();
      else if (window.confirm('Close NexEase?')) void App.exitApp();
    }).then(h => { if (removed) void h.remove(); else handle = h; });
    return () => { removed = true; void handle?.remove(); };
  }, [pathname, router]);
  return offline ? <div className="nx-offline" role="status">You’re offline. Changes cannot be saved. Reconnect before continuing.</div> : null;
}
