import type { Schedule } from "../../types/schedule";

type WithStatus = Schedule & { status?: string; deletedAt?: string | null; isActive?: boolean };


export function selectActiveSchedules(items: Schedule[]): Schedule[] {
  return items.filter((item) => {
    const row = item as WithStatus;
    if (row.deletedAt) return false;
    if (row.status === "cancelled") return false;
    if (typeof row.isActive === "boolean") return row.isActive;
    return true;
  });
}


export function selectScheduleById(
  items: Schedule[],
  id: string,
): Schedule | undefined {
  return items.find((item) => item.id === id);
}


export function selectSchedulesByStatus(
  items: Schedule[],
  status: string,
): Schedule[] {
  return items.filter((item) => (item as WithStatus).status === status);
}


export function countSchedulesByStatus(items: Schedule[]): Record<string, number> {
  return items.reduce<Record<string, number>>((acc, item) => {
    const status = (item as WithStatus).status ?? "unknown";
    acc[status] = (acc[status] ?? 0) + 1;
    return acc;
  }, {});
}


export function sortSchedulesByUpdated(
  items: Schedule[],
  direction: "asc" | "desc" = "desc",
): Schedule[] {
  return [...items].sort((a, b) => {
    const cmp = a.updatedAt.localeCompare(b.updatedAt);
    return direction === "asc" ? cmp : -cmp;
  });
}
