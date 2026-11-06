import { describe, expect, it } from "vitest";
import { peakYear, yearSeries } from "../assets/js/years.js";
import { speechCount, termYears } from "../assets/js/format.js";

describe("yearSeries", () => {
  it("sorts the years and divides the speeches by the tagged speeches", () => {
    const rows = yearSeries([{ year: 2002, n: 1, tagged: 4 }, { year: "2001", n: "3", tagged: 0 }]);
    expect(rows).toEqual([{ year: 2001, n: 3, tagged: 0, rate: 0 }, { year: 2002, n: 1, tagged: 4, rate: 0.25 }]);
  });
});

describe("peakYear", () => {
  it("takes the earlier year on a tie, and null when no year has a speech", () => {
    expect(peakYear([{ year: 2000, n: 2 }, { year: 2001, n: 2 }]).year).toBe(2000);
    expect(peakYear([{ year: 2000, n: 0 }])).toBeNull();
  });
});

describe("format helpers", () => {
  it("names the count of speeches and the years of a term", () => {
    expect(speechCount(1)).toBe("1 speech");
    expect(speechCount(1234)).toBe("1,234 speeches");
    expect([13, 14, 18, 99].map(termYears)).toEqual(["1999–2004", "2004–09", "2024–", ""]);
  });
});
