      /** Outbound notification delivery records. */
      export interface Notification {
        id: string;
        tenantId: string;
        recipient_id: string | null;
recipient_email: string | null;
channel: string;
template_key: string;
subject: string | null;
body: string;
status: string;
sent_at: string | null;
payload_meta: Record<string, unknown> | null;
        createdAt: string;
        updatedAt: string;
        deletedAt: string | null;
      }

      export interface NotificationCreate {
        recipient_id: string | null;
recipient_email: string | null;
channel?: string;
template_key?: string;
subject: string | null;
body?: string;
sent_at: string | null;
payload_meta: Record<string, unknown> | null;
      }

      export interface NotificationUpdate {
        recipient_id?: string | null;
recipient_email?: string | null;
channel?: string;
template_key?: string;
subject?: string | null;
body?: string;
status?: string;
sent_at?: string | null;
payload_meta?: Record<string, unknown> | null;
      }

      export interface NotificationListParams {
        page?: number;
        pageSize?: number;
        search?: string;
        orderBy?: string;
        orderDir?: 'asc' | 'desc';
          recipient_id?: string | null;
channel?: string;
status?: string;
      }

      export interface NotificationListResponse {
        items: Notification[];
        total: number;
        page: number;
        pageSize: number;
        pages: number;
      }

      export function isNotificationActive(record: Notification): boolean {
        const row = record as { isActive?: boolean; status?: string; deletedAt?: string | null };
        if (row.deletedAt) return false;
        if (typeof row.isActive === 'boolean') return row.isActive;
        if (row.status) return !['cancelled', 'inactive', 'void'].includes(row.status);
        return true;
      }

      export function notificationDisplayName(record: Notification): string {
        const row = record as { name?: string; title?: string; orderNumber?: string; displayName?: string };
        return row.displayName || row.name || row.title || row.orderNumber || record.id.slice(0, 8);
      }
