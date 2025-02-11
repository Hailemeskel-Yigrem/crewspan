import type { PartsRequest } from "../../types/parts_request";
import { formatDateTime } from "../../utils/dates";
import { titleCase } from "../../utils/formatting";


export function formatPartsRequestLabel(item: PartsRequest): string {
  const record = item as { name?: string; title?: string; number?: string; orderNumber?: string; id: string };
  return record.name || record.title || record.orderNumber || record.number || record.id.slice(0, 8);
}


export function formatPartsRequestStatus(item: PartsRequest): string {
  const status = (item as { status?: string }).status ?? "unknown";
  return titleCase(status);
}


export function formatPartsRequestSummary(item: PartsRequest): string {
  const label = formatPartsRequestLabel(item);
  const updated = formatDateTime(item.updatedAt);
  return `${label} · updated ${updated}`;
}


export function formatPartsRequestListTitle(count: number): string {
  const noun = "PartsRequest" + (count === 1 ? "" : "s");
  return `${count} ${noun}`;
}
