import type { InventoryItem } from "../../types/inventory_item";

type WithStatus = InventoryItem & { status?: string; deletedAt?: string | null; isActive?: boolean };


export function selectActiveInventoryItems(items: InventoryItem[]): InventoryItem[] {
  return items.filter((item) => {
    const row = item as WithStatus;
    if (row.deletedAt) return false;
    if (row.status === "cancelled") return false;
    if (typeof row.isActive === "boolean") return row.isActive;
    return true;
  });
}


export function selectInventoryItemById(
  items: InventoryItem[],
  id: string,
): InventoryItem | undefined {
  return items.find((item) => item.id === id);
}


export function selectInventoryItemsByStatus(
  items: InventoryItem[],
  status: string,
): InventoryItem[] {
  return items.filter((item) => (item as WithStatus).status === status);
}


export function countInventoryItemsByStatus(items: InventoryItem[]): Record<string, number> {
  return items.reduce<Record<string, number>>((acc, item) => {
    const status = (item as WithStatus).status ?? "unknown";
    acc[status] = (acc[status] ?? 0) + 1;
    return acc;
  }, {});
}


export function sortInventoryItemsByUpdated(
  items: InventoryItem[],
  direction: "asc" | "desc" = "desc",
): InventoryItem[] {
  return [...items].sort((a, b) => {
    const cmp = a.updatedAt.localeCompare(b.updatedAt);
    return direction === "asc" ? cmp : -cmp;
  });
}
