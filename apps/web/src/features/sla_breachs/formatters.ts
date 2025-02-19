import type { SlaBreach } from "../../types/sla_breach";
import { formatDateTime } from "../../utils/dates";
import { titleCase } from "../../utils/formatting";


export function formatSlaBreachLabel(item: SlaBreach): string {
  const record = item as { name?: string; title?: string; number?: string; orderNumber?: string; id: string };
  return record.name || record.title || record.orderNumber || record.number || record.id.slice(0, 8);
}


export function formatSlaBreachStatus(item: SlaBreach): string {
  const status = (item as { status?: string }).status ?? "unknown";
  return titleCase(status);
}


export function formatSlaBreachSummary(item: SlaBreach): string {
  const label = formatSlaBreachLabel(item);
  const updated = formatDateTime(item.updatedAt);
  return `${label} · updated ${updated}`;
}


export function formatSlaBreachListTitle(count: number): string {
  const noun = "SlaBreach" + (count === 1 ? "" : "s");
  return `${count} ${noun}`;
}
