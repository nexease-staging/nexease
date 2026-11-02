import {beforeEach,describe,it,expect,vi} from 'vitest';
import {Capacitor} from '@capacitor/core';
import {LocalNotifications} from '@capacitor/local-notifications';
import {PushNotifications} from '@capacitor/push-notifications';
import {apiRequest} from '@/lib/api/client';
import {safeNotificationRoute,showDeviceNotice,disableDeviceNotifications,DEVICE_PREF,DEVICE_TOKEN} from './device-notifications';
vi.mock('@capacitor/core',()=>({Capacitor:{isNativePlatform:vi.fn(()=>true)}}));
vi.mock('@capacitor/local-notifications',()=>({LocalNotifications:{checkPermissions:vi.fn(async()=>({display:'granted'})),schedule:vi.fn(),getPending:vi.fn(async()=>({notifications:[]})),removeAllDeliveredNotifications:vi.fn()}}));
vi.mock('@capacitor/push-notifications',()=>({PushNotifications:{unregister:vi.fn(),removeAllDeliveredNotifications:vi.fn()}}));
vi.mock('@/lib/api/client',()=>({apiRequest:vi.fn()}));
beforeEach(()=>{vi.clearAllMocks();localStorage.clear();vi.mocked(Capacitor.isNativePlatform).mockReturnValue(true)});
describe('Device notification isolation',()=>{
 it('rejects external navigation from a notification',()=>{expect(safeNotificationRoute('https://evil.test')).toBe('/home');expect(safeNotificationRoute('//evil.test')).toBe('/home');expect(safeNotificationRoute('/invoices')).toBe('/invoices')});
 it('does not notify without opt-in',async()=>{await showDeviceNotice('Saved','Invoice saved');expect(LocalNotifications.schedule).not.toHaveBeenCalled()});
 it('notifies when the device user opted in',async()=>{localStorage.setItem(DEVICE_PREF,'u');await showDeviceNotice('Saved','Invoice saved');expect(LocalNotifications.schedule).toHaveBeenCalledOnce()});
 it('removes the server device token and unregisters on disable',async()=>{localStorage.setItem(DEVICE_PREF,'u');localStorage.setItem(DEVICE_TOKEN,'token-value');await disableDeviceNotifications();expect(apiRequest).toHaveBeenCalledWith('/notifications/device/',{method:'DELETE',body:{token:'token-value'}});expect(PushNotifications.unregister).toHaveBeenCalledOnce();expect(localStorage.getItem(DEVICE_TOKEN)).toBeNull()});
});
