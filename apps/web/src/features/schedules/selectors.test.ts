import { describe, expect, it } from "vitest";
import { selectActiveSchedules } from "./selectors";


describe("schedules selectors", () => {
  it("filters cancelled rows", () => {
    const rows = [
      { id: "1", status: "active" },
      { id: "2", status: "cancelled" },
    ] as never[];
    expect(selectActiveSchedules(rows)).toHaveLength(1);
  });
});
