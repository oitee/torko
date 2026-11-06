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

describe("yearLabels", () => {
  it("keeps the first and last year and the fifth years that do not touch them", async () => {
    const { yearLabels } = await import("../pages/trends/CompareChart.jsx");
    const years = Array.from({ length: 28 }, (_, i) => 1999 + i);
    expect(yearLabels(years)).toEqual([1999, 2005, 2010, 2015, 2020, 2026]);
  });
});

describe("displayName, defaultCompare and toCsv", () => {
  it("tidies tag names from the stored data for display only", async () => {
    const { displayName } = await import("../pages/trends/trendsData.js");
    expect(displayName("Novel Coronavirus (COVID -19)")).toBe("Novel Coronavirus (COVID-19)");
    expect(displayName("Insurance Regulatory and Development Authority (IRDA")).toBe(
      "Insurance Regulatory and Development Authority (IRDA)"
    );
    expect(displayName("NATIONAL FOOD SECURITY ACT")).toBe("National Food Security Act");
    expect(displayName("Women")).toBe("Women");
  });

  it("compares the leading subjects of the newest complete year and the year before", async () => {
    const { defaultCompare } = await import("../pages/trends/trendsData.js");
    const years = [
      { year: 2026, tagged: 1166, subjects: [{ slug: "women" }] },
      { year: 2025, tagged: 5659, subjects: [{ slug: "jal-jeevan" }] },
      { year: 2024, tagged: 4298, subjects: [{ slug: "jal-jeevan" }, { slug: "ayushman" }] },
    ];
    expect(defaultCompare(years)).toEqual({ slugs: ["jal-jeevan", "ayushman"], years: [2025, 2024] });
  });

  it("quotes a CSV cell that holds a comma or a quote", async () => {
    const { toCsv } = await import("../pages/trends/trendsData.js");
    expect(toCsv([["name", "n"], ['Bills, "pending"', 3]])).toBe('name,n\n"Bills, ""pending""",3');
  });
});
