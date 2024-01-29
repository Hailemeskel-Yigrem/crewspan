      /** Customer master records for field service accounts and billing. */
      export interface Customer {
        id: string;
        tenantId: string;
        account_number: string;
name: string;
customer_type: string;
billing_email: string | null;
billing_address: Record<string, unknown> | null;
credit_limit: string | null;
payment_terms_days: number;
notes: string | null;
is_active: boolean;
        createdAt: string;
        updatedAt: string;
        deletedAt: string | null;
      }

      export interface CustomerCreate {
        account_number?: string;
name?: string;
billing_email: string | null;
billing_address: Record<string, unknown> | null;
credit_limit: string | null;
notes: string | null;
      }

      export interface CustomerUpdate {
        account_number?: string;
name?: string;
customer_type?: string;
billing_email?: string | null;
billing_address?: Record<string, unknown> | null;
credit_limit?: string | null;
payment_terms_days?: number;
notes?: string | null;
is_active?: boolean;
      }

      export interface CustomerListParams {
        page?: number;
        pageSize?: number;
        search?: string;
        orderBy?: string;
        orderDir?: 'asc' | 'desc';
          account_number?: string;
name?: string;
      }

      export interface CustomerListResponse {
        items: Customer[];
        total: number;
        page: number;
        pageSize: number;
        pages: number;
      }

      export function isCustomerActive(record: Customer): boolean {
        const row = record as { isActive?: boolean; status?: string; deletedAt?: string | null };
        if (row.deletedAt) return false;
        if (typeof row.isActive === 'boolean') return row.isActive;
        if (row.status) return !['cancelled', 'inactive', 'void'].includes(row.status);
        return true;
      }

      export function customerDisplayName(record: Customer): string {
        const row = record as { name?: string; title?: string; orderNumber?: string; displayName?: string };
        return row.displayName || row.name || row.title || row.orderNumber || record.id.slice(0, 8);
      }
