import type { Payment } from "../../types/payment";
import { formatDateTime } from "../../utils/dates";
import { titleCase } from "../../utils/formatting";


export function formatPaymentLabel(item: Payment): string {
  const record = item as { name?: string; title?: string; number?: string; orderNumber?: string; id: string };
  return record.name || record.title || record.orderNumber || record.number || record.id.slice(0, 8);
}


export function formatPaymentStatus(item: Payment): string {
  const status = (item as { status?: string }).status ?? "unknown";
  return titleCase(status);
}


export function formatPaymentSummary(item: Payment): string {
  const label = formatPaymentLabel(item);
  const updated = formatDateTime(item.updatedAt);
  return `${label} · updated ${updated}`;
}


export function formatPaymentListTitle(count: number): string {
  const noun = "Payment" + (count === 1 ? "" : "s");
  return `${count} ${noun}`;
}
