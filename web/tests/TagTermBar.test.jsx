import React from "react";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import TagTermBar from "../pages/tag/TagTermBar.jsx";

afterEach(cleanup);

describe("TagTermBar component", () => {
  const mockTag = {
    total: 205,
    sessions: [
      { term: 13, year: 1999, n: 5 },
      { term: 16, year: 2014, n: 20 },
      { term: 17, year: 2019, n: 41 },
      { term: 17, year: 2020, n: 15 },
    ],
  };

  it("renders All terms button and buttons for terms in sessions", () => {
    const handleTermChange = vi.fn();
    render(
      <TagTermBar
        tag={mockTag}
        selectedTerm=""
        onTermChange={handleTermChange}
      />
    );

    const allBtn = screen.getByRole("button", { name: "All terms" });
    expect(allBtn.getAttribute("aria-pressed")).toBe("true");
    expect(allBtn.classList.contains("tag-term-button--selected")).toBe(true);

    expect(screen.getByRole("button", { name: "13th · 1999–2004" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "16th · 2014–19" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "17th · 2019–24" })).toBeTruthy();
    // 14th and 15th are not in sessions, so they should not appear
    expect(screen.queryByRole("button", { name: /14th/ })).toBeNull();
  });

  it("calls onTermChange when a term button is clicked", () => {
    const handleTermChange = vi.fn();
    render(
      <TagTermBar
        tag={mockTag}
        selectedTerm=""
        onTermChange={handleTermChange}
      />
    );

    const term17Btn = screen.getByRole("button", { name: "17th · 2019–24" });
    fireEvent.click(term17Btn);
    expect(handleTermChange).toHaveBeenCalledWith("17");
  });

  it("shows meta line with speeches count when a term is selected", () => {
    render(
      <TagTermBar
        tag={mockTag}
        selectedTerm="17"
        onTermChange={() => {}}
      />
    );

    const term17Btn = screen.getByRole("button", { name: "17th · 2019–24" });
    expect(term17Btn.getAttribute("aria-pressed")).toBe("true");
    expect(term17Btn.classList.contains("tag-term-button--selected")).toBe(true);

    // 41 + 15 = 56 speeches in the 17th Lok Sabha
    expect(
      screen.getByText("56 of 205 speeches in the 17th Lok Sabha")
    ).toBeTruthy();
  });
});
