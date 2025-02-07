import type { InventoryItem } from "../../types/inventory_item";
import { formatDateTime } from "../../utils/dates";
import { titleCase } from "../../utils/formatting";


export function formatInventoryItemLabel(item: InventoryItem): string {
  const record = item as { name?: string; title?: string; number?: string; orderNumber?: string; id: string };
  return record.name || record.title || record.orderNumber || record.number || record.id.slice(0, 8);
}


export function formatInventoryItemStatus(item: InventoryItem): string {
  const status = (item as { status?: string }).status ?? "unknown";
  return titleCase(status);
}


export function formatInventoryItemSummary(item: InventoryItem): string {
  const label = formatInventoryItemLabel(item);
  const updated = formatDateTime(item.updatedAt);
  return `${label} · updated ${updated}`;
}


export function formatInventoryItemListTitle(count: number): string {
  const noun = "InventoryItem" + (count === 1 ? "" : "s");
  return `${count} ${noun}`;
}
