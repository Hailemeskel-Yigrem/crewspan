interface TechnicianAvatarProps {
  name: string;
  status?: string;
  size?: number;
  showStatus?: boolean;
}

const STATUS_DOT: Record<string, string> = {
  available: '#22c55e', busy: '#f59e0b', offline: '#64748b', on_leave: '#ef4444',
};

function initials(name: string): string {
  return name.split(/\s+/).map((p) => p[0]).slice(0, 2).join('').toUpperCase();
}

export function TechnicianAvatar({ name, status = 'available', size = 40, showStatus = true }: TechnicianAvatarProps) {
  const dotColor = STATUS_DOT[status] ?? '#64748b';
  return (
    <div className="tech-avatar" style={{ width: size, height: size, fontSize: size * 0.35 }} title={`${name} (${status})`}>
      <span className="tech-initials">{initials(name)}</span>
      {showStatus ? <span className="tech-status-dot" style={{ background: dotColor }} /> : null}
      <style>{`
        .tech-avatar { position: relative; border-radius: 50%; background: var(--color-bg-muted); border: 2px solid var(--color-border); display: inline-flex; align-items: center; justify-content: center; font-weight: 600; color: var(--color-primary); }
        .tech-status-dot { position: absolute; bottom: 0; right: 0; width: 30%; height: 30%; border-radius: 50%; border: 2px solid var(--color-surface); }
      `}</style>
    </div>
  );
}
