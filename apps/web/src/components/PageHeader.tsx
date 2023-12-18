import { ReactNode } from 'react';

interface PageHeaderProps {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
  breadcrumbs?: { label: string; href?: string }[];
}

export function PageHeader({ title, subtitle, actions, breadcrumbs }: PageHeaderProps) {
  return (
    <header className="page-header">
      {breadcrumbs?.length ? (
        <nav className="breadcrumbs" aria-label="Breadcrumb">
          {breadcrumbs.map((b, i) => (
            <span key={b.label}>
              {i > 0 ? <span className="sep">/</span> : null}
              {b.href ? <a href={b.href}>{b.label}</a> : <span>{b.label}</span>}
            </span>
          ))}
        </nav>
      ) : null}
      <div className="page-header-row">
        <div>
          <h1>{title}</h1>
          {subtitle ? <p className="subtitle">{subtitle}</p> : null}
        </div>
        {actions ? <div className="page-actions">{actions}</div> : null}
      </div>
      <style>{`
        .page-header { margin-bottom: 1.5rem; }
        .breadcrumbs { font-size: 0.8rem; color: var(--color-text-muted); margin-bottom: 0.5rem; }
        .breadcrumbs .sep { margin: 0 0.35rem; }
        .page-header-row { display: flex; justify-content: space-between; align-items: flex-start; gap: 1rem; flex-wrap: wrap; }
        .page-header h1 { margin: 0; font-size: 1.5rem; font-weight: 600; }
        .subtitle { margin: 0.25rem 0 0; color: var(--color-text-muted); font-size: 0.9rem; }
        .page-actions { display: flex; gap: 0.5rem; flex-wrap: wrap; }
      `}</style>
    </header>
  );
}
