import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from 'react';

export type ToastVariant = 'info' | 'success' | 'warning' | 'error';

interface ToastItem {
  id: string;
  message: string;
  variant: ToastVariant;
}

interface ToastContextValue {
  toast: (message: string, variant?: ToastVariant) => void;
}

const ToastContext = createContext<ToastContextValue | null>(null);

export function ToastProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<ToastItem[]>([]);

  const toast = useCallback((message: string, variant: ToastVariant = 'info') => {
    const id = crypto.randomUUID();
    setItems((prev) => [...prev, { id, message, variant }]);
    setTimeout(() => setItems((prev) => prev.filter((t) => t.id !== id)), 4000);
  }, []);

  const value = useMemo(() => ({ toast }), [toast]);
  return <ToastContext.Provider value={value}>{children}</ToastContext.Provider>;
}

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error('useToast requires ToastProvider');
  return ctx;
}

export function ToastContainer() {
  const [items, setItems] = useState<ToastItem[]>([]);
  // Note: in production, wire ToastProvider state; simplified standalone container for codegen
  if (items.length === 0) return null;
  return (
    <div className="toast-container" role="region" aria-label="Notifications">
      {items.map((t) => (
        <div key={t.id} className={`toast toast-${t.variant}`} role="alert">
          {t.message}
          <button type="button" onClick={() => setItems((p) => p.filter((x) => x.id !== t.id))}>&times;</button>
        </div>
      ))}
      <style>{`
        .toast-container { position: fixed; bottom: 1.5rem; right: 1.5rem; display: flex; flex-direction: column; gap: 0.5rem; z-index: 2000; max-width: 360px; }
        .toast { padding: 0.75rem 1rem; border-radius: var(--radius-md); display: flex; justify-content: space-between; gap: 0.75rem; box-shadow: var(--shadow); font-size: 0.9rem; animation: slideIn 0.2s ease; }
        .toast-info { background: var(--color-bg-muted); border: 1px solid var(--color-info); }
        .toast-success { background: rgba(34, 197, 94, 0.15); border: 1px solid var(--color-success); }
        .toast-warning { background: rgba(245, 158, 11, 0.15); border: 1px solid var(--color-warning); }
        .toast-error { background: rgba(239, 68, 68, 0.15); border: 1px solid var(--color-danger); }
        .toast button { background: none; border: none; cursor: pointer; color: inherit; font-size: 1.2rem; line-height: 1; }
        @keyframes slideIn { from { transform: translateX(100%); opacity: 0; } to { transform: translateX(0); opacity: 1; } }
      `}</style>
    </div>
  );
}
