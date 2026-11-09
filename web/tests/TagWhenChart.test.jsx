import React from "react";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { MemoryRouter } from "react-router-dom";
import TagWhenChart, { countReadout, yearSearchHref } from "../pages/tag/TagWhenChart.jsx";

afterEach(cleanup);

describe("TagWhenChart component", () => {
  const mockYears = [
    { year: 2004, n: 10, tagged: 1000 },
    { year: 2000, n: 0, tagged: 0 },
    { year: 2001, n: 20, tagged: 8000 },
  ];

  it("writes the count of a year on the Tag page", () => {
    expect(countReadout({ year: 2014, n: 23 })).toBe("2014: 23 speeches");
    expect(countReadout({ year: 2014, n: 1 })).toBe("2014: 1 speech");
    expect(countReadout({ year: 2015, n: 0 })).toBe("2015: no speech with this tag");
  });

  it("draws the bar height from the count, with no rate switch and no note on the bar height", () => {
    render(<TagWhenChart years={mockYears} selectedTerm="" />);

    expect(screen.getByRole("heading", { name: "When" })).toBeTruthy();
    // At rest the highest year is green, with no pop-up.
    expect(screen.getByTestId("year-col-2001").className).toContain("tag-when-chart__col--active");
    expect(document.querySelector(".bar-tip")).toBeNull();
    expect(screen.getByTestId("year-col-2001").style.height).toBe("100%");
    expect(screen.getByTestId("year-col-2004").style.height).toBe("50%");
    expect(screen.getByTestId("year-col-2000").style.height).toBe("0%");
    expect(screen.queryByRole("button", { name: /Rate per 1,000|Counts/ })).toBeNull();
    expect(screen.queryByText(/Bar height/)).toBeNull();
  });

  it("updates the readout on hover", () => {
    render(<TagWhenChart years={mockYears} selectedTerm="" />);

    const col2001 = screen.getByTestId("year-col-2001");
    fireEvent.mouseEnter(col2001);
    fireEvent.mouseEnter(screen.getByTestId("year-col-2004"));
    expect(screen.getByText("2004: 10 speeches")).toBeTruthy();

    fireEvent.mouseLeave(col2001);
    fireEvent.mouseLeave(document.querySelector(".tag-when-chart__plot"));
    expect(document.querySelector(".bar-tip")).toBeNull();
    fireEvent.mouseEnter(col2001);
    expect(screen.getByText("2001: 20 speeches")).toBeTruthy();
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

  it("keeps the readout of a clicked year and links to the Search page for that year", () => {
    render(
      <MemoryRouter>
        <TagWhenChart years={mockYears} selectedTerm="" slug="arrears" />
      </MemoryRouter>
    );
    const col = screen.getByTestId("year-col-2001");
    fireEvent.click(col);
    fireEvent.mouseLeave(col);
    expect(screen.getByText("2001: 20 speeches")).toBeTruthy();
    const link = screen.getByRole("link", { name: "Read the 20 speeches of 2001" });
    expect(link.getAttribute("href")).toBe("/search?tag=arrears&date_from=2001-01-01&date_to=2001-12-31");
    expect(yearSearchHref("arrears", 2001)).toContain("date_to=2001-12-31");
  });

  it("rests on the year with the most speeches in green, and moves the green and the pop-up to the year under the pointer", () => {
    const { container } = render(<TagWhenChart years={mockYears} selectedTerm="" />);
    expect(screen.getByTestId("year-col-2001").className).toContain("tag-when-chart__col--active");
    expect(screen.getByTestId("year-col-2004").className).not.toContain("tag-when-chart__col--active");
    expect(container.textContent).not.toMatch(/peak/i);
    fireEvent.mouseEnter(screen.getByTestId("year-col-2004"));
    // Only one bar is green: the highest year stops being green while another bar is active.
    expect(screen.getByTestId("year-col-2004").className).toContain("tag-when-chart__col--active");
    expect(screen.getByTestId("year-col-2001").className).not.toContain("tag-when-chart__col--active");
    expect(container.querySelector(".bar-tip").textContent).toBe("2004: 10 speeches");
  });

  it("labels the value axis and every fifth year", () => {
    render(<TagWhenChart years={mockYears} selectedTerm="" />);
    expect(screen.getAllByText("20").length).toBeGreaterThan(0);
    expect(screen.getAllByText("2000").length).toBeGreaterThan(0);
    expect(screen.queryAllByText("2001").some((e) => e.className.includes("axis-year"))).toBe(false);
  });

  it("draws nothing when there are no years", () => {
    const { container } = render(<TagWhenChart years={[]} />);
    expect(container.innerHTML).toBe("");
  });
});
