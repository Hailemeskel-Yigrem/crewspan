import type { WorkOrder } from "../../types/work_order";
import { formatDateTime } from "../../utils/dates";
import { titleCase } from "../../utils/formatting";


export function formatWorkOrderLabel(item: WorkOrder): string {
  const record = item as { name?: string; title?: string; number?: string; orderNumber?: string; id: string };
  return record.name || record.title || record.orderNumber || record.number || record.id.slice(0, 8);
}


export function formatWorkOrderStatus(item: WorkOrder): string {
  const status = (item as { status?: string }).status ?? "unknown";
  return titleCase(status);
}


export function formatWorkOrderSummary(item: WorkOrder): string {
  const label = formatWorkOrderLabel(item);
  const updated = formatDateTime(item.updatedAt);
  return `${label} · updated ${updated}`;
}


export function formatWorkOrderListTitle(count: number): string {
  const noun = "WorkOrder" + (count === 1 ? "" : "s");
  return `${count} ${noun}`;
}
