      /** Customer invoices generated from completed work. */
      export interface Invoice {
        id: string;
        tenantId: string;
        invoice_number: string;
customer_id: string;
work_order_id: string | null;
status: string;
issue_date: string;
due_date: string;
subtotal: string;
tax_amount: string;
total_amount: string;
currency: string;
notes: string | null;
        createdAt: string;
        updatedAt: string;
        deletedAt: string | null;
      }

      export interface InvoiceCreate {
        invoice_number?: string;
customer_id?: string;
work_order_id: string | null;
issue_date?: string;
due_date?: string;
notes: string | null;
      }

      export interface InvoiceUpdate {
        invoice_number?: string;
customer_id?: string;
work_order_id?: string | null;
status?: string;
issue_date?: string;
due_date?: string;
subtotal?: string;
tax_amount?: string;
total_amount?: string;
currency?: string;
notes?: string | null;
      }

      export interface InvoiceListParams {
        page?: number;
        pageSize?: number;
        search?: string;
        orderBy?: string;
        orderDir?: 'asc' | 'desc';
          invoice_number?: string;
customer_id?: string;
work_order_id?: string | null;
status?: string;
      }

      export interface InvoiceListResponse {
        items: Invoice[];
        total: number;
        page: number;
        pageSize: number;
        pages: number;
      }

      export function isInvoiceActive(record: Invoice): boolean {
        const row = record as { isActive?: boolean; status?: string; deletedAt?: string | null };
        if (row.deletedAt) return false;
        if (typeof row.isActive === 'boolean') return row.isActive;
        if (row.status) return !['cancelled', 'inactive', 'void'].includes(row.status);
        return true;
      }

      export function invoiceDisplayName(record: Invoice): string {
        const row = record as { name?: string; title?: string; orderNumber?: string; displayName?: string };
        return row.displayName || row.name || row.title || row.orderNumber || record.id.slice(0, 8);
      }
