      /** Warehouses, vans, and stock locations. */
      export interface InventoryLocation {
        id: string;
        tenantId: string;
        code: string;
name: string;
location_type: string;
technician_id: string | null;
address: Record<string, unknown> | null;
is_active: boolean;
        createdAt: string;
        updatedAt: string;
        deletedAt: string | null;
      }

      export interface InventoryLocationCreate {
        code?: string;
name?: string;
technician_id?: string | null;
address?: Record<string, unknown> | null;
      }

      export interface InventoryLocationUpdate {
        code?: string;
name?: string;
location_type?: string;
technician_id?: string | null;
address?: Record<string, unknown> | null;
is_active?: boolean;
      }

      export interface InventoryLocationListParams {
        page?: number;
        pageSize?: number;
        search?: string;
        orderBy?: string;
        orderDir?: 'asc' | 'desc';
          code?: string;
technician_id?: string | null;
      }

      export interface InventoryLocationListResponse {
        items: InventoryLocation[];
        total: number;
        page: number;
        pageSize: number;
        pages: number;
      }

      export function isInventoryLocationActive(record: InventoryLocation): boolean {
        const row = record as { isActive?: boolean; status?: string; deletedAt?: string | null };
        if (row.deletedAt) return false;
        if (typeof row.isActive === 'boolean') return row.isActive;
        if (row.status) return !['cancelled', 'inactive', 'void'].includes(row.status);
        return true;
      }

      export function inventoryLocationDisplayName(record: InventoryLocation): string {
        const row = record as { name?: string; title?: string; orderNumber?: string; displayName?: string };
        return row.displayName || row.name || row.title || row.orderNumber || record.id.slice(0, 8);
      }
