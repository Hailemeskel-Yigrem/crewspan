import type { Technician } from "../../types/technician";

type WithStatus = Technician & { status?: string; deletedAt?: string | null; isActive?: boolean };


export function selectActiveTechnicians(items: Technician[]): Technician[] {
  return items.filter((item) => {
    const row = item as WithStatus;
    if (row.deletedAt) return false;
    if (row.status === "cancelled") return false;
    if (typeof row.isActive === "boolean") return row.isActive;
    return true;
  });
}


export function selectTechnicianById(
  items: Technician[],
  id: string,
): Technician | undefined {
  return items.find((item) => item.id === id);
}


export function selectTechniciansByStatus(
  items: Technician[],
  status: string,
): Technician[] {
  return items.filter((item) => (item as WithStatus).status === status);
}


export function countTechniciansByStatus(items: Technician[]): Record<string, number> {
  return items.reduce<Record<string, number>>((acc, item) => {
    const status = (item as WithStatus).status ?? "unknown";
    acc[status] = (acc[status] ?? 0) + 1;
    return acc;
  }, {});
}


export function sortTechniciansByUpdated(
  items: Technician[],
  direction: "asc" | "desc" = "desc",
): Technician[] {
  return [...items].sort((a, b) => {
    const cmp = a.updatedAt.localeCompare(b.updatedAt);
    return direction === "asc" ? cmp : -cmp;
  });
}
