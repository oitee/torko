import React from "react";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter } from "react-router-dom";
import HomeHero, { groupIdeas, ideaHref } from "../pages/home/HomeHero.jsx";
import homeAnswer from "./fixtures/home/home.json";
import featuredAnswer from "./fixtures/home/home_featured.json";

afterEach(cleanup);

function renderHero(props) {
  return render(
    <MemoryRouter>
      <HomeHero {...props} />
    </MemoryRouter>
  );
}

describe("ideaHref", () => {
  it("opens the page of a place", () => {
    expect(ideaHref({ type: "place", slug: "latur" })).toBe("/place/latur");
  });

  it("opens the search for the speeches of any other tag", () => {
    expect(ideaHref({ type: "topic", slug: "arrears" })).toBe("/search?tag=arrears");
    expect(ideaHref({ type: "scheme", slug: "a-b" })).toBe("/search?tag=a-b");
  });
});

describe("HomeHero", () => {
  it("shows the date range of the corpus in the opening text", () => {
    renderHero({ corpus: homeAnswer.corpus });
    expect(screen.getByText("20 Oct 1999")).toBeTruthy();
    expect(screen.getByText("18 Apr 2026")).toBeTruthy();
  });

  it("shows each search idea as a link", () => {
    renderHero({ corpus: homeAnswer.corpus, ideas: featuredAnswer.search_ideas });
    expect(screen.getByRole("link", { name: "Latur" }).getAttribute("href")).toBe("/place/latur");
    expect(screen.getByRole("link", { name: "Arrears" }).getAttribute("href")).toBe("/search?tag=arrears");
    expect(screen.getByRole("link", { name: "Gaya" }).getAttribute("href")).toBe("/place/gaya");
  });

  it("hides the ideas row when there are no ideas", () => {
    renderHero({ corpus: homeAnswer.corpus, ideas: [] });
    expect(screen.queryByText("Try")).toBeNull();
  });

  it("shows the loading state while the corpus loads", () => {
    renderHero({});
    expect(screen.getByRole("status")).toBeTruthy();
    expect(screen.getByRole("search")).toBeTruthy();
  });

  it("shows the error state and retries the corpus", () => {
    const retry = vi.fn();
    renderHero({ corpusError: { status: 500, message: "The server could not answer. Try again." }, onRetryCorpus: retry });
    fireEvent.click(screen.getByRole("button", { name: "Try again" }));
    expect(retry).toHaveBeenCalledTimes(1);
  });

  it("shows the static opening text before the corpus loads, and the dates when it arrives", () => {
    const { container, rerender } = renderHero({});
    expect(container.querySelector(".home-hero__lede").textContent).toContain(
      "Torko reads the Lok Sabha debates on sansad.in. It finds the member who spoke each turn"
    );
    expect(screen.queryByText("20 Oct 1999")).toBeNull();
    rerender(
      <MemoryRouter>
        <HomeHero corpus={homeAnswer.corpus} />
      </MemoryRouter>
    );
    expect(container.querySelector(".home-hero__lede").textContent).toContain("sansad.in from 20 Oct 1999 to 18 Apr 2026.");
  });

  it("links to the page that finds an MP, in the text and on the marked seat", () => {
    renderHero({ corpus: homeAnswer.corpus });
    expect(screen.getByRole("link", { name: "Find your MP by the name of your seat" }).getAttribute("href")).toBe("/my-mp");
    expect(screen.getByRole("link", { name: "Find your MP: the marked seat" }).getAttribute("href")).toBe("/my-mp");
  });

  it("groups the search ideas by kind", () => {
    renderHero({ corpus: homeAnswer.corpus, ideas: featuredAnswer.search_ideas });
    expect(screen.getByRole("group", { name: "Places" }).textContent).toContain("Latur");
    expect(screen.getByRole("group", { name: "Places" }).textContent).toContain("Gaya");
    expect(screen.getByRole("group", { name: "Schemes" }).textContent).toContain("MNREGA");
    expect(screen.getByRole("group", { name: "Topics" }).textContent).toContain("Arrears");
  });
});

describe("groupIdeas", () => {
  it("keeps the order of the answer for the groups and for the ideas in a group", () => {
    const groups = groupIdeas([
      { name: "B", slug: "b", type: "topic" },
      { name: "A", slug: "a", type: "place" },
      { name: "C", slug: "c", type: "topic" },
    ]);
    expect(groups.map((g) => g.kind)).toEqual(["topic", "place"]);
    expect(groups[0].ideas.map((i) => i.name)).toEqual(["B", "C"]);
  });

  it("names an unknown kind with its own word", () => {
    expect(groupIdeas([{ name: "X", slug: "x", type: "bill" }])[0].label).toBe("Bill");
    expect(groupIdeas(undefined)).toEqual([]);
  });
});
