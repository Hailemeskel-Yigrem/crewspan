import { describe, expect, it } from "vitest";
import { selectActiveSlaBreachs } from "./selectors";


describe("sla_breachs selectors", () => {
  it("filters cancelled rows", () => {
    const rows = [
      { id: "1", status: "active" },
      { id: "2", status: "cancelled" },
    ] as never[];
    expect(selectActiveSlaBreachs(rows)).toHaveLength(1);
  });
});
