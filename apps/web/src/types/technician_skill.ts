      /** Skill and certification assignments for technicians. */
      export interface TechnicianSkill {
        id: string;
        tenantId: string;
        technician_id: string;
skill_code: string;
skill_name: string;
proficiency_level: number;
certified_at: string | null;
expires_at: string | null;
        createdAt: string;
        updatedAt: string;
        deletedAt: string | null;
      }

      export interface TechnicianSkillCreate {
        technician_id?: string;
skill_code?: string;
skill_name?: string;
certified_at?: string | null;
expires_at?: string | null;
      }

      export interface TechnicianSkillUpdate {
        technician_id?: string;
skill_code?: string;
skill_name?: string;
proficiency_level?: number;
certified_at?: string | null;
expires_at?: string | null;
      }

      export interface TechnicianSkillListParams {
        page?: number;
        pageSize?: number;
        search?: string;
        orderBy?: string;
        orderDir?: 'asc' | 'desc';
          technician_id?: string;
skill_code?: string;
      }

      export interface TechnicianSkillListResponse {
        items: TechnicianSkill[];
        total: number;
        page: number;
        pageSize: number;
        pages: number;
      }

      export function isTechnicianSkillActive(record: TechnicianSkill): boolean {
        const row = record as { isActive?: boolean; status?: string; deletedAt?: string | null };
        if (row.deletedAt) return false;
        if (typeof row.isActive === 'boolean') return row.isActive;
        if (row.status) return !['cancelled', 'inactive', 'void'].includes(row.status);
        return true;
      }

      export function technicianSkillDisplayName(record: TechnicianSkill): string {
        const row = record as { name?: string; title?: string; orderNumber?: string; displayName?: string };
        return row.displayName || row.name || row.title || row.orderNumber || record.id.slice(0, 8);
      }
