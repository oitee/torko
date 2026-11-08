import React from "react";
import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter } from "react-router-dom";
import * as api from "../assets/js/api.js";
import Parties, { shareText, termsText } from "../pages/parties.jsx";
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
    { code: "BJP", name: "Bharatiya Janata Party", speeches: 600, members: 50, terms: [13, 14, 15] },
    { code: "BJD", name: "Biju Janata Dal", speeches: 1, members: 1, terms: [14, 16] },
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
  it("lists every party with a link, its share and its terms, and filters by name", async () => {
    vi.spyOn(api, "getJSON").mockResolvedValue(PARTIES);
    render(
      <MemoryRouter>
        <Parties />
      </MemoryRouter>
    );
    const table = await screen.findByRole("table");
    expect(within(table).getByRole("link", { name: "Bharatiya Janata Party" }).getAttribute("href")).toBe("/party/BJP");
    expect(screen.getByText("60.0%")).toBeTruthy();
    expect(screen.getByText("13th–15th LS")).toBeTruthy();
    fireEvent.change(screen.getByLabelText("Find a party"), { target: { value: "biju" } });
    expect(within(screen.getByRole("table")).queryByRole("link", { name: "Bharatiya Janata Party" })).toBeNull();
    expect(screen.getByText("1 of 2 parties")).toBeTruthy();
  });

  it("draws the speaking weight with a table view and a method panel", async () => {
    vi.spyOn(api, "getJSON").mockResolvedValue(PARTIES);
    render(
      <MemoryRouter>
        <Parties />
      </MemoryRouter>
    );
    expect(await screen.findByRole("heading", { name: "How much each party speaks for its size" })).toBeTruthy();
    expect(screen.getByRole("heading", { name: "All parties" })).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Show as table" }));
    // A term with too few members has no value. The table says so with a dash.
    expect(screen.getByText("2.00×")).toBeTruthy();
    expect(screen.getByText("–")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "How this is calculated" }));
    expect(screen.getByRole("dialog").textContent).toContain("Weight = (speeches of the party / members of the party who spoke)");
  });

  it("writes small shares and broken term runs plainly", () => {
    expect(shareText(1, 1000)).toBe("0.1%");
    expect(shareText(1, 100000)).toBe("under 0.1%");
    expect(termsText([14, 16])).toBe("14th, 16th LS");
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
