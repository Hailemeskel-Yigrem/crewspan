import type { Notification } from "../../types/notification";

type WithStatus = Notification & { status?: string; deletedAt?: string | null; isActive?: boolean };


export function selectActiveNotifications(items: Notification[]): Notification[] {
  return items.filter((item) => {
    const row = item as WithStatus;
    if (row.deletedAt) return false;
    if (row.status === "cancelled") return false;
    if (typeof row.isActive === "boolean") return row.isActive;
    return true;
  });
}


export function selectNotificationById(
  items: Notification[],
  id: string,
): Notification | undefined {
  return items.find((item) => item.id === id);
}


export function selectNotificationsByStatus(
  items: Notification[],
  status: string,
): Notification[] {
  return items.filter((item) => (item as WithStatus).status === status);
}


export function countNotificationsByStatus(items: Notification[]): Record<string, number> {
  return items.reduce<Record<string, number>>((acc, item) => {
    const status = (item as WithStatus).status ?? "unknown";
    acc[status] = (acc[status] ?? 0) + 1;
    return acc;
  }, {});
}


export function sortNotificationsByUpdated(
  items: Notification[],
  direction: "asc" | "desc" = "desc",
): Notification[] {
  return [...items].sort((a, b) => {
    const cmp = a.updatedAt.localeCompare(b.updatedAt);
    return direction === "asc" ? cmp : -cmp;
  });
}
