export const STATUS_COLORS: Record<string, string> = {
  draft: '#64748b', pending: '#f59e0b', submitted: '#38bdf8', in_progress: '#0ea5e9',
  completed: '#14b8a6', cancelled: '#ef4444', active: '#22c55e', inactive: '#64748b',
  available: '#22c55e', busy: '#f97316', offline: '#475569', critical: '#dc2626',
  high: '#ea580c', normal: '#94a3b8', low: '#64748b',
};

export function statusColor(status: string): string {
  return STATUS_COLORS[status.toLowerCase()] ?? '#94a3b8';
}

export function priorityWeight(priority: string): number {
  const weights: Record<string, number> = { critical: 4, high: 3, normal: 2, low: 1 };
  return weights[priority.toLowerCase()] ?? 0;
}
