import type { Webhook } from "../../types/webhook";

type WithStatus = Webhook & { status?: string; deletedAt?: string | null; isActive?: boolean };


export function selectActiveWebhooks(items: Webhook[]): Webhook[] {
  return items.filter((item) => {
    const row = item as WithStatus;
    if (row.deletedAt) return false;
    if (row.status === "cancelled") return false;
    if (typeof row.isActive === "boolean") return row.isActive;
    return true;
  });
}


export function selectWebhookById(
  items: Webhook[],
  id: string,
): Webhook | undefined {
  return items.find((item) => item.id === id);
}


export function selectWebhooksByStatus(
  items: Webhook[],
  status: string,
): Webhook[] {
  return items.filter((item) => (item as WithStatus).status === status);
}


export function countWebhooksByStatus(items: Webhook[]): Record<string, number> {
  return items.reduce<Record<string, number>>((acc, item) => {
    const status = (item as WithStatus).status ?? "unknown";
    acc[status] = (acc[status] ?? 0) + 1;
    return acc;
  }, {});
}


export function sortWebhooksByUpdated(
  items: Webhook[],
  direction: "asc" | "desc" = "desc",
): Webhook[] {
  return [...items].sort((a, b) => {
    const cmp = a.updatedAt.localeCompare(b.updatedAt);
    return direction === "asc" ? cmp : -cmp;
  });
}
