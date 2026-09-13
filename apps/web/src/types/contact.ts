      /** Customer contacts for scheduling and notification routing. */
      export interface Contact {
        id: string;
        tenantId: string;
        customer_id: string;
site_id: string | null;
first_name: string;
last_name: string;
email: string | null;
phone: string | null;
role_title: string | null;
is_primary: boolean;
notify_on_dispatch: boolean;
        createdAt: string;
        updatedAt: string;
        deletedAt: string | null;
      }

      export interface ContactCreate {
        customer_id?: string;
site_id?: string | null;
first_name?: string;
last_name?: string;
email?: string | null;
phone?: string | null;
role_title?: string | null;
      }

      export interface ContactUpdate {
        customer_id?: string;
site_id?: string | null;
first_name?: string;
last_name?: string;
email?: string | null;
phone?: string | null;
role_title?: string | null;
is_primary?: boolean;
notify_on_dispatch?: boolean;
      }

      export interface ContactListParams {
        page?: number;
        pageSize?: number;
        search?: string;
        orderBy?: string;
        orderDir?: 'asc' | 'desc';
          customer_id?: string;
site_id?: string | null;
      }

      export interface ContactListResponse {
        items: Contact[];
        total: number;
        page: number;
        pageSize: number;
        pages: number;
      }

      export function isContactActive(record: Contact): boolean {
        const row = record as { isActive?: boolean; status?: string; deletedAt?: string | null };
        if (row.deletedAt) return false;
        if (typeof row.isActive === 'boolean') return row.isActive;
        if (row.status) return !['cancelled', 'inactive', 'void'].includes(row.status);
        return true;
      }

      export function contactDisplayName(record: Contact): string {
        const row = record as { name?: string; title?: string; orderNumber?: string; displayName?: string };
        return row.displayName || row.name || row.title || row.orderNumber || record.id.slice(0, 8);
      }
