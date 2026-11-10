/* eslint-disable react-hooks/set-state-in-effect -- Hydrate device capabilities only after mounting in the browser. */
"use client";

import { useEffect, useState } from 'react';
import { App } from '@capacitor/app';
import { Capacitor, type PluginListenerHandle } from '@capacitor/core';
import { LocalNotifications } from '@capacitor/local-notifications';
import { useAuth } from '@/features/auth/auth-context';
import { CHANNEL, DEVICE_PREF, disableDeviceNotifications } from '@/lib/device-notifications';

export default function DeviceNotificationSettings() {
  const { authentication } = useAuth();
  const userId = authentication?.user.id;
  const [native, setNative] = useState(false);
  const [enabled, setEnabled] = useState(false);
  const [blocked, setBlocked] = useState(false);
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!Capacitor.isNativePlatform() || !userId) return;
    setNative(true);
    let disposed = false;
    let listener: PluginListenerHandle | undefined;
    async function syncPermission() {
      try {
        const { display } = await LocalNotifications.checkPermissions();
        if (disposed) return;
        const selected = localStorage.getItem(DEVICE_PREF) === userId;
        setBlocked(display === 'denied');
        setEnabled(selected && display === 'granted');
        if (selected && display === 'granted') {
          window.dispatchEvent(new Event('nex-enable-device-notifications'));
        }
      } catch {
        if (!disposed) setMessage('Could not check device notification permission.');
      }
    }
    const status = (event: Event) => setMessage((event as CustomEvent<string>).detail);
    window.addEventListener('nex-device-status', status);
    void syncPermission();
    void App.addListener('appStateChange', state => {
      if (state.isActive) void syncPermission();
    }).then(handle => {
      if (disposed) void handle.remove();
      else listener = handle;
    }).catch(() => {});
    return () => {
      disposed = true;
      void listener?.remove();
      window.removeEventListener('nex-device-status', status);
    };
  }, [userId]);

  if (!native || !userId) return null;

  async function toggle() {
    if (!userId) return;
    setBusy(true);
    try {
      if (enabled) {
        await disableDeviceNotifications();
        setEnabled(false);
        setMessage('Device alerts disabled.');
      } else {
        const { display } = await LocalNotifications.requestPermissions();
        setBlocked(display === 'denied');
        if (display !== 'granted') return;
        await LocalNotifications.createChannel({ id: CHANNEL, name: 'NexEase business alerts', importance: 4 });
        localStorage.setItem(DEVICE_PREF, userId);
        setEnabled(true);
        setMessage('Activity notifications enabled. Connecting background alerts…');
        window.dispatchEvent(new Event('nex-enable-device-notifications'));
      }
    } catch {
      setMessage('Could not update device alerts. Try again.');
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="mt-6 rounded-xl border p-4">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h3 className="font-semibold">Device notifications</h3>
          <p className="text-xs text-slate-500">Saved activity and business reminders</p>
        </div>
        <button type="button" role="switch" aria-label="Device notifications" aria-checked={enabled} className="easy-switch" disabled={busy} onClick={() => void toggle()}><span /></button>
      </div>
      <p className="mt-3 text-xs" role="status">
        {blocked ? 'Notifications are blocked. Enable them in Android Settings → Apps → NexEase → Notifications.'
          : message || 'Camera permission is requested when you choose Use camera.'}
      </p>
    </section>
  );
}
