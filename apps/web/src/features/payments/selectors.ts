import type { Payment } from "../../types/payment";

type WithStatus = Payment & { status?: string; deletedAt?: string | null; isActive?: boolean };


export function selectActivePayments(items: Payment[]): Payment[] {
  return items.filter((item) => {
    const row = item as WithStatus;
    if (row.deletedAt) return false;
    if (row.status === "cancelled") return false;
    if (typeof row.isActive === "boolean") return row.isActive;
    return true;
  });
}


export function selectPaymentById(
  items: Payment[],
  id: string,
): Payment | undefined {
  return items.find((item) => item.id === id);
}


export function selectPaymentsByStatus(
  items: Payment[],
  status: string,
): Payment[] {
  return items.filter((item) => (item as WithStatus).status === status);
}


export function countPaymentsByStatus(items: Payment[]): Record<string, number> {
  return items.reduce<Record<string, number>>((acc, item) => {
    const status = (item as WithStatus).status ?? "unknown";
    acc[status] = (acc[status] ?? 0) + 1;
    return acc;
  }, {});
}


export function sortPaymentsByUpdated(
  items: Payment[],
  direction: "asc" | "desc" = "desc",
): Payment[] {
  return [...items].sort((a, b) => {
    const cmp = a.updatedAt.localeCompare(b.updatedAt);
    return direction === "asc" ? cmp : -cmp;
  });
}
