"use client";
import {useEffect} from 'react';
import {useRouter} from 'next/navigation';
import {Capacitor,type PluginListenerHandle} from '@capacitor/core';
import {PushNotifications} from '@capacitor/push-notifications';
import {LocalNotifications} from '@capacitor/local-notifications';
import {useAuth} from '@/features/auth/auth-context';
import {apiRequest} from '@/lib/api/client';
import {CHANNEL,DEVICE_PREF,DEVICE_TOKEN,showDeviceNotice,safeNotificationRoute} from '@/lib/device-notifications';
export default function DeviceNotifications(){
 const {authentication}=useAuth();const router=useRouter();const userId=authentication?.user.id;
 useEffect(()=>{
  if(!Capacitor.isNativePlatform()||!userId)return;
  let disposed=false;const handles:PluginListenerHandle[]=[];let started=false;let bound=false;
  const status=(message:string)=>{if(!disposed)window.dispatchEvent(new CustomEvent('nex-device-status',{detail:message}))};
  const keep=async(p:Promise<PluginListenerHandle>)=>{const h=await p;if(disposed)await h.remove();else handles.push(h)};
  const onNotice=(event:Event)=>{const n=(event as CustomEvent<{kind:string;message:string}>).detail;if(localStorage.getItem(DEVICE_PREF)===userId&&n.kind==='success')void showDeviceNotice('NexEase activity',n.message).catch(()=>{})};
  async function register(){
   if(started||disposed||localStorage.getItem(DEVICE_PREF)!==userId)return;
   try{
    await LocalNotifications.createChannel({id:CHANNEL,name:'NexEase business alerts',importance:4});
    const response=await apiRequest<{push_enabled:boolean}>('/notifications/device/');
    if(!response.data.push_enabled||process.env.NEXT_PUBLIC_PUSH_ENABLED!=='true'){status('Activity alerts enabled. Background alerts need Firebase setup and a rebuilt APK.');return;}
    started=true;
    if(!bound){bound=true;
    await keep(PushNotifications.addListener('registration',token=>{if(disposed||localStorage.getItem(DEVICE_PREF)!==userId)return;localStorage.setItem(DEVICE_TOKEN,token.value);void apiRequest('/notifications/device/',{method:'POST',body:{token:token.value}}).then(()=>status('Activity and background alerts enabled.')).catch(()=>{started=false;status('Could not register background alerts. Reopen your profile to retry.');})}));
    await keep(PushNotifications.addListener('registrationError',()=>{started=false;status('Background registration failed. Check Firebase configuration.')}));
    await keep(PushNotifications.addListener('pushNotificationReceived',n=>{if(!disposed&&localStorage.getItem(DEVICE_PREF)===userId)void showDeviceNotice(n.title||'NexEase',n.body||'You have a business update.',n.data?.url).catch(()=>{})}));
    await keep(PushNotifications.addListener('pushNotificationActionPerformed',n=>{if(!disposed&&localStorage.getItem(DEVICE_PREF)===userId)router.push(safeNotificationRoute(n.notification.data?.url))}));
    }
    if(disposed)return;
    const permission=await PushNotifications.checkPermissions();if(permission.receive!=='granted'){status('Enable notifications in Android Settings.');started=false;return;}
    await PushNotifications.createChannel({id:CHANNEL,name:'NexEase business alerts',importance:4});
    await PushNotifications.register();
   }catch{started=false;status('Background alerts unavailable. Check your connection and Firebase setup.');}
  }
  void keep(LocalNotifications.addListener('localNotificationActionPerformed',n=>{if(localStorage.getItem(DEVICE_PREF)===userId)router.push(safeNotificationRoute(n.notification.extra?.url))}));
  const disabled=()=>{started=false};
  window.addEventListener('nex-disable-device-notifications',disabled);
  window.addEventListener('nex-feedback',onNotice);window.addEventListener('nex-enable-device-notifications',register);void register();
  return()=>{disposed=true;window.removeEventListener('nex-disable-device-notifications',disabled);handles.forEach(h=>void h.remove());window.removeEventListener('nex-feedback',onNotice);window.removeEventListener('nex-enable-device-notifications',register)};
 },[userId,router]);return null;
}
