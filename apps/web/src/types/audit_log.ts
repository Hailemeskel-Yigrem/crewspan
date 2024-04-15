      /** Immutable audit trail for compliance and forensics. */
      export interface AuditLog {
        id: string;
        tenantId: string;
        actor_id: string | null;
action: string;
resource_type: string;
resource_id: string | null;
changes: Record<string, unknown> | null;
ip_address: string | null;
user_agent: string | null;
        createdAt: string;
        updatedAt: string;

      }

      export interface AuditLogCreate {
        actor_id: string | null;
action?: string;
resource_type?: string;
resource_id: string | null;
changes: Record<string, unknown> | null;
ip_address: string | null;
user_agent: string | null;
      }

      export interface AuditLogUpdate {
        actor_id?: string | null;
action?: string;
resource_type?: string;
resource_id?: string | null;
changes?: Record<string, unknown> | null;
ip_address?: string | null;
user_agent?: string | null;
      }

      export interface AuditLogListParams {
        page?: number;
        pageSize?: number;
        search?: string;
        orderBy?: string;
        orderDir?: 'asc' | 'desc';
          actor_id?: string | null;
action?: string;
resource_type?: string;
resource_id?: string | null;
      }

      export interface AuditLogListResponse {
        items: AuditLog[];
        total: number;
        page: number;
        pageSize: number;
        pages: number;
      }

      export function isAuditLogActive(record: AuditLog): boolean {
        const row = record as { isActive?: boolean; status?: string; deletedAt?: string | null };
        if (row.deletedAt) return false;
        if (typeof row.isActive === 'boolean') return row.isActive;
        if (row.status) return !['cancelled', 'inactive', 'void'].includes(row.status);
        return true;
      }

      export function auditLogDisplayName(record: AuditLog): string {
        const row = record as { name?: string; title?: string; orderNumber?: string; displayName?: string };
        return row.displayName || row.name || row.title || row.orderNumber || record.id.slice(0, 8);
      }
