import type { PartsRequest } from "../../types/parts_request";

type WithStatus = PartsRequest & { status?: string; deletedAt?: string | null; isActive?: boolean };


export function selectActivePartsRequests(items: PartsRequest[]): PartsRequest[] {
  return items.filter((item) => {
    const row = item as WithStatus;
    if (row.deletedAt) return false;
    if (row.status === "cancelled") return false;
    if (typeof row.isActive === "boolean") return row.isActive;
    return true;
  });
}


export function selectPartsRequestById(
  items: PartsRequest[],
  id: string,
): PartsRequest | undefined {
  return items.find((item) => item.id === id);
}


export function selectPartsRequestsByStatus(
  items: PartsRequest[],
  status: string,
): PartsRequest[] {
  return items.filter((item) => (item as WithStatus).status === status);
}


export function countPartsRequestsByStatus(items: PartsRequest[]): Record<string, number> {
  return items.reduce<Record<string, number>>((acc, item) => {
    const status = (item as WithStatus).status ?? "unknown";
    acc[status] = (acc[status] ?? 0) + 1;
    return acc;
  }, {});
}


export function sortPartsRequestsByUpdated(
  items: PartsRequest[],
  direction: "asc" | "desc" = "desc",
): PartsRequest[] {
  return [...items].sort((a, b) => {
    const cmp = a.updatedAt.localeCompare(b.updatedAt);
    return direction === "asc" ? cmp : -cmp;
  });
}
