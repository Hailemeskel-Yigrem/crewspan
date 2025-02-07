import type { Invoice } from "../../types/invoice";

type WithStatus = Invoice & { status?: string; deletedAt?: string | null; isActive?: boolean };


export function selectActiveInvoices(items: Invoice[]): Invoice[] {
  return items.filter((item) => {
    const row = item as WithStatus;
    if (row.deletedAt) return false;
    if (row.status === "cancelled") return false;
    if (typeof row.isActive === "boolean") return row.isActive;
    return true;
  });
}


export function selectInvoiceById(
  items: Invoice[],
  id: string,
): Invoice | undefined {
  return items.find((item) => item.id === id);
}


export function selectInvoicesByStatus(
  items: Invoice[],
  status: string,
): Invoice[] {
  return items.filter((item) => (item as WithStatus).status === status);
}


export function countInvoicesByStatus(items: Invoice[]): Record<string, number> {
  return items.reduce<Record<string, number>>((acc, item) => {
    const status = (item as WithStatus).status ?? "unknown";
    acc[status] = (acc[status] ?? 0) + 1;
    return acc;
  }, {});
}


export function sortInvoicesByUpdated(
  items: Invoice[],
  direction: "asc" | "desc" = "desc",
): Invoice[] {
  return [...items].sort((a, b) => {
    const cmp = a.updatedAt.localeCompare(b.updatedAt);
    return direction === "asc" ? cmp : -cmp;
  });
}
