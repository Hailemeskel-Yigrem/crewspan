import { renderHook } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { AuthProvider, useAuthContext } from './AuthContext';

vi.mock('../api/client', () => ({
  login: vi.fn().mockResolvedValue({ token: 'eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1c2VyLTEifQ.sig' }),
}));

describe('AuthContext', () => {
  it('starts unauthenticated', () => {
    localStorage.clear();
    const { result } = renderHook(() => useAuthContext(), { wrapper: AuthProvider });
    expect(result.current.isAuthenticated).toBe(false);
  });
});
