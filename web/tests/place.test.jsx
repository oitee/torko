import React from "react";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import Place from "../pages/place.jsx";
import {
  formatMonthYear,
  formatSpan,
  getKindLabel,
  getStateFromDescription,
} from "../pages/place/PlaceHead.jsx";
import { termOrdinal } from "../pages/place/PlaceWhen.jsx";
import * as api from "../assets/js/api.js";

afterEach(cleanup);

const mockLaturData = {
  name: "Latur",
  slug: "latur",
  subtype: "district_constituency",
  domain: null,
  description: "District and Lok Sabha constituency in Maharashtra, India.",
  aliases: ["Lattur", "लातूर"],
  total: 135,
  debates: 126,
  n_members: 28,
  first: "1999-12-13",
  last: "2026-01-29",
  sessions: [
    { term: 13, session: 2, year: 1999, n: 1 },
    { term: 17, session: 1, year: 2019, n: 10 },
    { term: 18, session: 1, year: 2024, n: 5 },
  ],
  holders: [
    {
      term: 13,
      id: 1288,
      name: "Shivraj V. Patil",
      party: "INC",
      seat: "Latur",
      state: "Maharashtra",
      since: "1999-10-20",
      first_spoke: "1999-10-26",
      last_spoke: "2004-02-05",
    },
    {
      term: 17,
      id: 1724,
      name: "Sudhakar Tukaram Shrangare",
      party: "BJP",
      seat: "Latur",
      state: "Maharashtra",
      since: "2019-06-17",
      first_spoke: "2019-06-25",
      last_spoke: "2024-02-05",
    },
  ],
  members: [
    {
      id: 1724,
      name: "Sudhakar Tukaram Shrangare",
      party: "BJP",
      seat: "Latur",
      state: "Maharashtra",
      n: 49,
      last: "2024-02-05",
      own_seat: true,
    },
    {
      id: 1288,
      name: "Shivraj V. Patil",
      party: "INC",
      seat: "Latur",
      state: "Maharashtra",
      n: 30,
      last: "2004-02-05",
      own_seat: true,
    },
  ],
  parties: [
    { party: "BJP", n: 76, per100: 0.19, party_total: 38987 },
    { party: "INC", n: 29, per100: 0.14, party_total: 20615 },
    { party: "SS", n: 18, per100: 0.61, party_total: 2949 },
  ],
  associated: [
    {
      name: "Atal Mission for Rejuvenation and Urban Transformation (AMRUT)",
      slug: "amrut",
      type: "scheme",
      n: 5,
      all: 72,
      lift: 55.5,
    },
  ],
  related: [
    {
      name: "Railway Connectivity",
      slug: "railway-connectivity",
      type: "topic",
      n: 48,
    },
  ],
  recent: [],
};

const mockWestBengalData = {
  name: "West Bengal",
  slug: "west-bengal",
  subtype: "state",
  domain: null,
  description: "State in eastern India",
  aliases: [],
  total: 3319,
  debates: 2302,
  n_members: 490,
  first: "1999-10-26",
  last: "2026-04-17",
  sessions: [
    { term: 13, session: 1, year: 1999, n: 10 },
  ],
  holders: [],
  members: [
    {
      id: 368,
      name: "Adhir Ranjan Chowdhury",
      party: "INC",
      seat: "Baharampur",
      state: "West Bengal",
      n: 215,
      last: "2023-12-07",
      own_seat: false,
    },
  ],
  parties: [
    { party: "AITC", n: 889, per100: 28.36, party_total: 3135 },
  ],
  associated: [],
  related: [],
  recent: [],
};

const mockEmptyPlaceData = {
  name: "Empty Place",
  slug: "empty-place",
  subtype: "district",
  description: "A district with no speeches yet.",
  aliases: [],
  total: 0,
  debates: 0,
  n_members: 0,
  first: null,
  last: null,
  sessions: [],
  holders: [],
  members: [],
  parties: [],
  associated: [],
  related: [],
  recent: [],
};

const mockSpeechesFacets = {
  total: 135,
  facets: {
    term: [{ term: 13, n: 1 }, { term: 17, n: 10 }, { term: 18, n: 5 }],
    party: [{ party: "BJP", n: 76 }, { party: "INC", n: 29 }],
    kind: [{ kind: "rule_377", label: "Rule 377", n: 46 }],
  },
  speeches: [],
};

function renderPlacePage(initialRoute = "/place/latur") {
  return render(
    <MemoryRouter initialEntries={[initialRoute]}>
      <Routes>
        <Route path="/place/:slug" element={<Place />} />
      </Routes>
    </MemoryRouter>
  );
}

describe("Place page helper functions", () => {
  it("formats dates into month and year correctly", () => {
    expect(formatMonthYear("1999-12-13")).toBe("Dec 1999");
    expect(formatMonthYear("2026-01-29")).toBe("Jan 2026");
    expect(formatMonthYear(null)).toBe("");
  });

  it("formats month spans with en-dash", () => {
    expect(formatSpan("1999-12-13", "2026-01-29")).toBe("Dec 1999 – Jan 2026");
    expect(formatSpan(null, null)).toBe("–");
  });

  it("extracts state from description only if it has 'in '", () => {
    expect(
      getStateFromDescription(
        "District and Lok Sabha constituency in Maharashtra, India.",
        "district_constituency"
      )
    ).toBe("Maharashtra");

    expect(
      getStateFromDescription("State in eastern India", "state")
    ).toBeNull();

    expect(
      getStateFromDescription("A place with no state info", "district")
    ).toBeNull();
  });

  it("formats kind label from subtype", () => {
    expect(getKindLabel("district_constituency")).toBe("Seat and district");
    expect(getKindLabel("state")).toBe("State");
    expect(getKindLabel("district")).toBe("District");
    expect(getKindLabel("constituency")).toBe("Seat");
  });

  it("formats term numbers into ordinals", () => {
    expect(termOrdinal(13)).toBe("13th");
    expect(termOrdinal(1)).toBe("1st");
    expect(termOrdinal(2)).toBe("2nd");
    expect(termOrdinal(3)).toBe("3rd");
  });
});

describe("Place page integration", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("shows loading state while fetching and then renders page content", async () => {
    vi.spyOn(api, "getJSON").mockImplementation((url) => {
      if (url.startsWith("/api/place/latur")) {
        return Promise.resolve(mockLaturData);
      }
      if (url.startsWith("/api/speeches")) {
        return Promise.resolve(mockSpeechesFacets);
      }
      return Promise.reject(new Error("Not found"));
    });

    renderPlacePage("/place/latur");

    expect(screen.getByRole("status").textContent).toContain("Loading");

    await waitFor(() => {
      const heading = screen.getByRole("heading", { level: 1 });
      expect(heading.textContent).toBe("Latur");
    });

    // Check document tab title
    expect(document.title).toBe("Latur · Torko");

    // Breadcrumb
    expect(screen.getByText("Places")).toBeTruthy();
    expect(screen.getAllByText("Maharashtra").length).toBeGreaterThan(0);

    // Kicker & Description
    expect(screen.getByText("Seat and district")).toBeTruthy();
    expect(
      screen.getByText(
        "District and Lok Sabha constituency in Maharashtra, India."
      )
    ).toBeTruthy();
    expect(screen.getByText("Also written: Lattur, लातूर")).toBeTruthy();

    // Big numbers
    expect(screen.getByText("135")).toBeTruthy();
    expect(screen.getByText("126")).toBeTruthy();
    expect(screen.getByText("28")).toBeTruthy();
    expect(screen.getByText("Dec 1999 – Jan 2026")).toBeTruthy();

    // When section
    expect(screen.getByRole("heading", { name: "When" })).toBeTruthy();
    expect(screen.getByText("Show as table")).toBeTruthy();

    // MPs for this seat section
    expect(
      screen.getByRole("heading", { name: "MPs for this seat" })
    ).toBeTruthy();
    expect(screen.getAllByText("Shivraj V. Patil").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Sudhakar Tukaram Shrangare").length).toBeGreaterThan(0);

    // Who spoke about it
    expect(
      screen.getByRole("heading", { name: "Who spoke about it" })
    ).toBeTruthy();
    expect(screen.getAllByText("own seat").length).toBeGreaterThan(0);

    // Which parties spoke about it
    expect(
      screen.getByRole("heading", { name: "Which parties spoke about it" })
    ).toBeTruthy();

    // What comes up here
    expect(
      screen.getByRole("heading", { name: "What comes up here" })
    ).toBeTruthy();
    expect(
      screen.getByText(
        "Atal Mission for Rejuvenation and Urban Transformation (AMRUT)"
      )
    ).toBeTruthy();
    expect(screen.getByText("Railway Connectivity")).toBeTruthy();

    // Speeches section
    expect(screen.getByRole("heading", { name: "Speeches" })).toBeTruthy();

    // Method section
    expect(
      screen.getByText(
        /A speech is about a place when one of its tags is the place\./
      )
    ).toBeTruthy();
  });

  it("handles state place correctly without seat holders or state breadcrumb", async () => {
    vi.spyOn(api, "getJSON").mockImplementation((url) => {
      if (url.startsWith("/api/place/west-bengal")) {
        return Promise.resolve(mockWestBengalData);
      }
      if (url.startsWith("/api/speeches")) {
        return Promise.resolve({ total: 3319, facets: {}, speeches: [] });
      }
      return Promise.reject(new Error("Not found"));
    });

    renderPlacePage("/place/west-bengal");

    await waitFor(() => {
      expect(screen.getByRole("heading", { level: 1 }).textContent).toBe(
        "West Bengal"
      );
    });

    expect(document.title).toBe("West Bengal · Torko");
    expect(screen.getByText("State")).toBeTruthy();

    // Should NOT have "MPs for this seat" section
    expect(
      screen.queryByRole("heading", { name: "MPs for this seat" })
    ).toBeNull();
  });

  it("handles 404 error with Page not found and document title", async () => {
    vi.spyOn(api, "getJSON").mockRejectedValueOnce({
      status: 404,
      message: "Not found",
    });

    renderPlacePage("/place/no-such-place");

    await waitFor(() => {
      expect(screen.getByRole("alert").textContent).toContain("Page not found");
    });

    expect(document.title).toBe("Page not found · Torko");
  });

  it("handles network error with retry button", async () => {
    vi.spyOn(api, "getJSON").mockRejectedValueOnce({
      status: 500,
      message: "Server error",
    });

    renderPlacePage("/place/latur");

    await waitFor(() => {
      expect(screen.getByRole("alert").textContent).toContain("Server error");
    });

    const retryBtn = screen.getByRole("button", { name: "Try again" });
    expect(retryBtn).toBeTruthy();

    vi.spyOn(api, "getJSON").mockResolvedValueOnce(mockLaturData);
    fireEvent.click(retryBtn);

    await waitFor(() => {
      expect(screen.getByRole("heading", { level: 1 }).textContent).toBe(
        "Latur"
      );
    });
  });

  it("shows empty state when place has 0 speeches", async () => {
    vi.spyOn(api, "getJSON").mockResolvedValueOnce(mockEmptyPlaceData);

    renderPlacePage("/place/empty-place");

    await waitFor(() => {
      expect(screen.getByRole("heading", { level: 1 }).textContent).toBe(
        "Empty Place"
      );
    });

    expect(
      screen.getByText("No speech in the record names this place yet.")
    ).toBeTruthy();
    expect(screen.queryByRole("heading", { name: "When" })).toBeNull();
  });
});
