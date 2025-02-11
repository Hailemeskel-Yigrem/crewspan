import type { Notification } from "../../types/notification";
import { formatDateTime } from "../../utils/dates";
import { titleCase } from "../../utils/formatting";


export function formatNotificationLabel(item: Notification): string {
  const record = item as { name?: string; title?: string; number?: string; orderNumber?: string; id: string };
  return record.name || record.title || record.orderNumber || record.number || record.id.slice(0, 8);
}


export function formatNotificationStatus(item: Notification): string {
  const status = (item as { status?: string }).status ?? "unknown";
  return titleCase(status);
}


export function formatNotificationSummary(item: Notification): string {
  const label = formatNotificationLabel(item);
  const updated = formatDateTime(item.updatedAt);
  return `${label} · updated ${updated}`;
}


export function formatNotificationListTitle(count: number): string {
  const noun = "Notification" + (count === 1 ? "" : "s");
  return `${count} ${noun}`;
}
