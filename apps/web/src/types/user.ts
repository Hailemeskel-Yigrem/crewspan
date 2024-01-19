      /** Platform user accounts scoped to tenants with authentication metadata. */
      export interface User {
        id: string;
        tenantId: string;
        email: string;
full_name: string;
password_hash: string;
phone: string | null;
role_id: string;
is_active: boolean;
last_login_at: string | null;
preferences: Record<string, unknown> | null;
        createdAt: string;
        updatedAt: string;
        deletedAt: string | null;
      }

      export interface UserCreate {
        email?: string;
full_name?: string;
password_hash?: string;
phone: string | null;
role_id?: string;
last_login_at: string | null;
preferences: Record<string, unknown> | null;
      }

      export interface UserUpdate {
        email?: string;
full_name?: string;
password_hash?: string;
phone?: string | null;
role_id?: string;
is_active?: boolean;
last_login_at?: string | null;
preferences?: Record<string, unknown> | null;
      }

      export interface UserListParams {
        page?: number;
        pageSize?: number;
        search?: string;
        orderBy?: string;
        orderDir?: 'asc' | 'desc';
          email?: string;
role_id?: string;
      }

      export interface UserListResponse {
        items: User[];
        total: number;
        page: number;
        pageSize: number;
        pages: number;
      }

      export function isUserActive(record: User): boolean {
        const row = record as { isActive?: boolean; status?: string; deletedAt?: string | null };
        if (row.deletedAt) return false;
        if (typeof row.isActive === 'boolean') return row.isActive;
        if (row.status) return !['cancelled', 'inactive', 'void'].includes(row.status);
        return true;
      }

      export function userDisplayName(record: User): string {
        const row = record as { name?: string; title?: string; orderNumber?: string; displayName?: string };
        return row.displayName || row.name || row.title || row.orderNumber || record.id.slice(0, 8);
      }
