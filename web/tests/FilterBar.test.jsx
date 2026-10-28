import React from "react";
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter, useLocation } from "react-router-dom";
import FilterBar from "../components/FilterBar.jsx";

function LocationDisplay() {
  const location = useLocation();
  return <div data-testid="location">{location.pathname + location.search}</div>;
}

function Harness({
  facets,
  total,
  unfilteredTotal,
  noun,
  groups,
  initialUrl = "/?page=2",
}) {
  return (
    <MemoryRouter initialEntries={[initialUrl]}>
      <LocationDisplay />
      <FilterBar
        facets={facets}
        total={total}
        unfilteredTotal={unfilteredTotal}
        noun={noun}
        groups={groups}
      />
    </MemoryRouter>
  );
}

const SAMPLE_FACETS = {
  term: [
    { term: 16, n: 120 },
    { term: 17, n: 80 },
  ],
  party: [
    { party: "BJP", n: 72 },
    { party: "INC", n: 35 },
  ],
  kind: [
    { kind: "zero_hour", label: "Zero Hour", n: 102 },
    { kind: "rule_377", label: "Rule 377", n: 60 },
  ],
  subject: [
    { id: 23204, label: "Wage and salary arrears", n: 31 },
  ],
};

describe("FilterBar", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    act(() => {
      vi.runOnlyPendingTimers();
    });
    vi.useRealTimers();
    vi.unstubAllGlobals();
    cleanup();
  });

  it("renders chip groups from facets with formatted counts", () => {
    render(<Harness facets={SAMPLE_FACETS} total={4812} noun="speeches" />);

    // Term labels with termShort
    expect(screen.getByText("16th LS")).toBeTruthy();
    expect(screen.getByText("120")).toBeTruthy();
    expect(screen.getByText("17th LS")).toBeTruthy();
    expect(screen.getByText("80")).toBeTruthy();

    // Party labels
    expect(screen.getByText("BJP")).toBeTruthy();
    expect(screen.getByText("72")).toBeTruthy();
    expect(screen.getByText("INC")).toBeTruthy();
    expect(screen.getByText("35")).toBeTruthy();

    // Kind labels
    expect(screen.getByText("Zero Hour")).toBeTruthy();
    expect(screen.getByText("102")).toBeTruthy();

    // Subject label
    expect(screen.getByText("Wage and salary arrears")).toBeTruthy();
    expect(screen.getByText("31")).toBeTruthy();

    // Count when no filter active: shows total speeches
    expect(screen.getByText("4,812 speeches")).toBeTruthy();

    // Reset filters should not be visible when no filters are active
    expect(screen.queryByRole("button", { name: "Reset filters" })).toBeNull();
  });

  it("clicking a chip writes comma-separated param to URL and removes page", () => {
    render(<Harness facets={SAMPLE_FACETS} total={4812} initialUrl="/?page=3" />);

    // Click 16th LS chip
    const term16Btn = screen.getByRole("button", { name: /16th LS 120/i });
    fireEvent.click(term16Btn);

    // page=3 is removed, term=16 is added
    expect(screen.getByTestId("location").textContent).toBe("/?term=16");

    // Click 17th LS chip to add to comma list
    const term17Btn = screen.getByRole("button", { name: /17th LS 80/i });
    fireEvent.click(term17Btn);

    expect(screen.getByTestId("location").textContent).toBe("/?term=16%2C17");
  });

  it("clicking an already active chip removes it from the comma list", () => {
    render(<Harness facets={SAMPLE_FACETS} total={4812} initialUrl="/?term=16,17&page=2" />);

    const term16Btn = screen.getByRole("button", { name: /✓ 16th LS 120/i });
    fireEvent.click(term16Btn);

    // term=16 removed, only 17 left, page removed
    expect(screen.getByTestId("location").textContent).toBe("/?term=17");

    // Click 17th LS again to remove it entirely
    const term17Btn = screen.getByRole("button", { name: /✓ 17th LS 80/i });
    fireEvent.click(term17Btn);

    expect(screen.getByTestId("location").textContent).toBe("/");
  });

  it("resets all active filters and removes page when Reset filters is clicked", () => {
    render(
      <Harness
        facets={SAMPLE_FACETS}
        total={715}
        unfilteredTotal={4812}
        initialUrl="/?term=16&party=BJP&page=4"
      />
    );

    const resetButton = screen.getByRole("button", { name: "Reset filters" });
    expect(resetButton).toBeTruthy();

    fireEvent.click(resetButton);
    expect(screen.getByTestId("location").textContent).toBe("/");
  });

  it("shows count as 'N of total speeches' when filters are active", () => {
    render(
      <Harness
        facets={SAMPLE_FACETS}
        total={715}
        unfilteredTotal={4812}
        initialUrl="/?term=16"
      />
    );

    expect(screen.getByText("715 of 4,812 speeches")).toBeTruthy();
  });

  it("displays Filters · N with total number of selected choices", () => {
    render(
      <Harness
        facets={SAMPLE_FACETS}
        total={200}
        initialUrl="/?term=16,17&party=BJP"
      />
    );

    // term has 2, party has 1 -> 3 total active filters
    expect(screen.getByRole("button", { name: "Filters · 3" })).toBeTruthy();
  });

  it("limits choices to 8 and displays Show all N button to expand", () => {
    const manyParties = Array.from({ length: 12 }, (_, i) => ({
      party: `P${i + 1}`,
      n: 10 + i,
    }));

    const facetsWithMany = {
      party: manyParties,
    };

    render(<Harness facets={facetsWithMany} total={500} initialUrl="/" />);

    // Only 8 parties visible initially
    expect(screen.getByText("P1")).toBeTruthy();
    expect(screen.getByText("P8")).toBeTruthy();
    expect(screen.queryByText("P9")).toBeNull();

    // Show all 12 button is rendered
    const showAllBtn = screen.getByRole("button", { name: "Show all 12" });
    expect(showAllBtn).toBeTruthy();

    fireEvent.click(showAllBtn);

    // Now all 12 parties are visible
    expect(screen.getByText("P9")).toBeTruthy();
    expect(screen.getByText("P12")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Show fewer" })).toBeTruthy();
  });

  it("copies address to clipboard and shows Link copied for 2 seconds", () => {
    const writeTextMock = vi.fn().mockResolvedValue(undefined);
    Object.assign(navigator, {
      clipboard: {
        writeText: writeTextMock,
      },
    });

    render(<Harness facets={SAMPLE_FACETS} total={4812} initialUrl="/?term=16" />);

    const copyBtn = screen.getByRole("button", { name: "Copy link" });
    act(() => {
      fireEvent.click(copyBtn);
    });

    expect(writeTextMock).toHaveBeenCalled();
    expect(screen.getByRole("button", { name: "Link copied" })).toBeTruthy();

    // Advance 2 seconds
    act(() => {
      vi.advanceTimersByTime(2000);
    });

    expect(screen.getByRole("button", { name: "Copy link" })).toBeTruthy();
  });

  it("omits groups that have no rows in facets", () => {
    const partialFacets = {
      party: [{ party: "BJP", n: 10 }],
    };

    render(<Harness facets={partialFacets} total={10} initialUrl="/" />);

    expect(screen.getByText("Party")).toBeTruthy();
    expect(screen.queryByText("Term")).toBeNull();
    expect(screen.queryByText("Type")).toBeNull();
    expect(screen.queryByText("Subject")).toBeNull();
  });
});
