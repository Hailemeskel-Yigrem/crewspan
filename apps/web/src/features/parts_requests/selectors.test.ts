import { describe, expect, it } from "vitest";
import { selectActivePartsRequests } from "./selectors";


describe("parts_requests selectors", () => {
  it("filters cancelled rows", () => {
    const rows = [
      { id: "1", status: "active" },
      { id: "2", status: "cancelled" },
    ] as never[];
    expect(selectActivePartsRequests(rows)).toHaveLength(1);
  });
});
