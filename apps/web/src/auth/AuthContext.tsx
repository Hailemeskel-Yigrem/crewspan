import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from 'react';
import { login as apiLogin } from '../api/client';

export interface AuthUser {
  id: string;
  email: string;
  fullName: string;
  tenantId: string;
}

interface AuthContextValue {
  user: AuthUser | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (email: string, password: string, tenantId: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

function decodeToken(token: string): AuthUser | null {
  try {
    const payload = JSON.parse(atob(token.split('.')[1] ?? ''));
    return {
      id: payload.sub ?? '',
      email: payload.email ?? '',
      fullName: payload.name ?? payload.email ?? 'User',
      tenantId: payload.tenant_id ?? localStorage.getItem('crewspan_tenant_id') ?? '',
    };
  } catch {
    return null;
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('crewspan_token'));
  const [user, setUser] = useState<AuthUser | null>(() => {
    const t = localStorage.getItem('crewspan_token');
    return t ? decodeToken(t) : null;
  });

  const login = useCallback(async (email: string, password: string, tenantId: string) => {
    localStorage.setItem('crewspan_tenant_id', tenantId);
    const { token: newToken } = await apiLogin(email, password, tenantId);
    localStorage.setItem('crewspan_token', newToken);
    setToken(newToken);
    setUser(decodeToken(newToken));
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem('crewspan_token');
    localStorage.removeItem('crewspan_tenant_id');
    setToken(null);
    setUser(null);
  }, []);

  const value = useMemo(
    () => ({ user, token, isAuthenticated: Boolean(token), login, logout }),
    [user, token, login, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuthContext(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuthContext must be used within AuthProvider');
  return ctx;
}
