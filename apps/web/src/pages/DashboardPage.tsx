import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { MetricCard } from '../components/MetricCard';
import { PageHeader } from '../components/PageHeader';
import { WorkOrderCard, type WorkOrderCardData } from '../components/WorkOrderCard';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { useWorkOrders } from '../hooks/useWorkOrders';
import { formatCurrency } from '../utils/formatting';

export function DashboardPage() {
  const navigate = useNavigate();
  const { workOrders, loading, error, refresh } = useWorkOrders({ pageSize: 6, status: 'in_progress' });
  const [metrics, setMetrics] = useState({ openOrders: 0, activeTechs: 0, revenue: 0, slaBreaches: 0 });

  useEffect(() => {
    // Simulated dashboard metrics — production would call /api/v1/reports/dashboard
    setMetrics({ openOrders: 47, activeTechs: 12, revenue: 128450, slaBreaches: 3 });
  }, []);

  const cards: WorkOrderCardData[] = workOrders.map((wo) => ({
    id: wo.id,
    orderNumber: wo.order_number,
    title: wo.title,
    status: wo.status,
    priority: wo.priority,
    scheduledStart: wo.scheduled_start,
  }));

  return (
    <div className="page">
      <PageHeader title="Operations Dashboard" subtitle="Real-time field service overview" actions={<button type="button" className="btn btn-secondary" onClick={() => void refresh()}>Refresh</button>} />
      <div className="metric-grid">
        <MetricCard label="Open Work Orders" value={metrics.openOrders} delta="+4 today" deltaPositive={false} icon="🔧" />
        <MetricCard label="Active Technicians" value={metrics.activeTechs} delta="92% utilization" deltaPositive icon="👷" />
        <MetricCard label="Revenue (MTD)" value={formatCurrency(metrics.revenue)} delta="+12.4%" deltaPositive icon="💰" />
        <MetricCard label="SLA Breaches" value={metrics.slaBreaches} delta="-2 vs last week" deltaPositive icon="⚠️" />
      </div>
      <h2 style={{ fontSize: '1.1rem', marginBottom: '1rem' }}>In Progress</h2>
      {loading ? <LoadingSpinner label="Loading work orders..." /> : null}
      {error ? <div className="alert alert-error">{error}</div> : null}
      <div className="card-grid">
        {cards.map((wo) => (
          <WorkOrderCard key={wo.id} workOrder={wo} onClick={(id) => navigate(`/work-orders/${id}`)} />
        ))}
      </div>
    </div>
  );
}
