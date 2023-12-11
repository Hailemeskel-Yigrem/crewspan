import { ReactNode } from 'react';

interface FormFieldProps {
  label: string;
  htmlFor: string;
  children: ReactNode;
  error?: string;
  hint?: string;
  required?: boolean;
}

export function FormField({ label, htmlFor, children, error, hint, required }: FormFieldProps) {
  return (
    <div className={`form-field${error ? ' has-error' : ''}`}>
      <label htmlFor={htmlFor}>{label}{required ? <span className="required">*</span> : null}</label>
      {children}
      {hint && !error ? <span className="form-hint">{hint}</span> : null}
      {error ? <span className="form-error" role="alert">{error}</span> : null}
      <style>{`
        .form-field { display: flex; flex-direction: column; gap: 0.35rem; flex: 1; min-width: 180px; }
        .form-field label { font-size: 0.85rem; font-weight: 500; color: var(--color-text-muted); }
        .required { color: var(--color-danger); margin-left: 0.2rem; }
        .form-hint { font-size: 0.75rem; color: var(--color-text-muted); }
        .form-error { font-size: 0.75rem; color: var(--color-danger); }
        .has-error input, .has-error select, .has-error textarea { border-color: var(--color-danger); }
      `}</style>
    </div>
  );
}
