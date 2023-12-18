interface StatusBadgeProps {
  status: string;
  size?: 'sm' | 'md';
}

const STATUS_COLORS: Record<string, string> = {
  draft: '#64748b', pending: '#f59e0b', active: '#22c55e', available: '#22c55e',
  in_progress: '#38bdf8', completed: '#14b8a6', cancelled: '#ef4444', critical: '#ef4444',
  high: '#f97316', normal: '#94a3b8', low: '#64748b', sent: '#22c55e', failed: '#ef4444',
};

export function StatusBadge({ status, size = 'md' }: StatusBadgeProps) {
  const color = STATUS_COLORS[status.toLowerCase()] ?? '#94a3b8';
  return (
    <span className={`status-badge status-badge-${size}`} style={{ ['--badge-color' as string]: color }}>
      {status.replace(/_/g, ' ')}
      <style>{`
        .status-badge { display: inline-block; padding: 0.15rem 0.5rem; border-radius: 999px; font-size: 0.75rem; font-weight: 500; text-transform: capitalize; background: color-mix(in srgb, var(--badge-color) 20%, transparent); color: var(--badge-color); border: 1px solid color-mix(in srgb, var(--badge-color) 40%, transparent); }
        .status-badge-sm { font-size: 0.65rem; padding: 0.1rem 0.4rem; }
      `}</style>
    </span>
  );
}
