import React from "react";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import TagWhenChart, { yearRates, yearReadout } from "../pages/tag/TagWhenChart.jsx";

afterEach(cleanup);

describe("TagWhenChart component", () => {
  // 2001 has more speeches with the tag than 2004, but a lower rate, because 2001 has more tagged speeches.
  const mockYears = [
    { year: 2004, n: 10, tagged: 1000 },
    { year: 2000, n: 0, tagged: 0 },
    { year: 2001, n: 20, tagged: 8000 },
  ];

  it("gives each year a rate per 1,000 tagged speeches, in year order", () => {
    const rates = yearRates(mockYears);
    expect(rates.map((r) => r.year)).toEqual([2000, 2001, 2004]);
    expect(rates.map((r) => r.per1000)).toEqual([null, 2.5, 10]);
  });

  it("writes one plain sentence for a year", () => {
    expect(yearReadout({ year: 2014, n: 12, tagged: 2840, per1000: 4.225 })).toBe(
      "2014: 4.2 in every 1,000 tagged speeches (12 speeches)"
    );
    expect(yearReadout({ year: 2014, n: 1, tagged: 400, per1000: 2.5 })).toBe(
      "2014: 2.5 in every 1,000 tagged speeches (1 speech)"
    );
    expect(yearReadout({ year: 2015, n: 0, tagged: 400, per1000: 0 })).toBe("2015: no speech with this tag");
    expect(yearReadout({ year: 2000, n: 0, tagged: 0, per1000: null })).toBe("2000: no tagged speeches");
  });

  it("draws the bar height from the rate, not the count", () => {
    render(<TagWhenChart years={mockYears} selectedTerm="" />);

    expect(screen.getByRole("heading", { name: "When" })).toBeTruthy();
    expect(screen.getByText("Point at a year")).toBeTruthy();
    expect(screen.getByTestId("year-col-2004").style.height).toBe("100%");
    expect(screen.getByTestId("year-col-2001").style.height).toBe("25%");
    expect(screen.getByTestId("year-col-2000").style.height).toBe("0%");
  });

  it("updates the readout on hover", () => {
    render(<TagWhenChart years={mockYears} selectedTerm="" />);

    const col2001 = screen.getByTestId("year-col-2001");
    fireEvent.mouseEnter(col2001);
    expect(screen.getByText("2001: 2.5 in every 1,000 tagged speeches (20 speeches)")).toBeTruthy();

    fireEvent.mouseLeave(col2001);
    expect(screen.getByText("Point at a year")).toBeTruthy();
  });

  it("fades years outside the selected term", () => {
    render(<TagWhenChart years={mockYears} selectedTerm="14" />);

    expect(screen.getByTestId("year-col-2000").classList.contains("tag-when-chart__col--faded")).toBe(true);
    expect(screen.getByTestId("year-col-2004").classList.contains("tag-when-chart__col--faded")).toBe(false);
  });

  it("toggles table view with Show as table button", () => {
    render(<TagWhenChart years={mockYears} selectedTerm="" />);

    fireEvent.click(screen.getByRole("button", { name: "Show as table" }));

    expect(screen.getByRole("button", { name: "Show as chart" })).toBeTruthy();
    expect(screen.getByRole("table").classList.contains("sr-only")).toBe(false);
  });

  it("draws nothing when there are no years", () => {
    const { container } = render(<TagWhenChart years={[]} />);
    expect(container.innerHTML).toBe("");
  });
});
