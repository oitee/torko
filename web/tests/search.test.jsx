import React from "react";
import { MemoryRouter } from "react-router-dom";
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { citationText, excerptParts, headingParts, pageWindow, readSearch, yearSpan } from "../pages/search/searchParams.js";
import { FIELDS, addFilterChanges, chipsFrom, draftChanges, draftFrom, pendingCount } from "../pages/search/filterRules.js";
import SearchResults, { SearchSpeechRow } from "../pages/search/SearchResults.jsx";
import StartBlock, { dataLine, startExamples } from "../pages/search/StartBlock.jsx";
import SearchMatches from "../pages/search/SearchMatches.jsx";

afterEach(cleanup);

describe("search address", () => {
  it("reads the scope, filters, view, sort and page, with defaults", () => {
    const out = readSearch(new URLSearchParams("q=arrears&term=17&party_not=BJP&view=members&sort=bad&page=x"));
    expect(out.scope).toEqual({ q: "arrears" });
    expect(out.filters).toEqual({ term: "17", party_not: "BJP" });
    expect(out.view).toBe("members");
    expect(out.sort).toBe("best");
    expect(readSearch(new URLSearchParams("tag=arrears&sort=best")).sort).toBe("latest");
    expect(readSearch(new URLSearchParams('q="triple talaq"')).sort).toBe("latest");
    expect(out.page).toBe(1);
  });
});

describe("old question links", () => {
  it("reads an old ?ask= link as a word search", () => {
    expect(readSearch(new URLSearchParams("ask=corruption by government officials")).scope).toEqual({ q: "corruption by government officials" });
    expect(readSearch(new URLSearchParams("q=water&ask=other")).scope).toEqual({ q: "water" });
  });

  it("allows the sort Most speeches first only in the Members view", () => {
    expect(readSearch(new URLSearchParams("tag=naxalism&view=members&sort=most")).sort).toBe("most");
    expect(readSearch(new URLSearchParams("tag=naxalism&sort=most")).sort).toBe("latest");
  });
});

describe("search heading", () => {
  it("puts the count first and agrees in number", () => {
    expect(headingParts({ scope: { q: "arrears" }, count: 375 })).toEqual({ lead: 375, rest: " speeches match “arrears”" });
    expect(headingParts({ scope: { q: "sugar cane" }, count: 1 }).rest).toBe(" speech matches “sugar cane”");
    expect(headingParts({ scope: { q: '"sugar cane"' }, count: 2 }).rest).toBe(" speeches use the exact words “sugar cane”");
    expect(headingParts({ scope: { tag: "arrears" }, count: 205, names: { tag: "Arrears" } }).rest).toBe(" speeches on Arrears");
    expect(headingParts({ scope: { tag: "a,b" }, count: 4, names: { tag: "Coastal Erosion and Cyclone Relief" } }).rest).toBe(" speeches on Coastal Erosion and Cyclone Relief");
    expect(headingParts({ scope: { tag: "a,b" }, count: 0, members: 16, names: { tag: "Sea Erosion and Cyclone Relief" } })).toEqual({ lead: 16, rest: " members raised Sea Erosion and Cyclone Relief" });
    expect(headingParts({ scope: { tag: "farmers", member: "1288" }, count: 3, names: { tag: "Farmers", member: "Shivraj V. Patil" } }).rest).toBe(" speeches on Farmers by Shivraj V. Patil");
    expect(headingParts({ scope: { q: "xqzvwk" }, count: 0 }).rest).toBe("No speech matches “xqzvwk”");
    expect(headingParts({ scope: {}, count: 10 }).rest).toBe("Search the speeches of the Lok Sabha");
    expect(headingParts({ scope: { q: "arrears" }, count: null })).toEqual({ lead: null, rest: "Speeches for “arrears”" });
  });
});

describe("excerpt window", () => {
  it("marks the words, cuts around the first mark and joins white space", () => {
    const text = `${"word ".repeat(60)}the wage\n\narrears were paid ${"late ".repeat(60)}`;
    const at = text.indexOf("arrears");
    const { parts, cutStart, cutEnd } = excerptParts(text, [[at, at + 7]]);
    expect(cutStart).toBe(true);
    expect(cutEnd).toBe(true);
    expect(parts.find((p) => p.mark).text).toBe("arrears");
    expect(parts.map((p) => p.text).join("")).toContain("the wage arrears were paid");
  });

  it("keeps a short excerpt whole and ignores bad marks", () => {
    const out = excerptParts("Pay the arrears.", [[8, 15], [40, 50]]);
    expect(out.cutStart).toBe(false);
    expect(out.cutEnd).toBe(false);
    expect(out.parts).toEqual([{ text: "Pay the ", mark: false }, { text: "arrears", mark: true }, { text: ".", mark: false }]);
    expect(excerptParts(null, null).parts).toEqual([]);
  });
});

describe("small helpers", () => {
  it("makes year spans and page windows", () => {
    expect(yearSpan("2004-01-01", "2024-05-01")).toBe("2004–2024");
    expect(yearSpan("2026-02-03", "2026-02-03")).toBe("2026");
    expect(pageWindow(1, 3)).toEqual([1, 2, 3]);
    expect(pageWindow(10, 20)).toEqual([1, null, 8, 9, 10, 11, 12, null, 20]);
  });
});

describe("search rows", () => {
  it("shows the marked word and Speaker not identified", () => {
    render(
      <MemoryRouter>
        <ul>
          <SearchSpeechRow speech={{ id: 1, date: "2024-03-12", term: 17, debate: "Budget", excerpt: "Pay the arrears.", marks: [[8, 15]], words: 120 }} />
        </ul>
      </MemoryRouter>
    );
    expect(screen.getByText("arrears").tagName).toBe("MARK");
    expect(screen.getByText("Speaker not identified")).toBeTruthy();
    expect(screen.getByText(/· 120 words$/)).toBeTruthy();
  });

  it("shows the TLDR and the marked words together in a word search", () => {
    const { container } = render(
      <MemoryRouter>
        <ul>
          <SearchSpeechRow
            speech={{ id: 2, date: "2025-02-01", term: 18, debate: "Budget", words: 900,
              summary: "Criticises the Budget for its lack of jobs.",
              excerpt: "This is a Budget that seems more like a Bollywood film.", marks: [[40, 49]] }}
          />
        </ul>
      </MemoryRouter>
    );
    expect(screen.getByText("Criticises the Budget for its lack of jobs.")).toBeTruthy();
    expect(screen.getByText("Bollywood").tagName).toBe("MARK");
    // The words of the member come before the TLDR.
    const tldr = container.querySelector(".search-row__tldr");
    const excerpt = container.querySelector(".search-row__excerpt");
    expect(excerpt.compareDocumentPosition(tldr) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  it("shows the TLDR alone in a search with no words, such as a tag", () => {
    const { container } = render(
      <MemoryRouter>
        <ul>
          <SearchSpeechRow speech={{ id: 3, date: "2025-02-01", term: 18, debate: "Finance Bill", summary: "Supports the Finance Bill." }} />
        </ul>
      </MemoryRouter>
    );
    expect(screen.getByText("Supports the Finance Bill.")).toBeTruthy();
    expect(container.querySelector(".search-row__excerpt")).toBeNull();
  });

  it("links tags and places, and a subject to its parent tag", () => {
    render(
      <MemoryRouter>
        <SearchMatches
          query="latur"
          results={[
            { kind: "place", name: "Latur", slug: "latur", state: "Maharashtra", n_speeches: 132 },
            { kind: "subject", name: "Latur Rail Coach Factory", parent_tag: "Railway Coach Factories", parent_tag_slug: "railway-coach-factories", n_speeches: 3 },
          ]}
        />
      </MemoryRouter>
    );
    expect(screen.getByRole("link", { name: "Latur" }).getAttribute("href")).toBe("/place/latur");
    expect(screen.queryByRole("link", { name: "Latur Rail Coach Factory" })).toBeNull();
    expect(screen.getByRole("link", { name: "Railway Coach Factories" }).getAttribute("href")).toBe("/search?tag=railway-coach-factories");
  });
});

describe("filter rules", () => {
  it("writes each operator to its own address key, and moves a value out of the opposite list", () => {
    expect(addFilterChanges({ party: "INC" }, "party", "one_of", { values: ["BJP"] })).toEqual({ party: "INC,BJP" });
    expect(addFilterChanges({ party: "INC,BJP" }, "party", "not", { values: ["BJP"] })).toEqual({ party: "INC", party_not: "BJP" });
    expect(addFilterChanges({}, "tag", "one_of", { values: ["a", "b"] })).toEqual({ tag_any: "a,b" });
    expect(addFilterChanges({ tag_any: "a" }, "tag", "is", { values: ["a"] })).toEqual({ tag_any: null, tag: "a" });
  });

  it("offers only fields that can show a list", () => {
    expect(FIELDS.map((f) => f.label)).toEqual(["Member", "Party", "State", "Term", "Session", "Tag", "Subject", "Place", "Debate type"]);
    expect(chipsFrom({ seat: "Kota", lang_not: "hi" }).map((c) => c.label)).toEqual(["Seat is Kota", "Spoken in is not Hindi"]);
  });

  it("makes one chip for each field and operator", () => {
    const labels = chipsFrom({ tag: "a,b", party: "INC", party_not: "BJP,DMK", date_from: "2014-01-01", date_to: "2024-12-31", min_words: "500" }, { slug: { a: "Farmers", b: "Union Budget" } });
    expect(labels.map((c) => c.label)).toEqual([
      "Tag is Farmers, Union Budget", "Party is INC", "Party is none of BJP, DMK", "Date is between 2014 and 2024", "Words in the speech is at least 500",
    ]);
    expect(labels[2].negative).toBe(true);
    expect(chipsFrom({ party: "A,B,C,D" })[0].label).toBe("Party is one of A, B +2");
  });

  it("counts the waiting changes, and turns them into address changes", () => {
    const params = { party: "INC", term: "17" };
    const draft = { ...draftFrom(params), party: ["BJP"], years: [2014, 2026] };
    expect(pendingCount(draftFrom(params), params)).toBe(0);
    expect(pendingCount(draft, params)).toBe(3);
    expect(draftChanges(draft)).toEqual({ tag: null, party: "BJP", term: "17", date_from: "2014-01-01", date_to: null });
  });
});

const SPEECH = {
  id: 293051, date: "2024-12-05", term: 18, kind_label: "Rule 377", words: 190, member: "Balabhadra Majhi", party: "BJP", seat: "Nabarangpur",
  debate: "Need to ensure daily payment of wages under MGNREGA-laid", source_url: "https://sansad.in/ls/debates/view-debate?ls=18",
  excerpt: "Payment under MGNREGA is delayed .", marks: [[14, 21]],
  tags: [1, 2, 3, 4, 5].map((n) => ({ name: `Tag ${n}`, slug: `tag-${n}` })),
};

describe("search row details", () => {
  it("puts the words in the meta line, tidies the title and removes the space before a full stop", () => {
    const { container } = render(<MemoryRouter><ul><SearchSpeechRow speech={SPEECH} /></ul></MemoryRouter>);
    expect(container.querySelector(".search-row__meta").textContent).toBe("2024-12-05 · 18th LS · Rule 377 · 190 words");
    const title = screen.getByRole("link", { name: "Need to ensure daily payment of wages under MGNREGA" });
    expect(title.getAttribute("title")).toBe("Need to ensure daily payment of wages under MGNREGA");
    expect(container.querySelector(".search-row__excerpt").textContent).toBe("“Payment under MGNREGA is delayed.”");
  });

  it("shows 3 tags as links that keep nothing else, and counts the rest", () => {
    render(<MemoryRouter><ul><SearchSpeechRow speech={SPEECH} /></ul></MemoryRouter>);
    expect(screen.getByRole("link", { name: "Tag 2" }).getAttribute("href")).toBe("/search?tag=tag-2");
    expect(screen.queryByRole("link", { name: "Tag 4" })).toBeNull();
    expect(screen.getByText("+2 more")).toBeTruthy();
  });

  it("links to sansad.in and copies one line of citation for 2 seconds", async () => {
    vi.useFakeTimers();
    const writeText = vi.fn().mockResolvedValue();
    Object.defineProperty(navigator, "clipboard", { value: { writeText }, configurable: true });
    render(<MemoryRouter><ul><SearchSpeechRow speech={SPEECH} /></ul></MemoryRouter>);
    expect(screen.getByRole("link", { name: "Open on sansad.in" }).getAttribute("href")).toBe(SPEECH.source_url);
    await act(async () => { fireEvent.click(screen.getByRole("button", { name: "Copy citation" })); });
    expect(writeText).toHaveBeenCalledWith(
      `\u201cPayment under MGNREGA is delayed.\u201d - Balabhadra Majhi, BJP, Nabarangpur, Lok Sabha, 2024-12-05. Torko: ${window.location.origin}/speech/293051`
    );
    expect(screen.getByRole("button", { name: "Copied" })).toBeTruthy();
    await act(async () => { vi.advanceTimersByTime(2100); });
    expect(screen.getByRole("button", { name: "Copy citation" })).toBeTruthy();
    vi.useRealTimers();
  });

  it("cites the summary when there is no excerpt, and a speaker who is not identified", () => {
    expect(citationText({ id: 5, date: "2020-01-02", summary: "Supports the Bill." }, "https://torko.in")).toBe(
      "\u201cSupports the Bill.\u201d - Speaker not identified, Lok Sabha, 2020-01-02. Torko: https://torko.in/speech/5"
    );
  });
});

describe("rows of the same debate", () => {
  const rows = [
    { id: 1, date: "2026-04-01", debate: "The Delimitation Bill?Contd..", member: "A", words: 10 },
    { id: 2, date: "2026-04-01", debate: "The Delimitation Bill?Contd..", member: "B", words: 20 },
    { id: 3, date: "2026-04-01", debate: "Other debate", member: "C", words: 30 },
  ];
  it("shows the title on every row, also when two rows share a debate", () => {
    render(
      <MemoryRouter>
        <SearchResults view="speeches" sort="latest" page={1} data={{ speeches: rows, total: 3, pages: 1, per_page: 20 }} loading={false}
          speechTotal={3} membersTotal={null} viewHref={() => "/search"} pageHref={() => "/search"} memberHref={() => "/"} onSort={() => {}} />
      </MemoryRouter>
    );
    expect(screen.getAllByText("The Delimitation Bill (contd.)")).toHaveLength(2);
    expect(screen.queryByText("Same debate")).toBeNull();
    expect(screen.getByText("Other debate")).toBeTruthy();
  });
});

describe("empty page start block", () => {
  const tagRows = [
    { slug: "farmers", tag: "Farmers", n: 17143 }, { slug: "railway-connectivity", tag: "Railway Connectivity", n: 7532 },
    { slug: "constitution", tag: "Constitution", n: 6676 }, { slug: "a", tag: "A", n: 5 }, { slug: "b", tag: "B", n: 4 }, { slug: "c", tag: "C", n: 3 },
    { slug: "d", tag: "Union Budget", n: 2 },
  ];
  it("builds the data line from the counts", () => {
    expect(dataLine({ total: 173225, members: 2165, first: "1999-10-20", last: "2026-04-18" })).toBe("173,225 speeches by 2,165 members, 1999 to 2026");
    expect(dataLine({ total: 5 })).toBe("5 speeches");
  });
  it("picks the examples by rule from the facets", () => {
    const ex = startExamples({ tagRows, topMember: { id: 7, name: "Om Birla", n: 956 } });
    expect(ex.map((e) => e.key)).toEqual(["tag-farmers", "tag-railway-connectivity", "tag-constitution", "tag-a", "tag-b", "phrase", "member"]);
    expect(ex[5].to).toBe("/search?q=%22Union%20Budget%22");
    expect(ex[6].to).toBe("/search?member=7");
  });
  it("shows the line, the example links and the terms", () => {
    render(
      <MemoryRouter>
        <StartBlock total={173225} members={2165} first="1999-10-20" last="2026-04-18" tagRows={tagRows}
          topMember={{ id: 7, name: "Om Birla", n: 956 }} termRows={[{ term: 17, n: 29891 }, { term: 18, n: 12676 }]} />
      </MemoryRouter>
    );
    expect(screen.getByText("173,225 speeches by 2,165 members, 1999 to 2026")).toBeTruthy();
    expect(screen.getByRole("link", { name: "Farmers" }).getAttribute("href")).toBe("/search?tag=farmers");
    expect(screen.getByRole("link", { name: "18th Lok Sabha" }).getAttribute("href")).toBe("/search?term=18");
    const terms = screen.getAllByRole("link", { name: /Lok Sabha$/ }).map((a) => a.textContent);
    expect(terms).toEqual(["18th Lok Sabha", "17th Lok Sabha"]);
  });
});
