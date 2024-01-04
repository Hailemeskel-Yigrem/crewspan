import { useEffect, useMemo, useState } from 'react';
import { inventoryItemApi } from '../api/inventory_item';
import { DataTable, type Column } from '../components/DataTable';
import { EmptyState } from '../components/EmptyState';
import { FormField } from '../components/FormField';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { PageHeader } from '../components/PageHeader';
import { StatusBadge } from '../components/StatusBadge';
import type { InventoryItem } from '../types/inventory_item';
import { formatNumber } from '../utils/formatting';

export function InventoryPage() {
  const [items, setItems] = useState<InventoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [skuFilter, setSkuFilter] = useState('');
  const [lowStockOnly, setLowStockOnly] = useState(false);

  useEffect(() => {
    void inventoryItemApi.list({ pageSize: 100 }).then((r) => { setItems(r.data); setLoading(false); });
  }, []);

  const filtered = useMemo(() => items.filter((row) => {
    const record = row as InventoryItem & { sku?: string; quantityOnHand?: number; reorderPoint?: number };
    if (skuFilter && !(record.sku ?? '').toLowerCase().includes(skuFilter.toLowerCase())) return false;
    if (lowStockOnly && (record.quantityOnHand ?? 0) > (record.reorderPoint ?? 0)) return false;
    return true;
  }), [items, skuFilter, lowStockOnly]);

  const columns: Column<InventoryItem>[] = [
    { key: 'sku', header: 'SKU', render: (r) => <code>{(r as { sku?: string }).sku ?? '—'}</code> },
    { key: 'name', header: 'Part', render: (r) => (r as { name?: string }).name ?? r.id.slice(0, 8) },
    { key: 'qty', header: 'On Hand', render: (r) => formatNumber((r as { quantityOnHand?: number }).quantityOnHand ?? 0) },
    { key: 'status', header: 'Status', render: (r) => {
      const qty = (r as { quantityOnHand?: number }).quantityOnHand ?? 0;
      const reorder = (r as { reorderPoint?: number }).reorderPoint ?? 0;
      return <StatusBadge status={qty <= reorder ? 'critical' : 'active'} />;
    }},
  ];

  return (
    <div className="page">
      <PageHeader title="Inventory" subtitle="Parts catalog, stock levels, and reorder alerts" />
      <div className="toolbar">
        <FormField label="SKU filter" htmlFor="inv-sku"><input id="inv-sku" value={skuFilter} onChange={(e) => setSkuFilter(e.target.value)} placeholder="Search SKU..." /></FormField>
        <FormField label="Low stock only" htmlFor="inv-low"><input id="inv-low" type="checkbox" checked={lowStockOnly} onChange={(e) => setLowStockOnly(e.target.checked)} /></FormField>
      </div>
      {loading ? <LoadingSpinner /> : filtered.length === 0 ? (
        <EmptyState title="No inventory items" description="Stock records will appear when parts are cataloged." />
      ) : (
        <DataTable columns={columns} data={filtered} keyExtractor={(r) => r.id} />
      )}
    </div>
  );
}
