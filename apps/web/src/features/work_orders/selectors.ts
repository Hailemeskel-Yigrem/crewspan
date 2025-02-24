import type { WorkOrder } from "../../types/work_order";

type WithStatus = WorkOrder & { status?: string; deletedAt?: string | null; isActive?: boolean };


export function selectActiveWorkOrders(items: WorkOrder[]): WorkOrder[] {
  return items.filter((item) => {
    const row = item as WithStatus;
    if (row.deletedAt) return false;
    if (row.status === "cancelled") return false;
    if (typeof row.isActive === "boolean") return row.isActive;
    return true;
  });
}


export function selectWorkOrderById(
  items: WorkOrder[],
  id: string,
): WorkOrder | undefined {
  return items.find((item) => item.id === id);
}


export function selectWorkOrdersByStatus(
  items: WorkOrder[],
  status: string,
): WorkOrder[] {
  return items.filter((item) => (item as WithStatus).status === status);
}


export function countWorkOrdersByStatus(items: WorkOrder[]): Record<string, number> {
  return items.reduce<Record<string, number>>((acc, item) => {
    const status = (item as WithStatus).status ?? "unknown";
    acc[status] = (acc[status] ?? 0) + 1;
    return acc;
  }, {});
}


export function sortWorkOrdersByUpdated(
  items: WorkOrder[],
  direction: "asc" | "desc" = "desc",
): WorkOrder[] {
  return [...items].sort((a, b) => {
    const cmp = a.updatedAt.localeCompare(b.updatedAt);
    return direction === "asc" ? cmp : -cmp;
  });
}
