import React from "react";
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { MemoryRouter } from "react-router-dom";
import TagRelatedTags from "../pages/tag/TagRelatedTags.jsx";

afterEach(cleanup);

describe("TagRelatedTags component", () => {
  const mockRelated = [
    { name: "Farmers", slug: "farmers", n: 70 },
    { name: "Farmers' Grievances", slug: "farmers-grievances", n: 54 },
    { name: "Sugar", slug: "sugar", speeches_shared: 47 },
  ];

  it("renders related tag chips with links and counts", () => {
    render(
      <MemoryRouter>
        <TagRelatedTags related={mockRelated} />
      </MemoryRouter>
    );

    expect(screen.getByRole("heading", { name: "Related tags" })).toBeTruthy();

    const chip1 = screen.getByRole("link", { name: /Farmers 70/ });
    expect(chip1.getAttribute("href")).toBe("/tag/farmers");

    const chip2 = screen.getByRole("link", { name: /Farmers' Grievances 54/ });
    expect(chip2.getAttribute("href")).toBe("/tag/farmers-grievances");

    const chip3 = screen.getByRole("link", { name: /Sugar 47/ });
    expect(chip3.getAttribute("href")).toBe("/tag/sugar");
  });

  it("limits related chips to at most 12", () => {
    const manyTags = Array.from({ length: 20 }, (_, i) => ({
      name: `Tag ${i}`,
      slug: `tag-${i}`,
      n: i + 1,
    }));

    render(
      <MemoryRouter>
        <TagRelatedTags related={manyTags} />
      </MemoryRouter>
    );

    const chips = screen.getAllByRole("link");
    expect(chips.length).toBe(12);
  });

  it("returns null when related is empty", () => {
    const { container } = render(<TagRelatedTags related={[]} />);
    expect(container.firstChild).toBeNull();
  });
});
