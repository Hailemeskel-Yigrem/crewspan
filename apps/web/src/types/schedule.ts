      /** Calendar blocks for technician availability and appointments. */
      export interface Schedule {
        id: string;
        tenantId: string;
        technician_id: string;
work_order_id: string | null;
event_type: string;
starts_at: string;
ends_at: string;
title: string;
notes: string | null;
is_locked: boolean;
        createdAt: string;
        updatedAt: string;
        deletedAt: string | null;
      }

      export interface ScheduleCreate {
        technician_id?: string;
work_order_id?: string | null;
starts_at?: string;
ends_at?: string;
title?: string;
notes?: string | null;
      }

      export interface ScheduleUpdate {
        technician_id?: string;
work_order_id?: string | null;
event_type?: string;
starts_at?: string;
ends_at?: string;
title?: string;
notes?: string | null;
is_locked?: boolean;
      }

      export interface ScheduleListParams {
        page?: number;
        pageSize?: number;
        search?: string;
        orderBy?: string;
        orderDir?: 'asc' | 'desc';
          technician_id?: string;
work_order_id?: string | null;
starts_at?: string;
      }

      export interface ScheduleListResponse {
        items: Schedule[];
        total: number;
        page: number;
        pageSize: number;
        pages: number;
      }

      export function isScheduleActive(record: Schedule): boolean {
        const row = record as { isActive?: boolean; status?: string; deletedAt?: string | null };
        if (row.deletedAt) return false;
        if (typeof row.isActive === 'boolean') return row.isActive;
        if (row.status) return !['cancelled', 'inactive', 'void'].includes(row.status);
        return true;
      }

      export function scheduleDisplayName(record: Schedule): string {
        const row = record as { name?: string; title?: string; orderNumber?: string; displayName?: string };
        return row.displayName || row.name || row.title || row.orderNumber || record.id.slice(0, 8);
      }
