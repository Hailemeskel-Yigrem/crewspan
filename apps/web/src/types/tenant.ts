      /** Multi-tenant organization registry with subscription tier and feature flags. */
      export interface Tenant {
        id: string;

        slug: string;
display_name: string;
legal_name: string | null;
subscription_tier: string;
timezone: string;
is_active: boolean;
feature_flags: Record<string, unknown> | null;
settings: Record<string, unknown> | null;
        createdAt: string;
        updatedAt: string;
        deletedAt: string | null;
      }

      export interface TenantCreate {
        slug?: string;
display_name?: string;
legal_name: string | null;
feature_flags: Record<string, unknown> | null;
settings: Record<string, unknown> | null;
      }

      export interface TenantUpdate {
        slug?: string;
display_name?: string;
legal_name?: string | null;
subscription_tier?: string;
timezone?: string;
is_active?: boolean;
feature_flags?: Record<string, unknown> | null;
settings?: Record<string, unknown> | null;
      }

      export interface TenantListParams {
        page?: number;
        pageSize?: number;
        search?: string;
        orderBy?: string;
        orderDir?: 'asc' | 'desc';
          slug?: string;
      }

      export interface TenantListResponse {
        items: Tenant[];
        total: number;
        page: number;
        pageSize: number;
        pages: number;
      }

      export function isTenantActive(record: Tenant): boolean {
        const row = record as { isActive?: boolean; status?: string; deletedAt?: string | null };
        if (row.deletedAt) return false;
        if (typeof row.isActive === 'boolean') return row.isActive;
        if (row.status) return !['cancelled', 'inactive', 'void'].includes(row.status);
        return true;
      }

      export function tenantDisplayName(record: Tenant): string {
        const row = record as { name?: string; title?: string; orderNumber?: string; displayName?: string };
        return row.displayName || row.name || row.title || row.orderNumber || record.id.slice(0, 8);
      }
