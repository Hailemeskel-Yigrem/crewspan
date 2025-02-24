import { describe, expect, it } from "vitest";
import { selectActiveWebhooks } from "./selectors";


describe("webhooks selectors", () => {
  it("filters cancelled rows", () => {
    const rows = [
      { id: "1", status: "active" },
      { id: "2", status: "cancelled" },
    ] as never[];
    expect(selectActiveWebhooks(rows)).toHaveLength(1);
  });
});
