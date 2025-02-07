import type { Dispatch } from "../../types/dispatch";
import { formatDateTime } from "../../utils/dates";
import { titleCase } from "../../utils/formatting";


export function formatDispatchLabel(item: Dispatch): string {
  const record = item as { name?: string; title?: string; number?: string; orderNumber?: string; id: string };
  return record.name || record.title || record.orderNumber || record.number || record.id.slice(0, 8);
}


export function formatDispatchStatus(item: Dispatch): string {
  const status = (item as { status?: string }).status ?? "unknown";
  return titleCase(status);
}


export function formatDispatchSummary(item: Dispatch): string {
  const label = formatDispatchLabel(item);
  const updated = formatDateTime(item.updatedAt);
  return `${label} · updated ${updated}`;
}


export function formatDispatchListTitle(count: number): string {
  const noun = "Dispatch" + (count === 1 ? "" : "s");
  return `${count} ${noun}`;
}
