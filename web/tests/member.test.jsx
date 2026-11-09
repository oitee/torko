import React from "react";
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import Member from "../pages/member.jsx";
import { buildMemberAnswer } from "../pages/member/MemberHead.jsx";
import * as api from "../assets/js/api.js";

afterEach(cleanup);

const mockMemberData = {
  id: 1052,
  name: "Mahua Moitra",
  seat: "Krishnanagar",
  seat_slug: "krishnanagar",
  state: "West Bengal",
  state_slug: "west-bengal",
  rule: { min_member: 3, min_all: 20 },
  counts_note: "Definitions of the counts.",
  party_path: [
    { code: "AITC", from: 2019, to: null },
  ],
  speeches: 66,
  tagged_speeches: 63,
  terms: [
    {
      term: 17,
      seat: "Krishnanagar",
      state: "West Bengal",
      parties: ["AITC"],
      speeches: 51,
      words: 34419,
      first: "2019-06-21",
      last: "2023-12-06",
      house_median: 32,
      house_members: 583,
    },
    {
      term: 18,
      seat: "Krishnanagar",
      state: "West Bengal",
      parties: ["AITC"],
      speeches: 15,
      words: 10200,
      first: "2024-07-01",
      last: "2026-03-10",
      house_median: 16,
      house_members: 558,
    },
  ],
  sessions: [
    { term: 17, session: 1, label: "Monsoon 2019", n: 16, house_median: 6 },
    { term: 17, session: 2, label: "Winter 2019", n: 10, house_median: 4 },
    { term: 18, session: 1, label: "Monsoon 2024", n: 8, house_median: 5 },
  ],
  typical: [
    {
      name: "Right to Privacy",
      slug: "right-to-privacy",
      n: 4,
      all: 83,
      member_share: 0.0635,
      house_share: 0.002,
      lift_terms: 32.5,
      subjects: [
        { id: 41562, label: "Supreme Court right to privacy judgment", n: 2, all: 2 },
      ],
    },
    {
      name: "Political Funding",
      slug: "political-funding",
      n: 3,
      all: 102,
      member_share: 0.0476,
      house_share: 0.0006,
      lift_terms: 78.1,
      subjects: [],
    },
  ],
  places: [
    {
      name: "Krishnanagar",
      slug: "krishnanagar",
      n: 20,
      all: 150,
      own_seat: true,
      subtype: "seat",
    },
    {
      name: "West Bengal",
      slug: "west-bengal",
      n: 15,
      all: 3319,
      own_seat: false,
      subtype: "state",
    },
  ],
  recent: [
    {
      id: 177309,
      date: "2026-03-10",
      debate: "Resolution regarding removal of Speaker from Office",
      kind: "other",
      kind_label: "Other",
      summary: "Supports the motion of no-confidence against the Lok Sabha Speaker.",
      words: 1537,
    },
    {
      id: 177308,
      date: "2025-12-15",
      debate: "Discussion on Railway Safety",
      kind: "discussion",
      kind_label: "Discussion",
      summary: "Questions recent derailments and safety upgrades.",
      words: 1200,
    },
  ],
};

const mockSpeechesResponse = {
  speeches: [
    {
      id: 177309,
      date: "2026-03-10",
      debate: "Resolution regarding removal of Speaker from Office",
      debate_id: 5925,
      term: 18,
      kind: "other",
      kind_label: "Other",
      member: "Mahua Moitra",
      member_id: 1052,
      seat: "Krishnanagar",
      words: 1537,
      summary: "Supports the motion of no-confidence against the Lok Sabha Speaker.",
    },
  ],
  total: 66,
  pages: 4,
  per_page: 20,
  facets: {
    term: [{ term: 17, n: 51 }, { term: 18, n: 15 }],
    kind: [
      { kind: "bill", label: "Bill", n: 23 },
      { kind: "rule_377", label: "Rule 377", n: 6 },
    ],
    subject: [
      { id: "right-to-privacy", label: "Right to Privacy", n: 4 },
    ],
  },
};

function renderMemberPage(initialRoute = "/member/1052") {
  return render(
    <MemoryRouter initialEntries={[initialRoute]}>
      <Routes>
        <Route path="/member/:id" element={<Member />} />
      </Routes>
    </MemoryRouter>
  );
}

describe("Member Page", () => {
  beforeEach(() => {
    vi.spyOn(api, "getJSON").mockImplementation((url, params) => {
      if (url.startsWith("/api/member/1052")) {
        return Promise.resolve(mockMemberData);
      }
      if (url.startsWith("/api/member/999999")) {
        return Promise.reject({ status: 404, message: "Member not found" });
      }
      if (url.startsWith("/api/speeches")) {
        return Promise.resolve(mockSpeechesResponse);
      }
      return Promise.reject(new Error(`Unhandled request: ${url}`));
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe("Unit helpers", () => {

    it("buildMemberAnswer builds answer with top typical subject", () => {
      const text = buildMemberAnswer(mockMemberData);
      expect(text).toContain("Mahua Moitra spoke 66 times in 2 terms of the Lok Sabha.");
      expect(text).not.toContain("median member");
      expect(text).toContain("Most often on Right to Privacy: 4 of 63 tagged speeches (6%).");
      expect(text).not.toContain("times the rate");
    });
  });

  describe("Rendering and structure", () => {
    it("renders member head, heading, party line, and big numbers", async () => {
      renderMemberPage();

      const heading = await screen.findByRole("heading", { level: 1, name: "Mahua Moitra" });
      expect(heading).toBeTruthy();

      expect(screen.queryByText("Member of the Lok Sabha")).toBeNull();
      expect(screen.getAllByRole("link", { name: "AITC" })[0].getAttribute("href")).toBe("/party/AITC");
      expect(document.querySelector(".member-head__line").textContent).toMatch(/^MP, Krishnanagar, West Bengal · AITC since 2019/);
      // The years use the font of the line, not the mono font.
      expect(document.querySelector(".member-head__line .mono")).toBeNull();

      // Answer sentence
      expect(
        screen.getByText(/Mahua Moitra spoke 66 times in 2 terms of the Lok Sabha/)
      ).toBeTruthy();

      // Big numbers
      expect(screen.getAllByText("2").length).toBeGreaterThan(0);
      expect(screen.getAllByText("terms").length).toBeGreaterThan(0);
      expect(screen.getAllByText("66").length).toBeGreaterThan(0);
      expect(screen.getByText("words spoken")).toBeTruthy();
      expect(screen.getAllByText("44,619").length).toBeGreaterThan(0);
      expect(screen.getByText("2019–2026")).toBeTruthy();
      expect(screen.queryByText(/sessions with a speech/)).toBeNull();
      // The head has two actions: Cite in a box, and Copy link as text. No CSV.
      const cite = screen.getByRole("button", { name: "Cite this page" });
      expect(cite.className).toContain("button--secondary");
      expect(screen.getByRole("button", { name: "Copy link" }).className).toContain("button--text");
      expect(screen.queryByRole("link", { name: /CSV|Download/ })).toBeNull();
      fireEvent.click(cite);
      expect(screen.getByRole("dialog", { name: "Citation" }).textContent).toContain("Mahua Moitra, 66 speeches in the Lok Sabha");

      // Document title
      await waitFor(() => expect(document.title).toBe("Mahua Moitra · Torko"));
    });

    it("renders breadcrumb linking seat to /place/<seat_slug>", async () => {
      renderMemberPage();

      await screen.findByRole("heading", { level: 1, name: "Mahua Moitra" });

      const nav = screen.getByRole("navigation", { name: "Breadcrumb" });
      expect(nav).toBeTruthy();
      expect(screen.getByRole("link", { name: "Members" }).getAttribute("href")).toBe("/search?view=members");
      expect(within(nav).getByRole("link", { name: "West Bengal" }).getAttribute("href")).toBe("/place/west-bengal");
      // The path stops at the seat. The name is the title under it.
      expect(nav.textContent).not.toContain("Mahua Moitra");
      // The seat is a link in the path and in the line under the name.
      expect(within(nav).getByRole("link", { name: "Krishnanagar" }).getAttribute("href")).toBe("/place/krishnanagar");
      expect(document.querySelector(".member-head__line a.member-head__seat-link").getAttribute("href")).toBe("/place/krishnanagar");

      const seatLinks = screen.getAllByRole("link", { name: "Krishnanagar" });
      expect(seatLinks.some((l) => l.getAttribute("href") === "/place/krishnanagar")).toBe(true);
    });

    it("renders the speech grid with a button to the Search page", async () => {
      renderMemberPage();

      await screen.findByRole("heading", { level: 1, name: "Mahua Moitra" });

      expect(screen.getByRole("heading", { name: "Speeches" })).toBeTruthy();
      expect(screen.getByText("2 of 66 speeches · newest first")).toBeTruthy();
      const allLink = screen.getByRole("link", { name: "See all 66 speeches in Search" });
      expect(allLink.getAttribute("href")).toBe("/search?member=1052");
      expect(
        screen.getAllByText("Resolution regarding removal of Speaker from Office").length
      ).toBeGreaterThan(0);
      expect(screen.queryByRole("button", { name: /Longest/ })).toBeNull();
    });

    it("renders activity section with table toggle control", async () => {
      renderMemberPage();

      await screen.findByRole("heading", { level: 1, name: "Mahua Moitra" });

      expect(screen.getByRole("heading", { name: "Activity" })).toBeTruthy();
      expect(screen.getByText(/More speeches than the median member in 3 of 3 sessions/)).toBeTruthy();
      // The session with the most speeches (Monsoon 2019, 16) has the green bar.
      const peakBars = document.querySelectorAll(".member-activity__bar--active, .member-activity__narrow-bar--active");
      expect(peakBars.length).toBeGreaterThan(0);
      expect(peakBars[0].closest("button").getAttribute("aria-label") || peakBars[0].closest("button").textContent).toMatch(/Monsoon 2019/);

      const toggleBtn = screen.getByRole("button", { name: "Show as table" });
      expect(toggleBtn).toBeTruthy();

      // Click to show table
      fireEvent.click(toggleBtn);
      expect(screen.getByRole("table")).toBeTruthy();
      expect(screen.getByRole("button", { name: "Show as chart" })).toBeTruthy();

      // Click again to show chart
      fireEvent.click(screen.getByRole("button", { name: "Show as chart" }));
      expect(screen.queryByRole("table")).toBeNull();
    });

    it("renders subjects table with expandable specific subjects and links", async () => {
      renderMemberPage();

      await screen.findByRole("heading", { level: 1, name: "Mahua Moitra" });

      expect(screen.getByRole("heading", { name: "Subjects" })).toBeTruthy();
      const privacyLink = screen.getByRole("link", { name: "Right to Privacy" });
      expect(privacyLink.getAttribute("href")).toBe("/tag/right-to-privacy");

      // Counts first. The ratio shows only from 10 speeches.
      expect(screen.getByText("4 of 63 tagged (6%) · house 0.2%")).toBeTruthy();
      expect(screen.queryByText(/× the house/)).toBeNull();
      expect(screen.getByText("3 of 63 tagged (5%) · house 0.1%").getAttribute("href")).toBe(
        "/search?member=1052&tag=political-funding"
      );

      // Caret toggle for specific subjects
      const caretBtn = screen.getByRole("button", {
        name: "Show specific subjects for Right to Privacy",
      });
      fireEvent.click(caretBtn);

      expect(
        screen.getByText("Supreme Court right to privacy judgment")
      ).toBeTruthy();
    });

    it("renders places cards marking own seat", async () => {
      renderMemberPage();

      await screen.findByRole("heading", { level: 1, name: "Mahua Moitra" });

      expect(screen.getByRole("heading", { name: "Places" })).toBeTruthy();
      expect(screen.getByText("own seat")).toBeTruthy();
      expect(screen.getByText(/Krishnanagar is the place named most often/)).toBeTruthy();
      // Each place is a tile with its count, its share and a bar.
      expect(document.querySelectorAll(".member-places__card").length).toBeGreaterThan(0);
    });

    it("renders margin counts including Rule 377 count and HowTorkoCounts note", async () => {
      renderMemberPage();

      await screen.findByRole("heading", { level: 1, name: "Mahua Moitra" });

      expect(screen.getByText("speeches in 2 terms")).toBeTruthy();
      expect(screen.getByText("of 66 speeches carry a tag")).toBeTruthy();
      expect(screen.getByText("Rule 377").previousSibling.textContent).toBe("6");
      expect(screen.getByRole("link", { name: "6" }).getAttribute("href")).toBe("/search?member=1052&kind=rule_377");

      expect(
        screen.getByText(/A speech is one time the member speaks/)
      ).toBeTruthy();
      // The record is named, not linked: sansad.in has no page for all debates.
      expect(screen.getByText("Lok Sabha Debates")).toBeTruthy();
      expect(screen.queryByRole("link", { name: "Lok Sabha Debates" })).toBeNull();
      expect(screen.queryByText("Exact definitions of each count")).toBeNull();
    });

    it("orders subjects by speeches first and by ratio on request", async () => {
      renderMemberPage();
      await screen.findByRole("heading", { level: 1, name: "Mahua Moitra" });
      const order = () => screen.getAllByRole("link", { name: /Right to Privacy|Political Funding/ }).filter((a) => a.getAttribute("href").startsWith("/tag/")).map((a) => a.textContent);
      expect(order()).toEqual(["Right to Privacy", "Political Funding"]);
      fireEvent.click(screen.getByRole("button", { name: /Most unusual/ }));
      expect(order()).toEqual(["Political Funding", "Right to Privacy"]);
      expect(screen.getByRole("button", { name: "Most unusual" }).getAttribute("aria-pressed")).toBe("true");
      expect(screen.queryByText(/Bar and first number/)).toBeNull();
    });

    it("handles 404 error correctly", async () => {
      renderMemberPage("/member/999999");

      await waitFor(() => {
        expect(screen.getByRole("heading", { level: 1, name: "Page not found." })).toBeTruthy();
      });

      await waitFor(() => expect(document.title).toBe("Page not found · Torko"));
    });
  });
});
