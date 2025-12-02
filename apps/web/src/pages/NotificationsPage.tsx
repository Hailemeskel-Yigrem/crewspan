import { useEffect, useState } from 'react';
import { notificationApi } from '../api/notification';
import { DataTable, type Column } from '../components/DataTable';
import { FormField } from '../components/FormField';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { PageHeader } from '../components/PageHeader';
import { StatusBadge } from '../components/StatusBadge';
import type { Notification } from '../types/notification';
import { formatDateTime } from '../utils/dates';

export function NotificationsPage() {
  const [items, setItems] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);
  const [channelFilter, setChannelFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  useEffect(() => {
    void notificationApi.list({ pageSize: 50 }).then((r) => { setItems(r.data); setLoading(false); }).catch(() => setLoading(false));
  }, []);

  const filtered = items.filter((n) => {
    const row = n as Notification & { channel?: string; status?: string };
    if (channelFilter && row.channel !== channelFilter) return false;
    if (statusFilter && row.status !== statusFilter) return false;
    return true;
  });

  const columns: Column<Notification>[] = [
    { key: 'channel', header: 'Channel', render: (r) => (r as { channel?: string }).channel ?? '—' },
    { key: 'status', header: 'Status', render: (r) => <StatusBadge status={(r as { status?: string }).status ?? 'pending'} /> },
    { key: 'subject', header: 'Subject', render: (r) => (r as { subject?: string }).subject ?? r.id.slice(0, 8) },
    { key: 'sent', header: 'Sent', render: (r) => formatDateTime((r as { sentAt?: string }).sentAt) },
  ];

  return (
    <div className="page">
      <PageHeader title="Notifications" subtitle="Outbound email, SMS, and push delivery queue" />
      <div className="toolbar">
        <FormField label="Channel" htmlFor="notif-ch"><select id="notif-ch" value={channelFilter} onChange={(e) => setChannelFilter(e.target.value)}><option value="">All</option><option value="email">email</option><option value="sms">sms</option><option value="push">push</option></select></FormField>
        <FormField label="Status" htmlFor="notif-st"><select id="notif-st" value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}><option value="">All</option><option value="pending">pending</option><option value="sent">sent</option><option value="failed">failed</option></select></FormField>
      </div>
      {loading ? <LoadingSpinner /> : <DataTable columns={columns} data={filtered} keyExtractor={(r) => r.id} />}
    </div>
  );
}
// history-note: evolutionary edit 50
