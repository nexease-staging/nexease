import {Capacitor} from '@capacitor/core';
import {LocalNotifications} from '@capacitor/local-notifications';
import {PushNotifications} from '@capacitor/push-notifications';
import {apiRequest} from '@/lib/api/client';
export const DEVICE_PREF='nx.device-notifications.user';
export const DEVICE_TOKEN='nx.device-notifications.token';
export const CHANNEL='nexease-business';
export function safeNotificationRoute(value:unknown) {return typeof value==='string'&&/^\/(?!\/)[a-zA-Z0-9/_-]*$/.test(value)?value:'/home';}
export async function showDeviceNotice(title:string,body:string,url='/home') {
 if(!Capacitor.isNativePlatform()||!localStorage.getItem(DEVICE_PREF))return;
 if((await LocalNotifications.checkPermissions()).display!=='granted')return;
 await LocalNotifications.schedule({notifications:[{id:Math.floor(Date.now()%2000000000),title,body,channelId:CHANNEL,smallIcon:'ic_stat_nexease',extra:{url:safeNotificationRoute(url)}}]});
}
export async function disableDeviceNotifications() {
 localStorage.removeItem(DEVICE_PREF);
 window.dispatchEvent(new Event('nex-disable-device-notifications'));
 if(!Capacitor.isNativePlatform())return;
 const token=localStorage.getItem(DEVICE_TOKEN);
 if(token) {
  await apiRequest('/notifications/device/',{method:'DELETE',body:{token}});
  await PushNotifications.unregister();
  await PushNotifications.removeAllDeliveredNotifications();
  localStorage.removeItem(DEVICE_TOKEN);
 }
 const pending=await LocalNotifications.getPending();
 if(pending.notifications.length)await LocalNotifications.cancel(pending);
 await LocalNotifications.removeAllDeliveredNotifications();
}
