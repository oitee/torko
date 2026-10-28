import React from "react";
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import TLDR from "../components/TLDR.jsx";

afterEach(cleanup);

describe("TLDR", () => {
  it("renders the label and summary text", () => {
    render(<TLDR text="The member spoke about rural employment." />);

    expect(screen.getByText("TLDR")).toBeTruthy();
    expect(
      screen.getByText("The member spoke about rural employment.")
    ).toBeTruthy();
  });

  it("returns null when text is missing or blank", () => {
    const { container: empty } = render(<TLDR text="" />);
    expect(empty.firstChild).toBeNull();

    const { container: missing } = render(<TLDR />);
    expect(missing.firstChild).toBeNull();

    const { container: spaces } = render(<TLDR text="   " />);
    expect(spaces.firstChild).toBeNull();
  });
});
