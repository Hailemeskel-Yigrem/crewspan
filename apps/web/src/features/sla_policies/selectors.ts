import type { SlaPolicy } from "../../types/sla_policy";

type WithStatus = SlaPolicy & { status?: string; deletedAt?: string | null; isActive?: boolean };


export function selectActiveSlaPolicys(items: SlaPolicy[]): SlaPolicy[] {
  return items.filter((item) => {
    const row = item as WithStatus;
    if (row.deletedAt) return false;
    if (row.status === "cancelled") return false;
    if (typeof row.isActive === "boolean") return row.isActive;
    return true;
  });
}


export function selectSlaPolicyById(
  items: SlaPolicy[],
  id: string,
): SlaPolicy | undefined {
  return items.find((item) => item.id === id);
}


export function selectSlaPolicysByStatus(
  items: SlaPolicy[],
  status: string,
): SlaPolicy[] {
  return items.filter((item) => (item as WithStatus).status === status);
}


export function countSlaPolicysByStatus(items: SlaPolicy[]): Record<string, number> {
  return items.reduce<Record<string, number>>((acc, item) => {
    const status = (item as WithStatus).status ?? "unknown";
    acc[status] = (acc[status] ?? 0) + 1;
    return acc;
  }, {});
}


export function sortSlaPolicysByUpdated(
  items: SlaPolicy[],
  direction: "asc" | "desc" = "desc",
): SlaPolicy[] {
  return [...items].sort((a, b) => {
    const cmp = a.updatedAt.localeCompare(b.updatedAt);
    return direction === "asc" ? cmp : -cmp;
  });
}
