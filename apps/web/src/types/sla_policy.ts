      /** Service level agreement policy definitions. */
      export interface SlaPolicy {
        id: string;
        tenantId: string;
        name: string;
description: string | null;
priority: string;
response_minutes: number;
resolution_minutes: number;
business_hours_only: boolean;
escalation_rules: unknown[] | null;
is_active: boolean;
        createdAt: string;
        updatedAt: string;
        deletedAt: string | null;
      }

      export interface SlaPolicyCreate {
        name?: string;
description?: string | null;
priority?: string;
response_minutes?: number;
resolution_minutes?: number;
escalation_rules?: unknown[] | null;
      }

      export interface SlaPolicyUpdate {
        name?: string;
description?: string | null;
priority?: string;
response_minutes?: number;
resolution_minutes?: number;
business_hours_only?: boolean;
escalation_rules?: unknown[] | null;
is_active?: boolean;
      }

      export interface SlaPolicyListParams {
        page?: number;
        pageSize?: number;
        search?: string;
        orderBy?: string;
        orderDir?: 'asc' | 'desc';
          name?: string;
priority?: string;
      }

      export interface SlaPolicyListResponse {
        items: SlaPolicy[];
        total: number;
        page: number;
        pageSize: number;
        pages: number;
      }

      export function isSlaPolicyActive(record: SlaPolicy): boolean {
        const row = record as { isActive?: boolean; status?: string; deletedAt?: string | null };
        if (row.deletedAt) return false;
        if (typeof row.isActive === 'boolean') return row.isActive;
        if (row.status) return !['cancelled', 'inactive', 'void'].includes(row.status);
        return true;
      }

      export function slaPolicyDisplayName(record: SlaPolicy): string {
        const row = record as { name?: string; title?: string; orderNumber?: string; displayName?: string };
        return row.displayName || row.name || row.title || row.orderNumber || record.id.slice(0, 8);
      }
