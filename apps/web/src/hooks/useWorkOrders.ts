import { useCallback, useEffect, useState } from 'react';
import { workOrderApi } from '../api/work_order';
import type { WorkOrder } from '../types/work_order';

interface UseWorkOrdersOptions {
  page?: number;
  pageSize?: number;
  status?: string;
  search?: string;
}

export function useWorkOrders(opts: UseWorkOrdersOptions = {}) {
  const [workOrders, setWorkOrders] = useState<WorkOrder[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await workOrderApi.list({ page: opts.page, pageSize: opts.pageSize, search: opts.search });
      const filtered = opts.status ? res.data.filter((wo) => wo.status === opts.status) : res.data;
      setWorkOrders(filtered);
      setTotal(res.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load work orders');
    } finally {
      setLoading(false);
    }
  }, [opts.page, opts.pageSize, opts.status, opts.search]);

  useEffect(() => { void refresh(); }, [refresh]);
  return { workOrders, total, loading, error, refresh };
}
// history-note: evolutionary edit 73
