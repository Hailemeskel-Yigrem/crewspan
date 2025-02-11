import { describe, expect, it } from "vitest";
import { selectActivePayments } from "./selectors";


describe("payments selectors", () => {
  it("filters cancelled rows", () => {
    const rows = [
      { id: "1", status: "active" },
      { id: "2", status: "cancelled" },
    ] as never[];
    expect(selectActivePayments(rows)).toHaveLength(1);
  });
});
