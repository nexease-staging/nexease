"use client";
import {useEffect,useState} from 'react';
import {Capacitor} from '@capacitor/core';
import {LocalNotifications} from '@capacitor/local-notifications';
import {useAuth} from '@/features/auth/auth-context';
import {DEVICE_PREF,CHANNEL,disableDeviceNotifications} from '@/lib/device-notifications';
export default function DeviceNotificationSettings(){
 const {authentication}=useAuth();const [native,setNative]=useState(false),[enabled,setEnabled]=useState(false),[message,setMessage]=useState(''),[busy,setBusy]=useState(false);
 useEffect(()=>{setNative(Capacitor.isNativePlatform());setEnabled(localStorage.getItem(DEVICE_PREF)===authentication?.user.id);const status=(e:Event)=>setMessage((e as CustomEvent<string>).detail);window.addEventListener('nex-device-status',status);return()=>window.removeEventListener('nex-device-status',status)},[authentication?.user.id]);
 if(!native)return null;
 async function toggle(){setBusy(true);try{if(enabled){await disableDeviceNotifications();setEnabled(false);setMessage('Device alerts disabled.')}else{const permission=await LocalNotifications.requestPermissions();if(permission.display!=='granted'){setMessage('Notifications are blocked. Enable them in Android Settings → Apps → NexEase → Notifications.');return}await LocalNotifications.createChannel({id:CHANNEL,name:'NexEase business alerts',importance:4});localStorage.setItem(DEVICE_PREF,authentication!.user.id);setEnabled(true);window.dispatchEvent(new Event('nex-enable-device-notifications'));setMessage('Activity notifications enabled. Connecting background alerts…')}}catch{setMessage('Could not update device alerts. Check your connection and try again.')}finally{setBusy(false)}}
 return <section className="mt-6 rounded-xl border p-4"><div className="flex items-center justify-between gap-4"><div><h3 className="font-semibold">Device notifications</h3><p className="text-xs text-slate-500">Saved activity and business reminders</p></div><button type="button" role="switch" aria-label="Device notifications" aria-checked={enabled} className="easy-switch" disabled={busy} onClick={()=>void toggle()}><span/></button></div><p className="mt-3 text-xs" role="status">{message||'Enable Android alerts here. Camera permission is requested when you choose Use camera.'}</p></section>
}
