      /** Payment records applied to invoices. */
      export interface Payment {
        id: string;
        tenantId: string;
        invoice_id: string;
amount: string;
payment_method: string;
payment_date: string;
reference_number: string | null;
status: string;
processor_response: Record<string, unknown> | null;
        createdAt: string;
        updatedAt: string;
        deletedAt: string | null;
      }

      export interface PaymentCreate {
        invoice_id?: string;
amount?: string;
payment_method?: string;
payment_date?: string;
reference_number?: string | null;
processor_response?: Record<string, unknown> | null;
      }

      export interface PaymentUpdate {
        invoice_id?: string;
amount?: string;
payment_method?: string;
payment_date?: string;
reference_number?: string | null;
status?: string;
processor_response?: Record<string, unknown> | null;
      }

      export interface PaymentListParams {
        page?: number;
        pageSize?: number;
        search?: string;
        orderBy?: string;
        orderDir?: 'asc' | 'desc';
          invoice_id?: string;
      }

      export interface PaymentListResponse {
        items: Payment[];
        total: number;
        page: number;
        pageSize: number;
        pages: number;
      }

      export function isPaymentActive(record: Payment): boolean {
        const row = record as { isActive?: boolean; status?: string; deletedAt?: string | null };
        if (row.deletedAt) return false;
        if (typeof row.isActive === 'boolean') return row.isActive;
        if (row.status) return !['cancelled', 'inactive', 'void'].includes(row.status);
        return true;
      }

      export function paymentDisplayName(record: Payment): string {
        const row = record as { name?: string; title?: string; orderNumber?: string; displayName?: string };
        return row.displayName || row.name || row.title || row.orderNumber || record.id.slice(0, 8);
      }
