import React from "react";
import { act, cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { RouterProvider, createMemoryRouter } from "react-router-dom";
import * as api from "../assets/js/api.js";
import Search from "../pages/search.jsx";

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

const LATEST = { total: 3, page: 1, per_page: 20, speeches: [], facets: {}, members_total: 2 };
const TAGS = { total: 3, facets: { tag: [{ slug: "farmers", tag: "Farmers", n: 9 }] } };

// The API: the words "slow" wait for a promise that the test resolves. Every other call answers at once.
function mockApi(slow) {
  vi.spyOn(api, "getJSON").mockImplementation((path, params = {}) => {
    if (path === "/api/home") return Promise.resolve({ corpus: { members: 2, first: "1999-10-20", last: "2026-04-18" } });
    if (path === "/api/search") return Promise.resolve({ results: [] });
    if (params.q === "slow" && !params.facets && !params.group && params.per_page !== 1) return slow;
    if (params.facets === "tag") return Promise.resolve(TAGS);
    if (params.group === "member") return Promise.resolve({ total: 3, members: [{ id: 392, name: "Priya Ranjan Dasmunsi" }], members_total: 2 });
    return Promise.resolve(LATEST);
  });
}

function renderAt(path) {
  const router = createMemoryRouter([{ path: "/search", element: <Search /> }], { initialEntries: [path] });
  render(<RouterProvider router={router} />);
  return router;
}

describe("Search landing", () => {
  it("shows a large box and suggested searches, with no filter panel", async () => {
    mockApi();
    renderAt("/search");
    expect(screen.getByRole("heading", { level: 1, name: "Search the speeches of the Lok Sabha" })).toBeTruthy();
    expect((await screen.findByRole("link", { name: "Constitution" })).getAttribute("href")).toBe("/search?tag=constitution");
    // A suggestion can carry two or three filters.
    expect(screen.getByRole("link", { name: "Farmers, 17th Lok Sabha, INC" }).getAttribute("href")).toBe("/search?tag=farmers&term=17&party=INC");
    expect(screen.getByRole("list", { name: "Suggested searches" })).toBeTruthy();
    expect(screen.queryByRole("button", { name: /Add filter/ })).toBeNull();
    expect(document.getElementById("latest-speeches")).toBeTruthy();
  });

  it("keeps the landing view until the results of a new search arrive, then shows the results view", async () => {
    let resolve;
    const slow = new Promise((r) => {
      resolve = r;
    });
    mockApi(slow);
    const router = renderAt("/search");
    await screen.findByRole("list", { name: "Suggested searches" });
    await act(async () => {
      await router.navigate("/search?q=slow");
    });
    expect(screen.getByRole("status").textContent).toBe("Searching…");
    expect(screen.queryByRole("button", { name: /Add filter/ })).toBeNull();
    await act(async () => {
      resolve({ ...LATEST, total: 1 });
    });
    expect(await screen.findByRole("button", { name: /Add filter/ })).toBeTruthy();
  });

  it("opens an old question link as a word search", async () => {
    mockApi();
    renderAt("/search?ask=what%20did%20members%20say");
    expect(await screen.findByRole("button", { name: /Add filter/ })).toBeTruthy();
    expect(document.querySelector("input[type=search]").value).toBe("what did members say");
  });

  it("shows a card for each place and tag that the words name", async () => {
    mockApi();
    const real = api.getJSON.getMockImplementation();
    api.getJSON.mockImplementation((path, params) => {
      if (path === "/api/search")
        return Promise.resolve({ results: [], named: [{ kind: "place", slug: "raipur", name: "Raipur" }, { kind: "tag", slug: "corruption", name: "Corruption" }] });
      if (path === "/api/place/raipur") return Promise.resolve({ name: "Raipur", total: 232, n_members: 84, first: "1999-10-22", last: "2026-04-17" });
      if (path === "/api/tag/corruption") return Promise.resolve({ name: "Corruption", total: 1302, n_members: 492, first: "1999-10-22", last: "2026-03-24" });
      return real(path, params);
    });
    renderAt("/search?q=raipur%20corruption");
    expect((await screen.findByRole("link", { name: "Open the place page →" })).getAttribute("href")).toBe("/place/raipur");
    expect(screen.getByRole("link", { name: "Open the tag page →" }).getAttribute("href")).toBe("/tag/corruption");
    expect(document.querySelectorAll(".search-scopes--named .search-scope").length).toBe(2);
  });

  it("opens the results view at once for a direct link to a search", () => {
    mockApi(new Promise(() => {}));
    renderAt("/search?q=slow");
    expect(screen.queryByRole("list", { name: "Suggested searches" })).toBeNull();
  });
});
