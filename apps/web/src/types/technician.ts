      /** Field technician profiles linked to user accounts. */
      export interface Technician {
        id: string;
        tenantId: string;
        user_id: string;
employee_id: string;
home_base_latitude: string | null;
home_base_longitude: string | null;
max_daily_hours: number;
status: string;
certifications: unknown[] | null;
vehicle_info: Record<string, unknown> | null;
        createdAt: string;
        updatedAt: string;
        deletedAt: string | null;
      }

      export interface TechnicianCreate {
        user_id?: string;
employee_id?: string;
home_base_latitude: string | null;
home_base_longitude: string | null;
certifications: unknown[] | null;
vehicle_info: Record<string, unknown> | null;
      }

      export interface TechnicianUpdate {
        user_id?: string;
employee_id?: string;
home_base_latitude?: string | null;
home_base_longitude?: string | null;
max_daily_hours?: number;
status?: string;
certifications?: unknown[] | null;
vehicle_info?: Record<string, unknown> | null;
      }

      export interface TechnicianListParams {
        page?: number;
        pageSize?: number;
        search?: string;
        orderBy?: string;
        orderDir?: 'asc' | 'desc';
          user_id?: string;
employee_id?: string;
status?: string;
      }

      export interface TechnicianListResponse {
        items: Technician[];
        total: number;
        page: number;
        pageSize: number;
        pages: number;
      }

      export function isTechnicianActive(record: Technician): boolean {
        const row = record as { isActive?: boolean; status?: string; deletedAt?: string | null };
        if (row.deletedAt) return false;
        if (typeof row.isActive === 'boolean') return row.isActive;
        if (row.status) return !['cancelled', 'inactive', 'void'].includes(row.status);
        return true;
      }

      export function technicianDisplayName(record: Technician): string {
        const row = record as { name?: string; title?: string; orderNumber?: string; displayName?: string };
        return row.displayName || row.name || row.title || row.orderNumber || record.id.slice(0, 8);
      }
