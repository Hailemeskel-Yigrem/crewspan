import { useEffect, useState } from 'react';
import { DataTable, type Column } from '../components/DataTable';
import { DateRangePicker, type DateRange } from '../components/DateRangePicker';
import { FormField } from '../components/FormField';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { PageHeader } from '../components/PageHeader';
import { formatDateTime } from '../utils/dates';

interface AuditEntry { id: string; action: string; resource: string; actor: string; timestamp: string; details: string }

export function AuditLogPage() {
  const [entries, setEntries] = useState<AuditEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionFilter, setActionFilter] = useState('');
  const [range, setRange] = useState<DateRange>({ start: '', end: '' });

  useEffect(() => {
    setLoading(true);
    setTimeout(() => {
      setEntries([
        { id: '1', action: 'update', resource: 'work_order', actor: 'user@example.com', timestamp: new Date().toISOString(), details: 'Status draft → submitted' },
        { id: '2', action: 'create', resource: 'invoice', actor: 'billing@example.com', timestamp: new Date(Date.now() - 3600000).toISOString(), details: 'Invoice INV-1042 created' },
      ]);
      setLoading(false);
    }, 300);
  }, []);

  const filtered = entries.filter((e) => !actionFilter || e.action === actionFilter);

  const columns: Column<AuditEntry>[] = [
    { key: 'timestamp', header: 'When', render: (r) => formatDateTime(r.timestamp) },
    { key: 'action', header: 'Action', render: (r) => r.action },
    { key: 'resource', header: 'Resource', render: (r) => r.resource },
    { key: 'actor', header: 'Actor', render: (r) => r.actor },
    { key: 'details', header: 'Details', render: (r) => r.details },
  ];

  return (
    <div className="page">
      <PageHeader title="Audit Log" subtitle="Immutable compliance trail for tenant activity" />
      <div className="toolbar">
        <FormField label="Action" htmlFor="audit-action"><select id="audit-action" value={actionFilter} onChange={(e) => setActionFilter(e.target.value)}><option value="">All</option><option value="create">create</option><option value="update">update</option><option value="delete">delete</option></select></FormField>
        <DateRangePicker value={range} onChange={setRange} />
      </div>
      {loading ? <LoadingSpinner /> : <DataTable columns={columns} data={filtered} keyExtractor={(r) => r.id} />}
    </div>
  );
}
