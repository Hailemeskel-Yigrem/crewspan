import { useEffect, useState } from 'react';
import { MetricCard } from '../components/MetricCard';
import { PageHeader } from '../components/PageHeader';
import { DateRangePicker, type DateRange } from '../components/DateRangePicker';
import { FormField } from '../components/FormField';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { formatCurrency, formatNumber } from '../utils/formatting';

interface ReportSnapshot {
  openWorkOrders: number;
  completedJobs: number;
  revenue: number;
  avgResponseMinutes: number;
  technicianUtilization: number;
}

export function ReportsPage() {
  const [loading, setLoading] = useState(true);
  const [range, setRange] = useState<DateRange>({ start: '', end: '' });
  const [snapshot, setSnapshot] = useState<ReportSnapshot | null>(null);
  const [exportFormat, setExportFormat] = useState<'csv' | 'json'>('csv');

  useEffect(() => {
    setLoading(true);
    const timer = setTimeout(() => {
      setSnapshot({
        openWorkOrders: 47,
        completedJobs: 128,
        revenue: 284500,
        avgResponseMinutes: 42,
        technicianUtilization: 87,
      });
      setLoading(false);
    }, 400);
    return () => clearTimeout(timer);
  }, [range]);

  const handleExport = () => {
    window.alert(`Export queued (${exportFormat.toUpperCase()}) — download will start when ready.`);
  };

  return (
    <div className="page">
      <PageHeader title="Reports" subtitle="Operational analytics and data exports" actions={
        <button type="button" className="btn btn-primary" onClick={handleExport}>Export</button>
      } />
      <div className="toolbar">
        <DateRangePicker value={range} onChange={setRange} label="Report period" />
        <FormField label="Export format" htmlFor="rep-fmt">
          <select id="rep-fmt" value={exportFormat} onChange={(e) => setExportFormat(e.target.value as 'csv' | 'json')}>
            <option value="csv">CSV</option>
            <option value="json">JSON</option>
          </select>
        </FormField>
      </div>
      {loading || !snapshot ? <LoadingSpinner label="Computing metrics..." /> : (
        <>
          <div className="metric-grid">
            <MetricCard label="Open Work Orders" value={snapshot.openWorkOrders} icon="🔧" />
            <MetricCard label="Completed Jobs" value={snapshot.completedJobs} delta="+18% vs prior period" deltaPositive icon="✅" />
            <MetricCard label="Revenue" value={formatCurrency(snapshot.revenue)} icon="💰" />
            <MetricCard label="Avg Response" value={`${snapshot.avgResponseMinutes}m`} icon="⏱️" />
            <MetricCard label="Tech Utilization" value={`${formatNumber(snapshot.technicianUtilization)}%`} icon="👷" />
          </div>
          <section style={{ marginTop: '2rem', padding: '1.5rem', background: 'var(--color-surface)', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border)' }}>
            <h2 style={{ marginTop: 0, fontSize: '1.1rem' }}>Scheduled Reports</h2>
            <p style={{ color: 'var(--color-text-muted)' }}>Daily digest at 06:00 tenant timezone · Weekly utilization summary on Mondays · Monthly revenue rollup on the 1st.</p>
          </section>
        </>
      )}
    </div>
  );
}
