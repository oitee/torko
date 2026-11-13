import React from "react";
import { MemoryRouter } from "react-router-dom";
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import SearchScopeCard from "../pages/search/SearchScopeCard.jsx";

afterEach(cleanup);

describe("SearchScopeCard for a place", () => {
  it("names the place, gives its figures, and links to its page", () => {
    render(
      <MemoryRouter>
        <SearchScopeCard kind="place" value="kerala" info={{ name: "Kerala", total: 3926, n_members: 337, first: "1999-10-22", last: "2026-04-17" }} />
      </MemoryRouter>
    );
    expect(screen.getByText("337 members · 1999–2026")).toBeTruthy();
    expect(screen.getByRole("link", { name: "Open the place page →" }).getAttribute("href")).toBe("/place/kerala");
  });
});
