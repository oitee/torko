import { describe, expect, it } from "vitest";
import { aboveAt, monthName, rankAt, shareAt } from "../pages/trends/raceData.js";
import { spreadLabels } from "../assets/js/spreadLabels.js";

const tagged = [1000, 1000, 0, 1000];
const a = { name: "Alpha", typical: 2, n: [50, 30, 0, 20] };
const b = { name: "Beta", typical: 1, n: [10, 60, 0, 10] };

describe("race data", () => {
  it("names a month", () => {
    expect(monthName("2001-06")).toBe("June 2001");
    expect(monthName("2026-01")).toBe("January 2026");
  });
  it("gives the share of a frame, and 0 for a frame with no tagged speech", () => {
    expect(shareAt(a, tagged, 0)).toBe(5);
    expect(shareAt(a, tagged, 2)).toBe(0);
  });
  it("moves in a straight line between two frames and stays inside the frames", () => {
    expect(aboveAt(a, tagged, 0)).toBe(3);
    expect(aboveAt(a, tagged, 0.5)).toBeCloseTo(2);
    expect(aboveAt(a, tagged, 3)).toBe(0);
    expect(aboveAt(a, tagged, 9)).toBe(0);
  });
  it("ranks by the distance above typical and keeps the top only", () => {
    expect(rankAt([a, b], tagged, 0, 2, 0).map((r) => r.subject.name)).toEqual(["Alpha", "Beta"]);
    expect(rankAt([a, b], tagged, 1, 1, 0).map((r) => r.subject.name)).toEqual(["Beta"]);
  });
  it("leaves out a subject with too few speeches in the nearest frame", () => {
    expect(rankAt([a, b], tagged, 0, 2, 20).map((r) => r.subject.name)).toEqual(["Alpha"]);
  });
  it("gives a tie to the earlier name", () => {
    const c = { name: "Gamma", typical: 2, n: [50, 0, 0, 0] };
    expect(rankAt([c, a], tagged, 0, 2, 0).map((r) => r.subject.name)).toEqual(["Alpha", "Gamma"]);
  });
  it("moves labels apart, keeps their order, and keeps them above the bottom", () => {
    expect(spreadLabels([100, 102, 300], 15, 0, 400)).toEqual([100, 115, 300]);
    expect(spreadLabels([395, 398], 15, 0, 400)).toEqual([385, 400]);
    expect(spreadLabels([50, 10], 15, 0, 400)).toEqual([50, 10]);
  });
});

describe("raceScale", () => {
  it("stops the scale at the 90th percentile of the monthly leaders, so one peak does not shrink every month", async () => {
    const { raceScale } = await import("../pages/trends/raceData.js");
    // 20 months. One subject leads with 2 points above usual in 19 months and with 20 points in one month.
    const tagged = Array(20).fill(100);
    const n = Array(20).fill(5);
    n[10] = 23;
    const subject = { n, typical: 3 }; // shares are in percent: 5% usually 3%, and 23% in the peak month
    const scale = raceScale([subject], tagged, 1);
    expect(scale.top).toBeLessThan(5);
    expect(scale.top).toBeGreaterThanOrEqual(2);
  });
});
