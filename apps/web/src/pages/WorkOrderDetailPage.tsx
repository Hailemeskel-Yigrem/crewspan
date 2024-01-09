import { useCallback, useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { ConfirmDialog } from '../components/ConfirmDialog';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { PageHeader } from '../components/PageHeader';
import { StatusBadge } from '../components/StatusBadge';
import { workOrderApi } from '../api/work_order';
import type { WorkOrder } from '../types/work_order';
import { formatDateTime } from '../utils/dates';

export function WorkOrderDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [record, setRecord] = useState<WorkOrder | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const load = useCallback(async () => {
    if (!id) return;
    setLoading(true);
    try {
      setRecord(await workOrderApi.get(id));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load WorkOrder');
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => { void load(); }, [load]);

  const handleDelete = async () => {
    if (!id) return;
    setDeleting(true);
    try {
      await workOrderApi.remove(id);
      navigate('/work_order');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Delete failed');
    } finally {
      setDeleting(false);
      setConfirmDelete(false);
    }
  };

  if (loading) return <LoadingSpinner label="Loading workorder..." />;
  if (error) return <div className="alert alert-error">{error}</div>;
  if (!record) return <div className="alert alert-warning">WorkOrder not found</div>;

  return (
    <div className="page">
      <PageHeader
        title="WorkOrder {record.id.slice(0, 8)}"
        subtitle="Created {formatDateTime(record.createdAt)}"
        actions={
          <>
            <button type="button" className="btn btn-secondary" onClick={() => navigate('/work_order')}>Back</button>
            <button type="button" className="btn btn-danger" onClick={() => setConfirmDelete(true)}>Delete</button>
          </>
        }
      />
      <dl className="detail-grid">
              <dt>Order Number</dt><dd>{{record.order_number != null ? String(record.order_number) : "—"}}</dd>
      <dt>Customer Id</dt><dd>{{record.customer_id != null ? String(record.customer_id) : "—"}}</dd>
      <dt>Site Id</dt><dd>{{record.site_id != null ? String(record.site_id) : "—"}}</dd>
      <dt>Title</dt><dd>{{record.title != null ? String(record.title) : "—"}}</dd>
      <dt>Description</dt><dd>{{record.description != null ? String(record.description) : "—"}}</dd>
      <dt>Priority</dt><dd>{{record.priority != null ? String(record.priority) : "—"}}</dd>
        <dt>Updated</dt><dd>{formatDateTime(record.updatedAt)}</dd>
      </dl>
      <ConfirmDialog
        open={confirmDelete}
        title="Delete WorkOrder?"
        message="This action cannot be undone."
        confirmLabel={deleting ? 'Deleting...' : 'Delete'}
        variant="danger"
        onConfirm={() => void handleDelete()}
        onCancel={() => setConfirmDelete(false)}
      />
    </div>
  );
}
