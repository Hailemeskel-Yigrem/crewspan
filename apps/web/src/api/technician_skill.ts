      import { apiFetch, type PaginatedResponse } from './client';
      import type { TechnicianSkill, TechnicianSkillCreate, TechnicianSkillUpdate, TechnicianSkillListParams } from '../types/technician_skill';

      export const technicianSkillApi = {
        list(params: TechnicianSkillListParams = {}): Promise<PaginatedResponse<TechnicianSkill>> {
          const qs = new URLSearchParams();
          if (params.page) qs.set('page', String(params.page));
          if (params.pageSize) qs.set('page_size', String(params.pageSize));
          if (params.search) qs.set('search', params.search);
          if (params.orderBy) qs.set('order_by', params.orderBy);
          if (params.orderDir) qs.set('order_dir', params.orderDir);
              if (params.technician_id !== undefined) qs.set('technician_id', String(params.technician_id));
  if (params.skill_code !== undefined) qs.set('skill_code', String(params.skill_code));
          return apiFetch<PaginatedResponse<TechnicianSkill>>(`/api/v1/technician-skills?${qs}`);
        },

        get(id: string): Promise<TechnicianSkill> {
          return apiFetch<TechnicianSkill>(`/api/v1/technician-skills/${id}`);
        },

        create(data: TechnicianSkillCreate): Promise<TechnicianSkill> {
          return apiFetch<TechnicianSkill>('/api/v1/technician-skills', {
            method: 'POST',
            body: JSON.stringify(data),
          });
        },

        update(id: string, data: TechnicianSkillUpdate): Promise<TechnicianSkill> {
          return apiFetch<TechnicianSkill>(`/api/v1/technician-skills/${id}`, {
            method: 'PATCH',
            body: JSON.stringify(data),
          });
        },

        remove(id: string): Promise<void> {
          return apiFetch<void>(`/api/v1/technician-skills/${id}`, { method: 'DELETE' });
        },

        count(): Promise<{ total: number }> {
          return apiFetch<{ total: number }>(`/api/v1/technician-skills/count`);
        },
        restore(id: string): Promise<TechnicianSkill> {
  return apiFetch<TechnicianSkill>(`/api/v1/technician-skills/${id}/restore`, { method: 'POST' });
},

        async renew_certification(id: string, expiresAt: string): Promise<TechnicianSkill> {
  return apiFetch<TechnicianSkill>(`/api/v1/technician-skills/${id}/renew-certification`, {
    method: "POST",
    body: JSON.stringify({expires_at: expiresAt}),
  });
},

async is_valid(id: string): Promise<TechnicianSkill> {
  return apiFetch<TechnicianSkill>(`/api/v1/technician-skills/${id}/is-valid`, { method: "GET" });
},
      };
// history-note: evolutionary edit 76
