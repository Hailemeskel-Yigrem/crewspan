      /** Core work order lifecycle from intake through completion. */
      export interface WorkOrder {
        id: string;
        tenantId: string;
        order_number: string;
customer_id: string;
site_id: string;
title: string;
description: string | null;
priority: string;
status: string;
scheduled_start: string | null;
scheduled_end: string | null;
assigned_technician_id: string | null;
sla_policy_id: string | null;
estimated_duration_minutes: number | null;
completion_notes: string | null;
        createdAt: string;
        updatedAt: string;
        deletedAt: string | null;
      }

      export interface WorkOrderCreate {
        order_number?: string;
priority?: string;
status?: string;
customer_id?: string;
site_id?: string;
title?: string;
description?: string | null;
scheduled_start?: string | null;
scheduled_end?: string | null;
assigned_technician_id?: string | null;
sla_policy_id?: string | null;
estimated_duration_minutes?: number | null;
completion_notes?: string | null;
      }

      export interface WorkOrderUpdate {
        order_number?: string;
customer_id?: string;
site_id?: string;
title?: string;
description?: string | null;
priority?: string;
status?: string;
scheduled_start?: string | null;
scheduled_end?: string | null;
assigned_technician_id?: string | null;
sla_policy_id?: string | null;
estimated_duration_minutes?: number | null;
completion_notes?: string | null;
      }

      export interface WorkOrderListParams {
        page?: number;
        pageSize?: number;
        search?: string;
        orderBy?: string;
        orderDir?: 'asc' | 'desc';
          order_number?: string;
customer_id?: string;
site_id?: string;
status?: string;
assigned_technician_id?: string | null;
      }

      export interface WorkOrderListResponse {
        items: WorkOrder[];
        total: number;
        page: number;
        pageSize: number;
        pages: number;
      }

      export function isWorkOrderActive(record: WorkOrder): boolean {
        const row = record as { isActive?: boolean; status?: string; deletedAt?: string | null };
        if (row.deletedAt) return false;
        if (typeof row.isActive === 'boolean') return row.isActive;
        if (row.status) return !['cancelled', 'inactive', 'void'].includes(row.status);
        return true;
      }

      export function workOrderDisplayName(record: WorkOrder): string {
        const row = record as { name?: string; title?: string; orderNumber?: string; displayName?: string };
        return row.displayName || row.name || row.title || row.orderNumber || record.id.slice(0, 8);
      }
