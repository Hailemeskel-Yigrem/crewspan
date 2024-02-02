      /** Physical service locations belonging to customers. */
      export interface CustomerSite {
        id: string;
        tenantId: string;
        customer_id: string;
site_code: string;
name: string;
address: Record<string, unknown>;
latitude: string | null;
longitude: string | null;
access_instructions: string | null;
service_window: Record<string, unknown> | null;
is_active: boolean;
        createdAt: string;
        updatedAt: string;
        deletedAt: string | null;
      }

      export interface CustomerSiteCreate {
        customer_id?: string;
site_code?: string;
name?: string;
address?: Record<string, unknown>;
latitude: string | null;
longitude: string | null;
access_instructions: string | null;
service_window: Record<string, unknown> | null;
      }

      export interface CustomerSiteUpdate {
        customer_id?: string;
site_code?: string;
name?: string;
address?: Record<string, unknown>;
latitude?: string | null;
longitude?: string | null;
access_instructions?: string | null;
service_window?: Record<string, unknown> | null;
is_active?: boolean;
      }

      export interface CustomerSiteListParams {
        page?: number;
        pageSize?: number;
        search?: string;
        orderBy?: string;
        orderDir?: 'asc' | 'desc';
          customer_id?: string;
site_code?: string;
      }

      export interface CustomerSiteListResponse {
        items: CustomerSite[];
        total: number;
        page: number;
        pageSize: number;
        pages: number;
      }

      export function isCustomerSiteActive(record: CustomerSite): boolean {
        const row = record as { isActive?: boolean; status?: string; deletedAt?: string | null };
        if (row.deletedAt) return false;
        if (typeof row.isActive === 'boolean') return row.isActive;
        if (row.status) return !['cancelled', 'inactive', 'void'].includes(row.status);
        return true;
      }

      export function customerSiteDisplayName(record: CustomerSite): string {
        const row = record as { name?: string; title?: string; orderNumber?: string; displayName?: string };
        return row.displayName || row.name || row.title || row.orderNumber || record.id.slice(0, 8);
      }
