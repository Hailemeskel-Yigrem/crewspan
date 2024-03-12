      /** Individual line items on customer invoices. */
      export interface InvoiceLineItem {
        id: string;
        tenantId: string;
        invoice_id: string;
description: string;
quantity: string;
unit_price: string;
tax_rate: string;
line_total: string;
item_type: string;
reference_id: string | null;
        createdAt: string;
        updatedAt: string;
        deletedAt: string | null;
      }

      export interface InvoiceLineItemCreate {
        invoice_id?: string;
description?: string;
unit_price?: string;
reference_id: string | null;
      }

      export interface InvoiceLineItemUpdate {
        invoice_id?: string;
description?: string;
quantity?: string;
unit_price?: string;
tax_rate?: string;
line_total?: string;
item_type?: string;
reference_id?: string | null;
      }

      export interface InvoiceLineItemListParams {
        page?: number;
        pageSize?: number;
        search?: string;
        orderBy?: string;
        orderDir?: 'asc' | 'desc';
          invoice_id?: string;
      }

      export interface InvoiceLineItemListResponse {
        items: InvoiceLineItem[];
        total: number;
        page: number;
        pageSize: number;
        pages: number;
      }

      export function isInvoiceLineItemActive(record: InvoiceLineItem): boolean {
        const row = record as { isActive?: boolean; status?: string; deletedAt?: string | null };
        if (row.deletedAt) return false;
        if (typeof row.isActive === 'boolean') return row.isActive;
        if (row.status) return !['cancelled', 'inactive', 'void'].includes(row.status);
        return true;
      }

      export function invoiceLineItemDisplayName(record: InvoiceLineItem): string {
        const row = record as { name?: string; title?: string; orderNumber?: string; displayName?: string };
        return row.displayName || row.name || row.title || row.orderNumber || record.id.slice(0, 8);
      }
