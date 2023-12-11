interface LoadingSpinnerProps {
  label?: string;
  size?: 'sm' | 'md' | 'lg';
}

export function LoadingSpinner({ label, size = 'md' }: LoadingSpinnerProps) {
  return (
    <div className={`spinner-wrap spinner-${size}`} role="status" aria-label={label ?? 'Loading'}>
      <div className="spinner" />
      {label ? <span>{label}</span> : null}
      <style>{`
        .spinner-wrap { display: flex; flex-direction: column; align-items: center; gap: 0.75rem; padding: 2rem; color: var(--color-text-muted); }
        .spinner { border: 3px solid var(--color-border); border-top-color: var(--color-primary); border-radius: 50%; animation: spin 0.8s linear infinite; }
        .spinner-sm .spinner { width: 16px; height: 16px; border-width: 2px; }
        .spinner-md .spinner { width: 32px; height: 32px; }
        .spinner-lg .spinner { width: 48px; height: 48px; border-width: 4px; }
        @keyframes spin { to { transform: rotate(360deg); } }
      `}</style>
    </div>
  );
}
