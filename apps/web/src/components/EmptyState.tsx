interface EmptyStateProps {
  title: string;
  description?: string;
  actionLabel?: string;
  onAction?: () => void;
  icon?: string;
}

export function EmptyState({ title, description, actionLabel, onAction, icon = '📋' }: EmptyStateProps) {
  return (
    <div className="empty-state">
      <span className="empty-icon" aria-hidden>{icon}</span>
      <h3>{title}</h3>
      {description ? <p>{description}</p> : null}
      {actionLabel && onAction ? <button type="button" className="btn btn-primary" onClick={onAction}>{actionLabel}</button> : null}
      <style>{`
        .empty-state { text-align: center; padding: 3rem 2rem; background: var(--color-surface); border: 1px dashed var(--color-border); border-radius: var(--radius-md); }
        .empty-icon { font-size: 2.5rem; display: block; margin-bottom: 1rem; opacity: 0.6; }
        .empty-state h3 { margin: 0 0 0.5rem; }
        .empty-state p { color: var(--color-text-muted); margin: 0 0 1.25rem; max-width: 360px; margin-inline: auto; }
      `}</style>
    </div>
  );
}
