import React from "react";
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { MemoryRouter } from "react-router-dom";
import HomeQuote, { MAX_QUOTE_TAGS, pickQuoteTags } from "../pages/home/HomeQuote.jsx";
import featuredAnswer from "./fixtures/home/home_featured.json";

afterEach(cleanup);

const quote = featuredAnswer.quote;

function renderQuote(q) {
  return render(
    <MemoryRouter>
      <HomeQuote quote={q} />
    </MemoryRouter>
  );
}

describe("pickQuoteTags", () => {
  it("takes the topic and scheme tags first, in the order of the answer", () => {
    expect(pickQuoteTags(quote.tags).map((t) => t.name)).toEqual([
      "Arrears",
      "Centrally Sponsored Schemes",
      "Mahatma Gandhi National Rural Employment Guarantee Act (MNREGA)",
    ]);
  });

  it("fills the free places with the other tags, in the order of the answer", () => {
    const tags = [
      { name: "A", type: "institution" },
      { name: "B", type: "topic" },
      { name: "C", type: "place" },
    ];
    expect(pickQuoteTags(tags).map((t) => t.name)).toEqual(["B", "A", "C"]);
  });

  it("never gives more than the limit", () => {
    expect(MAX_QUOTE_TAGS).toBe(3);
    expect(pickQuoteTags(quote.tags)).toHaveLength(3);
    expect(pickQuoteTags([])).toEqual([]);
    expect(pickQuoteTags(undefined)).toEqual([]);
  });
});

describe("HomeQuote", () => {
  it("shows the exact words in curly quotes, with the member and the date", () => {
    renderQuote(quote);
    expect(screen.getByText(`“${quote.text}”`)).toBeTruthy();
    expect(screen.getByRole("link", { name: "Mahua Moitra" }).getAttribute("href")).toBe("/member/1052");
    expect(screen.getByText("17 Dec 2025")).toBeTruthy();
  });

  it("shows the chosen tags as links, with the count of all tags of the speech", () => {
    renderQuote(quote);
    expect(screen.getByRole("link", { name: "Arrears" }).getAttribute("href")).toBe("/tag/arrears");
    expect(screen.queryByRole("link", { name: "Supreme Court" })).toBeNull();
    expect(screen.getByText("3 of 13 tags of this speech")).toBeTruthy();
  });

  it("links a place tag to its place page", () => {
    renderQuote({ ...quote, tags: [{ name: "Delhi", slug: "delhi", type: "place" }] });
    expect(screen.getByRole("link", { name: "Delhi" }).getAttribute("href")).toBe("/place/delhi");
    expect(screen.getByText("1 of 1 tags of this speech")).toBeTruthy();
  });

  it("hides the tag row when the speech has no tags", () => {
    renderQuote({ ...quote, tags: [] });
    expect(screen.queryByText(/tags of this speech/)).toBeNull();
  });

  it("links to the whole speech", () => {
    renderQuote(quote);
    expect(
      screen.getByRole("link", { name: "Read the full speech by Mahua Moitra (17 Dec 2025)" }).getAttribute("href")
    ).toBe("/speech/178379");
  });

  it("names the term next to the date, and links the source page on sansad.in", () => {
    const { container } = renderQuote(quote);
    expect(container.querySelector(".home-quote__meta").textContent).toContain("17 Dec 2025 · 18th Lok Sabha · ");
    expect(screen.getByRole("link", { name: "Source on sansad.in" }).getAttribute("href")).toBe(quote.source_url);
  });

  it("leaves out the source link when the answer has none", () => {
    renderQuote({ ...quote, source_url: null });
    expect(screen.queryByRole("link", { name: "Source on sansad.in" })).toBeNull();
  });

  it("links the count of tags to the speech, where all tags show", () => {
    renderQuote(quote);
    expect(screen.getByRole("link", { name: "See all 13 tags" }).getAttribute("href")).toBe("/speech/178379");
  });

  it("shows no link to more tags when the chips show all of them", () => {
    renderQuote({ ...quote, tags: quote.tags.slice(0, 2) });
    expect(screen.queryByRole("link", { name: /See all/ })).toBeNull();
  });
});
