import React from "react";
import { cleanup, fireEvent, render, waitFor, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter } from "react-router-dom";
import * as api from "../assets/js/api.js";
import Parties, { shareText } from "../pages/parties.jsx";
import { areaShort, houseLayout, largestGap, namedAndOthers, termsText } from "../pages/parties/TermViews.jsx";
import Places, { filterStates } from "../pages/places.jsx";

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

const PARTIES = {
  total: 1000,
  count: 2,
  weights: {
    terms: [{ term: 17, speeches: 100, members: 10 }, { term: 18, speeches: 50, members: 10 }],
    series: [
      { code: "BJP", points: [{ term: 17, speeches: 60, members: 3, weight: 2 }, { term: 18, speeches: 20, members: 2, weight: null }] },
    ],
  },
  parties: [
    { code: "BJP", name: "Bharatiya Janata Party", speeches: 600, members: 50, terms: [13, 14, 15], first: "1999-10-20", last: "2026-03-01" },
    { code: "BJD", name: "Biju Janata Dal", speeches: 1, members: 1, terms: [14, 16], first: "2004-06-02", last: "2019-02-01" },
  ],
  terms: [
    {
      term: 17, years: "2019–2024", members: 3, speeches: 60, tagged: 50,
      parties: [{ code: "BJP", members: 3, speeches: 60, tagged: 50, member_share: 1, speech_share: 1, typical: [] }],
      grid: { areas: [], rows: [] },
    },
    {
      term: 18, years: "2024–", members: 4, speeches: 50, tagged: 40,
      parties: [
        { code: "BJP", members: 3, speeches: 20, tagged: 30, member_share: 0.75, speech_share: 0.4, typical: [] },
        { code: "BJD", members: 1, speeches: 30, tagged: 10, member_share: 0.25, speech_share: 0.6, typical: [{ tag: "Ports", slug: "ports", n: 8, lift: 3.1 }] },
      ],
      grid: {
        areas: [{ name: "Economy, Finance and Taxation", speeches: 30 }],
        rows: [{ code: "BJP", tagged: 30, cells: [{ n: 25, lift: 1.62 }] }, { code: "BJD", tagged: 10, cells: [{ n: 3, lift: null }] }],
      },
    },
  ],
};

const PLACES = {
  seat_count: 3,
  state_count: 2,
  featured: [{ name: "Latur", slug: "latur", page: true, speeches: 9, state: "Maharashtra" }],
  states: [
    { name: "Kerala", slug: "kerala", page: true, speeches: 40, seats: [{ name: "Alappuzha", slug: "alappuzha", page: false, speeches: null }] },
    {
      name: "Maharashtra",
      slug: "maharashtra",
      page: true,
      speeches: 90,
      seats: [
        { name: "Latur", slug: "latur", page: true, speeches: 9 },
        { name: "Pune", slug: "pune", page: true, speeches: 12 },
      ],
    },
  ],
};

describe("Parties", () => {
  const show = (address = "/parties") => {
    vi.spyOn(api, "getJSON").mockResolvedValue(PARTIES);
    render(
      <MemoryRouter initialEntries={[address]}>
        <Parties />
      </MemoryRouter>
    );
  };

  it("shows the newest term first: one dot for each member, the two shares, and the grid, in one block with the term chips", async () => {
    show();
    expect(await screen.findByRole("heading", { name: "The House, by party" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "18th · 2024" }).getAttribute("aria-pressed")).toBe("true");
    expect(document.querySelectorAll(".parties-house circle").length).toBe(4);
    // Two parties have the same difference. The party with more members comes first.
    expect(screen.getByText(/BJP: 75% of the members, 40% of the speeches/)).toBeTruthy();
    // A cell with too few speeches has no value.
    const grid = within(document.querySelector(".parties-grid"));
    expect(grid.getByText("1.6×")).toBeTruthy();
    expect(grid.getByText("Too few speeches")).toBeTruthy();
    expect(grid.getByRole("columnheader", { name: /Economy, Finance and Taxation/ })).toBeTruthy();
    // The chips are inside the term block, and the block has the name of the term.
    const block = document.querySelector(".parties-term");
    expect(within(block).getByRole("heading", { name: /18th Lok Sabha/ })).toBeTruthy();
    expect(within(block).getByRole("button", { name: "17th · 2019" })).toBeTruthy();
  });

  it("shows the term of the address, and changes the term with a chip", async () => {
    show("/parties?term=17");
    expect((await screen.findByRole("button", { name: "17th · 2019" })).getAttribute("aria-pressed")).toBe("true");
    expect(document.querySelectorAll(".parties-house circle").length).toBe(3);
    fireEvent.click(screen.getByRole("button", { name: "18th · 2024" }));
    expect(document.querySelectorAll(".parties-house circle").length).toBe(4);
  });

  it("keeps the party cards the same in every term: all-term counts, no subject tags", async () => {
    show("/parties?term=17");
    await screen.findByRole("heading", { name: "All parties" });
    const cards = () => [...document.querySelectorAll(".parties-card")].map((c) => c.textContent);
    const before = cards();
    // BJD has no member in the 17th term. Its card shows in each term.
    expect(before).toEqual([
      "Bharatiya Janata Party600 speeches · 50 members who spoke13th–15th LS",
      "Biju Janata Dal1 speech · 1 member who spoke14th, 16th LS",
    ]);
    fireEvent.click(screen.getByRole("button", { name: "18th · 2024" }));
    expect(cards()).toEqual(before);
    expect(screen.queryByRole("link", { name: "Ports" })).toBeNull();
  });

  it("shows only the parties with the most speeches as cards, and finds each other party with the filter", async () => {
    const many = Array.from({ length: 10 }, (_, i) => ({ code: `P${i}`, name: `Party ${i}`, speeches: 100 - i, members: 2, terms: [18] }));
    vi.spyOn(api, "getJSON").mockResolvedValue({ ...PARTIES, parties: many });
    render(<MemoryRouter initialEntries={["/parties"]}><Parties /></MemoryRouter>);
    await waitFor(() => expect(document.querySelectorAll(".parties-card").length).toBe(8));
    expect(screen.queryByText(/most speeches in all terms/)).toBeNull();
    fireEvent.change(screen.getByLabelText("Find a party"), { target: { value: "party 9" } });
    expect(within(document.querySelector(".index-table")).getByRole("link", { name: "Party 9" })).toBeTruthy();
    expect(screen.getByText("1 of 10 parties")).toBeTruthy();
    fireEvent.change(screen.getByLabelText("Find a party"), { target: { value: "" } });
    fireEvent.click(screen.getByRole("button", { name: "Show all 10 parties as a table" }));
    expect(document.querySelectorAll(".index-table tbody tr").length).toBe(10);
  });

  it("lists every party of all terms in a table, with a link, its share and its terms", async () => {
    show();
    await screen.findByRole("heading", { name: "All parties" });
    fireEvent.change(screen.getByLabelText("Find a party"), { target: { value: "b" } });
    const table = document.querySelector(".index-table");
    expect(within(table).getByRole("link", { name: "Bharatiya Janata Party" }).getAttribute("href")).toBe("/party/BJP");
    expect(screen.getByText("60.0%")).toBeTruthy();
    expect(within(table).getByText("13th–15th LS")).toBeTruthy();
    fireEvent.change(screen.getByLabelText("Find a party"), { target: { value: "biju" } });
    expect(within(document.querySelector(".index-table")).queryByRole("link", { name: "Bharatiya Janata Party" })).toBeNull();
    expect(screen.getByText("1 of 2 parties")).toBeTruthy();
  });

  it("writes small shares and broken term runs plainly", () => {
    expect(shareText(1, 1000)).toBe("0.1%");
    expect(shareText(1, 100000)).toBe("under 0.1%");
    expect(termsText([14, 16])).toBe("14th, 16th LS");
  });

  it("puts the parties after the named ones into one row, and gives a subject area a short name", () => {
    const rows = namedAndOthers([
      { code: "A", members: 5, speeches: 9, member_share: 0.5, speech_share: 0.6 },
      { code: "B", members: 3, speeches: 4, member_share: 0.3, speech_share: 0.3 },
      { code: "C", members: 2, speeches: 2, member_share: 0.2, speech_share: 0.1 },
    ], 1);
    expect(rows.map((r) => [r.code, r.members])).toEqual([["A", 5], ["Others", 5]]);
    expect(rows[1].count).toBe(2);
    expect(largestGap(rows).code).toBe("A");
    expect(areaShort("Law, Justice and Constitution")).toBe("Law");
    expect(areaShort("Home Affairs and Law and Order")).toBe("Home Affairs");
    expect(houseLayout(559).length).toBe(559);
  });
});

describe("Places", () => {
  it("links seats that have a page and leaves the others as text", async () => {
    vi.spyOn(api, "getJSON").mockResolvedValue(PLACES);
    render(
      <MemoryRouter>
        <Places />
      </MemoryRouter>
    );
    expect((await screen.findAllByRole("link", { name: "Latur" }))[0].getAttribute("href")).toBe("/place/latur");
    expect(screen.queryByRole("link", { name: "Alappuzha" })).toBeNull();
    expect(screen.getByText("Alappuzha")).toBeTruthy();
  });

  it("keeps a state that matches with all its seats, and else only the seats that match", () => {
    expect(filterStates(PLACES.states, "kerala").map((s) => s.name)).toEqual(["Kerala"]);
    const pune = filterStates(PLACES.states, "pune");
    expect(pune.map((s) => [s.name, s.seats.map((x) => x.name)])).toEqual([["Maharashtra", ["Pune"]]]);
  });
});

describe("PartyWeightChart rules", () => {
  it("keeps the colour of a party whatever its rank, and gives a spare colour to a new party", async () => {
    const { colourSlots } = await import("../pages/parties/PartyWeightChart.jsx");
    expect(colourSlots(["INC", "BJP", "RJD"])).toEqual([2, 1, 7]);
  });

  it("uses a log axis that always holds 0.5x to 2x", async () => {
    const { weightDomain } = await import("../pages/parties/PartyWeightChart.jsx");
    expect(weightDomain([{ points: [{ weight: 1.2 }] }])).toEqual([0.5, 2]);
    const [lo, hi] = weightDomain([{ points: [{ weight: 0.37 }, { weight: 2.4 }] }]);
    expect(lo).toBeLessThan(0.37);
    expect(hi).toBeGreaterThan(2.4);
  });

  it("tells the story of the last full term by rule", async () => {
    const { storyOf } = await import("../pages/parties/PartyWeightChart.jsx");
    const weights = {
      terms: [{ term: 16 }, { term: 17 }, { term: 18 }],
      series: [
        { code: "INC", points: [{}, { weight: 1.375 }, {}] },
        { code: "SP", points: [{}, { weight: 0.37 }, {}] },
      ],
    };
    const story = storyOf(weights, { INC: "Indian National Congress", SP: "Samajwadi Party" });
    expect(story.term).toBe(17);
    expect(story.text).toBe(
      "In the 17th Lok Sabha, the last full term, a member of Indian National Congress spoke 1.4 times as often as the average member. A member of Samajwadi Party spoke 0.4 times as often."
    );
  });

  it("shows one party alone on a click, all again on a second click, and adds one with Ctrl", async () => {
    const { nextShown } = await import("../pages/parties/PartyWeightChart.jsx");
    const all = ["BJP", "INC", "SP"];
    const one = nextShown(new Set(all), "INC", all, false);
    expect([...one]).toEqual(["INC"]);
    expect([...nextShown(one, "INC", all, false)]).toEqual(all);
    expect([...nextShown(one, "SP", all, true)]).toEqual(["INC", "SP"]);
  });
});
