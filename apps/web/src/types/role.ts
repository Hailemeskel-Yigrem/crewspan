      /** Role-based access control definitions with permission sets. */
      export interface Role {
        id: string;
        tenantId: string;
        name: string;
description: string | null;
permissions: unknown[];
is_system: boolean;
        createdAt: string;
        updatedAt: string;
        deletedAt: string | null;
      }

      export interface RoleCreate {
        name?: string;
description: string | null;
permissions?: unknown[];
      }

      export interface RoleUpdate {
        name?: string;
description?: string | null;
permissions?: unknown[];
is_system?: boolean;
      }

      export interface RoleListParams {
        page?: number;
        pageSize?: number;
        search?: string;
        orderBy?: string;
        orderDir?: 'asc' | 'desc';
          name?: string;
      }

      export interface RoleListResponse {
        items: Role[];
        total: number;
        page: number;
        pageSize: number;
        pages: number;
      }

      export function isRoleActive(record: Role): boolean {
        const row = record as { isActive?: boolean; status?: string; deletedAt?: string | null };
        if (row.deletedAt) return false;
        if (typeof row.isActive === 'boolean') return row.isActive;
        if (row.status) return !['cancelled', 'inactive', 'void'].includes(row.status);
        return true;
      }

      export function roleDisplayName(record: Role): string {
        const row = record as { name?: string; title?: string; orderNumber?: string; displayName?: string };
        return row.displayName || row.name || row.title || row.orderNumber || record.id.slice(0, 8);
      }
