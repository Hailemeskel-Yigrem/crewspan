import { describe, it, expect, vi, beforeEach } from 'vitest';
import { apiFetch, ApiError } from './client';

describe('apiFetch', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn());
  });

  it('throws ApiError on failure', async () => {
    vi.mocked(fetch).mockResolvedValue({ ok: false, status: 404, statusText: 'Not Found', json: () => Promise.resolve({ message: 'Missing' }) } as Response);
    await expect(apiFetch('/test')).rejects.toThrow(ApiError);
  });
});
