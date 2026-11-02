import { describe, expect, it } from 'vitest';
import { normalizeServer } from './mobile-config';
describe('mobile connection boundary', () => {
  it('accepts a TLS domain and the existing API prefix', () => {
    expect(normalizeServer(' https://api.nexease.test/ ')).toBe('https://api.nexease.test/api/v1');
    expect(normalizeServer('https://api.nexease.test/api/v1/')).toBe('https://api.nexease.test/api/v1');
  });
  it.each(['http://example.com', 'https://user:password@example.com', 'javascript:alert(1)', 'https://example.com/login', 'https://example.com/?token=secret', 'https://example.com/#token'])('rejects unsafe or incorrect addresses: %s', value => {
    expect(() => normalizeServer(value)).toThrow();
  });
});
