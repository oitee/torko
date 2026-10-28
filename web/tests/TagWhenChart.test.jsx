import React from "react";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import TagWhenChart from "../pages/tag/TagWhenChart.jsx";

afterEach(cleanup);

describe("TagWhenChart component", () => {
  const mockSessions = [
    { term: 13, year: 2000, n: 10 },
    { term: 13, year: 2001, n: 20 },
    { term: 14, year: 2004, n: 50 },
  ];

  it("renders chart bars with min and max years", () => {
    render(<TagWhenChart sessions={mockSessions} selectedTerm="" />);

    expect(screen.getByRole("heading", { name: "When" })).toBeTruthy();
    expect(screen.getByText("Hover a year for the count")).toBeTruthy();
    expect(screen.getAllByText("2000").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("2004").length).toBeGreaterThanOrEqual(1);

    const col2004 = screen.getByTestId("year-col-2004");
    expect(col2004.getAttribute("aria-label")).toBe("2004: 50 speeches");
  });

  it("updates readout on hovering a year column", () => {
    render(<TagWhenChart sessions={mockSessions} selectedTerm="" />);

    const col2001 = screen.getByTestId("year-col-2001");
    fireEvent.mouseEnter(col2001);

    expect(screen.getByText("2001 · 20 speeches")).toBeTruthy();

    fireEvent.mouseLeave(col2001);
    expect(screen.getByText("Hover a year for the count")).toBeTruthy();
  });

  it("fades years outside the selected term", () => {
    render(<TagWhenChart sessions={mockSessions} selectedTerm="14" />);

    const col2000 = screen.getByTestId("year-col-2000");
    const col2004 = screen.getByTestId("year-col-2004");

    expect(col2000.classList.contains("tag-when-chart__col--faded")).toBe(true);
    expect(col2004.classList.contains("tag-when-chart__col--faded")).toBe(false);
  });

  it("toggles table view with Show as table button", () => {
    render(<TagWhenChart sessions={mockSessions} selectedTerm="" />);

    const toggleBtn = screen.getByRole("button", { name: "Show as table" });
    fireEvent.click(toggleBtn);

    expect(screen.getByRole("button", { name: "Show as chart" })).toBeTruthy();
    expect(screen.getByRole("table").classList.contains("sr-only")).toBe(false);
  });
});
