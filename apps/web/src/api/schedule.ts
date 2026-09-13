      import { apiFetch, type PaginatedResponse } from './client';
      import type { Schedule, ScheduleCreate, ScheduleUpdate, ScheduleListParams } from '../types/schedule';

      export const scheduleApi = {
        list(params: ScheduleListParams = {}): Promise<PaginatedResponse<Schedule>> {
          const qs = new URLSearchParams();
          if (params.page) qs.set('page', String(params.page));
          if (params.pageSize) qs.set('page_size', String(params.pageSize));
          if (params.search) qs.set('search', params.search);
          if (params.orderBy) qs.set('order_by', params.orderBy);
          if (params.orderDir) qs.set('order_dir', params.orderDir);
              if (params.technician_id !== undefined) qs.set('technician_id', String(params.technician_id));
  if (params.work_order_id !== undefined) qs.set('work_order_id', String(params.work_order_id));
  if (params.starts_at !== undefined) qs.set('starts_at', String(params.starts_at));
          return apiFetch<PaginatedResponse<Schedule>>(`/api/v1/schedules?${qs}`);
        },

        get(id: string): Promise<Schedule> {
          return apiFetch<Schedule>(`/api/v1/schedules/${id}`);
        },

        create(data: ScheduleCreate): Promise<Schedule> {
          return apiFetch<Schedule>('/api/v1/schedules', {
            method: 'POST',
            body: JSON.stringify(data),
          });
        },

        update(id: string, data: ScheduleUpdate): Promise<Schedule> {
          return apiFetch<Schedule>(`/api/v1/schedules/${id}`, {
            method: 'PATCH',
            body: JSON.stringify(data),
          });
        },

        remove(id: string): Promise<void> {
          return apiFetch<void>(`/api/v1/schedules/${id}`, { method: 'DELETE' });
        },

        count(): Promise<{ total: number }> {
          return apiFetch<{ total: number }>(`/api/v1/schedules/count`);
        },
        restore(id: string): Promise<Schedule> {
  return apiFetch<Schedule>(`/api/v1/schedules/${id}/restore`, { method: 'POST' });
},

        async lock(id: string): Promise<Schedule> {
  return apiFetch<Schedule>(`/api/v1/schedules/${id}/lock`, {
    method: "POST",
    body: undefined,
  });
},

async unlock(id: string): Promise<Schedule> {
  return apiFetch<Schedule>(`/api/v1/schedules/${id}/unlock`, {
    method: "POST",
    body: undefined,
  });
},

async detect_conflicts(id: string, startsAt: string, endsAt: string): Promise<Schedule> {
  return apiFetch<Schedule>(`/api/v1/schedules/${id}/detect-conflicts`, {
    method: "POST",
    body: JSON.stringify({starts_at: startsAt, ends_at: endsAt}),
  });
},
      };
