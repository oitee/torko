import React from "react";
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { MemoryRouter } from "react-router-dom";
import SpeechRow from "../components/SpeechRow.jsx";

afterEach(cleanup);

describe("SpeechRow", () => {
  const sampleSpeech = {
    id: 178379,
    date: "2025-12-17",
    term: 18,
    kind_label: "Bill",
    debate: "VB-G RAM G Bill",
    member: "Mahua Moitra",
    member_id: 1052,
    party: "AITC",
    seat: "Krishnanagar",
    summary: "Opposes the VB-GRAM G Bill.",
    excerpt: "माननीय अध्यक्ष जी",
    words: 1916,
    tags: [{ name: "Arrears", slug: "arrears" }],
  };

  it("renders all speech elements in order", () => {
    render(
      <MemoryRouter>
        <SpeechRow speech={sampleSpeech} />
      </MemoryRouter>
    );

    expect(
      screen.getByText("2025-12-17 · 18th LS · Bill · 1,916 words")
    ).toBeTruthy();

    const debateLink = screen.getByRole("link", { name: "VB-G RAM G Bill" });
    expect(debateLink.getAttribute("href")).toBe("/speech/178379");

    expect(screen.getByText("Opposes the VB-GRAM G Bill.")).toBeTruthy();
    expect(screen.getByRole("link", { name: "Mahua Moitra" })).toBeTruthy();

    const excerpt = screen.getByText("“माननीय अध्यक्ष जी”");
    expect(excerpt).toBeTruthy();
    expect(excerpt.getAttribute("lang")).toBe("hi");

    expect(screen.getByText("Arrears")).toBeTruthy();
  });

  it("renders speech with no identified member", () => {
    const unidentifiedSpeech = {
      id: 100,
      date: "2024-03-12",
      term: 17,
      kind_label: "Discussion",
      debate: "General Debate",
      member: null,
      member_id: null,
      party: null,
      seat: null,
      summary: null,
      excerpt: null,
      words: 24,
      tags: [],
    };

    render(
      <MemoryRouter>
        <SpeechRow speech={unidentifiedSpeech} />
      </MemoryRouter>
    );

    expect(screen.getByText("Speaker not identified")).toBeTruthy();
    expect(screen.queryByText(/“/)).toBeNull();
  });

  it("returns null when speech prop is missing", () => {
    const { container } = render(<SpeechRow />);
    expect(container.firstChild).toBeNull();
  });
});
