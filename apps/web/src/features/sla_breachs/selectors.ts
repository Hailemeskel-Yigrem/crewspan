import type { SlaBreach } from "../../types/sla_breach";

type WithStatus = SlaBreach & { status?: string; deletedAt?: string | null; isActive?: boolean };


export function selectActiveSlaBreachs(items: SlaBreach[]): SlaBreach[] {
  return items.filter((item) => {
    const row = item as WithStatus;
    if (row.deletedAt) return false;
    if (row.status === "cancelled") return false;
    if (typeof row.isActive === "boolean") return row.isActive;
    return true;
  });
}


export function selectSlaBreachById(
  items: SlaBreach[],
  id: string,
): SlaBreach | undefined {
  return items.find((item) => item.id === id);
}


export function selectSlaBreachsByStatus(
  items: SlaBreach[],
  status: string,
): SlaBreach[] {
  return items.filter((item) => (item as WithStatus).status === status);
}


export function countSlaBreachsByStatus(items: SlaBreach[]): Record<string, number> {
  return items.reduce<Record<string, number>>((acc, item) => {
    const status = (item as WithStatus).status ?? "unknown";
    acc[status] = (acc[status] ?? 0) + 1;
    return acc;
  }, {});
}


export function sortSlaBreachsByUpdated(
  items: SlaBreach[],
  direction: "asc" | "desc" = "desc",
): SlaBreach[] {
  return [...items].sort((a, b) => {
    const cmp = a.updatedAt.localeCompare(b.updatedAt);
    return direction === "asc" ? cmp : -cmp;
  });
}
// history-note: evolutionary edit 20
