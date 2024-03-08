      /** Dispatch board assignments linking technicians to work orders. */
      export interface Dispatch {
        id: string;
        tenantId: string;
        work_order_id: string;
technician_id: string;
dispatched_at: string;
accepted_at: string | null;
status: string;
dispatch_notes: string | null;
route_eta_minutes: number | null;
        createdAt: string;
        updatedAt: string;
        deletedAt: string | null;
      }

      export interface DispatchCreate {
        work_order_id?: string;
technician_id?: string;
dispatched_at?: string;
accepted_at: string | null;
dispatch_notes: string | null;
route_eta_minutes: number | null;
      }

      export interface DispatchUpdate {
        work_order_id?: string;
technician_id?: string;
dispatched_at?: string;
accepted_at?: string | null;
status?: string;
dispatch_notes?: string | null;
route_eta_minutes?: number | null;
      }

      export interface DispatchListParams {
        page?: number;
        pageSize?: number;
        search?: string;
        orderBy?: string;
        orderDir?: 'asc' | 'desc';
          work_order_id?: string;
technician_id?: string;
status?: string;
      }

      export interface DispatchListResponse {
        items: Dispatch[];
        total: number;
        page: number;
        pageSize: number;
        pages: number;
      }

      export function isDispatchActive(record: Dispatch): boolean {
        const row = record as { isActive?: boolean; status?: string; deletedAt?: string | null };
        if (row.deletedAt) return false;
        if (typeof row.isActive === 'boolean') return row.isActive;
        if (row.status) return !['cancelled', 'inactive', 'void'].includes(row.status);
        return true;
      }

      export function dispatchDisplayName(record: Dispatch): string {
        const row = record as { name?: string; title?: string; orderNumber?: string; displayName?: string };
        return row.displayName || row.name || row.title || row.orderNumber || record.id.slice(0, 8);
      }
