import React from "react";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import Member from "../pages/member.jsx";
import { formatPartyPath, buildMemberAnswer } from "../pages/member/MemberHead.jsx";
import * as api from "../assets/js/api.js";

afterEach(cleanup);

const mockMemberData = {
  id: 1052,
  name: "Mahua Moitra",
  seat: "Krishnanagar",
  seat_slug: "krishnanagar",
  state: "West Bengal",
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
    it("formatPartyPath formats single current party", () => {
      const path = [{ code: "BJP", from: 2014, to: null }];
      expect(formatPartyPath(path)).toBe("BJP since 2014");
    });

    it("formatPartyPath formats multiple parties in date order", () => {
      const path = [
        { code: "NCP", from: 2014, to: 2019 },
        { code: "INC", from: 2019, to: null },
      ];
      expect(formatPartyPath(path)).toBe("INC since 2019 · NCP 2014–2019");
    });

    it("buildMemberAnswer builds answer with top typical subject", () => {
      const text = buildMemberAnswer(mockMemberData);
      expect(text).toContain("Mahua Moitra has made 66 speeches in the Lok Sabha over 2 terms.");
      expect(text).toContain("The member speaks most often on right to privacy: 32.5 times the rate of the house.");
    });
  });

  describe("Rendering and structure", () => {
    it("renders member head, kicker, heading, party line, and big numbers", async () => {
      renderMemberPage();

      const heading = await screen.findByRole("heading", { level: 1, name: "Mahua Moitra" });
      expect(heading).toBeTruthy();

      expect(screen.getByText("Member of the Lok Sabha")).toBeTruthy();
      expect(screen.getByText(/AITC since 2019/)).toBeTruthy();

      // Answer sentence
      expect(
        screen.getByText(/Mahua Moitra has made 66 speeches in the Lok Sabha over 2 terms/)
      ).toBeTruthy();

      // Big numbers
      expect(screen.getByText("2")).toBeTruthy();
      expect(screen.getAllByText("terms").length).toBeGreaterThan(0);
      expect(screen.getAllByText("66").length).toBeGreaterThan(0);
      expect(screen.getByText("first")).toBeTruthy();
      expect(screen.getByText("latest")).toBeTruthy();

      // Document title
      expect(document.title).toBe("Mahua Moitra · Torko");
    });

    it("renders breadcrumb linking seat to /place/<seat_slug>", async () => {
      renderMemberPage();

      await screen.findByRole("heading", { level: 1, name: "Mahua Moitra" });

      const nav = screen.getByRole("navigation", { name: "Breadcrumb" });
      expect(nav).toBeTruthy();
      expect(screen.getByText("Members")).toBeTruthy();
      expect(screen.getAllByText("West Bengal").length).toBeGreaterThan(0);

      const seatLinks = screen.getAllByRole("link", { name: "Krishnanagar" });
      expect(seatLinks.some((l) => l.getAttribute("href") === "/place/krishnanagar")).toBe(true);
    });

    it("renders latest speeches section with link to #speeches", async () => {
      renderMemberPage();

      await screen.findByRole("heading", { level: 1, name: "Mahua Moitra" });

      expect(screen.getByRole("heading", { name: "Latest speeches" })).toBeTruthy();
      const allLink = screen.getByRole("link", { name: "All 66 speeches" });
      expect(allLink.getAttribute("href")).toBe("#speeches");

      expect(
        screen.getAllByRole("link", { name: "Resolution regarding removal of Speaker from Office" }).length
      ).toBeGreaterThan(0);
    });

    it("renders activity section with table toggle control", async () => {
      renderMemberPage();

      await screen.findByRole("heading", { level: 1, name: "Mahua Moitra" });

      expect(screen.getByRole("heading", { name: "Activity" })).toBeTruthy();
      expect(screen.getByText(/Above the typical member in 3 of 3 sessions/)).toBeTruthy();

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

      expect(screen.getByText("32.5× the house")).toBeTruthy();

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
    });

    it("toggles 'Hide remarks under 50 words' checkbox", async () => {
      renderMemberPage();

      await screen.findByRole("heading", { level: 1, name: "Mahua Moitra" });

      const checkbox = screen.getByRole("checkbox", {
        name: "Hide remarks under 50 words",
      });
      expect(checkbox.checked).toBe(false);

      fireEvent.click(checkbox);
      expect(checkbox.checked).toBe(true);

      // Verify that api.getJSON was called with min_words=50
      await waitFor(() => {
        expect(api.getJSON).toHaveBeenCalledWith(
          "/api/speeches",
          expect.objectContaining({ min_words: "50" }),
          expect.anything()
        );
      });
    });

    it("renders margin counts including Rule 377 count and HowTorkoCounts note", async () => {
      renderMemberPage();

      await screen.findByRole("heading", { level: 1, name: "Mahua Moitra" });

      expect(screen.getByText("speeches over 2 terms")).toBeTruthy();
      expect(screen.getByText("of 66 carry a tag")).toBeTruthy();
      expect(screen.getByText("matters raised under Rule 377")).toBeTruthy();

      expect(
        screen.getByText(/A speech is one time the member speaks/)
      ).toBeTruthy();
      expect(screen.getByText(/Lok Sabha Debates, 2019–2026/)).toBeTruthy();
    });

    it("handles 404 error correctly", async () => {
      renderMemberPage("/member/999999");

      await waitFor(() => {
        expect(screen.getByText("Page not found")).toBeTruthy();
      });

      expect(document.title).toBe("Page not found · Torko");
    });
  });
});
