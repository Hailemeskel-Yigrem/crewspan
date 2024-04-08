      /** Tenant webhook subscriptions for outbound event delivery. */
      export interface Webhook {
        id: string;
        tenantId: string;
        name: string;
url: string;
secret: string;
event_types: unknown[];
is_active: boolean;
failure_count: number;
last_triggered_at: string | null;
        createdAt: string;
        updatedAt: string;
        deletedAt: string | null;
      }

      export interface WebhookCreate {
        name?: string;
url?: string;
secret?: string;
event_types?: unknown[];
last_triggered_at: string | null;
      }

      export interface WebhookUpdate {
        name?: string;
url?: string;
secret?: string;
event_types?: unknown[];
is_active?: boolean;
failure_count?: number;
last_triggered_at?: string | null;
      }

      export interface WebhookListParams {
        page?: number;
        pageSize?: number;
        search?: string;
        orderBy?: string;
        orderDir?: 'asc' | 'desc';

      }

      export interface WebhookListResponse {
        items: Webhook[];
        total: number;
        page: number;
        pageSize: number;
        pages: number;
      }

      export function isWebhookActive(record: Webhook): boolean {
        const row = record as { isActive?: boolean; status?: string; deletedAt?: string | null };
        if (row.deletedAt) return false;
        if (typeof row.isActive === 'boolean') return row.isActive;
        if (row.status) return !['cancelled', 'inactive', 'void'].includes(row.status);
        return true;
      }

      export function webhookDisplayName(record: Webhook): string {
        const row = record as { name?: string; title?: string; orderNumber?: string; displayName?: string };
        return row.displayName || row.name || row.title || row.orderNumber || record.id.slice(0, 8);
      }
