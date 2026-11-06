import React from "react";
import { MemoryRouter } from "react-router-dom";
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { askHref, excerptParts, headingParts, isQuestion, pageWindow, readSearch, yearSpan } from "../pages/search/searchParams.js";
import AskLine, { askAnswers } from "../pages/search/AskLine.jsx";
import { FIELDS, addFilterChanges, chipsFrom, draftChanges, draftFrom, pendingCount } from "../pages/search/filterRules.js";
import { SearchSpeechRow } from "../pages/search/SearchResults.jsx";
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

describe("questions in plain language", () => {
  it("treats three or more words, or Hindi script, as a question, and a phrase in quote marks as words", () => {
    expect(isQuestion("Kerala MPs on fishermen")).toBe(true);
    expect(isQuestion("बाढ़")).toBe(true);
    expect(isQuestion("price rise")).toBe(false);
    expect(isQuestion('"price rise in Kerala"')).toBe(false);
    expect(isQuestion("")).toBe(false);
  });

  it("builds the address of the filters and keeps the question", () => {
    const href = askHref({ params: { state: "Kerala", tag: "fishermen", q: "", view: "members", sort: "most" } }, "Kerala MPs?");
    expect(href).toBe("/search?state=Kerala&tag=fishermen&view=members&sort=most&asked=Kerala+MPs%3F");
  });

  it("allows the sort Most speeches first only in the Members view", () => {
    expect(readSearch(new URLSearchParams("tag=naxalism&view=members&sort=most")).sort).toBe("most");
    expect(readSearch(new URLSearchParams("tag=naxalism&sort=most")).sort).toBe("latest");
    expect(readSearch(new URLSearchParams("asked=x&state=Kerala")).asked).toBe("x");
  });

  it("shows the Read as line from the answer, with each dropped name", () => {
    askAnswers.set("Owaisi on triple talaq", {
      read_as: [{ key: "tag", text: "on Triple Talaq" }],
      words: "",
      dropped: [{ text: "Owaisi", why: "2 members have this name" }],
    });
    render(
      <MemoryRouter>
        <AskLine question="Owaisi on triple talaq" />
      </MemoryRouter>
    );
    expect(screen.getByText(/on Triple Talaq/)).toBeTruthy();
    expect(screen.getByText(/“Owaisi” is not a filter: 2 members have this name\./)).toBeTruthy();
    const link = screen.getByRole("link", { name: /search the words of the question instead/ });
    expect(link.getAttribute("href")).toBe("/search?q=Owaisi%20on%20triple%20talaq");
  });

  it("uses the chips when the answer is not in memory, as for a shared link", () => {
    render(
      <MemoryRouter>
        <AskLine question="shared question" chips={[{ key: "state", label: "State: Kerala" }]} />
      </MemoryRouter>
    );
    expect(screen.getByText(/State: Kerala/)).toBeTruthy();
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
    expect(screen.getByText("120 words")).toBeTruthy();
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
    // The TLDR comes before the excerpt, under the debate name.
    const tldr = container.querySelector(".search-row__tldr");
    const excerpt = container.querySelector(".search-row__excerpt");
    expect(tldr.compareDocumentPosition(excerpt) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
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
      "Tag has all of Farmers, Union Budget", "Party is INC", "Party is none of BJP, DMK", "Date is between 2014 and 2024", "Words in the speech is at least 500",
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
