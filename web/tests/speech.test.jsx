import React from "react";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import Speech, { formatCitation } from "../pages/speech.jsx";
import * as api from "../assets/js/api.js";

afterEach(cleanup);

const mockSpeech = {
  id: 178379,
  date: "2025-12-17",
  term: 18,
  session: 6,
  debate: "Viksit Bharat Gurantee Bill",
  debate_id: 683,
  debate_type: "Government bills",
  member: "Mahua Moitra",
  member_id: 1052,
  party: "AITC",
  seat: "Krishnanagar",
  state: "West Bengal",
  language: "en",
  words: 1962,
  turns: 3,
  interruptions: 2,
  summary: "Opposes the proposed bill and demands release of arrears.",
  source_url: "https://sansad.in/debate/683",
  tags: [
    {
      name: "All India Trinamool Congress",
      slug: "all-india-trinamool-congress",
      source: "llm",
      why: [],
    },
    {
      name: "Arrears",
      slug: "arrears",
      source: "dictionary",
      why: [],
    },
  ],
  turn_list: [
    {
      seq: 35,
      own: true,
      attributed: true,
      member: "Mahua Moitra",
      member_id: 1052,
      words: 1744,
      text: "First paragraph of the speech.\n\nSecond paragraph of the speech.",
    },
    {
      seq: 36,
      own: false,
      attributed: false,
      role_kind: "presiding",
      words: 2,
      text: "Order, order.",
    },
    {
      seq: 37,
      own: true,
      attributed: true,
      member: "Mahua Moitra",
      member_id: 1052,
      words: 216,
      text: "Concluding remarks.",
    },
  ],
  before: [
    {
      seq: 34,
      attributed: true,
      member: "Earlier Member",
      member_id: 88,
      text: "Earlier turn text in the debate.",
    },
  ],
  after: [
    {
      seq: 38,
      attributed: true,
      member: "Later Member",
      member_id: 99,
      text: "Later turn text in the debate.",
    },
  ],
  earlier_speeches: 12,
  later_speeches: 119,
  debate_speeches: 132,
  debate_members: 98,
  member_counts: {
    term: 18,
    term_speeches: 15,
  },
};

const mockNoMemberSpeech = {
  ...mockSpeech,
  id: 413512,
  member: null,
  member_id: null,
  party: null,
  seat: null,
  state: null,
  summary: null,
  tags: [],
  member_counts: null,
};

describe("Speech Page", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("shows loading state initially", () => {
    vi.spyOn(api, "getJSON").mockReturnValue(new Promise(() => {}));

    render(
      <MemoryRouter initialEntries={["/speech/178379"]}>
        <Routes>
          <Route path="/speech/:id" element={<Speech />} />
        </Routes>
      </MemoryRouter>
    );

    expect(screen.getByRole("status")).toBeTruthy();
    expect(screen.getByText("Loading")).toBeTruthy();
  });

  it("renders 404 error state when API returns 404", async () => {
    vi.spyOn(api, "getJSON").mockRejectedValue({
      status: 404,
      message: "Speech not found",
    });

    render(
      <MemoryRouter initialEntries={["/speech/999999999"]}>
        <Routes>
          <Route path="/speech/:id" element={<Speech />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText("Page not found")).toBeTruthy();
    });
    expect(document.title).toBe("Page not found · Torko");
  });

  it("renders error state with retry on 500 error", async () => {
    const getSpy = vi
      .spyOn(api, "getJSON")
      .mockRejectedValueOnce({ status: 500, message: "Server error" })
      .mockResolvedValueOnce(mockSpeech);

    render(
      <MemoryRouter initialEntries={["/speech/178379"]}>
        <Routes>
          <Route path="/speech/:id" element={<Speech />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText("Server error")).toBeTruthy();
    });

    const retryBtn = screen.getByRole("button", { name: "Try again" });
    fireEvent.click(retryBtn);

    await waitFor(() => {
      expect(screen.getByRole("heading", { level: 1, name: "Viksit Bharat Gurantee Bill" })).toBeTruthy();
    });
  });

  it("renders speech page with member, answer, tags, speech text, margin, and around speech", async () => {
    vi.spyOn(api, "getJSON").mockResolvedValue(mockSpeech);

    render(
      <MemoryRouter initialEntries={["/speech/178379"]}>
        <Routes>
          <Route path="/speech/:id" element={<Speech />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByRole("heading", { level: 1, name: "Viksit Bharat Gurantee Bill" })).toBeTruthy();
    });

    // Check tab title
    expect(document.title).toBe("Mahua Moitra · 17 Dec 2025 · Torko");

    // Check breadcrumb
    expect(screen.getByRole("navigation", { name: "Breadcrumb" })).toBeTruthy();
    expect(screen.getByText("18th Lok Sabha")).toBeTruthy();
    expect(screen.getByText("Session 6")).toBeTruthy();
    expect(screen.getAllByText("17 Dec 2025").length).toBeGreaterThanOrEqual(1);

    // Check TLDR
    expect(screen.getByText("TLDR")).toBeTruthy();
    expect(screen.getByText(/Opposes the proposed bill/)).toBeTruthy();

    // Check tags
    expect(screen.getByText("All India Trinamool Congress")).toBeTruthy();
    expect(screen.getByText("Arrears")).toBeTruthy();

    // Check paragraphs and interruption
    expect(screen.getByText("¶1")).toBeTruthy();
    expect(screen.getByText("¶2")).toBeTruthy();
    expect(screen.getByText("The Chair")).toBeTruthy();
    expect(screen.getByText("¶3")).toBeTruthy();

    // Check margin
    expect(screen.getByText((_, el) => el?.tagName === "DD" && el.textContent === "speeches by Mahua Moitra in the 18th LS")).toBeTruthy();
    expect(
      screen.getByText((_, el) => el?.tagName === "DD" && el.textContent === "speeches in this debate. This is speech 13.")
    ).toBeTruthy();
    expect(
      screen.getByText((_, el) => el?.tagName === "DD" && el.textContent === "interruptions inside this speech")
    ).toBeTruthy();
    expect(screen.getByText("How Torko counts")).toBeTruthy();
    expect(screen.getByText("sansad.in")).toBeTruthy();

    // Check around speech
    expect(screen.getByText("Earlier Member")).toBeTruthy();
    expect(document.querySelector(".around-speech__row--current")?.textContent).toContain("this speech");
    expect(screen.getByText("Later Member")).toBeTruthy();
  });

  it("renders speech with no member correctly", async () => {
    vi.spyOn(api, "getJSON").mockResolvedValue(mockNoMemberSpeech);

    render(
      <MemoryRouter initialEntries={["/speech/413512"]}>
        <Routes>
          <Route path="/speech/:id" element={<Speech />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(
        screen.getByRole("heading", { level: 1, name: "Viksit Bharat Gurantee Bill" })
      ).toBeTruthy();
    });

    expect(document.title).toBe("Speech · 17 Dec 2025 · Torko");
    expect(screen.queryByText("TLDR")).toBeNull();
  });

  it("formats citation correctly and opens citation popover", async () => {
    vi.spyOn(api, "getJSON").mockResolvedValue(mockSpeech);

    render(
      <MemoryRouter initialEntries={["/speech/178379"]}>
        <Routes>
          <Route path="/speech/:id" element={<Speech />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Cite this speech" })).toBeTruthy();
    });

    const citeBtn = screen.getByRole("button", { name: "Cite this speech" });
    fireEvent.click(citeBtn);

    const expectedCitation =
      "Mahua Moitra. Speech in the Lok Sabha, Viksit Bharat Gurantee Bill, 17 Dec 2025. 18th Lok Sabha. Source: https://sansad.in/debate/683";
    expect(screen.getByText(expectedCitation)).toBeTruthy();
    expect(
      screen.getByText("Cite the speech, not the TLDR. The TLDR is machine text.")
    ).toBeTruthy();

    const copyBtn = screen.getByRole("button", { name: "Copy citation" });
    fireEvent.click(copyBtn);
    expect(screen.getByText("Citation copied")).toBeTruthy();
  });
});
