import React from "react";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import DebateDiscussed from "../pages/debate/DebateDiscussed.jsx";

afterEach(cleanup);

describe("DebateDiscussed", () => {
  const sampleTags = [
    { name: "Rural Development", slug: "rural-development", speeches: 15 },
    { name: "PMAY-G Housing", slug: "pmay-g-housing", speeches: 8 },
  ];

  it("renders heading, top tag answer, and tag chips with counts", () => {
    const onSelect = vi.fn();
    render(
      <DebateDiscussed
        tags={sampleTags}
        speechesCount={20}
        selectedTagSlug="rural-development"
        onSelectTag={onSelect}
      />
    );

    expect(screen.getByRole("heading", { name: "What was discussed" })).toBeTruthy();
    expect(
      screen.getByText(
        "Rural Development comes up most, in 15 of 20 speeches. Pick a tag to filter the debate below."
      )
    ).toBeTruthy();

    const selectedChip = screen.getByRole("button", { name: /Rural Development 15/ });
    expect(selectedChip.getAttribute("aria-pressed")).toBe("true");

    const otherChip = screen.getByRole("button", { name: /PMAY-G Housing 8/ });
    expect(otherChip.getAttribute("aria-pressed")).toBe("false");

    fireEvent.click(otherChip);
    expect(onSelect).toHaveBeenCalledWith("pmay-g-housing");

    // Clicking already selected tag toggles it off
    fireEvent.click(selectedChip);
    expect(onSelect).toHaveBeenCalledWith(null);
  });

  it("limits to 12 chips initially and shows Show all button when more than 12", () => {
    const manyTags = Array.from({ length: 15 }, (_, i) => ({
      name: `Tag ${i + 1}`,
      slug: `tag-${i + 1}`,
      speeches: 20 - i,
    }));

    render(
      <DebateDiscussed
        tags={manyTags}
        speechesCount={50}
        onSelectTag={() => {}}
      />
    );

    expect(screen.getByRole("button", { name: "Show all 15 tags" })).toBeTruthy();
    expect(screen.getAllByRole("button").length).toBe(13); // 12 chips + 1 show all

    fireEvent.click(screen.getByRole("button", { name: "Show all 15 tags" }));
    expect(screen.getAllByRole("button").length).toBe(15);
  });
});
