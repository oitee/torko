import React from "react";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import Margin from "../components/Margin.jsx";

afterEach(cleanup);

describe("Margin", () => {
  it("renders content and toggle button", () => {
    render(
      <Margin>
        <p>Margin content here.</p>
      </Margin>
    );

    expect(screen.getByText("Margin content here.")).toBeTruthy();

    const button = screen.getByRole("button", { name: "Counts and method +" });
    expect(button.getAttribute("aria-expanded")).toBe("false");

    fireEvent.click(button);
    expect(button.getAttribute("aria-expanded")).toBe("true");
    expect(screen.getByText("−")).toBeTruthy();
  });

  it("supports custom label prop", () => {
    render(
      <Margin label="Filter details">
        <div>Custom content</div>
      </Margin>
    );

    const button = screen.getByRole("button", { name: "Filter details +" });
    expect(button).toBeTruthy();
  });

  it("returns null when children is missing", () => {
    const { container } = render(<Margin />);
    expect(container.firstChild).toBeNull();
  });
});
