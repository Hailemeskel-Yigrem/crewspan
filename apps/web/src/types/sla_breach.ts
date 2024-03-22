      /** Recorded SLA violations for reporting and escalation. */
      export interface SlaBreach {
        id: string;
        tenantId: string;
        work_order_id: string;
sla_policy_id: string;
breach_type: string;
expected_at: string;
detected_at: string;
minutes_overdue: number;
acknowledged: boolean;
escalation_level: number;
        createdAt: string;
        updatedAt: string;
        deletedAt: string | null;
      }

      export interface SlaBreachCreate {
        work_order_id?: string;
sla_policy_id?: string;
breach_type?: string;
expected_at?: string;
detected_at?: string;
minutes_overdue?: number;
      }

      export interface SlaBreachUpdate {
        work_order_id?: string;
sla_policy_id?: string;
breach_type?: string;
expected_at?: string;
detected_at?: string;
minutes_overdue?: number;
acknowledged?: boolean;
escalation_level?: number;
      }

      export interface SlaBreachListParams {
        page?: number;
        pageSize?: number;
        search?: string;
        orderBy?: string;
        orderDir?: 'asc' | 'desc';
          work_order_id?: string;
sla_policy_id?: string;
breach_type?: string;
      }

      export interface SlaBreachListResponse {
        items: SlaBreach[];
        total: number;
        page: number;
        pageSize: number;
        pages: number;
      }

      export function isSlaBreachActive(record: SlaBreach): boolean {
        const row = record as { isActive?: boolean; status?: string; deletedAt?: string | null };
        if (row.deletedAt) return false;
        if (typeof row.isActive === 'boolean') return row.isActive;
        if (row.status) return !['cancelled', 'inactive', 'void'].includes(row.status);
        return true;
      }

      export function slaBreachDisplayName(record: SlaBreach): string {
        const row = record as { name?: string; title?: string; orderNumber?: string; displayName?: string };
        return row.displayName || row.name || row.title || row.orderNumber || record.id.slice(0, 8);
      }
