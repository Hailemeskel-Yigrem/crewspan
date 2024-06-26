import { describe, it, expect, vi, beforeEach } from 'vitest';
import { inventoryitemApi } from '../inventory_item';

describe('inventory_itemApi', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ data: [], total: 0, page: 1, pageSize: 25, pages: 1 }),
    }));
  });

  it('list calls correct endpoint', async () => {
    await inventoryitemApi.list({ page: 1 });
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/inventory-items'),
      expect.any(Object),
    );
  });
});
