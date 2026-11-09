import React from "react";
import { MemoryRouter } from "react-router-dom";
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { exactMatch, SearchTopMatch } from "../pages/search/SearchMatches.jsx";

afterEach(cleanup);

// The first answers of /api/search for "Kerala" and "Raipur" on the real database.
const kerala = [
  { kind: "place", name: "Kerala", slug: "kerala", n_speeches: 3926 },
  { kind: "tag", name: "Government of Kerala", slug: "government-of-kerala", n_speeches: 153 },
  { kind: "subject", name: "Kerala High Court", n_speeches: 71 },
];
const raipur = [
  { kind: "place", name: "Raipur", slug: "raipur", n_speeches: 232 },
  { kind: "member", name: "Ramesh Bais", id: 7, n_speeches: 40 },
];

describe("exactMatch", () => {
  it("finds the place with the same name as the words, in any case", () => {
    expect(exactMatch(kerala, " kerala ").slug).toBe("kerala");
    expect(exactMatch(raipur, "Raipur").slug).toBe("raipur");
  });

  it("finds nothing when no page has the same name", () => {
    expect(exactMatch(kerala, "Kerala High")).toBeNull();
    expect(exactMatch(kerala, "Kerala High Court")).toBeNull();
    expect(exactMatch(kerala, "")).toBeNull();
  });
});

describe("SearchTopMatch", () => {
  it("links to the place page", () => {
    render(
      <MemoryRouter>
        <SearchTopMatch results={kerala} query="Kerala" />
      </MemoryRouter>
    );
    expect(screen.getByRole("link", { name: "Open the place page for Kerala" }).getAttribute("href")).toBe("/place/kerala");
  });
});
