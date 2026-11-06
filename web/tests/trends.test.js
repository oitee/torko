import { describe, expect, it } from "vitest";
import { addSlug, headline, niceMax, readSlugs, removeSlug, yearRates } from "../pages/trends/trendsData.js";

describe("trends data", () => {
  it("reads at most four different subjects from the address", () => {
    expect(readSlugs("a,b,a,c,d,e")).toEqual(["a", "b", "c", "d"]);
    expect(readSlugs(null)).toEqual([]);
  });
  it("adds and removes a subject, within the limit", () => {
    expect(addSlug(["a"], "b")).toEqual(["a", "b"]);
    expect(addSlug(["a"], "a")).toEqual(["a"]);
    expect(addSlug(["a", "b", "c", "d"], "e")).toHaveLength(4);
    expect(removeSlug(["a", "b"], "a")).toEqual(["b"]);
  });
  it("gives the share of a year, and no share with no tagged speech", () => {
    expect(yearRates([{ year: 2000, n: 5, tagged: 50 }, { year: 2001, n: 0, tagged: 0 }]).map((y) => y.rate)).toEqual([10, null]);
  });
  it("rounds the top of the chart up to a simple number", () => {
    expect([niceMax(0), niceMax(0.3), niceMax(3.4), niceMax(12.1)]).toEqual([1, 0.5, 5, 20]);
  });
  it("writes the top sentence from the largest share of any year", () => {
    const years = [{ year: 2011, subjects: [{ name: "Lokpal", share: 6.6 }] }, { year: 2020, subjects: [{ name: "COVID", share: 12.1 }] }];
    expect(headline(years)).toEqual({ year: 2020, name: "COVID", share: 12.1, phrase: "one in 8" });
    expect(headline([{ year: 2000, subjects: [{ name: "A", share: 2.7 }] }]).phrase).toBe("2.7%");
    expect(headline([])).toBeNull();
    expect(headline([{ year: 2026, tagged: 1141, subjects: [{ name: "Thin", share: 19.9 }] }, { year: 2020, tagged: 3394, subjects: [{ name: "COVID", share: 12.1 }] }]).year).toBe(2020);
  });
});
