import type { Schedule } from "../../types/schedule";
import { formatDateTime } from "../../utils/dates";
import { titleCase } from "../../utils/formatting";


export function formatScheduleLabel(item: Schedule): string {
  const record = item as { name?: string; title?: string; number?: string; orderNumber?: string; id: string };
  return record.name || record.title || record.orderNumber || record.number || record.id.slice(0, 8);
}


export function formatScheduleStatus(item: Schedule): string {
  const status = (item as { status?: string }).status ?? "unknown";
  return titleCase(status);
}


export function formatScheduleSummary(item: Schedule): string {
  const label = formatScheduleLabel(item);
  const updated = formatDateTime(item.updatedAt);
  return `${label} · updated ${updated}`;
}


export function formatScheduleListTitle(count: number): string {
  const noun = "Schedule" + (count === 1 ? "" : "s");
  return `${count} ${noun}`;
}
