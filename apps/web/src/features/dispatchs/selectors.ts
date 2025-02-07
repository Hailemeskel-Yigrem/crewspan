import type { Dispatch } from "../../types/dispatch";

type WithStatus = Dispatch & { status?: string; deletedAt?: string | null; isActive?: boolean };


export function selectActiveDispatchs(items: Dispatch[]): Dispatch[] {
  return items.filter((item) => {
    const row = item as WithStatus;
    if (row.deletedAt) return false;
    if (row.status === "cancelled") return false;
    if (typeof row.isActive === "boolean") return row.isActive;
    return true;
  });
}


export function selectDispatchById(
  items: Dispatch[],
  id: string,
): Dispatch | undefined {
  return items.find((item) => item.id === id);
}


export function selectDispatchsByStatus(
  items: Dispatch[],
  status: string,
): Dispatch[] {
  return items.filter((item) => (item as WithStatus).status === status);
}


export function countDispatchsByStatus(items: Dispatch[]): Record<string, number> {
  return items.reduce<Record<string, number>>((acc, item) => {
    const status = (item as WithStatus).status ?? "unknown";
    acc[status] = (acc[status] ?? 0) + 1;
    return acc;
  }, {});
}


export function sortDispatchsByUpdated(
  items: Dispatch[],
  direction: "asc" | "desc" = "desc",
): Dispatch[] {
  return [...items].sort((a, b) => {
    const cmp = a.updatedAt.localeCompare(b.updatedAt);
    return direction === "asc" ? cmp : -cmp;
  });
}
