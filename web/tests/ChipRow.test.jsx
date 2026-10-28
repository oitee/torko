import React from "react";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { MemoryRouter } from "react-router-dom";
import ChipRow from "../components/ChipRow.jsx";

afterEach(cleanup);

describe("ChipRow", () => {
  it("renders a list of chips up to max", () => {
    const tags = [
      { name: "Tag 1", slug: "tag-1" },
      { name: "Tag 2", slug: "tag-2" },
      { name: "Tag 3", slug: "tag-3" },
    ];

    render(
      <MemoryRouter>
        <ChipRow tags={tags} max={8} />
      </MemoryRouter>
    );

    expect(screen.getByText("Tag 1")).toBeTruthy();
    expect(screen.getByText("Tag 2")).toBeTruthy();
    expect(screen.getByText("Tag 3")).toBeTruthy();
    expect(screen.queryByText(/Show all/)).toBeNull();
  });

  it("collapses tags exceeding max and reveals them on click", () => {
    const tags = Array.from({ length: 10 }, (_, i) => ({
      name: `Tag ${i + 1}`,
      slug: `tag-${i + 1}`,
    }));

    render(
      <MemoryRouter>
        <ChipRow tags={tags} max={8} />
      </MemoryRouter>
    );

    expect(screen.getByText("Tag 1")).toBeTruthy();
    expect(screen.getByText("Tag 8")).toBeTruthy();
    expect(screen.queryByText("Tag 9")).toBeNull();

    const button = screen.getByRole("button", { name: "Show all 10 tags" });
    expect(button).toBeTruthy();

    fireEvent.click(button);

    expect(screen.getByText("Tag 9")).toBeTruthy();
    expect(screen.getByText("Tag 10")).toBeTruthy();
    expect(screen.queryByRole("button", { name: /Show all/ })).toBeNull();
  });

  it("returns null when tags is empty or omitted", () => {
    const { container: empty } = render(<ChipRow tags={[]} />);
    expect(empty.firstChild).toBeNull();

    const { container: omitted } = render(<ChipRow />);
    expect(omitted.firstChild).toBeNull();
  });
});
