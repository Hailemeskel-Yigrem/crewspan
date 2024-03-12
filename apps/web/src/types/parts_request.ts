      /** Parts requisitions linked to work orders. */
      export interface PartsRequest {
        id: string;
        tenantId: string;
        work_order_id: string;
requested_by_id: string;
status: string;
needed_by: string | null;
fulfillment_location_id: string | null;
line_items: unknown[];
notes: string | null;
        createdAt: string;
        updatedAt: string;
        deletedAt: string | null;
      }

      export interface PartsRequestCreate {
        work_order_id?: string;
requested_by_id?: string;
needed_by: string | null;
fulfillment_location_id: string | null;
line_items?: unknown[];
notes: string | null;
      }

      export interface PartsRequestUpdate {
        work_order_id?: string;
requested_by_id?: string;
status?: string;
needed_by?: string | null;
fulfillment_location_id?: string | null;
line_items?: unknown[];
notes?: string | null;
      }

      export interface PartsRequestListParams {
        page?: number;
        pageSize?: number;
        search?: string;
        orderBy?: string;
        orderDir?: 'asc' | 'desc';
          work_order_id?: string;
requested_by_id?: string;
status?: string;
      }

      export interface PartsRequestListResponse {
        items: PartsRequest[];
        total: number;
        page: number;
        pageSize: number;
        pages: number;
      }

      export function isPartsRequestActive(record: PartsRequest): boolean {
        const row = record as { isActive?: boolean; status?: string; deletedAt?: string | null };
        if (row.deletedAt) return false;
        if (typeof row.isActive === 'boolean') return row.isActive;
        if (row.status) return !['cancelled', 'inactive', 'void'].includes(row.status);
        return true;
      }

      export function partsRequestDisplayName(record: PartsRequest): string {
        const row = record as { name?: string; title?: string; orderNumber?: string; displayName?: string };
        return row.displayName || row.name || row.title || row.orderNumber || record.id.slice(0, 8);
      }
