import { describe, expect, it } from "vitest";
import { selectActiveDispatchs } from "./selectors";


describe("dispatchs selectors", () => {
  it("filters cancelled rows", () => {
    const rows = [
      { id: "1", status: "active" },
      { id: "2", status: "cancelled" },
    ] as never[];
    expect(selectActiveDispatchs(rows)).toHaveLength(1);
  });
});
