import { describe, expect, it } from "vitest";
import { selectActiveTechnicians } from "./selectors";


describe("technicians selectors", () => {
  it("filters cancelled rows", () => {
    const rows = [
      { id: "1", status: "active" },
      { id: "2", status: "cancelled" },
    ] as never[];
    expect(selectActiveTechnicians(rows)).toHaveLength(1);
  });
});
