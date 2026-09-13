import { renderHook, act } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { usePagination } from './usePagination';

describe('usePagination', () => {
  it('calculates total pages', () => {
    const { result } = renderHook(() => usePagination({ total: 100, pageSize: 25 }));
    expect(result.current.totalPages).toBe(4);
  });

  it('updates page', () => {
    const { result } = renderHook(() => usePagination({ total: 50, pageSize: 10 }));
    act(() => result.current.setPage(3));
    expect(result.current.page).toBe(3);
  });
});
