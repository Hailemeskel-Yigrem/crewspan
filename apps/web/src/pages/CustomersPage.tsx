import { useCallback, useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { customerApi } from '../api/customer';
import { DataTable, type Column } from '../components/DataTable';
import { EmptyState } from '../components/EmptyState';
import { FormField } from '../components/FormField';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { Modal } from '../components/Modal';
import { PageHeader } from '../components/PageHeader';
import { StatusBadge } from '../components/StatusBadge';
import { useDebounce } from '../hooks/useDebounce';
import { usePagination } from '../hooks/usePagination';
import type { Customer } from '../types/customer';
import { formatCurrency } from '../utils/formatting';

const TYPE_OPTIONS = ['residential', 'commercial', 'government'];

export function CustomersPage() {
  const navigate = useNavigate();
  const [items, setItems] = useState<Customer[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [activeOnly, setActiveOnly] = useState(true);
  const debouncedSearch = useDebounce(search, 300);
  const { page, setPage, totalPages } = usePagination({ total, pageSize: 25 });
  const [createOpen, setCreateOpen] = useState(false);
  const [form, setForm] = useState({ name: '', accountNumber: '', customerType: 'commercial', billingEmail: '' });

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await customerApi.list({ page, pageSize: 25, search: debouncedSearch || undefined });
      setItems(res.data);
      setTotal(res.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load customers');
    } finally {
      setLoading(false);
    }
  }, [page, debouncedSearch]);

  useEffect(() => { void load(); }, [load]);

  const filtered = useMemo(() => items.filter((c) => {
    if (typeFilter && c.customer_type !== typeFilter) return false;
    if (activeOnly && !c.is_active) return false;
    return true;
  }), [items, typeFilter, activeOnly]);

  const columns: Column<Customer>[] = [
    { key: 'accountNumber', header: 'Account #', render: (r) => <code>{r.account_number}</code> },
    { key: 'name', header: 'Name', render: (r) => r.name },
    { key: 'customerType', header: 'Type', render: (r) => <StatusBadge status={r.customer_type} /> },
    { key: 'creditLimit', header: 'Credit Limit', render: (r) => r.credit_limit ? formatCurrency(Number(r.credit_limit)) : '—' },
    { key: 'isActive', header: 'Status', render: (r) => <StatusBadge status={r.is_active ? 'active' : 'inactive'} /> },
  ];

  const handleCreate = async () => {
    await customerApi.create({
      name: form.name,
      account_number: form.accountNumber,
      customer_type: form.customerType,
      billing_email: form.billingEmail || null,
      is_active: true,
      payment_terms_days: 30,
    });
    setCreateOpen(false);
    void load();
  };

  return (
    <div className="page">
      <PageHeader title="Customers" subtitle="Customer accounts and billing profiles" actions={
        <button type="button" className="btn btn-primary" onClick={() => setCreateOpen(true)}>New Customer</button>
      } />
      <div className="toolbar">
        <FormField label="Search" htmlFor="cust-search"><input id="cust-search" value={search} onChange={(e) => { setSearch(e.target.value); setPage(1); }} placeholder="Name or account #" /></FormField>
        <FormField label="Type" htmlFor="cust-type"><select id="cust-type" value={typeFilter} onChange={(e) => setTypeFilter(e.target.value)}><option value="">All types</option>{TYPE_OPTIONS.map((t) => <option key={t} value={t}>{t}</option>)}</select></FormField>
        <FormField label="Active only" htmlFor="cust-active"><input id="cust-active" type="checkbox" checked={activeOnly} onChange={(e) => setActiveOnly(e.target.checked)} /></FormField>
      </div>
      {loading ? <LoadingSpinner /> : error ? <div className="alert alert-error">{error}</div> : filtered.length === 0 ? (
        <EmptyState title="No customers" description="Add your first customer account." actionLabel="New Customer" onAction={() => setCreateOpen(true)} />
      ) : (
        <DataTable columns={columns} data={filtered} keyExtractor={(r) => r.id} onRowClick={(r) => navigate(`/customers/${r.id}`)} pagination={{ page, pageSize: 25, totalPages, onPageChange: setPage }} />
      )}
      <Modal open={createOpen} title="New Customer" onClose={() => setCreateOpen(false)} footer={<><button type="button" className="btn btn-secondary" onClick={() => setCreateOpen(false)}>Cancel</button><button type="button" className="btn btn-primary" disabled={!form.name || !form.accountNumber} onClick={() => void handleCreate()}>Create</button></>}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <FormField label="Name" htmlFor="cust-name" required><input id="cust-name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} /></FormField>
          <FormField label="Account Number" htmlFor="cust-acct" required><input id="cust-acct" value={form.accountNumber} onChange={(e) => setForm({ ...form, accountNumber: e.target.value })} /></FormField>
          <FormField label="Type" htmlFor="cust-ctype"><select id="cust-ctype" value={form.customerType} onChange={(e) => setForm({ ...form, customerType: e.target.value })}>{TYPE_OPTIONS.map((t) => <option key={t} value={t}>{t}</option>)}</select></FormField>
          <FormField label="Billing Email" htmlFor="cust-email"><input id="cust-email" type="email" value={form.billingEmail} onChange={(e) => setForm({ ...form, billingEmail: e.target.value })} /></FormField>
        </div>
      </Modal>
    </div>
  );
}
// history-note: evolutionary edit 35
