import React from "react";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import MyMp from "../pages/my_mp.jsx";
import { speechLine, termYears, termsText } from "../pages/my_mp/SeatCard.jsx";
import { splitQuery, suggestSeats } from "../pages/my_mp.jsx";
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
      place_page: true,
      same_name_note: null,
      current: [
        {
          id: 699,
          member: "Shivaji Bandappa Kalge",
          party: "INC",
          state: "Maharashtra",
          terms: [18],
          speeches: 22,
          last_speech: "2026-01-29",
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

const places = {
  state_count: 2,
  seat_count: 3,
  featured: [{ name: "Jammu", slug: "jammu", page: true, speeches: 882, state: "Jammu and Kashmir" }],
  states: [
    { name: "Maharashtra", slug: "maharashtra", page: true, seats: [{ name: "Latur", slug: "latur", page: true }, { name: "Pune", slug: "pune", page: true }] },
    { name: "Odisha", slug: "odisha", page: true, seats: [{ name: "Latur Road", slug: "latur-road", page: false }] },
  ],
};

// The page asks for the seat list and for the seat words. This mock answers both by address.
function mockApi(result) {
  return vi.spyOn(api, "getJSON").mockImplementation((url) =>
    Promise.resolve(url === "/api/places" ? places : result)
  );
}

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
    const spy = mockApi(latur);
    renderPage("/my-mp");
    expect(screen.getByRole("heading", { level: 1 }).textContent).toBe("Find your MP");
    expect(screen.getByLabelText("Lok Sabha seat")).toBeTruthy();
    expect(spy).not.toHaveBeenCalledWith("/api/my-mp", expect.anything(), expect.anything());
  });

  it("shows the member now, the subjects, and the members before", async () => {
    mockApi(latur);
    renderPage();

    expect(await screen.findByRole("heading", { level: 2, name: "Latur" })).toBeTruthy();
    expect(api.getJSON).toHaveBeenCalledWith("/api/my-mp", { q: "latur" }, { signal: expect.any(AbortSignal) });
    expect(screen.getByText("Found 1 seat: Latur, Maharashtra.")).toBeTruthy();
    expect(screen.getByRole("link", { name: "Latur" }).getAttribute("href")).toBe("/place/latur");
    expect(screen.getByText("Spoke 22 times in all terms. Latest speech 29 Jan 2026.")).toBeTruthy();
    expect(screen.getByRole("link", { name: "Shivaji Bandappa Kalge" }).getAttribute("href")).toBe("/member/699");
    expect(screen.getAllByRole("link", { name: "INC" })[0].getAttribute("href")).toBe("/party/INC");
    expect(screen.getByText(/· 18th LS/)).toBeTruthy();
    expect(screen.getByRole("link", { name: /Farmers/ }).getAttribute("href")).toBe("/tag/farmers");
    expect(screen.queryByText("null")).toBeNull();
  });

  it("shows 10 members before, then all of them on request", async () => {
    mockApi(latur);
    renderPage();
    await screen.findByRole("heading", { level: 2, name: "Latur" });

    expect(screen.queryByText("Older member 11")).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Show all 12 members" }));
    expect(screen.getByText("Older member 12")).toBeTruthy();
  });

  it("says so when no seat matches", async () => {
    mockApi({ q: "zzz", latest_term: 18, seat_count: 0, seats: [] });
    renderPage("/my-mp?q=zzz");
    expect(await screen.findByText(/No Lok Sabha seat has “zzz” in its name/)).toBeTruthy();
  });

  it("says so when a seat has no member in the latest term", async () => {
    mockApi({
      ...latur,
      seats: [{ ...latur.seats[0], seat: "Purnea", slug: "purnea", current: [] }],
    });
    renderPage("/my-mp?q=purnea");
    expect(await screen.findByText("Torko has no member for this seat in the 18th LS.")).toBeTruthy();
  });

  it("shows how to start and the example seats before any search", async () => {
    mockApi(latur);
    renderPage("/my-mp");
    expect(await screen.findByRole("link", { name: /Jammu/ })).toBeTruthy();
    expect(screen.getByRole("link", { name: /Jammu/ }).getAttribute("href")).toBe("/my-mp?q=Jammu");
    expect(screen.getByText(/The 1 seats with the most speeches/)).toBeTruthy();
    expect(screen.queryByText("How Torko counts")).toBeNull();
  });

  it("suggests seats while the reader types", async () => {
    mockApi(latur);
    renderPage("/my-mp");
    await screen.findByRole("link", { name: /Jammu/ });
    const box = screen.getByLabelText("Lok Sabha seat");
    fireEvent.focus(box);
    fireEvent.change(box, { target: { value: "lat" } });
    expect(screen.getByRole("button", { name: /Latur Maharashtra/ })).toBeTruthy();
    expect(screen.getByRole("button", { name: /Latur Road Odisha/ })).toBeTruthy();
  });

  it("splits a seat and a state, and keeps the seats of that state", () => {
    expect(splitQuery("Latur, Maharashtra")).toEqual({ seat: "Latur", state: "Maharashtra" });
    expect(suggestSeats(places.states, "latur, odi").map((x) => x.name)).toEqual(["Latur Road"]);
    expect(suggestSeats(places.states, "")).toEqual([]);
  });

  it("writes the speech line and the years of the terms", () => {
    expect(speechLine({ speeches: 0 })).toBe("No speech of this member is in the record.");
    expect(speechLine({})).toBeNull();
    expect(termYears([17, 18])).toBe("2019–24, 2024–");
  });
});
