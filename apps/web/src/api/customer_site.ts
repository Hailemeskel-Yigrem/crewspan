      import { apiFetch, type PaginatedResponse } from './client';
      import type { CustomerSite, CustomerSiteCreate, CustomerSiteUpdate, CustomerSiteListParams } from '../types/customer_site';

      export const customerSiteApi = {
        list(params: CustomerSiteListParams = {}): Promise<PaginatedResponse<CustomerSite>> {
          const qs = new URLSearchParams();
          if (params.page) qs.set('page', String(params.page));
          if (params.pageSize) qs.set('page_size', String(params.pageSize));
          if (params.search) qs.set('search', params.search);
          if (params.orderBy) qs.set('order_by', params.orderBy);
          if (params.orderDir) qs.set('order_dir', params.orderDir);
              if (params.customer_id !== undefined) qs.set('customer_id', String(params.customer_id));
  if (params.site_code !== undefined) qs.set('site_code', String(params.site_code));
          return apiFetch<PaginatedResponse<CustomerSite>>(`/api/v1/customer-sites?${qs}`);
        },

        get(id: string): Promise<CustomerSite> {
          return apiFetch<CustomerSite>(`/api/v1/customer-sites/${id}`);
        },

        create(data: CustomerSiteCreate): Promise<CustomerSite> {
          return apiFetch<CustomerSite>('/api/v1/customer-sites', {
            method: 'POST',
            body: JSON.stringify(data),
          });
        },

        update(id: string, data: CustomerSiteUpdate): Promise<CustomerSite> {
          return apiFetch<CustomerSite>(`/api/v1/customer-sites/${id}`, {
            method: 'PATCH',
            body: JSON.stringify(data),
          });
        },

        remove(id: string): Promise<void> {
          return apiFetch<void>(`/api/v1/customer-sites/${id}`, { method: 'DELETE' });
        },

        count(): Promise<{ total: number }> {
          return apiFetch<{ total: number }>(`/api/v1/customer-sites/count`);
        },
        restore(id: string): Promise<CustomerSite> {
  return apiFetch<CustomerSite>(`/api/v1/customer-sites/${id}/restore`, { method: 'POST' });
},

        async geocode(id: string): Promise<CustomerSite> {
  return apiFetch<CustomerSite>(`/api/v1/customer-sites/${id}/geocode`, {
    method: "POST",
    body: undefined,
  });
},

async validate_access_window(id: string, at: string): Promise<CustomerSite> {
  return apiFetch<CustomerSite>(`/api/v1/customer-sites/${id}/validate-access-window`, {
    method: "POST",
    body: JSON.stringify({at: at}),
  });
},
      };
