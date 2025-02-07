import type { Invoice } from "../../types/invoice";
import { formatDateTime } from "../../utils/dates";
import { titleCase } from "../../utils/formatting";


export function formatInvoiceLabel(item: Invoice): string {
  const record = item as { name?: string; title?: string; number?: string; orderNumber?: string; id: string };
  return record.name || record.title || record.orderNumber || record.number || record.id.slice(0, 8);
}


export function formatInvoiceStatus(item: Invoice): string {
  const status = (item as { status?: string }).status ?? "unknown";
  return titleCase(status);
}


export function formatInvoiceSummary(item: Invoice): string {
  const label = formatInvoiceLabel(item);
  const updated = formatDateTime(item.updatedAt);
  return `${label} · updated ${updated}`;
}


export function formatInvoiceListTitle(count: number): string {
  const noun = "Invoice" + (count === 1 ? "" : "s");
  return `${count} ${noun}`;
}
