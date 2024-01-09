import { useEffect, useState } from 'react';
import { slaPolicyApi } from '../api/sla_policy';
import { DataTable, type Column } from '../components/DataTable';
import { EmptyState } from '../components/EmptyState';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { PageHeader } from '../components/PageHeader';
import { StatusBadge } from '../components/StatusBadge';
import type { SlaPolicy } from '../types/sla_policy';

export function SlaPoliciesPage() {
  const [policies, setPolicies] = useState<SlaPolicy[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    void slaPolicyApi.list({ pageSize: 50 }).then((r) => { setPolicies(r.data); setLoading(false); }).catch(() => setLoading(false));
  }, []);

  const columns: Column<SlaPolicy>[] = [
    { key: 'name', header: 'Policy', render: (r) => (r as { name?: string }).name ?? r.id.slice(0, 8) },
    { key: 'priority', header: 'Priority', render: (r) => <StatusBadge status={(r as { priority?: string }).priority ?? 'normal'} /> },
    { key: 'response', header: 'Response (min)', render: (r) => String((r as { responseMinutes?: number }).responseMinutes ?? '—') },
    { key: 'resolution', header: 'Resolution (min)', render: (r) => String((r as { resolutionMinutes?: number }).resolutionMinutes ?? '—') },
    { key: 'active', header: 'Active', render: (r) => <StatusBadge status={(r as { isActive?: boolean }).isActive ? 'active' : 'inactive'} /> },
  ];

  return (
    <div className="page">
      <PageHeader title="SLA Policies" subtitle="Response and resolution targets by priority" />
      {loading ? <LoadingSpinner /> : policies.length === 0 ? (
        <EmptyState title="No SLA policies" description="Define policies to track breach risk on work orders." />
      ) : (
        <DataTable columns={columns} data={policies} keyExtractor={(r) => r.id} />
      )}
    </div>
  );
}
