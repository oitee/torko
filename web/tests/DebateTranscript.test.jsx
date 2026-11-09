import React from "react";
import { describe, it, expect, afterEach } from "vitest";
import { cleanup, render, screen, fireEvent, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import DebateTranscript from "../pages/debate/DebateTranscript.jsx";

afterEach(cleanup);

const mockSpeeches = [
  {
    id: 101,
    start: 1,
    end: 2,
    words: 250,
    turns: 2,
    interruptions: 0,
    member: "Speaker Alpha",
    member_id: 1,
    party: "ABC",
    seat: "North",
    summary: "Alpha talks about infrastructure and budget allocations.",
    tags: [
      { name: "Economy", slug: "economy" },
      { name: "Railways", slug: "railways" },
    ],
  },
  {
    id: 102,
    start: 3,
    end: 4,
    words: 80,
    turns: 2,
    interruptions: 1,
    member: "Speaker Beta",
    member_id: 2,
    party: "XYZ",
    seat: "South",
    summary: null,
    tags: [{ name: "Health", slug: "health" }],
  },
];

const mockTurns = [
  {
    seq: 1,
    speech: 101,
    member: "Speaker Alpha",
    member_id: 1,
    party: "ABC",
    seat: "North",
    attributed: true,
    kind: "member",
    role_in_debate: "speech",
    words: 150,
    text: "Paragraph one of a very long speech with many words explaining the topic.\n\nParagraph two with even more text so that it exceeds the limit for collapsing in the turn preview.\n\nParagraph three continues further with details and specifics.",
  },
  {
    seq: 2,
    speech: 101,
    member: "Speaker Alpha",
    member_id: 1,
    party: "ABC",
    seat: "North",
    attributed: true,
    kind: "member",
    role_in_debate: "speech",
    words: 100,
    text: "Second turn of speech 101.",
  },
  {
    seq: 3,
    speech: 102,
    member: "Speaker Beta",
    member_id: 2,
    party: "XYZ",
    seat: "South",
    attributed: true,
    kind: "member",
    role_in_debate: "speech",
    words: 50,
    text: "Turn of speech 102.",
  },
  {
    seq: 4,
    speech: 102,
    member: null,
    member_id: null,
    attributed: false,
    kind: "presiding",
    role_kind: "presiding",
    role_in_debate: "interruption",
    inside_speech: 102,
    words: 30,
    text: "Order, order in the house.",
  },
];

const mockPeople = [
  { id: 1, name: "Speaker Alpha", party: "ABC", seat: "North", speeches: 1, turns: 2, words: 250 },
  { id: 2, name: "Speaker Beta", party: "XYZ", seat: "South", speeches: 1, turns: 1, words: 50 },
];

const mockTags = [
  { name: "Economy", slug: "economy", speeches: 1 },
  { name: "Railways", slug: "railways", speeches: 1 },
  { name: "Health", slug: "health", speeches: 1 },
];

describe("DebateTranscript", () => {
  it("renders the rail, turns, and speech cards", () => {
    render(
      <MemoryRouter>
        <DebateTranscript
          speeches={mockSpeeches}
          turns={mockTurns}
          people={mockPeople}
          tags={mockTags}
        />
      </MemoryRouter>
    );

    // Rail should show both speeches
    const railNav = screen.getByRole("navigation", { name: "Speeches in this debate" });
    expect(railNav).toBeTruthy();
    expect(within(railNav).getByText("Speaker Alpha")).toBeTruthy();
    expect(within(railNav).getByText("Speaker Beta")).toBeTruthy();

    // Turn speakers
    expect(screen.getAllByText("The Chair").length).toBeGreaterThan(0);

    // TLDR on right card
    expect(
      screen.getByText("Alpha talks about infrastructure and budget allocations.")
    ).toBeTruthy();
  });

  it("toggles read-more on long turns", () => {
    render(
      <MemoryRouter>
        <DebateTranscript
          speeches={mockSpeeches}
          turns={mockTurns}
          people={mockPeople}
          tags={mockTags}
        />
      </MemoryRouter>
    );

    // Turn 1 has 3 paragraphs (> 2), so it should have a …Read more toggle
    const readMoreBtn = screen.getByRole("button", { name: /^Read more/ });
    expect(readMoreBtn).toBeTruthy();

    // Before clicking, paragraph 3 is not visible
    expect(
      screen.queryByText(/Paragraph three continues further with details and specifics\./)
    ).toBeNull();

    // Click to expand
    fireEvent.click(readMoreBtn);
    expect(
      screen.getByText(/Paragraph three continues further with details and specifics\./)
    ).toBeTruthy();
    expect(screen.queryByRole("button", { name: /^Read more/ })).toBeNull();
    expect(screen.getByRole("button", { name: "Read less" })).toBeTruthy();
  });

  it("folds turns when a tag filter is active and toggles unfold", () => {
    render(
      <MemoryRouter>
        <DebateTranscript
          speeches={mockSpeeches}
          turns={mockTurns}
          people={mockPeople}
          tags={mockTags}
          activeTagSlug="health"
        />
      </MemoryRouter>
    );

    // Turns for speech 101 are not tagged 'health', so they should be folded
    const foldBar = screen.getByRole("button", { name: /Show \d+ hidden turns/ });
    expect(foldBar).toBeTruthy();
    expect(foldBar.textContent).toContain("turns hidden");

    // Click Show to unfold
    fireEvent.click(foldBar);
    expect(screen.getByText(/Opened\. These turns are outside the filter\./)).toBeTruthy();

    // Click Hide to fold back
    const hideBtn = screen.getByRole("button", { name: /Opened/ });
    fireEvent.click(hideBtn);
    expect(screen.getByRole("button", { name: /Show \d+ hidden turns/ })).toBeTruthy();
  });

  it("handles debates with no speeches", () => {
    const rawTurns = [
      {
        seq: 1,
        speech: null,
        member: null,
        kind: "presiding",
        role_kind: "presiding",
        role_in_debate: "between",
        words: 10,
        text: "The House stands adjourned.",
      },
    ];

    render(
      <MemoryRouter>
        <DebateTranscript
          speeches={[]}
          turns={rawTurns}
          people={[]}
          tags={[]}
        />
      </MemoryRouter>
    );

    // No speeches rail
    expect(screen.queryByRole("navigation", { name: "Speeches in this debate" })).toBeNull();
    // Turn is rendered
    expect(screen.getByText("The House stands adjourned.")).toBeTruthy();
    // Filter sentence notes no speeches
    expect(screen.getByText("This debate has no speech. It has 1 turn.")).toBeTruthy();
  });
});

describe("DebateTranscript counts and filters", () => {
  it("writes one speech in the singular and hides filters with no options", () => {
    render(
      <MemoryRouter>
        <DebateTranscript
          speeches={[{ ...mockSpeeches[0], member: null, member_id: null, tags: [] }]}
          turns={[{ ...mockTurns[1], member: null, member_id: null, attributed: false, kind: "unattributed" }]}
          people={[]}
          tags={[]}
        />
      </MemoryRouter>
    );
    expect(
      screen.getByText("Showing the whole debate in order.")
    ).toBeTruthy();
    expect(screen.queryByRole("combobox")).toBeNull();
    expect(screen.queryByText(/1 speeches/)).toBeNull();
  });
});

import { commonTagSlugs, isHeadingTurn } from "../pages/debate/DebateTranscript.jsx";
import { speechIdFromHash } from "../pages/debate/jump.js";

describe("heading lines", () => {
  const heading = {
    seq: 0, kind: "heading", label: null, member: null, member_id: null, attributed: false,
    role_in_debate: "between", speech: null, words: 4, text: "VB-G RAM G Bill",
  };

  it("follows the kind that the API sends", () => {
    expect(isHeadingTurn(heading)).toBe(true);
  });

  it("never treats a turn of another kind as a heading, also an unknown speaker with a label", () => {
    expect(isHeadingTurn({ ...heading, kind: "member", member: "A B", member_id: 5, attributed: true })).toBe(false);
    expect(isHeadingTurn({ ...heading, kind: "unattributed", label: "SHRI L.K. ADVANI", text: "How can it be permitted?" })).toBe(false);
  });

  it("shows a heading with no speaker label", () => {
    render(
      <MemoryRouter>
        <DebateTranscript speeches={mockSpeeches} turns={[heading, ...mockTurns]} people={mockPeople} tags={mockTags} />
      </MemoryRouter>
    );
    expect(screen.getByText("VB-G RAM G Bill")).toBeTruthy();
    expect(screen.queryByText("Speaker not identified")).toBeNull();
  });
});

describe("speech cards and links", () => {
  it("finds the tags that every speech carries", () => {
    const sp = [
      { tags: [{ slug: "a" }, { slug: "b" }] },
      { tags: [{ slug: "a" }] },
    ];
    expect([...commonTagSlugs(sp)]).toEqual(["a"]);
    expect(commonTagSlugs([{ tags: [{ slug: "a" }] }]).size).toBe(0);
  });

  it("reads the speech id from a hash", () => {
    expect(speechIdFromHash("#speech-178368")).toBe("178368");
    expect(speechIdFromHash("#other")).toBeNull();
  });

  it("names the card link, with no quote note and no Back to top link", () => {
    const turns = mockTurns.map((t, i) => (i === 0 ? { ...t, text: "He said ?hello world? to them" } : t));
    render(
      <MemoryRouter>
        <DebateTranscript speeches={mockSpeeches} turns={turns} people={mockPeople} tags={mockTags} />
      </MemoryRouter>
    );
    expect(screen.getAllByRole("link", { name: "Open this speech" }).length).toBe(2);
    expect(screen.queryByText(/lost some quote marks/)).toBeNull();
    expect(screen.queryByRole("link", { name: "Back to top" })).toBeNull();
  });

  it("names the button Read more, with no counts", () => {
    render(
      <MemoryRouter>
        <DebateTranscript speeches={mockSpeeches} turns={mockTurns} people={mockPeople} tags={mockTags} />
      </MemoryRouter>
    );
    expect(screen.getByRole("button", { name: "Read more" })).toBeTruthy();
  });
});
