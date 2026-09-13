import { describe, it, expect, vi, beforeEach } from 'vitest';
import { slaPolicyApi } from './sla_policy';

describe('sla_policyApi', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ data: [], total: 0, page: 1, pageSize: 25, pages: 1 }),
    }));
  });

  it('list calls correct endpoint', async () => {
    await slaPolicyApi.list({ page: 1 });
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/sla-policies'),
      expect.any(Object),
    );
  });
});
