      /** Recurring service agreements with customers. */
      export interface ServiceContract {
        id: string;
        tenantId: string;
        customer_id: string;
contract_number: string;
name: string;
start_date: string;
end_date: string | null;
billing_frequency: string;
annual_value: string | null;
covered_sites: unknown[] | null;
terms: Record<string, unknown> | null;
status: string;
        createdAt: string;
        updatedAt: string;
        deletedAt: string | null;
      }

      export interface ServiceContractCreate {
        customer_id?: string;
contract_number?: string;
name?: string;
start_date?: string;
end_date: string | null;
annual_value: string | null;
covered_sites: unknown[] | null;
terms: Record<string, unknown> | null;
      }

      export interface ServiceContractUpdate {
        customer_id?: string;
contract_number?: string;
name?: string;
start_date?: string;
end_date?: string | null;
billing_frequency?: string;
annual_value?: string | null;
covered_sites?: unknown[] | null;
terms?: Record<string, unknown> | null;
status?: string;
      }

      export interface ServiceContractListParams {
        page?: number;
        pageSize?: number;
        search?: string;
        orderBy?: string;
        orderDir?: 'asc' | 'desc';
          customer_id?: string;
contract_number?: string;
status?: string;
      }

      export interface ServiceContractListResponse {
        items: ServiceContract[];
        total: number;
        page: number;
        pageSize: number;
        pages: number;
      }

      export function isServiceContractActive(record: ServiceContract): boolean {
        const row = record as { isActive?: boolean; status?: string; deletedAt?: string | null };
        if (row.deletedAt) return false;
        if (typeof row.isActive === 'boolean') return row.isActive;
        if (row.status) return !['cancelled', 'inactive', 'void'].includes(row.status);
        return true;
      }

      export function serviceContractDisplayName(record: ServiceContract): string {
        const row = record as { name?: string; title?: string; orderNumber?: string; displayName?: string };
        return row.displayName || row.name || row.title || row.orderNumber || record.id.slice(0, 8);
      }
