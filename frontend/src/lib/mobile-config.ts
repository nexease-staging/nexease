export const SERVER_KEY = 'nexease.mobile.server.v1';
export function normalizeServer(value: string): string {
  const url = new URL(value.trim());
  if (url.protocol !== 'https:' || url.username || url.password || url.search || url.hash) {
    throw new Error('Enter your secure HTTPS backend address, without credentials or query parameters.');
  }
  const path = url.pathname.replace(/\/+$/, '');
  if (path && path !== '/api/v1') throw new Error('Use the backend domain or its /api/v1 address.');
  return `${url.origin}/api/v1`;
}
export function savedServer(): string {
  if (typeof window === 'undefined') return '';
  try { const value = localStorage.getItem(SERVER_KEY); return value ? normalizeServer(value) : ''; }
  catch { return ''; }
}
