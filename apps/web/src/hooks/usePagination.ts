import { useMemo, useState } from 'react';

interface UsePaginationOptions {
  total: number;
  pageSize?: number;
  initialPage?: number;
}

export function usePagination({ total, pageSize = 25, initialPage = 1 }: UsePaginationOptions) {
  const [page, setPage] = useState(initialPage);
  const totalPages = useMemo(() => Math.max(1, Math.ceil(total / pageSize)), [total, pageSize]);
  const clampedPage = Math.min(page, totalPages);
  return { page: clampedPage, pageSize, setPage, totalPages, offset: (clampedPage - 1) * pageSize };
}
