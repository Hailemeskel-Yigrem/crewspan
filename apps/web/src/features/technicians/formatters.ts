import type { Technician } from "../../types/technician";
import { formatDateTime } from "../../utils/dates";
import { titleCase } from "../../utils/formatting";


export function formatTechnicianLabel(item: Technician): string {
  const record = item as { name?: string; title?: string; number?: string; orderNumber?: string; id: string };
  return record.name || record.title || record.orderNumber || record.number || record.id.slice(0, 8);
}


export function formatTechnicianStatus(item: Technician): string {
  const status = (item as { status?: string }).status ?? "unknown";
  return titleCase(status);
}


export function formatTechnicianSummary(item: Technician): string {
  const label = formatTechnicianLabel(item);
  const updated = formatDateTime(item.updatedAt);
  return `${label} · updated ${updated}`;
}


export function formatTechnicianListTitle(count: number): string {
  const noun = "Technician" + (count === 1 ? "" : "s");
  return `${count} ${noun}`;
}
