import { useEffect, useState } from 'react';
import { invoiceApi } from '../api/invoice';
import { DataTable, type Column } from '../components/DataTable';
import { DateRangePicker, type DateRange } from '../components/DateRangePicker';
import { FormField } from '../components/FormField';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { PageHeader } from '../components/PageHeader';
import { StatusBadge } from '../components/StatusBadge';
import type { Invoice } from '../types/invoice';
import { formatCurrency } from '../utils/formatting';
import { formatDateTime } from '../utils/dates';

const STATUS_OPTIONS = ['draft', 'finalized', 'sent', 'paid', 'void'];

export function InvoicesPage() {
  const [items, setItems] = useState<Invoice[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('');
  const [range, setRange] = useState<DateRange>({ start: '', end: '' });

  useEffect(() => {
    void invoiceApi.list({ pageSize: 50 }).then((r) => { setItems(r.data); setLoading(false); });
  }, []);

  const filtered = items.filter((inv) => {
    const record = inv as Invoice & { status?: string; createdAt?: string };
    if (statusFilter && record.status !== statusFilter) return false;
    if (range.start && record.createdAt && record.createdAt < range.start) return false;
    if (range.end && record.createdAt && record.createdAt > range.end) return false;
    return true;
  });

  const columns: Column<Invoice>[] = [
    { key: 'number', header: 'Invoice #', render: (r) => <code>{(r as { invoiceNumber?: string }).invoiceNumber ?? r.id.slice(0, 8)}</code> },
    { key: 'status', header: 'Status', render: (r) => <StatusBadge status={(r as { status?: string }).status ?? 'draft'} /> },
    { key: 'total', header: 'Total', render: (r) => formatCurrency(Number((r as { totalAmount?: string }).totalAmount ?? 0)) },
    { key: 'created', header: 'Created', render: (r) => formatDateTime((r as { createdAt?: string }).createdAt) },
  ];

  return (
    <div className="page">
      <PageHeader title="Invoices" subtitle="Billing documents and payment tracking" />
      <div className="toolbar">
        <FormField label="Status" htmlFor="inv-status"><select id="inv-status" value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}><option value="">All</option>{STATUS_OPTIONS.map((s) => <option key={s} value={s}>{s}</option>)}</select></FormField>
        <DateRangePicker value={range} onChange={setRange} label="Created between" />
      </div>
      {loading ? <LoadingSpinner /> : <DataTable columns={columns} data={filtered} keyExtractor={(r) => r.id} />}
    </div>
  );
}
