      /** Inventory transactions: receipts, issues, transfers, adjustments. */
      export interface StockMovement {
        id: string;
        tenantId: string;
        item_id: string;
from_location_id: string | null;
to_location_id: string | null;
quantity: string;
movement_type: string;
reference_type: string | null;
reference_id: string | null;
performed_by_id: string | null;
notes: string | null;
        createdAt: string;
        updatedAt: string;
        deletedAt: string | null;
      }

      export interface StockMovementCreate {
        item_id?: string;
from_location_id: string | null;
to_location_id: string | null;
quantity?: string;
movement_type?: string;
reference_type: string | null;
reference_id: string | null;
performed_by_id: string | null;
notes: string | null;
      }

      export interface StockMovementUpdate {
        item_id?: string;
from_location_id?: string | null;
to_location_id?: string | null;
quantity?: string;
movement_type?: string;
reference_type?: string | null;
reference_id?: string | null;
performed_by_id?: string | null;
notes?: string | null;
      }

      export interface StockMovementListParams {
        page?: number;
        pageSize?: number;
        search?: string;
        orderBy?: string;
        orderDir?: 'asc' | 'desc';
          item_id?: string;
from_location_id?: string | null;
to_location_id?: string | null;
movement_type?: string;
      }

      export interface StockMovementListResponse {
        items: StockMovement[];
        total: number;
        page: number;
        pageSize: number;
        pages: number;
      }

      export function isStockMovementActive(record: StockMovement): boolean {
        const row = record as { isActive?: boolean; status?: string; deletedAt?: string | null };
        if (row.deletedAt) return false;
        if (typeof row.isActive === 'boolean') return row.isActive;
        if (row.status) return !['cancelled', 'inactive', 'void'].includes(row.status);
        return true;
      }

      export function stockMovementDisplayName(record: StockMovement): string {
        const row = record as { name?: string; title?: string; orderNumber?: string; displayName?: string };
        return row.displayName || row.name || row.title || row.orderNumber || record.id.slice(0, 8);
      }
