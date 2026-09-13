import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ConfirmDialog } from '../components/ConfirmDialog';
import { DataTable, type Column } from '../components/DataTable';
import { EmptyState } from '../components/EmptyState';
import { FormField } from '../components/FormField';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { Modal } from '../components/Modal';
import { PageHeader } from '../components/PageHeader';
import { StatusBadge } from '../components/StatusBadge';
import { useDebounce } from '../hooks/useDebounce';
import { usePagination } from '../hooks/usePagination';
import { useWorkOrders } from '../hooks/useWorkOrders';
import { workOrderApi } from '../api/work_order';
import type { WorkOrder } from '../types/work_order';
import { formatDateTime } from '../utils/dates';

const STATUS_OPTIONS = ['draft', 'submitted', 'in_progress', 'completed', 'cancelled'];
const PRIORITY_OPTIONS = ['low', 'normal', 'high', 'critical'];

export function WorkOrdersPage() {
  const navigate = useNavigate();
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [priorityFilter, setPriorityFilter] = useState('');
  const debouncedSearch = useDebounce(search, 300);
  const { workOrders, total, loading, error } = useWorkOrders({
    search: debouncedSearch || undefined,
    status: statusFilter || undefined,
    pageSize: 25,
  });
  const { page, setPage, totalPages } = usePagination({ total, pageSize: 25 });
  const [createOpen, setCreateOpen] = useState(false);
  const [form, setForm] = useState({ title: '', description: '', priority: 'normal', customerId: '' });
  const [saving, setSaving] = useState(false);
  const [deleteId, setDeleteId] = useState<string | null>(null);

  const filtered = useMemo(
    () => workOrders.filter((wo) => !priorityFilter || wo.priority === priorityFilter),
    [workOrders, priorityFilter],
  );

  const columns: Column<WorkOrder>[] = [
    { key: 'orderNumber', header: 'Order #', render: (r) => <code>{r.order_number}</code> },
    { key: 'title', header: 'Title', render: (r) => r.title },
    { key: 'status', header: 'Status', render: (r) => <StatusBadge status={r.status} /> },
    { key: 'priority', header: 'Priority', render: (r) => <StatusBadge status={r.priority} /> },
    { key: 'scheduledStart', header: 'Scheduled', render: (r) => r.scheduled_start ? formatDateTime(r.scheduled_start) : '—' },
  ];

  const handleCreate = async () => {
    setSaving(true);
    try {
      const created = await workOrderApi.create({ title: form.title, description: form.description, priority: form.priority, customer_id: form.customerId, site_id: '', order_number: `WO-${Date.now()}` });
      setCreateOpen(false);
      navigate(`/work-orders/${created.id}`);
    } catch { /* toast */ } finally { setSaving(false); }
  };

  return (
    <div className="page">
      <PageHeader title="Work Orders" subtitle="Track and manage field service jobs" actions={<button type="button" className="btn btn-primary" onClick={() => setCreateOpen(true)}>New Work Order</button>} />
      <div className="toolbar">
        <FormField label="Search" htmlFor="wo-search"><input id="wo-search" value={search} onChange={(e) => { setSearch(e.target.value); setPage(1); }} placeholder="Order #, title..." /></FormField>
        <FormField label="Status" htmlFor="wo-status"><select id="wo-status" value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}><option value="">All</option>{STATUS_OPTIONS.map((s) => <option key={s} value={s}>{s}</option>)}</select></FormField>
        <FormField label="Priority" htmlFor="wo-priority"><select id="wo-priority" value={priorityFilter} onChange={(e) => setPriorityFilter(e.target.value)}><option value="">All</option>{PRIORITY_OPTIONS.map((p) => <option key={p} value={p}>{p}</option>)}</select></FormField>
      </div>
      {loading ? <LoadingSpinner /> : error ? <div className="alert alert-error">{error}</div> : filtered.length === 0 ? (
        <EmptyState title="No work orders" description="Create your first work order to get started." actionLabel="New Work Order" onAction={() => setCreateOpen(true)} />
      ) : (
        <DataTable columns={columns} data={filtered} keyExtractor={(r) => r.id} onRowClick={(r) => navigate(`/work-orders/${r.id}`)} pagination={{ page, pageSize: 25, totalPages, onPageChange: setPage }} />
      )}
      <Modal open={createOpen} title="New Work Order" onClose={() => setCreateOpen(false)} footer={<><button type="button" className="btn btn-secondary" onClick={() => setCreateOpen(false)}>Cancel</button><button type="button" className="btn btn-primary" disabled={saving || !form.title} onClick={() => void handleCreate()}>{saving ? 'Creating...' : 'Create'}</button></>}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <FormField label="Title" htmlFor="wo-title" required><input id="wo-title" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} /></FormField>
          <FormField label="Customer ID" htmlFor="wo-customer" required><input id="wo-customer" value={form.customerId} onChange={(e) => setForm({ ...form, customerId: e.target.value })} /></FormField>
          <FormField label="Priority" htmlFor="wo-new-priority"><select id="wo-new-priority" value={form.priority} onChange={(e) => setForm({ ...form, priority: e.target.value })}>{PRIORITY_OPTIONS.map((p) => <option key={p} value={p}>{p}</option>)}</select></FormField>
          <FormField label="Description" htmlFor="wo-desc"><textarea id="wo-desc" rows={3} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} /></FormField>
        </div>
      </Modal>
      <ConfirmDialog open={Boolean(deleteId)} title="Delete work order?" message="This cannot be undone." variant="danger" onConfirm={() => setDeleteId(null)} onCancel={() => setDeleteId(null)} />
    </div>
  );
}
// history-note: evolutionary edit 24
