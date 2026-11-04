import React from "react";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import MyMp from "../pages/my_mp.jsx";
import { termsText } from "../pages/my_mp/SeatCard.jsx";
import * as api from "../assets/js/api.js";

afterEach(cleanup);

// A cut of the real answer of /api/my-mp?q=latur.
const latur = {
  q: "latur",
  latest_term: 18,
  seat_count: 1,
  seats: [
    {
      seat: "Latur",
      slug: "latur",
      same_name_note: null,
      current: [
        {
          id: 699,
          member: "Shivaji Bandappa Kalge",
          party: "INC",
          state: "Maharashtra",
          terms: [18],
          top_tags: [{ name: "Farmers", slug: "farmers", speeches: 5, type: "topic" }],
        },
      ],
      older: Array.from({ length: 12 }, (_, i) => ({
        id: 100 + i,
        member: `Older member ${i + 1}`,
        party: i % 2 ? "BJP" : null,
        state: "Maharashtra",
        terms: [17 - (i % 5)],
      })),
    },
  ],
};

function renderPage(path = "/my-mp?q=latur") {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/my-mp" element={<MyMp />} />
      </Routes>
    </MemoryRouter>
  );
}

describe("Your MP page", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("writes the terms of a member in short form", () => {
    expect(termsText([16, 17])).toBe("16th LS, 17th LS");
    expect(termsText(null)).toBe("");
  });

  it("shows only the seat box when the address has no words", () => {
    const spy = vi.spyOn(api, "getJSON");
    renderPage("/my-mp");
    expect(screen.getByRole("heading", { level: 1 }).textContent).toBe("Find your MP");
    expect(screen.getByLabelText("Lok Sabha seat")).toBeTruthy();
    expect(spy).not.toHaveBeenCalled();
  });

  it("shows the member now, the subjects, and the members before", async () => {
    vi.spyOn(api, "getJSON").mockResolvedValueOnce(latur);
    renderPage();

    expect(await screen.findByRole("heading", { level: 2, name: "Latur" })).toBeTruthy();
    expect(api.getJSON).toHaveBeenCalledWith("/api/my-mp", { q: "latur" }, { signal: expect.any(AbortSignal) });
    expect(screen.getByText("1 seat has “latur” in its name")).toBeTruthy();
    expect(screen.getByRole("link", { name: "Shivaji Bandappa Kalge" }).getAttribute("href")).toBe("/member/699");
    expect(screen.getByText("INC · 18th LS")).toBeTruthy();
    expect(screen.getByRole("link", { name: /Farmers/ }).getAttribute("href")).toBe("/tag/farmers");
    expect(screen.queryByText("null")).toBeNull();
  });

  it("shows 10 members before, then all of them on request", async () => {
    vi.spyOn(api, "getJSON").mockResolvedValueOnce(latur);
    renderPage();
    await screen.findByRole("heading", { level: 2, name: "Latur" });

    expect(screen.queryByText("Older member 11")).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Show all 12 members" }));
    expect(screen.getByText("Older member 12")).toBeTruthy();
  });

  it("says so when no seat matches", async () => {
    vi.spyOn(api, "getJSON").mockResolvedValueOnce({ q: "zzz", latest_term: 18, seat_count: 0, seats: [] });
    renderPage("/my-mp?q=zzz");
    expect(await screen.findByText(/No Lok Sabha seat has “zzz” in its name/)).toBeTruthy();
  });

  it("says so when a seat has no member in the latest term", async () => {
    vi.spyOn(api, "getJSON").mockResolvedValueOnce({
      ...latur,
      seats: [{ ...latur.seats[0], seat: "Purnea", slug: "purnea", current: [] }],
    });
    renderPage("/my-mp?q=purnea");
    expect(await screen.findByText("Torko has no member for this seat in the 18th LS.")).toBeTruthy();
  });
});
