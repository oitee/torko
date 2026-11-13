import { describe, expect, it } from "vitest";
import { tickName } from "../pages/search/FilterRail.jsx";

// A screen reader reads tickName as the name of a filter tick box.
describe("tickName", () => {
  it("names the value and its count, with a space and a noun", () => {
    expect(tickName({ label: "Students", n: 92 })).toBe("Students, 92 speeches");
  });

  it("uses the singular for one speech", () => {
    expect(tickName({ label: "BJD", n: 1 })).toBe("BJD, 1 speech");
  });

  it("gives only the value when the row shows no count", () => {
    expect(tickName({ label: "Education", n: 313 }, false)).toBe("Education");
    expect(tickName({ label: "Education", n: null })).toBe("Education");
  });
});
