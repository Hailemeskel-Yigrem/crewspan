      /** Customer-owned equipment and assets under service. */
      export interface Equipment {
        id: string;
        tenantId: string;
        customer_id: string;
site_id: string | null;
asset_tag: string;
name: string;
manufacturer: string | null;
model_number: string | null;
serial_number: string | null;
install_date: string | null;
warranty_expires: string | null;
specifications: Record<string, unknown> | null;
status: string;
        createdAt: string;
        updatedAt: string;
        deletedAt: string | null;
      }

      export interface EquipmentCreate {
        customer_id?: string;
site_id: string | null;
asset_tag?: string;
name?: string;
manufacturer: string | null;
model_number: string | null;
serial_number: string | null;
install_date: string | null;
warranty_expires: string | null;
specifications: Record<string, unknown> | null;
      }

      export interface EquipmentUpdate {
        customer_id?: string;
site_id?: string | null;
asset_tag?: string;
name?: string;
manufacturer?: string | null;
model_number?: string | null;
serial_number?: string | null;
install_date?: string | null;
warranty_expires?: string | null;
specifications?: Record<string, unknown> | null;
status?: string;
      }

      export interface EquipmentListParams {
        page?: number;
        pageSize?: number;
        search?: string;
        orderBy?: string;
        orderDir?: 'asc' | 'desc';
          customer_id?: string;
site_id?: string | null;
asset_tag?: string;
serial_number?: string | null;
      }

      export interface EquipmentListResponse {
        items: Equipment[];
        total: number;
        page: number;
        pageSize: number;
        pages: number;
      }

      export function isEquipmentActive(record: Equipment): boolean {
        const row = record as { isActive?: boolean; status?: string; deletedAt?: string | null };
        if (row.deletedAt) return false;
        if (typeof row.isActive === 'boolean') return row.isActive;
        if (row.status) return !['cancelled', 'inactive', 'void'].includes(row.status);
        return true;
      }

      export function equipmentDisplayName(record: Equipment): string {
        const row = record as { name?: string; title?: string; orderNumber?: string; displayName?: string };
        return row.displayName || row.name || row.title || row.orderNumber || record.id.slice(0, 8);
      }
