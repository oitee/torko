import React from "react";
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import HowTorkoCounts from "../components/HowTorkoCounts.jsx";

afterEach(cleanup);

describe("HowTorkoCounts", () => {
  it("renders heading and note text", () => {
    render(
      <HowTorkoCounts>
        <p>A turn under 50 words is counted as a short remark.</p>
      </HowTorkoCounts>
    );

    expect(screen.getByText("How Torko counts")).toBeTruthy();
    expect(
      screen.getByText("A turn under 50 words is counted as a short remark.")
    ).toBeTruthy();
  });

  it("returns null when children is missing", () => {
    const { container } = render(<HowTorkoCounts />);
    expect(container.firstChild).toBeNull();
  });
});
