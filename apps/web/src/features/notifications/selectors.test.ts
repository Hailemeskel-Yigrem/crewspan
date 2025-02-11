import { describe, expect, it } from "vitest";
import { selectActiveNotifications } from "./selectors";


describe("notifications selectors", () => {
  it("filters cancelled rows", () => {
    const rows = [
      { id: "1", status: "active" },
      { id: "2", status: "cancelled" },
    ] as never[];
    expect(selectActiveNotifications(rows)).toHaveLength(1);
  });
});
