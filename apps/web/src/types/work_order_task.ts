      /** Checklist tasks attached to work orders. */
      export interface WorkOrderTask {
        id: string;
        tenantId: string;
        work_order_id: string;
sequence: number;
title: string;
instructions: string | null;
is_required: boolean;
status: string;
completed_at: string | null;
completed_by_id: string | null;
        createdAt: string;
        updatedAt: string;
        deletedAt: string | null;
      }

      export interface WorkOrderTaskCreate {
        work_order_id?: string;
title?: string;
instructions: string | null;
completed_at: string | null;
completed_by_id: string | null;
      }

      export interface WorkOrderTaskUpdate {
        work_order_id?: string;
sequence?: number;
title?: string;
instructions?: string | null;
is_required?: boolean;
status?: string;
completed_at?: string | null;
completed_by_id?: string | null;
      }

      export interface WorkOrderTaskListParams {
        page?: number;
        pageSize?: number;
        search?: string;
        orderBy?: string;
        orderDir?: 'asc' | 'desc';
          work_order_id?: string;
      }

      export interface WorkOrderTaskListResponse {
        items: WorkOrderTask[];
        total: number;
        page: number;
        pageSize: number;
        pages: number;
      }

      export function isWorkOrderTaskActive(record: WorkOrderTask): boolean {
        const row = record as { isActive?: boolean; status?: string; deletedAt?: string | null };
        if (row.deletedAt) return false;
        if (typeof row.isActive === 'boolean') return row.isActive;
        if (row.status) return !['cancelled', 'inactive', 'void'].includes(row.status);
        return true;
      }

      export function workOrderTaskDisplayName(record: WorkOrderTask): string {
        const row = record as { name?: string; title?: string; orderNumber?: string; displayName?: string };
        return row.displayName || row.name || row.title || row.orderNumber || record.id.slice(0, 8);
      }
