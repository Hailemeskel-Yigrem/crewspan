import { describe, expect, it } from "vitest";
import { selectActiveSlaPolicys } from "./selectors";


describe("sla_policies selectors", () => {
  it("filters cancelled rows", () => {
    const rows = [
      { id: "1", status: "active" },
      { id: "2", status: "cancelled" },
    ] as never[];
    expect(selectActiveSlaPolicys(rows)).toHaveLength(1);
  });
});
