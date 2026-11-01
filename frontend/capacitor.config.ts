import { KeyboardResize } from '@capacitor/keyboard';
import type { CapacitorConfig } from '@capacitor/cli';
const config: CapacitorConfig = {
  appId: 'com.nexease.business',
  appName: 'NexEase',
  webDir: 'out',
  server: { androidScheme: 'https', hostname: 'localhost' },
  android: { allowMixedContent: false },
  plugins: {
    CapacitorHttp: { enabled: true },
    CapacitorCookies: { enabled: true },
    Keyboard: { resize: KeyboardResize.Body, resizeOnFullScreen: true },
  },
};
export default config;
