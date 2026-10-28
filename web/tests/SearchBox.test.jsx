import React from "react";
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter, useLocation } from "react-router-dom";
import SearchBox from "../components/SearchBox.jsx";

function LocationDisplay() {
  const location = useLocation();
  return <div data-testid="location">{location.pathname + location.search}</div>;
}

function Harness({ initial = "" }) {
  return (
    <MemoryRouter initialEntries={["/"]}>
      <LocationDisplay />
      <SearchBox initial={initial} />
    </MemoryRouter>
  );
}

const SAMPLE_RESULTS = [
  { kind: "tag", name: "Arrears", slug: "arrears", n_speeches: 249 },
  { kind: "tag", name: "Sugarcane Farmers' Arrears", slug: "sugarcane-farmers-arrears", n_speeches: 236 },
  { kind: "place", name: "Latur", slug: "latur", n_speeches: 88 },
  { kind: "subject", name: "Sugarcane farmers' arrears", n_speeches: 100 },
  { kind: "member", name: "Mahua Moitra", id: 4123, n_speeches: 66 },
];

describe("SearchBox", () => {
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

  it("renders with initial value and search button", () => {
    render(<Harness initial="farmers" />);

    const input = screen.getByRole("combobox");
    expect(input.value).toBe("farmers");
    expect(screen.getByRole("button", { name: "Search" })).toBeTruthy();
  });

  it("calls /api/search after typing 2+ chars and waiting 250ms, grouping suggestions", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ results: SAMPLE_RESULTS }),
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<Harness />);
    const input = screen.getByRole("combobox");

    fireEvent.change(input, { target: { value: "arr" } });

    // Before 250ms: not yet called
    expect(fetchMock).not.toHaveBeenCalled();

    // Advance 250ms
    await act(async () => {
      vi.advanceTimersByTime(250);
    });

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/search?q=arr",
      expect.objectContaining({ signal: expect.any(AbortSignal) })
    );

    // Check headings
    expect(screen.getByText("Tags")).toBeTruthy();
    expect(screen.getByText("Places")).toBeTruthy();
    expect(screen.getByText("Subjects")).toBeTruthy();
    expect(screen.getByText("Members")).toBeTruthy();

    // Check suggestion items and counts
    expect(screen.getByText("Arrears")).toBeTruthy();
    expect(screen.getByText("249")).toBeTruthy();
    expect(screen.getByText("Latur")).toBeTruthy();
    expect(screen.getByText("88")).toBeTruthy();
    expect(screen.getByText("Sugarcane farmers' arrears")).toBeTruthy();
    expect(screen.getByText("100")).toBeTruthy();
    expect(screen.getByText("Mahua Moitra")).toBeTruthy();
    expect(screen.getByText("66")).toBeTruthy();
  });

  it("limits each group to at most 5 suggestions", async () => {
    const manyTags = Array.from({ length: 8 }, (_, i) => ({
      kind: "tag",
      name: `Tag ${i + 1}`,
      slug: `tag-${i + 1}`,
      n_speeches: 10 + i,
    }));

    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ results: manyTags }),
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<Harness />);
    const input = screen.getByRole("combobox");

    fireEvent.change(input, { target: { value: "tag" } });
    await act(async () => {
      vi.advanceTimersByTime(250);
    });

    expect(screen.getByText("Tag 1")).toBeTruthy();
    expect(screen.getByText("Tag 5")).toBeTruthy();
    expect(screen.queryByText("Tag 6")).toBeNull();
  });

  it("renders correct links for tags, places, subjects and members", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ results: SAMPLE_RESULTS }),
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<Harness />);
    const input = screen.getByRole("combobox");

    fireEvent.change(input, { target: { value: "test" } });
    await act(async () => {
      vi.advanceTimersByTime(250);
    });

    const tagLink = screen.getByRole("option", { name: /Arrears 249/i });
    expect(tagLink.getAttribute("href")).toBe("/search?tag=arrears");

    const placeLink = screen.getByRole("option", { name: /Latur 88/i });
    expect(placeLink.getAttribute("href")).toBe("/place/latur");

    const subjectLink = screen.getByRole("option", { name: /Sugarcane farmers' arrears 100/i });
    expect(subjectLink.getAttribute("href")).toBe("/search?q=Sugarcane%20farmers'%20arrears");

    const memberLink = screen.getByRole("option", { name: /Mahua Moitra 66/i });
    expect(memberLink.getAttribute("href")).toBe("/member/4123");
  });

  it("navigates suggestions using up and down arrow keys and selects with Enter", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ results: SAMPLE_RESULTS }),
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<Harness />);
    const input = screen.getByRole("combobox");

    fireEvent.change(input, { target: { value: "arr" } });
    await act(async () => {
      vi.advanceTimersByTime(250);
    });

    // Press ArrowDown to select first suggestion (Arrears)
    fireEvent.keyDown(input, { key: "ArrowDown" });
    const firstOption = screen.getByRole("option", { name: /Arrears 249/i });
    expect(firstOption.getAttribute("aria-selected")).toBe("true");

    // Press ArrowDown to select second suggestion
    fireEvent.keyDown(input, { key: "ArrowDown" });
    const secondOption = screen.getByRole("option", { name: /Sugarcane Farmers' Arrears 236/i });
    expect(secondOption.getAttribute("aria-selected")).toBe("true");

    // Press Enter to navigate to selected suggestion
    fireEvent.keyDown(input, { key: "Enter" });
    expect(screen.getByTestId("location").textContent).toBe("/search?tag=sugarcane-farmers-arrears");
  });

  it("navigates to /search?q=<text> when Enter is pressed with no suggestion selected", () => {
    render(<Harness initial="budget" />);
    const input = screen.getByRole("combobox");

    fireEvent.keyDown(input, { key: "Enter" });
    expect(screen.getByTestId("location").textContent).toBe("/search?q=budget");
  });

  it("navigates to /search?q=<text> when Search button is clicked", () => {
    render(<Harness initial="railways" />);
    const searchButton = screen.getByRole("button", { name: "Search" });

    fireEvent.click(searchButton);
    expect(screen.getByTestId("location").textContent).toBe("/search?q=railways");
  });

  it("shows no suggestions and no error when API call fails", async () => {
    const fetchMock = vi.fn().mockRejectedValue(new Error("Network failure"));
    vi.stubGlobal("fetch", fetchMock);

    render(<Harness />);
    const input = screen.getByRole("combobox");

    fireEvent.change(input, { target: { value: "fail" } });
    await act(async () => {
      vi.advanceTimersByTime(250);
    });

    expect(screen.queryByRole("listbox")).toBeNull();
    expect(screen.queryByText(/Tags|Places|Subjects|Members/)).toBeNull();

    // The Search button still works
    const searchButton = screen.getByRole("button", { name: "Search" });
    fireEvent.click(searchButton);
    expect(screen.getByTestId("location").textContent).toBe("/search?q=fail");
  });

  it("cancels old fetch call when text changes quickly", async () => {
    let abortedCount = 0;
    const fetchMock = vi.fn().mockImplementation((_url, options) => {
      options.signal.addEventListener("abort", () => {
        abortedCount += 1;
      });
      return new Promise(() => {}); // never resolves
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<Harness />);
    const input = screen.getByRole("combobox");

    fireEvent.change(input, { target: { value: "first" } });
    await act(async () => {
      vi.advanceTimersByTime(250);
    });
    expect(fetchMock).toHaveBeenCalledTimes(1);

    // Typing a new letter aborts previous call
    fireEvent.change(input, { target: { value: "second" } });
    expect(abortedCount).toBe(1);
  });
});
