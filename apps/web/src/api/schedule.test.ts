import { describe, it, expect, vi, beforeEach } from 'vitest';
import { scheduleApi } from './schedule';

describe('scheduleApi', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ data: [], total: 0, page: 1, pageSize: 25, pages: 1 }),
    }));
  });

  it('list calls correct endpoint', async () => {
    await scheduleApi.list({ page: 1 });
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/schedules'),
      expect.any(Object),
    );
  });
});
