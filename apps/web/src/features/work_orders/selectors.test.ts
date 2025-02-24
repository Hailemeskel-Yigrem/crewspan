import { describe, expect, it } from "vitest";
import { selectActiveWorkOrders } from "./selectors";


describe("work_orders selectors", () => {
  it("filters cancelled rows", () => {
    const rows = [
      { id: "1", status: "active" },
      { id: "2", status: "cancelled" },
    ] as never[];
    expect(selectActiveWorkOrders(rows)).toHaveLength(1);
  });
});
