import React from "react";
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { MemoryRouter } from "react-router-dom";
import TagRelatedTags from "../pages/tag/TagRelatedTags.jsx";

afterEach(cleanup);

const related = [
  { name: "Rare pair", slug: "rare", n: 8, lift: 237.5 },
  { name: "Common pair", slug: "common", n: 48, lift: 12 },
];

describe("TagRelatedTags order", () => {
  it("orders by shared speeches, with no switch to another order", () => {
    render(
      <MemoryRouter>
        <TagRelatedTags related={related} total={210} />
      </MemoryRouter>
    );
    const names = () => screen.getAllByRole("link").map((a) => a.textContent);
    expect(names()[0]).toContain("Common pair");
    expect(screen.queryByRole("button", { name: /Most unusual|Most shared/ })).toBeNull();
    expect(screen.getByText(/of 210 speeches with this tag/)).toBeTruthy();
  });
});
