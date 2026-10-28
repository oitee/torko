import React from "react";
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { MemoryRouter } from "react-router-dom";
import TagMembersList from "../pages/tag/TagMembersList.jsx";

afterEach(cleanup);

describe("TagMembersList component", () => {
  const mockMembers = [
    {
      id: 844,
      name: "Kunwar Danish Ali",
      party: "BSP",
      seat: "Amroha",
      first: "2019-07-29",
      last: "2022-08-05",
      n: 8,
    },
    {
      id: 1168,
      name: "Jagdambika Pal",
      party: "BJP",
      seat: "Domariyaganj",
      first: "2014-08-07",
      last: "2018-01-04",
      n: 6,
    },
  ];

  it("renders numbered members with links, party, seat, span, and count", () => {
    render(
      <MemoryRouter>
        <TagMembersList members={mockMembers} selectedTerm="17" />
      </MemoryRouter>
    );

    expect(screen.getByRole("heading", { name: "Who spoke" })).toBeTruthy();
    expect(screen.getByText("most speeches · 17th Lok Sabha")).toBeTruthy();

    const link1 = screen.getByRole("link", { name: /Kunwar Danish Ali/ });
    expect(link1.getAttribute("href")).toBe("/member/844");
    expect(screen.getByText("BSP · Amroha · 2019–2022")).toBeTruthy();
    expect(screen.getByText("8")).toBeTruthy();

    const link2 = screen.getByRole("link", { name: /Jagdambika Pal/ });
    expect(link2.getAttribute("href")).toBe("/member/1168");
    expect(screen.getByText("BJP · Domariyaganj · 2014–2018")).toBeTruthy();
    expect(screen.getByText("6")).toBeTruthy();

    expect(
      screen.getByText("Members with 3 or more speeches on this tag.")
    ).toBeTruthy();
  });

  it("shows empty message when members array is empty", () => {
    render(
      <MemoryRouter>
        <TagMembersList members={[]} selectedTerm="" />
      </MemoryRouter>
    );

    expect(
      screen.getByText("No sample members for this term yet.")
    ).toBeTruthy();
  });
});
