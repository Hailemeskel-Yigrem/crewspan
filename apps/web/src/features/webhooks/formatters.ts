import type { Webhook } from "../../types/webhook";
import { formatDateTime } from "../../utils/dates";
import { titleCase } from "../../utils/formatting";


export function formatWebhookLabel(item: Webhook): string {
  const record = item as { name?: string; title?: string; number?: string; orderNumber?: string; id: string };
  return record.name || record.title || record.orderNumber || record.number || record.id.slice(0, 8);
}


export function formatWebhookStatus(item: Webhook): string {
  const status = (item as { status?: string }).status ?? "unknown";
  return titleCase(status);
}


export function formatWebhookSummary(item: Webhook): string {
  const label = formatWebhookLabel(item);
  const updated = formatDateTime(item.updatedAt);
  return `${label} · updated ${updated}`;
}


export function formatWebhookListTitle(count: number): string {
  const noun = "Webhook" + (count === 1 ? "" : "s");
  return `${count} ${noun}`;
}
