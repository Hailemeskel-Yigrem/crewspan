import { describe, expect, it } from "vitest";
import { selectActiveInventoryItems } from "./selectors";


describe("inventory_items selectors", () => {
  it("filters cancelled rows", () => {
    const rows = [
      { id: "1", status: "active" },
      { id: "2", status: "cancelled" },
    ] as never[];
    expect(selectActiveInventoryItems(rows)).toHaveLength(1);
  });
});
