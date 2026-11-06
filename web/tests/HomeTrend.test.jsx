import React from "react";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { MemoryRouter } from "react-router-dom";
import HomeTrend, { yearShares } from "../pages/home/HomeTrend.jsx";
import featuredAnswer from "./fixtures/home/home_featured.json";

afterEach(cleanup);

const trend = featuredAnswer.trend;

function renderTrend(t) {
  return render(
    <MemoryRouter>
      <HomeTrend trend={t} />
    </MemoryRouter>
  );
}

describe("yearShares", () => {
  it("divides the speeches with the tag by the tagged speeches of the year", () => {
    const shares = yearShares(trend.years);
    const y2014 = shares.find((d) => d.year === 2014);
    expect(y2014.rate).toBeCloseTo(21 / 4973);
    expect(shares).toHaveLength(trend.years.length);
  });

  it("gives a share of 0 to a year with no tagged speech", () => {
    expect(yearShares([{ year: 2000, n: 3, tagged: 0 }])[0].rate).toBe(0);
  });

  it("sorts the years", () => {
    const shares = yearShares([{ year: 2002, n: 1, tagged: 2 }, { year: 2001, n: 1, tagged: 2 }]);
    expect(shares.map((d) => d.year)).toEqual([2001, 2002]);
  });
});

describe("HomeTrend", () => {
  it("draws one bar for each year, labelled with its share and its count", () => {
    renderTrend(trend);
    expect(screen.getByTestId("trend-year-2014").getAttribute("aria-label")).toBe("2014: 0.4% (21 of 4,973)");
    expect(screen.getAllByTestId(/^trend-year-/)).toHaveLength(trend.years.length);
  });

  it("makes the bar of the year with the highest share the tallest, not the year with the most speeches", () => {
    renderTrend(trend);
    const heights = Object.fromEntries(
      trend.years.map((y) => [y.year, parseFloat(screen.getByTestId(`trend-year-${y.year}`).style.height)])
    );
    // 2014 has 21 of 4,973. 2019 has 18 of 8,243: fewer per tagged speech.
    expect(heights[2014]).toBe(100);
    expect(heights[2019]).toBeLessThan(heights[2014]);
  });

  it("moves the pop-up and the green to the year under the pointer, and back to the highest year after", () => {
    const { container } = renderTrend(trend);
    const tip = () => container.querySelector(".bar-tip").textContent;
    fireEvent.mouseEnter(screen.getByTestId("trend-year-2019"));
    expect(tip()).toMatch(/^2019 · /);
    // Only the bar under the pointer is green. The highest year is not green while another bar is active.
    expect(screen.getByTestId("trend-year-2019").className).toContain("home-trend__col--active");
    expect(screen.getByTestId("trend-year-2014").className).not.toContain("home-trend__col--active");
    fireEvent.mouseLeave(container.querySelector(".home-trend__plot"));
    // Back at rest: the highest year is green again, with no pop-up.
    expect(container.querySelector(".bar-tip")).toBeNull();
    expect(screen.getByTestId("trend-year-2014").className).toContain("home-trend__col--active");
    fireEvent.mouseEnter(screen.getByTestId("trend-year-2014"));
    expect(tip()).toBe("2014 · 0.4% (21 of 4,973)");
  });

  it("shows the data as a table on request", () => {
    renderTrend(trend);
    fireEvent.click(screen.getByRole("button", { name: "Show as table" }));
    expect(screen.getByRole("table").className).toBe("home-trend__table");
    expect(screen.getByRole("button", { name: "Show as chart" })).toBeTruthy();
  });

  it("states the total and links to the tag", () => {
    renderTrend(trend);
    expect(screen.getByText("205 speeches carry the tag Arrears in all years.")).toBeTruthy();
    expect(screen.getByRole("link", { name: "Open the tag Arrears and read its speeches" }).getAttribute("href")).toBe("/tag/arrears");
  });

  it("rests on the highest year without the word peak, and labels the middle year of the axis", () => {
    const { container } = renderTrend(trend);
    // At rest the highest year is green, with no pop-up.
    expect(container.querySelector(".bar-tip")).toBeNull();
    expect(container.textContent).not.toMatch(/peak/i);
    expect(screen.getByTestId("trend-year-2014").className).toContain("home-trend__col--active");
    const ticks = [...container.querySelectorAll(".home-trend__axis span")].map((n) => n.textContent);
    const years = trend.years.map((y) => y.year);
    const lo = Math.min(...years);
    const hi = Math.max(...years);
    expect(ticks).toEqual([String(lo), String(Math.round((lo + hi) / 2)), String(hi)]);
  });

  it("shows the share of the year under a finger that touches the chart", () => {
    const { container } = renderTrend(trend);
    const plot = container.querySelector(".home-trend__plot");
    plot.getBoundingClientRect = () => ({ left: 0, width: 100 });
    fireEvent.touchStart(plot, { touches: [{ clientX: 0 }] });
    const first = [...trend.years].sort((a, b) => a.year - b.year)[0];
    expect(container.querySelector(".bar-tip").textContent).toMatch(new RegExp(`^${first.year} · `));
  });

  it("shows nothing without years", () => {
    const { container } = renderTrend({ ...trend, years: [] });
    expect(container.innerHTML).toBe("");
  });
});
