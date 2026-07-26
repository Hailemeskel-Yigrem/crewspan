import { FormEvent, useState } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { FormField } from '../components/FormField';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { useAuth } from '../hooks/useAuth';

export function LoginPage() {
  const { login, isAuthenticated } = useAuth();
  const location = useLocation();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [tenantId, setTenantId] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const from = (location.state as { from?: { pathname: string } })?.from?.pathname ?? '/';

  if (isAuthenticated) return <Navigate to={from} replace />;

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login(email, password, tenantId);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-brand">
          <span className="login-logo">Fieldspan</span>
          <p className="login-tagline">Field service operations platform</p>
        </div>
        <form onSubmit={(e) => void handleSubmit(e)} className="login-form">
          <FormField label="Tenant ID" htmlFor="tenant-id" required>
            <input id="tenant-id" value={tenantId} onChange={(e) => setTenantId(e.target.value)} required autoComplete="organization" />
          </FormField>
          <FormField label="Email" htmlFor="email" required>
            <input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required autoComplete="username" />
          </FormField>
          <FormField label="Password" htmlFor="password" required>
            <input id="password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required autoComplete="current-password" />
          </FormField>
          {error ? <div className="alert alert-error">{error}</div> : null}
          <button type="submit" className="btn btn-primary login-submit" disabled={loading}>
            {loading ? <LoadingSpinner size="sm" /> : 'Sign in'}
          </button>
        </form>
      </div>
      <style>{`
        .login-page { min-height: 100vh; display: flex; align-items: center; justify-content: center; background: linear-gradient(135deg, #0f172a 0%, #134e4a 100%); }
        .login-card { width: 100%; max-width: 420px; background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-lg); padding: 2rem; box-shadow: var(--shadow); }
        .login-logo { font-size: 1.75rem; font-weight: 700; color: var(--color-primary); letter-spacing: -0.02em; }
        .login-tagline { color: var(--color-text-muted); margin: 0.25rem 0 1.5rem; font-size: 0.9rem; }
        .login-form { display: flex; flex-direction: column; gap: 1rem; }
        .login-submit { width: 100%; justify-content: center; margin-top: 0.5rem; }
      `}</style>
    </div>
  );
}
