import { StatusBadge } from './StatusBadge';
import { formatDateTime } from '../utils/dates';

export interface WorkOrderCardData {
  id: string;
  orderNumber: string;
  title: string;
  status: string;
  priority: string;
  customerName?: string;
  scheduledStart?: string | null;
  technicianName?: string;
}

interface WorkOrderCardProps {
  workOrder: WorkOrderCardData;
  onClick?: (id: string) => void;
  selected?: boolean;
}

export function WorkOrderCard({ workOrder, onClick, selected }: WorkOrderCardProps) {
  return (
    <article
      className={`wo-card${selected ? ' selected' : ''}${onClick ? ' clickable' : ''}`}
      onClick={() => onClick?.(workOrder.id)}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
      onKeyDown={(e) => { if (onClick && (e.key === 'Enter' || e.key === ' ')) { e.preventDefault(); onClick(workOrder.id); } }}
    >
      <header>
        <span className="wo-number">{workOrder.orderNumber}</span>
        <StatusBadge status={workOrder.priority} size="sm" />
      </header>
      <h4>{workOrder.title}</h4>
      <div className="wo-meta">
        <StatusBadge status={workOrder.status} size="sm" />
        {workOrder.customerName ? <span>{workOrder.customerName}</span> : null}
      </div>
      {workOrder.scheduledStart ? <time>{formatDateTime(workOrder.scheduledStart)}</time> : null}
      {workOrder.technicianName ? <span className="wo-tech">{workOrder.technicianName}</span> : null}
      <style>{`
        .wo-card { background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-md); padding: 1rem; transition: border-color 0.15s; }
        .wo-card.clickable { cursor: pointer; }
        .wo-card.clickable:hover, .wo-card.selected { border-color: var(--color-primary); }
        .wo-card header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem; }
        .wo-number { font-family: monospace; font-size: 0.8rem; color: var(--color-text-muted); }
        .wo-card h4 { margin: 0 0 0.75rem; font-size: 0.95rem; }
        .wo-meta { display: flex; gap: 0.5rem; align-items: center; flex-wrap: wrap; margin-bottom: 0.5rem; font-size: 0.85rem; color: var(--color-text-muted); }
        .wo-tech { display: block; font-size: 0.8rem; color: var(--color-primary); margin-top: 0.35rem; }
      `}</style>
    </article>
  );
}
