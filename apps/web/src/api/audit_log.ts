      import { apiFetch, type PaginatedResponse } from './client';
      import type { AuditLog, AuditLogCreate, AuditLogUpdate, AuditLogListParams } from '../types/audit_log';

      export const auditLogApi = {
        list(params: AuditLogListParams = {}): Promise<PaginatedResponse<AuditLog>> {
          const qs = new URLSearchParams();
          if (params.page) qs.set('page', String(params.page));
          if (params.pageSize) qs.set('page_size', String(params.pageSize));
          if (params.search) qs.set('search', params.search);
          if (params.orderBy) qs.set('order_by', params.orderBy);
          if (params.orderDir) qs.set('order_dir', params.orderDir);
              if (params.actor_id !== undefined) qs.set('actor_id', String(params.actor_id));
  if (params.action !== undefined) qs.set('action', String(params.action));
  if (params.resource_type !== undefined) qs.set('resource_type', String(params.resource_type));
  if (params.resource_id !== undefined) qs.set('resource_id', String(params.resource_id));
          return apiFetch<PaginatedResponse<AuditLog>>(`/api/v1/audit-logs?${qs}`);
        },

        get(id: string): Promise<AuditLog> {
          return apiFetch<AuditLog>(`/api/v1/audit-logs/${id}`);
        },

        create(data: AuditLogCreate): Promise<AuditLog> {
          return apiFetch<AuditLog>('/api/v1/audit-logs', {
            method: 'POST',
            body: JSON.stringify(data),
          });
        },

        update(id: string, data: AuditLogUpdate): Promise<AuditLog> {
          return apiFetch<AuditLog>(`/api/v1/audit-logs/${id}`, {
            method: 'PATCH',
            body: JSON.stringify(data),
          });
        },

        remove(id: string): Promise<void> {
          return apiFetch<void>(`/api/v1/audit-logs/${id}`, { method: 'DELETE' });
        },

        count(): Promise<{ total: number }> {
          return apiFetch<{ total: number }>(`/api/v1/audit-logs/count`);
        },

        async search_by_resource(id: string, resourceType: str, resourceId: string): Promise<AuditLog> {
  return apiFetch<AuditLog>('/api/v1/audit-logs/${id}/by-resource', { method: "GET", body: JSON.stringify({resourceType: resourceType, resourceId: resourceId}) });
}
      };
