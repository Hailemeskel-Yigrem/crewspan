interface MetricCardProps {
  label: string;
  value: string | number;
  delta?: string;
  deltaPositive?: boolean;
  icon?: string;
}

export function MetricCard({ label, value, delta, deltaPositive, icon }: MetricCardProps) {
  return (
    <div className="metric-card">
      <div className="metric-top">
        <span className="metric-label">{label}</span>
        {icon ? <span className="metric-icon" aria-hidden>{icon}</span> : null}
      </div>
      <div className="metric-value">{value}</div>
      {delta ? <div className={`metric-delta${deltaPositive ? ' positive' : ' negative'}`}>{delta}</div> : null}
      <style>{`
        .metric-card { background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-md); padding: 1.25rem; }
        .metric-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem; }
        .metric-label { font-size: 0.8rem; color: var(--color-text-muted); text-transform: uppercase; letter-spacing: 0.04em; }
        .metric-icon { opacity: 0.5; }
        .metric-value { font-size: 1.75rem; font-weight: 700; color: var(--color-text); line-height: 1.2; }
        .metric-delta { font-size: 0.8rem; margin-top: 0.35rem; }
        .metric-delta.positive { color: var(--color-success); }
        .metric-delta.negative { color: var(--color-danger); }
      `}</style>
    </div>
  );
}
