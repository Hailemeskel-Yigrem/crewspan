import type { SlaPolicy } from "../../types/sla_policy";
import { formatDateTime } from "../../utils/dates";
import { titleCase } from "../../utils/formatting";


export function formatSlaPolicyLabel(item: SlaPolicy): string {
  const record = item as { name?: string; title?: string; number?: string; orderNumber?: string; id: string };
  return record.name || record.title || record.orderNumber || record.number || record.id.slice(0, 8);
}


export function formatSlaPolicyStatus(item: SlaPolicy): string {
  const status = (item as { status?: string }).status ?? "unknown";
  return titleCase(status);
}


export function formatSlaPolicySummary(item: SlaPolicy): string {
  const label = formatSlaPolicyLabel(item);
  const updated = formatDateTime(item.updatedAt);
  return `${label} · updated ${updated}`;
}


export function formatSlaPolicyListTitle(count: number): string {
  const noun = "SlaPolicy" + (count === 1 ? "" : "s");
  return `${count} ${noun}`;
}
