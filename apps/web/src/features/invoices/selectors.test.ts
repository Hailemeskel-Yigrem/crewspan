import { describe, expect, it } from "vitest";
import { selectActiveInvoices } from "./selectors";


describe("invoices selectors", () => {
  it("filters cancelled rows", () => {
    const rows = [
      { id: "1", status: "active" },
      { id: "2", status: "cancelled" },
    ] as never[];
    expect(selectActiveInvoices(rows)).toHaveLength(1);
  });
});
