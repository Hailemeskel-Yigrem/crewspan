      import { apiFetch, type PaginatedResponse } from './client';
      import type { Technician, TechnicianCreate, TechnicianUpdate, TechnicianListParams } from '../types/technician';

      export const technicianApi = {
        list(params: TechnicianListParams = {}): Promise<PaginatedResponse<Technician>> {
          const qs = new URLSearchParams();
          if (params.page) qs.set('page', String(params.page));
          if (params.pageSize) qs.set('page_size', String(params.pageSize));
          if (params.search) qs.set('search', params.search);
          if (params.orderBy) qs.set('order_by', params.orderBy);
          if (params.orderDir) qs.set('order_dir', params.orderDir);
              if (params.user_id !== undefined) qs.set('user_id', String(params.user_id));
  if (params.employee_id !== undefined) qs.set('employee_id', String(params.employee_id));
  if (params.status !== undefined) qs.set('status', String(params.status));
          return apiFetch<PaginatedResponse<Technician>>(`/api/v1/technicians?${qs}`);
        },

        get(id: string): Promise<Technician> {
          return apiFetch<Technician>(`/api/v1/technicians/${id}`);
        },

        create(data: TechnicianCreate): Promise<Technician> {
          return apiFetch<Technician>('/api/v1/technicians', {
            method: 'POST',
            body: JSON.stringify(data),
          });
        },

        update(id: string, data: TechnicianUpdate): Promise<Technician> {
          return apiFetch<Technician>(`/api/v1/technicians/${id}`, {
            method: 'PATCH',
            body: JSON.stringify(data),
          });
        },

        remove(id: string): Promise<void> {
          return apiFetch<void>(`/api/v1/technicians/${id}`, { method: 'DELETE' });
        },

        count(): Promise<{ total: number }> {
          return apiFetch<{ total: number }>(`/api/v1/technicians/count`);
        },
        restore(id: string): Promise<Technician> {
  return apiFetch<Technician>(`/api/v1/technicians/${id}/restore`, { method: 'POST' });
},

        async set_status(id: string, status: str): Promise<Technician> {
  return apiFetch<Technician>(`/api/v1/technicians/{id}/set-status`, {
    method: "POST",
    body: JSON.stringify({status: status}),
  });
}

async update_location(id: string, lat: Decimal, lng: Decimal): Promise<Technician> {
  return apiFetch<Technician>(`/api/v1/technicians/{id}/update-location`, {
    method: "POST",
    body: JSON.stringify({lat: lat, lng: lng}),
  });
}

async calculate_utilization(id: string, start: date, end: date): Promise<Technician> {
  return apiFetch<Technician>(`/api/v1/technicians/{id}/calculate-utilization`, {
    method: "POST",
    body: JSON.stringify({start: start, end: end}),
  });
}
      };
