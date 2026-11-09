import React from "react";
import { waitFor, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import Party from "../pages/party.jsx";
import { scaleTop, shortYears, termSentence } from "../pages/party/PartyShareChart.jsx";
import { headNumbers, partyColourVars, percent, perThousand, subjectSentence, timesText } from "../pages/party/partyData.js";
import * as api from "../assets/js/api.js";

afterEach(cleanup);

// A cut of the real answer of /api/party/CPI(M).
const term = (t, years, speaking, tagged, all, share, typical = []) => ({
  term: t, years, members_speaking: speaking, members_tagged: speaking, tagged, all_tagged: all,
  share_of_tagged: share, typical,
});
const cpim = {
  code: "CPI(M)",
  name: "Communist Party of India (Marxist)",
  colour: "#CC0D0D",
  total_tagged: 6050,
  all_tagged: 107949,
  terms: [
    term(13, "1999–2004", 35, 1858, 18348, 0.1013, [
      { tag: "Haldia Port", slug: "haldia-port", type: "institution", n: 6, share: 0.0032, base: 0.0003, lift: 9.88, extra: 5.4 },
    ]),
    term(17, "2019–2024", 4, 210, 22888, 0.0092),
    term(18, "2024–", 0, 0, 9895, 0),
  ],
  typical_all: [
    { tag: "Burn Standard Co", slug: "burn-standard-co", type: "institution", n: 18, share: 0.003, base: 0.0002, lift: 12.35, extra: 16.8 },
    { tag: "Government of Kerala", slug: "government-of-kerala", type: "institution", n: 78, share: 0.0129, base: 0.0014, lift: 9.28, extra: 69.5 },
  ],
  places: [{ tag: "Kannur", slug: "kannur", type: "place", n: 84, share: 0.0139, base: 0.0015, lift: 9.25, extra: 74.9 }],
  top3: [{ tag: "Burn Standard Co", slug: "burn-standard-co", members: [{ id: 12, name: "Sunil Khan", n: 6, terms: [14] }] }],
  rules: { min_party_tagged: 30, min_n_term: 6, min_n_all: 15, min_n_place: 10, min_members: 3, min_members_place: 2, general_share: 0.03, top: 8 },
};

function renderParty(path = "/party/CPI(M)") {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/party/:code" element={<Party />} />
      </Routes>
    </MemoryRouter>
  );
}

describe("party helpers", () => {
  it("formats shares, rates and lifts", () => {
    expect(percent(0.4049)).toBe("40.5%");
    expect(percent(null)).toBe("–");
    expect(perThousand(0.0021)).toBe("2.1");
    expect(perThousand(0.0139)).toBe("14");
    expect(timesText(3.5)).toBe("3.5 times");
    expect(timesText(12.35)).toBe("12 times");
  });

  it("puts the top of the scale at the next round step above the highest share", () => {
    expect(scaleTop([0.2599, 0.4857])).toBe(0.5);
    expect(scaleTop([0.1013, 0.1432])).toBe(0.15);
    expect(scaleTop([0.0067, 0.0055])).toBe(0.01);
    expect(scaleTop([0])).toBe(0.01);
  });

  it("uses the token of a known party and derived shades for any other", () => {
    expect(partyColourVars("BJP", "#FF9933")).toEqual({ "--pc-light": "var(--party-bjp)", "--pc-dark": "var(--party-bjp)" });
    const vars = partyColourVars("CPI(M)", "#CC0D0D");
    expect(vars["--pc-light"]).toMatch(/^#[0-9a-f]{6}$/);
    expect(partyColourVars("XYZ", null)).toEqual({});
  });

  it("writes one sentence for a term and for a subject, with the denominator", () => {
    expect(termSentence(cpim.terms[0], "CPI(M)")).toBe(
      "13th Lok Sabha, 1999–2004: 10.1% of tagged speeches (1,858 of 18,348). 35 members spoke."
    );
    expect(termSentence(cpim.terms[2], "CPI(M)")).toBe("18th Lok Sabha, 2024–: no tagged CPI(M) speeches.");
    expect(subjectSentence(cpim.places[0], "CPI(M)")).toBe(
      "Kannur: 14 in every 1,000 tagged CPI(M) speeches, 1.5 for all parties. 84 speeches, 75 above the rate of all parties."
    );
    expect(subjectSentence({ ...cpim.places[0], members: 15 }, "CPI(M)")).toBe(
      "Kannur: 14 in every 1,000 tagged CPI(M) speeches, 1.5 for all parties. 84 speeches by 15 members, 75 above the rate of all parties."
    );
  });

  it("counts the share of the House and the terms with speeches", () => {
    const values = headNumbers(cpim).map((n) => n.value);
    expect(values).toEqual(["6,050", "5.6%", "2", "0"]);
  });
});

describe("Party page", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("shows the head, the charts, and the leaders", async () => {
    vi.spyOn(api, "getJSON").mockResolvedValueOnce(cpim);
    renderParty();

    expect(await screen.findByRole("heading", { level: 1, name: "Communist Party of India (Marxist)" })).toBeTruthy();
    expect(api.getJSON).toHaveBeenCalledWith("/api/party/CPI(M)", undefined, { signal: expect.any(AbortSignal) });
    await waitFor(() => expect(document.title).toBe("Communist Party of India (Marxist) · Torko"));
    expect(screen.getByRole("heading", { name: "Share of the House, by term" })).toBeTruthy();
    // The term with the most members who spoke (13th, 35 members) is green. The share chart keeps the party colour.
    expect(screen.getByTestId("party-members-13").className).toContain("party-share__col--green");
    expect(screen.getByTestId("party-members-17").className).not.toContain("party-share__col--green");
    expect(screen.getByRole("heading", { name: "Subjects the party raises more than the House" })).toBeTruthy();
    expect(screen.getByRole("heading", { name: "Places the party talks about more than the House" })).toBeTruthy();
    expect(screen.getByRole("link", { name: /^Sunil Khan.* 6$/ }).getAttribute("href")).toBe("/member/12");
    expect(screen.getByRole("link", { name: /^Kannur:/ }).getAttribute("href")).toBe("/place/kannur");
  });

  it("places the party dot and the all-parties ring on one scale", async () => {
    vi.spyOn(api, "getJSON").mockResolvedValueOnce(cpim);
    renderParty();
    await screen.findByRole("heading", { level: 1, name: "Communist Party of India (Marxist)" });

    // The highest value in the list (0.0129) is at 100%.
    expect(screen.getByTestId("party-dot-government-of-kerala").style.left).toBe("100%");
    expect(screen.getByTestId("party-dot-burn-standard-co").style.left).toMatch(/^23\.2/);
  });

  it("shows the subjects of one term when the reader picks it", async () => {
    vi.spyOn(api, "getJSON").mockResolvedValueOnce(cpim);
    renderParty();
    await screen.findByRole("heading", { level: 1, name: "Communist Party of India (Marxist)" });

    fireEvent.click(screen.getByRole("button", { name: "13th LS · 1999–2004" }));
    expect(screen.getByRole("link", { name: /^Haldia Port:/ })).toBeTruthy();
    expect(screen.queryByRole("link", { name: /^Burn Standard Co:/ })).toBeNull();
  });

  it("shows a term sentence on focus", async () => {
    vi.spyOn(api, "getJSON").mockResolvedValueOnce(cpim);
    renderParty();
    await screen.findByRole("heading", { level: 1, name: "Communist Party of India (Marxist)" });

    fireEvent.focus(screen.getByTestId("party-share-17"));
    expect(screen.getByText("17th Lok Sabha, 2019–2024: 0.9% of tagged speeches (210 of 22,888). 4 members spoke.")).toBeTruthy();
  });

  it("shows the extra speeches of each row, the number that orders the list", async () => {
    vi.spyOn(api, "getJSON").mockResolvedValueOnce(cpim);
    renderParty();
    await screen.findByRole("heading", { level: 1, name: "Communist Party of India (Marxist)" });

    const row = screen.getByRole("link", { name: /^Kannur:/ }).closest("li");
    expect(row.textContent).toContain("75");
  });

  it("states the rule that orders the subjects", async () => {
    vi.spyOn(api, "getJSON").mockResolvedValueOnce(cpim);
    renderParty();
    await screen.findByRole("heading", { level: 1, name: "Communist Party of India (Marxist)" });

    const text = document.body.textContent;
    expect(text).toContain("The list orders the subjects by the extra speeches above that number.");
    expect(text).toContain("A subject needs at least 3 members");
    expect(text).not.toContain("the first rate divided by the second");
  });

  it("links Parties to the index, and shows the recent speeches with a link to the search", async () => {
    vi.spyOn(api, "getJSON").mockResolvedValueOnce({
      ...cpim,
      recent: [{ id: 5, member: "Sunil Khan", party: "CPI(M)", seat: "Kannur", date: "2026-01-02", debate: "Rail line-Laid", summary: "Asks for a line.", tags: [] }],
    });
    renderParty();
    await screen.findByRole("heading", { level: 1, name: "Communist Party of India (Marxist)" });
    expect(screen.getByRole("link", { name: "Parties" }).getAttribute("href")).toBe("/parties");
    expect(screen.getByText("Rail line")).toBeTruthy();
    expect(screen.getByRole("link", { name: /Read all CPI\(M\) speeches/ }).getAttribute("href")).toBe("/search?party=CPI(M)");
  });

  it("shows the sentence of a term in a pop-up on its bar, and the years in two digits", async () => {
    vi.spyOn(api, "getJSON").mockResolvedValueOnce(cpim);
    const { container } = renderParty();
    await screen.findByRole("heading", { level: 1, name: "Communist Party of India (Marxist)" });
    // At rest there is no pop-up: every bar already prints its value.
    expect(container.querySelector(".bar-tip")).toBeNull();
    fireEvent.mouseEnter(screen.getByTestId("party-share-17"));
    expect(container.querySelector(".bar-tip").textContent).toMatch(/^17th Lok Sabha, 2019–2024: 0\.9%/);
    // The term under the pointer is the green bar of the members chart, not the term with the most members.
    expect(screen.getByTestId("party-members-17").className).toContain("party-share__col--green");
    expect(screen.getByTestId("party-members-13").className).not.toContain("party-share__col--green");
    expect(shortYears("1999–2004")).toBe("99–04");
    expect(shortYears("2024–")).toBe("24–");
  });

  it("writes the denominator of the share in the head, and does not colour the number", async () => {
    vi.spyOn(api, "getJSON").mockResolvedValueOnce(cpim);
    renderParty();
    await screen.findByRole("heading", { level: 1, name: "Communist Party of India (Marxist)" });
    expect(screen.getByText("of all 107,949 tagged speeches in the House")).toBeTruthy();
    expect(document.querySelector(".party-head__stat--lead")).toBeNull();
  });

  it("shows Page not found for an unknown party", async () => {
    vi.spyOn(api, "getJSON").mockRejectedValueOnce({ status: 404 });
    renderParty("/party/XYZ");
    expect(await screen.findByRole("heading", { level: 1, name: "Page not found." })).toBeTruthy();
  });
});
